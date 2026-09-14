"""Separate, non-randomized test contexts; never count as study allocations."""
import copy
import hashlib
import json

TEST_PURPOSES = {'A': 'test_a', 'B': 'test_b'}


def test_notice(base, arm):
    notice = copy.deepcopy(base)
    notice['purpose'] = TEST_PURPOSES[arm]
    notice['title'] = f'DIANA · Variante {arm} außerhalb der Umfrage testen'
    notice['consent_text'] = ('Ich habe die Datenschutzhinweise gelesen und willige freiwillig in die Verarbeitung '
        'meiner Angaben für diesen separaten DIANA-Test einschließlich der OpenAI-Verarbeitung ein. '
        'Es werden keine Umfrageantworten erhoben. Ich kann meine Einwilligung jederzeit widerrufen.')
    replacements = {
        'Zweck und Freiwilligkeit': 'Dieser freiwillige Test dient dem Ausprobieren von DIANA außerhalb der wissenschaftlichen Umfrage. '
            'Es erfolgt keine zufällige Studienzuteilung. Der Test erzeugt keine Umfrageantwort und wird nicht in die Studienauswertung aufgenommen. '
            'Rechtsgrundlage für die Verarbeitung ist deine Einwilligung nach Art. 6 Abs. 1 Buchst. a DSGVO.',
        'Studienvarianten': f'Du testest gezielt Variante {arm}. A ist die allgemeine KI-Jobsuche; B bietet eine einstellbare Suchpersönlichkeit. '
            'Beide Testseiten und die Umfrage verwenden getrennte Einwilligungen und Suchsitzungen.',
        'Welche Daten werden verarbeitet?': 'Suchprofil, optionaler Lebenslauftext, KI-Persönlichkeit und Chatnachrichten werden nur vorübergehend '
            'im Arbeitsspeicher verarbeitet. Die Sitzung verfällt nach einer Stunde ohne neue Such- oder Chataktion oder beim Serverneustart. '
            'Es werden keine demografischen Angaben oder Umfragebewertungen erhoben. Bitte verwende möglichst das Beispielprofil und keine sensiblen Daten.',
        'Speicherung und Empfänger': 'Gespeichert wird ein zufälliger Einwilligungsnachweis mit Zeitpunkt, Wortlaut und Testvariante. '
            'Er ermöglicht den Widerruf und die Zuordnung deiner vorübergehenden Suchsitzung. Such- und Chattexte werden nicht dauerhaft gespeichert. '
            'Der Einwilligungsnachweis unterliegt den in diesen Hinweisen genannten Aufbewahrungs- und Löschregeln. '
            + next((text.partition('Der Nachweis enthält Zeitpunkt und Wortlaut der Einwilligung. ')[2] for title, text in base['sections'] if title == 'Speicherung und Empfänger'), ''),
    }
    notice['sections'] = [[title, replacements.get(title, text)] for title, text in notice['sections']]
    # Keep readiness operational, while consent text and test purpose define its version.
    content = {key:value for key,value in notice.items() if key not in ('ready','configuration_complete','version')}
    notice['version'] = hashlib.sha256(json.dumps(content, ensure_ascii=False, sort_keys=True).encode()).hexdigest()
    return notice
