from copy import deepcopy
import json

import pytest

from advisor import AdvisorConfig, PRESETS, resolve_advisor, score_from_components
import persona_mlds
from persona_mlds import (
    MLDSError, PERSONAS_DIR, advisor_from_mlds, advisor_to_mlds,
    load_neutral_advisor, load_templates, personality_schema,
)


@pytest.mark.parametrize('preset', list(PRESETS))
def test_legacy_presets_keep_their_complete_runtime_semantics(preset):
    legacy = {'preset': preset}
    original = deepcopy(legacy)
    config = AdvisorConfig.model_validate(legacy).model_dump()
    document = advisor_to_mlds(legacy, origin='legacy')
    assert advisor_from_mlds(legacy) == config
    assert advisor_from_mlds(document) == config
    assert resolve_advisor(advisor_from_mlds(document)) == resolve_advisor(legacy)
    assert legacy == original


def test_custom_roundtrip_preserves_text_order_name_and_effective_scores():
    config = {
        'mode': 'custom', 'preset': 'steve', 'name': 'Meine ÄÖ-Beratung',
        'description': 'Prüfe "Wirkung".\nDann: 🧭 nächste Schritte; {keine Vorlage}.',
        'traits': ['neugierig', 'direkt', 'empathisch', 'kritisch'],
        'focus': 'fachliche_tiefe',
    }
    original = deepcopy(config)
    document = advisor_to_mlds(config)
    # Real JSON persistence round-trip, including quotes, Unicode and linebreaks.
    loaded = advisor_from_mlds(json.dumps(document, ensure_ascii=False))
    assert loaded == config == original
    assert document['personality']['name'] == 'Meine ÄÖ-Beratung'
    assert 'scoring_weights' not in document['personality']
    assert resolve_advisor(loaded) == resolve_advisor(config)
    components = {'technical_fit': 82, 'preferences_fit': 55,
                  'technical_depth': 91, 'learning': None, 'innovation': 10, 'clarity': 68}
    assert score_from_components(components, loaded) == score_from_components(components, config)


def test_existing_normalization_is_the_only_roundtrip_normalization():
    raw = {'mode': 'custom', 'name': '  Beratung  ', 'traits': ['analytisch'],
           'description': '\nZeile 1\nZeile 2  '}
    config = AdvisorConfig.model_validate(raw)
    assert advisor_from_mlds(advisor_to_mlds(raw)) == config.model_dump()
    assert advisor_from_mlds(advisor_to_mlds(config)) == config.model_dump()


def test_legacy_without_description_receives_existing_defaults():
    raw = {'mode': 'custom', 'name': 'Alt', 'traits': ['analytisch']}
    assert advisor_from_mlds(raw)['description'] == ''
    assert advisor_from_mlds({}) == AdvisorConfig().model_dump()


@pytest.mark.parametrize('key,value', [
    ('format', 'MLDS'), ('schema_version', 2), ('schema_version', True),
    ('schema_version', 1.0), ('schema_version', '1'),
    ('provenance', {'method': 'MLDS', 'reference': 'https://example.com', 'origin': 'session'}),
    ('unexpected', 'field'), ('personality', []),
])
def test_invalid_envelopes_are_rejected_without_falling_back(key, value):
    document = advisor_to_mlds()
    document[key] = value
    with pytest.raises(MLDSError):
        advisor_from_mlds(document)


@pytest.mark.parametrize('missing', ['format', 'schema_version', 'provenance', 'personality'])
def test_missing_envelope_fields_are_rejected(missing):
    document = advisor_to_mlds()
    del document[missing]
    with pytest.raises(MLDSError):
        advisor_from_mlds(document)


@pytest.mark.parametrize('missing', list(AdvisorConfig.model_fields))
def test_mlds_needs_complete_config_even_though_legacy_fields_can_default(missing):
    document = advisor_to_mlds()
    del document['personality'][missing]
    with pytest.raises(MLDSError):
        advisor_from_mlds(document)


@pytest.mark.parametrize('update', [
    {'traits': ['analytisch', 'analytisch']}, {'traits': ['unbekannt']},
    {'traits': []}, {'traits': ['analytisch', 'direkt', 'kritisch', 'kreativ', 'empathisch']},
    {'description': 'x' * 2001}, {'description': 5}, {'name': ' '}, {'name': 'x' * 61},
    {'focus': 'höheres_gehalt'}, {'preset': 'career'}, {'scoring_weights': {'technical_fit': 0}},
])
def test_domain_constraints_apply_to_both_legacy_and_mlds(update):
    config = {'mode': 'custom', 'name': 'Test', 'traits': ['analytisch'], **update}
    document = advisor_to_mlds({'mode': 'custom', 'name': 'Test', 'traits': ['analytisch']})
    document['personality'].update(update)
    for value in (config, document):
        with pytest.raises(MLDSError):
            advisor_from_mlds(value)
    with pytest.raises(MLDSError):
        advisor_to_mlds(config)


