"""Descriptive, version-separated aggregates. No model calls or data mutations."""
from collections import Counter
from copy import deepcopy
from statistics import mean, median

from survey_store import (SURVEY_DEFINITION, V9_SURVEY_DEFINITION, V8_SURVEY_DEFINITION, V7_SURVEY_DEFINITION, V6_SURVEY_DEFINITION, V5_SURVEY_DEFINITION,
                          V4_SURVEY_DEFINITION, LEGACY_SURVEY_DEFINITION, answer_status,
                          QUESTIONS, ADDED_VALUE_LABELS, PREFERENCE_LABELS)

DEFINITIONS = {d['version']: d for d in (SURVEY_DEFINITION, V9_SURVEY_DEFINITION, V8_SURVEY_DEFINITION, V7_SURVEY_DEFINITION, V6_SURVEY_DEFINITION,
               V5_SURVEY_DEFINITION, V4_SURVEY_DEFINITION, LEGACY_SURVEY_DEFINITION)}
DEFINITIONS['diana-v2'] = deepcopy(LEGACY_SURVEY_DEFINITION)
for category in [DEFINITIONS['diana-v2']['demographics'], *DEFINITIONS['diana-v2']['categories']]:
    category['fields'] = [field for field in category['fields'] if not field['name'].endswith('_usefulness')]
DEFINITIONS['diana-v1'] = dict(demographics=dict(title='Erste Umfrage', fields=[
    dict(name='chat_helpfulness', title=QUESTIONS[0], kind='scale', scale=dict(min=1,max=5,low='Gar nicht hilfreich',high='Sehr hilfreich')),
    dict(name='added_value', title=QUESTIONS[1], kind='choice', options=list(ADDED_VALUE_LABELS.items())),
    dict(name='future_preference', title=QUESTIONS[2], kind='choice', options=list(PREFERENCE_LABELS.items())),
    dict(name='feedback', title=QUESTIONS[3], kind='text', optional=True),
]), categories=[])


def summarize(field, rows):
    maximum = field.get('scale', {}).get('max', 10)
    statuses = Counter()
    values = []
    texts = []
    for row in rows:
        answers = row['answers']
        status = answer_status(field, answers)
        value = answers.get(field['name'])
        if status == 'answered':
            if field['kind'] == 'scale' and (type(value) is not int or not 1 <= value <= maximum):
                status = 'invalid'
            elif field['kind'] == 'choice' and value not in dict(field.get('options', [])):
                status = 'invalid'
            elif field['kind'] in ('text', 'textarea'):
                if isinstance(value, str) and value.strip():
                    texts.append({'id': row['id'], 'participation_id': row['participation_id'],
                                  'arm': row['study_arm'], 'text': value})
                else:
                    status = 'no_answer'
            if status == 'answered':
                values.append(value)
        statuses[status] += 1
    counts = Counter(values)
    options = [(i, str(i)) for i in range(1, maximum+1)] if field['kind'] == 'scale' else field.get('options', [])
    return dict(total=len(rows), n=len(values), statuses=dict(statuses),
                mean=round(mean(values), 3) if values and field['kind'] == 'scale' else None,
                median=median(values) if values and field['kind'] == 'scale' else None,
                distribution=[dict(value=value, label=label, count=counts[value],
                                   percent=round(100 * counts[value] / len(values), 1) if values else 0)
                              for value, label in options if value not in ('not_used', 'not_assessable', 'not_specified')],
                texts=texts[:50], remaining_texts=max(0, len(texts) - 50))


def analytics(rows, version):
    """Require a version; separate migrated experiment cohorts within that version."""
    definition = DEFINITIONS.get(version)
    result = dict(version=version, total=len(rows), completed=sum(r['response_status']=='completed' for r in rows),
                  in_progress=sum(r['response_status']=='in_progress' for r in rows),
                  versions=dict(Counter(r['survey_version'] for r in rows)), cohorts=[])
    if not definition:
        result['message'] = 'Für Diagramme bitte eine einzelne Fragebogenversion auswählen. Die Skalen und Fragen verschiedener Versionen werden nicht vermischt.'
        return result
    rows = [r for r in rows if r['survey_version'] == version]
    def cohort_key(row):
        return (row.get('experiment_id') or '', tuple(row.get('presentation_versions') or ['undocumented']))
    experiments = sorted({cohort_key(r) for r in rows}) or [('', ('undocumented',))]
    for experiment, presentation in experiments:
        members = [r for r in rows if cohort_key(r) == (experiment, presentation)]
        arms = sorted({r['study_arm'] for r in members if r['study_arm']})
        cohort = dict(experiment_id=experiment, presentation_versions=list(presentation), total=len(members),
                      arms={arm: sum(r['study_arm']==arm for r in members) for arm in arms}, categories=[])
        for category in [definition['demographics'], *definition['categories']]:
            questions = []
            for field in category['fields']:
                if field.get('systemProvided'):
                    continue
                questions.append(dict(name=field['name'], title=field['title'], kind=field['kind'],
                                      scale=field.get('scale', definition.get('scale', {})),
                                      reverse=field['name']=='search_effort', visible_if=field.get('visibleIf'),
                                      overall=summarize(field, members),
                                      groups={arm: summarize(field, [r for r in members if r['study_arm']==arm]) for arm in arms}))
            cohort['categories'].append(dict(title=category['title'], questions=questions))
        result['cohorts'].append(cohort)
    return result
