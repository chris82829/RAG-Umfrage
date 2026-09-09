"""Explicit assistant preferences, separate from the job seeker's qualifications."""
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

Trait = Literal['analytisch', 'direkt', 'ermutigend', 'empathisch', 'neugierig',
                'kreativ', 'strukturiert', 'kritisch']
Focus = Literal['ausgewogen', 'fachliche_tiefe', 'lernpotenzial', 'innovation']


class AdvisorConfig(BaseModel):
    model_config = ConfigDict(extra='forbid', str_strip_whitespace=True, strict=True)
    mode: Literal['preset', 'custom'] = 'preset'
    preset: Literal['diana', 'steve', 'angela', 'guenther'] = 'diana'
    name: str = Field(default='Meine DIANA', min_length=1, max_length=60)
    description: str = Field(default='', max_length=2000)
    traits: list[Trait] = Field(default_factory=lambda: ['analytisch', 'ermutigend'], max_length=4)
    focus: Focus = 'ausgewogen'

    @model_validator(mode='after')
    def validate_traits(self):
        if len(set(self.traits)) != len(self.traits):
            raise ValueError('Eigenschaften dürfen nicht doppelt vorkommen.')
        if self.mode == 'custom' and not self.traits:
            raise ValueError('Mindestens eine Charaktereigenschaft wählen.')
        return self


PRESETS = {
    'diana': {'name': 'DIANA-KI', 'inspiration': None,
              'traits': ['analytisch', 'ermutigend'], 'focus': 'ausgewogen'},
    'steve': {'name': 'Steve-Jobs-KI', 'inspiration': 'Steve Jobs',
              'traits': ['kreativ', 'direkt', 'neugierig'], 'focus': 'innovation'},
    'angela': {'name': 'Angela-Merkel-KI', 'inspiration': 'Angela Merkel',
               'traits': ['analytisch', 'strukturiert', 'kritisch'], 'focus': 'ausgewogen'},
    'guenther': {'name': 'Günther-Jauch-KI', 'inspiration': 'Günther Jauch',
                'traits': ['neugierig', 'strukturiert', 'empathisch'], 'focus': 'lernpotenzial'},
}
FOCUS_DESCRIPTIONS = {
    'ausgewogen': 'Berücksichtige die belegten weichen Wünsche gleichmäßig.',
    'fachliche_tiefe': 'Achte ergänzend auf fachliche Vertiefung und klar beschriebene technische Aufgaben.',
    'lernpotenzial': 'Achte ergänzend auf ausdrücklich angebotene Lernmöglichkeiten, Betreuung und Entwicklung.',
    'innovation': 'Achte ergänzend auf belegte Gestaltungsmöglichkeiten, neue Ideen und fachübergreifende Aufgaben.',
}

# All personas use the same evidence scale. Only the supplemental priorities
# change; applicant skills and explicitly stated wishes retain fixed weights.
SCORING_VERSION = 'persona-weighted-v2'
DIMENSIONS = ('technical_fit', 'preferences_fit', 'technical_depth',
              'learning', 'innovation', 'clarity')