@pytest.mark.parametrize('text', [
    'null', '[]', '"config"', 'true', '{', '{"preset":"steve","preset":"angela"}',
    '{"name":NaN}', '{"name":Infinity}', '{"traits":[-Infinity]}',
    '{"schema_version":' + ('1' * 5000) + '}',
    '{"description":"' + ('x' * 65536) + '"}',
])
def test_non_objects_non_json_and_ambiguous_json_are_rejected(text):
    with pytest.raises(MLDSError):
        advisor_from_mlds(text)


def test_invalid_config_does_not_echo_participant_free_text():
    private = 'Private Teilnehmerangabe'
    with pytest.raises(MLDSError) as caught:
        advisor_to_mlds({'description': private, 'traits': ['invalid']})
    assert private not in str(caught.value)


def test_builtin_catalog_reproduces_original_editable_templates():
    catalog = load_templates()
    assert list(catalog) == ['career', 'expert']
    career, expert = catalog['career'], catalog['expert']
    assert career['name'] == 'Top-Berufsberater'
    assert career['traits'] == ['empathisch', 'strukturiert', 'ermutigend']
    assert career['focus'] == 'lernpotenzial'
    assert career['instructions'].startswith('Arbeite als besonders sorgfältiger KI-Berufsberater.')
    assert expert['name'] == 'Fachexperte'
    assert expert['traits'] == ['analytisch', 'kritisch', 'strukturiert']
    assert expert['focus'] == 'fachliche_tiefe'
    assert 'das aus dem Suchziel und den Fähigkeiten im Nutzerprofil hervorgeht' in expert['instructions']
    assert 'bei uneindeutigen oder mehreren Gebieten nicht ohne Beleg fest' in expert['instructions']
    for value in catalog.values():
        assert value['advisor']['mode'] == 'custom'
        assert value['instructions'] == value['advisor']['description']
        assert advisor_from_mlds(value['mlds']) == value['advisor']
        assert value['mlds']['provenance']['origin'] == 'builtin'
    neutral = load_neutral_advisor()
    assert neutral == {'mode': 'preset', 'preset': 'neutral', 'name': 'DIANA',
                       'traits': [], 'focus': 'ausgewogen', 'description': ''}
    assert resolve_advisor(neutral) == resolve_advisor({'preset': 'neutral'})


def test_catalog_and_serializer_return_isolated_data():
    catalog = load_templates()
    pristine = deepcopy(catalog)
    catalog['career']['traits'].clear()
    catalog['career']['advisor']['traits'].clear()
    catalog['career']['mlds']['personality']['description'] = 'Verändert'
    assert load_templates() == pristine
    config = pristine['expert']['advisor']
    document = advisor_to_mlds(config)
    document['personality']['traits'].clear()
    assert config['traits'] == ['analytisch', 'kritisch', 'strukturiert']


def test_builtin_identity_and_provenance_are_validated(tmp_path, monkeypatch):
    document = load_templates()['career']['mlds']
    document['template']['id'] = 'expert'
    (tmp_path / 'career.mlds').write_text(json.dumps(document))
    monkeypatch.setattr(persona_mlds, 'PERSONAS_DIR', tmp_path)
    with pytest.raises(MLDSError):
        load_templates()


@pytest.mark.parametrize('mutate', [
    lambda doc: doc['provenance'].update(origin='session'),
    lambda doc: doc.pop('template'),
    lambda doc: doc['template'].update(selectable=False),
    lambda doc: doc['personality'].update(mode='preset'),
])
def test_invalid_builtin_relationships_are_rejected(mutate):
    document = load_templates()['career']['mlds']
    mutate(document)
    with pytest.raises(MLDSError):
        advisor_from_mlds(document)


def test_published_mldsi_cannot_drift_from_runtime_contract():
    published = json.loads((PERSONAS_DIR / 'Personality.mldsi').read_text())
    assert published == personality_schema()
    assert published['$schema'] == 'https://json-schema.org/draft/2020-12/schema'
    advisor = published['$defs']['AdvisorConfig']
    assert set(advisor['required']) == set(AdvisorConfig.model_fields)
    assert advisor['properties']['traits']['uniqueItems'] is True
