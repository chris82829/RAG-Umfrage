"""Chat-only title cleanup and compact B/C messages; never modify assessments."""
import re

COMPACT_CHAT_VERSION = 'short-job-bullets-v2'
MAX_BC_ANSWER_CHARS = 380
MAX_BC_WELCOME_CHARS = 420
SCORE_SCALE = {'minimum': 1, 'maximum': 100, 'unit': 'Punkte', 'is_probability': False}
CHAT_PRESENTATION_VERSION = 'readable-complete-job-points-v2'

COMPACT_CHAT_INSTRUCTIONS = """
VERBINDLICHES KURZFORMAT FÜR assistant_message (v2):
Höchstens 45 Wörter und 380 Zeichen insgesamt, einschließlich Rückfrage.
Bei einer Suchansprache oder einem Stellenvergleich: zwei kurze Aufzählungspunkte,
jeweils in einer eigenen Zeile mit '- Stellentitel: ein konkreter passender Beleg'.
Verwende die exakten Stellentitel aus den Daten, damit sie anklickbar bleiben.
Schreibe zum Titel genau einen vollständigen Satz mit höchstens zwölf Wörtern.
Sprich den Nutzer direkt an: zum Beispiel 'Deine Python-Kenntnisse passen zu den Datenaufgaben.'
Keine Stichwortketten, Pluszeichen oder durch Semikolon getrennte Faktenlisten.
Erkläre einen konkreten Nutzen in einfacher Sprache; keine Ansammlung von Fachbegriffen.
Verwende niemals Auslassungspunkte ('...' oder '…') und breche keinen Satz ab.
Kürze durch Weglassen zusätzlicher Aspekte, nicht durch Satzfragmente.
Kürze den Beleg, nicht den Titel. Bei sehr langen Titeln genügt ein Stellenpunkt.
Bei nur einer passenden Stelle genügt ebenfalls ein Punkt. Keine Zusammenfassung.
Nenne niemals Job-IDs, job:-Verweise, Markdown-Links oder technische Kennungen.
Die Stellen-Scores reichen von 1 bis 100 Punkten, niemals von 1 bis 10.
Übernimm erwähnte Scores exakt aus den bereitgestellten Daten (z. B. 85/100).
Erfinde keine Punktzahl, rechne sie nicht auf zehn um und nenne sie nicht Prozent.
Schreibe keine Begrüßung, Trefferzahl, Hinweise zur Ergebnisansicht oder den Satz
über 'Weitere Stellen anzeigen'; die Oberfläche zeigt die Trefferzahl selbst.
Wenn eine konkrete Rückfrage sinnvoll und follow_up_allowed wahr ist, stelle
genau eine kurze Frage in einem eigenen Absatz, möglichst höchstens 80 Zeichen.
Halte die gewählte Persönlichkeit innerhalb dieses knappen Formats bei.
Diese Darstellungsvorgabe verändert keine Fakten, Bewertungen oder Gewichte.
""".strip()


def remove_gender_suffixes(text: str) -> str:
    """Remove job-title gender markers, retaining technical parentheses and line breaks."""
    return re.sub(r'[ \t]*\(\s*[mwfdx]\s*[/|]\s*[mwfdx]\s*[/|]\s*[mwfdx]\s*\)',
                  '', text, flags=re.I)


def clean_job_references(text: str) -> str:
    """Keep human labels, including malformed/escaped references from older prompts."""
    text = re.sub(r'\[([^\]\n]+)\]\\?\(job:[^\s)]*\\?\)', r'\1', text)
    text = re.sub(r'\[([^\]\n]+)\]\\?\(job:[^\n)]*$', r'\1', text)
    text = re.sub(r'\[([^\]\n]+)\]\\?\(?\s*$', r'\1', text)
    text = re.sub(r'\*\*([^*]+)\*\*', r'\1', text)
    text = re.sub(r'\(?\bJob[- ]?ID\s*:?\s*[\w-]+\)?', '', text, flags=re.I)
    text = re.sub(r'\\?\(?\bjob:[\w%.-]*\\?\)?', '', text, flags=re.I)
    text = re.sub(r'[;,.]?\s*weitere findest du über\s*[„"«]?Weitere Stellen anzeigen[“"»]?\.?', '', text, flags=re.I)
    return re.sub(r'…|\.{3,}', '', remove_gender_suffixes(text)).strip()


def _fit(text: str, budget: int) -> str:
    text = re.sub(r'\s+', ' ', text).strip()
    if len(text) <= budget:
        return text
    # Keep only complete sentences when a paragraph exceeds the available space.
    sentences = re.split(r'(?<=[.!?])\s+', text)
    result = ''
    for sentence in sentences:
        candidate = (result + ' ' + sentence).strip()
        if len(candidate) > budget:
            break
        result = candidate
    if result:
        return result
    return ''  # Never return a sentence fragment to satisfy a character budget.


def compact_advice(text: str, *, intro_jobs: list[dict] | None = None,
                   max_characters: int = MAX_BC_ANSWER_CHARS) -> str:
    """Bound both final responses and previews without shrinking the JSON schema.

    Complete short questions keep their own paragraph. Initial prose that ignores
    the list instruction falls back to the actual leading titles, not invented
    recommendations. Normal chat answers retain their own wording.
    """
    body = clean_job_references(text)
    question = ''
    if body.endswith('?'):
        sentences = re.split(r'(?<=[.!?])\s+|\n+', body)
        last = sentences[-1].strip()
        if len(last) <= 150:
            question = last
            body = body[:-len(last)].rstrip()
    budget = max_characters - (len(question) + 2 if question else 0)
    lines = [line.strip() for line in body.splitlines() if line.strip()]
    bullets = [re.sub(r'^(?:[-•*]|\d+[.)])\s+', '', line)
               for line in lines if re.match(r'^(?:[-•*]|\d+[.)])\s+', line)][:2]
    if intro_jobs is not None and not bullets:
        bullets = [clean_job_references(job.get('title', 'Stellenangebot'))
                   for job in intro_jobs[:2]]
    if bullets:
        # Keep each full title and one complete sentence. If two explanations do
        # not fit, show one useful point rather than clipping both mid-sentence.
        formatted = []
        for item in bullets:
            title, separator, evidence = item.partition(': ')
            if separator:
                evidence = re.split(r'(?<=[.!?])\s+', evidence.strip(), maxsplit=1)[0]
                item = title + separator + evidence if evidence else title
            candidate = '- ' + item
            if len('\n\n'.join(formatted + [candidate])) <= budget:
                formatted.append(candidate)
        if not formatted:
            # Extremely long generated prose must not erase the actual job title.
            title = bullets[0].partition(': ')[0]
            if len(title) + 2 <= budget:
                formatted = ['- ' + title]
        body = '\n\n'.join(formatted)
    else:
        kept = []
        for line in lines:
            remaining = budget - sum(len(item) + 1 for item in kept)
            if remaining < 15:
                break
            kept.append(_fit(line, remaining))
        body = '\n'.join(kept)
    return '\n\n'.join(part for part in (body, question) if part).strip() or 'Dazu fehlen mir verlässliche Angaben.'