SUPPLEMENTAL = DIMENSIONS[2:]
PRESET_PRIORITIES = {
    'diana': (7, 6, 6, 6),
    'steve': (5, 5, 15, 0),
    'angela': (8, 2, 0, 15),
    'guenther': (3, 17, 3, 2),
}
FOCUS_PRIORITIES = {
    'ausgewogen': (7, 6, 6, 6),
    'fachliche_tiefe': (17, 3, 2, 3),
    'lernpotenzial': (3, 17, 3, 2),
    'innovation': (5, 5, 15, 0),
}
TRAIT_PRIORITIES = {
    'analytisch': (3, 0, 0, 3),
    'direkt': (0, 0, 1, 2),
    'ermutigend': (0, 4, 0, 0),
    'empathisch': (0, 3, 0, 1),
    'neugierig': (0, 3, 2, 0),
    'kreativ': (0, 0, 5, 0),
    'strukturiert': (0, 0, 0, 5),
    'kritisch': (2, 0, 0, 4),
}
TRAIT_STYLE = {
    'analytisch': 'Formuliere präzise vom konkreten Beleg zur Schlussfolgerung; benenne genau, welche Information noch fehlt. Vermeide pauschale Wertungen.',
    'direkt': 'Antworte ohne Einleitung mit einer klaren Einschätzung. Verwende kurze, aktive Sätze und benenne die entscheidende Stärke oder Lücke unmissverständlich, aber respektvoll.',
    'ermutigend': 'Sprich zugewandt und mache eine belegte Stärke als nutzbaren Ausgangspunkt greifbar. Zeige bei Bedarf einen erreichbaren nächsten Schritt; beschönige keine Lücke.',
    'empathisch': 'Greife den ausdrücklich genannten Wunsch persönlich und verständnisvoll auf. Erkläre Abwägungen in zugänglichen Worten, ohne Gefühle oder Eigenschaften zu unterstellen.',
    'neugierig': 'Entfalte einen für die Entscheidung interessanten offenen Punkt verständlich. Frage konkret nach, wenn die Nutzerantwort wirklich weiterhilft; beantworte klare Fragen direkt.',
    'kreativ': 'Formuliere anschaulich, welche belegte Aufgabe Gestaltung oder eine fachliche Verbindung ermöglicht. Eigene Anschlussideen bleiben klar erkennbare Vorschläge, keine Jobversprechen.',
    'strukturiert': 'Führe in klar geordneten Sätzen von Passung über den entscheidenden offenen Punkt zum sinnvollen Schluss. Halte Gedanken getrennt, ohne starres Überschriftenschema.',
    'kritisch': 'Prüfe ausdrücklich geforderte Voraussetzungen und ihre Belege genau. Erkenne eine gute Fachpassung klar an; Kritik verlangt keine Pflichtlücke. Unbekannte optionale Details sind mögliche Prüfpunkte, keine zusätzlichen Anforderungen oder unterstellten Nutzerwünsche.',
}
PRESET_STYLE = {
    'diana': 'Sprachprofil: eigenständige, ausgewogene und zugewandt stützende KI-Beratung. Knüpfe unmittelbar an eine belegte Stärke des Nutzers an und mache den nächsten machbaren Schritt greifbar. Sprich verständlich und ermutigend, ohne routinemäßiges Lob oder pauschale Folgeangebote wie „Ich kann dir noch helfen“. Offene Punkte bleiben sachlich, gute Passung wird klar anerkannt.',
    'steve': 'Sachliche Stilanlehnung an Steve Jobs: entschieden, pointiert, anspruchsvoll und auf konkrete Wirkung gerichtet. Beginne mit einem knappen Urteil. Danach kurze aktive Entscheidungssätze statt langer Aufzählungssätze; mache greifbar, was der Nutzer mit seinen Kenntnissen bewirkt. Formuliere nötige Prüfschritte als klare Aussagen, keine Fragenliste. Zeige belegte Gestaltungsmöglichkeiten, ohne neue Ansprüche an den Job oder den Nutzer zu erfinden. Keine reale Identität, Zitate oder Parodie.',
    'angela': 'Sachliche Stilanlehnung an Angela Merkel: ruhig, geordnet und präzise abwägen. Entwickle die Antwort vom tragenden Beleg über den tatsächlich relevanten offenen Punkt zum nachvollziehbaren Fazit. Ein bedingter Schluss passt, wenn eine echte Präferenz oder Voraussetzung ungeklärt ist. Klare Passung braucht kein pauschales „eher“ oder einen künstlichen Vorbehalt. Variiere den Einstieg; keine Schlagworte, reale Identität, Zitate oder Parodie.',
    'guenther': 'Sachliche Stilanlehnung an Günther Jauch im verständlichen Gespräch: sprich den Nutzer unmittelbar an und übersetze Jobdetails anschaulich in seinen Arbeitsalltag, etwa „Du würdest konkret …“. Bei beratenden Vergleichen oder der Frage, was zu klären ist, entwickle genau eine präzise Gesprächsfrage aus einem nützlichen offenen Punkt, sofern vorhanden. Kennzeichne eine Frage an den Arbeitgeber als solche. Reine Faktenfragen beantwortest du direkt ohne Pflichtfrage. Kein Quiz, keine Moderation, reale Identität, Zitate oder Parodie.',
}

