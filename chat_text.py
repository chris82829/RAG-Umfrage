"""Chat-only title cleanup and compact B/C messages; never modify assessments."""
import re

COMPACT_CHAT_VERSION = 'short-job-bullets-v2'
MAX_BC_ANSWER_CHARS = 380
MAX_BC_WELCOME_CHARS = 420
SCORE_SCALE = {'minimum': 1, 'maximum': 100, 'unit': 'Punkte', 'is_probability': False}
CHAT_PRESENTATION_VERSION = 'clean-job-titles-welcome-v1'

COMPACT_CHAT_INSTRUCTIONS = """
VERBINDLICHES KURZFORMAT FÜR assistant_message (v2):
Höchstens 45 Wörter und 380 Zeichen insgesamt, einschließlich Rückfrage.
Bei einer Suchansprache oder einem Stellenvergleich: zwei kurze Aufzählungspunkte,
jeweils in einer eigenen Zeile mit '- Stellentitel: ein konkreter passender Beleg'.
Verwende die exakten Stellentitel aus den Daten, damit sie anklickbar bleiben.
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
    return remove_gender_suffixes(text).strip()


def _fit(text: str, budget: int) -> str:
    text = re.sub(r'\s+', ' ', text).strip()
    if len(text) <= budget:
        return text
    # Prefer complete sentences; otherwise stop at a word boundary, never an ID/link.
    sentences = re.split(r'(?<=[.!?])\s+', text)
    result = ''
    for sentence in sentences:
        candidate = (result + ' ' + sentence).strip()
        if len(candidate) > budget:
            break
        result = candidate
    if result:
        return result
    fragment = text[:max(0, budget - 1)].rsplit(' ', 1)[0].rstrip(' ,;:–-')
    return fragment + '…' if fragment else ''


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
        # Drop a redundant prose lead-in before a list; spend the space on the
        # job titles and evidence. Shorten evidence before shortening a title.
        parts = [item.rpartition(': ') for item in bullets]
        minimum = [len(title) + 18 if separator else len(item)
                   for item, (title, separator, _) in zip(bullets, parts)]
        while len(bullets) > 1 and sum(minimum) + 3 * len(bullets) > budget:
            bullets.pop(); parts.pop(); minimum.pop()
        extra = max(0, budget - sum(minimum) - 3 * len(bullets)) // len(bullets)
        formatted = []
        for item, (title, separator, evidence), needed in zip(bullets, parts, minimum):
            item_budget = min(budget - 3, needed + extra)
            if separator and len(title) + 4 < item_budget:
                item = title + separator + _fit(evidence, item_budget - len(title) - 2)
            else:
                item = _fit(item, item_budget)
            formatted.append('- ' + item)
        body = '\n'.join(formatted)
    else:
        kept = []
        for line in lines:
            remaining = budget - sum(len(item) + 1 for item in kept)
            if remaining < 15:
                break
            kept.append(_fit(line, remaining))
        body = '\n'.join(kept)
    return '\n\n'.join(part for part in (body, question) if part).strip() or 'Dazu fehlen mir verlässliche Angaben.'
