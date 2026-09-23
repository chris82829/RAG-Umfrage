"""A conclusion after C's third committed user turn, without a new counter."""
from chat_text import clean_job_references, sentence_parts


C_THIRD_TURN_VERSION = 'custom-third-successful-turn-no-truncation-v2'
C_SELECTION_CONCLUSION = (
    'Das ist meine aktuelle Auswahl für dich, abgestimmt auf dein Profil und unser Gespräch. '
    'Schau dir jetzt deine Favoriten genauer an.'
)
C_EMPTY_CONCLUSION = (
    'Aktuell sind keine Stellen in deiner Auswahl. '
    'Du kannst dein Suchprofil anpassen und eine neue Suche starten.'
)


def without_followup_question(text):
    """Keep factual sentences; a finished third turn must not solicit another reply."""
    lines = []
    for line in clean_job_references(text).splitlines():
        sentences = sentence_parts(line.strip())
        kept = [sentence for sentence in sentences if '?' not in sentence]
        if kept:
            lines.append(' '.join(kept))
    return '\n'.join(lines).strip()


def custom_chat_preview(text):
    """Delay questions and unfinished sentences until the transaction is committed."""
    return '\n'.join(
        ' '.join(sentence for sentence in sentence_parts(line.strip())
                 if sentence.endswith(('.', '!')) and '?' not in sentence)
        for line in clean_job_references(text).splitlines()
    ).strip()


def conclude_custom_chat(answer, jobs):
    """Preserve the complete answer, then add a truthful conclusion."""
    conclusion = C_SELECTION_CONCLUSION if jobs else C_EMPTY_CONCLUSION
    text = without_followup_question(answer)
    # Remain idempotent if a saved answer is passed through the finalizer again.
    text = text.replace(conclusion, '').strip()
    return '\n\n'.join(part for part in (text, conclusion) if part)