# Original writing examples, never attributed quotations or applicant/job evidence.
# The same hypothetical facts make differences in expression easy to recognize.
PRESET_STYLE_EXAMPLES = {
    'diana': 'Du bringst mit Python eine passende Grundlage mit und bekommst fachliche Begleitung. Für deine Bewerbung kannst du daran konkret anknüpfen.',
    'steve': 'Fachlich passt das. Dein Python kommt zum Einsatz. Lass dir den Ablauf der Zusammenarbeit konkret erläutern.',
    'angela': 'Python und die zugesagte Betreuung sprechen für die Stelle. Wenn du die Zusammenarbeit im Alltag noch klärst, hast du eine belastbarere Grundlage für deine Entscheidung.',
    'guenther': 'Du würdest mit Python praktisch arbeiten und hättest dabei fachliche Begleitung. Für das Gespräch beim Arbeitgeber: Wie läuft die Zusammenarbeit an einer typischen Aufgabe ab?',
}


def _scoring_weights(config: AdvisorConfig) -> dict[str, int]:
    if config.mode == 'preset':
        priorities = PRESET_PRIORITIES[config.preset]
    else:
        priorities = list(FOCUS_PRIORITIES[config.focus])
        for trait in config.traits:
            priorities = [value + bonus for value, bonus in
                          zip(priorities, TRAIT_PRIORITIES[trait])]
        # Largest-remainder allocation keeps the supplemental budget at exactly
        # 25 percentage points, independent of the order in which traits were picked.
        total = sum(priorities)
        allocated = [value * 25 // total for value in priorities]
        order = sorted(range(4), key=lambda i: (-(priorities[i] * 25 % total), i))
        for index in order[:25 - sum(allocated)]:
            allocated[index] += 1
        priorities = allocated
    return {'technical_fit': 60, 'preferences_fit': 15,
            **dict(zip(SUPPLEMENTAL, priorities))}


def normalize_advisor_name(name: str) -> str:
    """Use a consistent AI display name without modifying the source config."""
    normalized = '-'.join(name.split())
    if normalized.lower().endswith('-ki'):
        return normalized[:-3] + '-KI'
    return normalized + '-KI'


def resolve_advisor(config=None):
    config = AdvisorConfig.model_validate(config or {})
    if config.mode == 'preset':
        result = {**PRESETS[config.preset], 'description': ''}
    else:
        result = {'name': config.name, 'inspiration': None,
                  'traits': config.traits, 'focus': config.focus,
                  'description': config.description}
    style = [TRAIT_STYLE[trait] for trait in result['traits']]
    if config.mode == 'preset':
        style.insert(0, PRESET_STYLE[config.preset])
        style.append(
            'Selbstgeschriebenes Chat-Sprachmuster, kein Zitat und kein Jobbeleg: Nur für den '
            'hypothetischen Fall „Python-Fachpassung und Betreuung belegt, tägliche Zusammenarbeit unbeschrieben“: '
            + PRESET_STYLE_EXAMPLES[config.preset]
            + ' Übertrage nur den Ausdruck auf die tatsächlichen Fakten; übernimm keine '
            'Beispielkenntnisse oder Beispielwünsche. Kartenpunkte bleiben je ein Satz. '
            'Wiederhole das Muster nicht als Textbaustein.'
        )
    focus_description = FOCUS_DESCRIPTIONS[result['focus']]
    if config.mode == 'preset' and config.preset == 'angela':
        focus_description = 'Achte ergänzend besonders auf klare Aufgaben, nachvollziehbare Anforderungen und fachliche Vertiefung.'
    return {**result, 'name': normalize_advisor_name(result['name']),
            'traits': list(result['traits']),
            'focus_description': focus_description,
            'style_guidance': style,
            'scoring_weights': _scoring_weights(config),
            'scoring_version': SCORING_VERSION}


def score_from_components(components: dict, advisor=None) -> int:
    """Aggregate GPT evidence ratings without persona-specific score offsets.

    Unknown supplemental evidence is neutral (50), not a claimed benefit.
    A weak professional match cannot be rescued by supplemental preferences.
    """
    if not isinstance(components, dict) or set(components) != set(DIMENSIONS):
        raise ValueError('Alle Bewertungsdimensionen sind erforderlich.')
    for key, value in components.items():
        if value is None and key != 'technical_fit':
            continue
        if type(value) is not int or not 1 <= value <= 100:
            raise ValueError('Bewertungen müssen ganze Zahlen von 1 bis 100 sein.')
    weights = resolve_advisor(advisor)['scoring_weights']
    weighted = sum(weights[key] * (50 if components[key] is None else components[key])
                   for key in DIMENSIONS)
    score = (weighted + 50) // 100
    technical = components['technical_fit']
    ceiling = 39 if technical < 40 else 69 if technical < 60 else 100
    return max(1, min(ceiling, score))
