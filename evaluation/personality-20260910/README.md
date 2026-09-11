# Prüfung der editierbaren KI-Suchpersönlichkeiten

10.09.2026 · GPT-5.4-Snapshot 2026-03-05 · Denkaufwand none

Geprüft wurden die tatsächlichen UI-Vorlagen (mode custom), die neutrale Variante B und eine freie Persönlichkeit. Alle erhalten dieselben fiktiven Jobtexte, dieselbe Frage und dieselben fachlichen Teilbewertungen. Keine Bewerberdaten oder Teilnehmerantworten wurden verwendet.

Drei Entwicklungsrunden mit je elf logischen Modellaufrufen sind vollständig archiviert. Runde 1 blieb sprachlich zu ähnlich und überschritt bei Angela die Vorgabe von höchstens einer Rückfrage. Runde 2 verkürzte die Antworten und bestand die mechanischen Checks; ein unabhängiges Blindreview ordnete fünf von fünf Stilen richtig zu, fand im Chat aber weiter Überschneidungen. Runde 3 schärft den direkten Einstieg und den dialogischen Aufbau. Die Quellhashes blieben während jeder Runde unverändert.

Die letzte Runde erfüllt die Schema-, Längen-, Kandidaten-, Cache- und Aktionsprüfungen. Alle Teilbewertungen blieben erhalten und die Frage löste weder eine neue Suche noch Profiländerungen aus. Die qualitative Sichtung zeigt stärkeren Kontrast, vor allem zwischen Steve (Wirkung, pointierte Sätze), Angela (geordnete Abwägung) und Günther (Alltag, Gespräch). Einzelne Formulierungen bleiben ähnlich; manche Antworten nennen unterschiedliche optionale Prüfpunkte. Das ist keine psychometrische Validierung oder Garantie für jeden Chat. Die letzte Runde wurde vom Hauptagenten gesichtet, nicht erneut unabhängig verblindet bewertet.

Die Antwortgrenze beträgt in B und C nun gleichermaßen 600 Zeichen. Der kurze serverseitige Einstieg zählt zusätzlich die tatsächlich bewerteten und eingeblendeten Karten. Scores erhalten keine künstlichen Persönlichkeitsboni.

Für die Haupterhebung muss ein menschlicher Pretest mit Zielgruppenmitgliedern prüfen, ob der Unterschied wahrgenommen wird. Die neue technische Release-ID ist von früheren Testständen zu unterscheiden. Alle drei Runden erhalten; nicht nur ausgewählte Antworten als Qualitätsbeleg verwenden.

## Tatsächliche Chatantworten der letzten Runde

### B_neutral

Ja, eher schon. Dafür spricht die klare Fachpassung: Python, Pandas und SQL sind gefordert, Berufserfahrung nicht. Auch Betreuung, Nürnberg, hybrid und 16 bis 20 Stunden passen zu deinen Wünschen. Vor der Bewerbung würde ich vor allem zwei Punkte klären: wie viel eigener Produktspielraum du wirklich hast und wie die Abstimmung im Team im Alltag organisiert ist.

56 Wörter · 363 Zeichen

### C_steve

Ja, die lohnt sich. Du würdest hier Nutzungsdaten auswerten und kleine Prototypen direkt im Produktteam erproben. Das ist der stärkste Punkt: Deine Analysen landen nicht nur im Bericht, sondern in konkreten Produktverbesserungen. Vor der Bewerbung klären solltest du den echten Entscheidungsspielraum und wie die Teamabstimmung bei eigenen Vorschlägen läuft.

49 Wörter · 358 Zeichen

### C_angela

Ja, eher ja. Dafür spricht: Python, SQL und Pandas passen direkt zu den Aufgaben, und die feste Fachbetreuung ist für deinen Einstieg ein klarer Vorteil.

Vor der Bewerbung klären: Wie viel eigener Spielraum bei Prototypen und Verbesserungsvorschlägen wirklich besteht und wie Entscheidungen im Produktteam abgestimmt werden. Fachlich wirkt die Stelle stimmig; der Gestaltungsspielraum ist der wichtigste Prüfpunkt.

57 Wörter · 415 Zeichen

### C_guenther

Du würdest dort Nutzungsdaten mit Python und SQL auswerten und kleine Prototypen direkt im Produktteam ausprobieren. Für deinen Wunsch nach praktischer Datenanalyse ist das eine starke Empfehlung, weil deine belegten Grundlagen genau passen und feste Fachbetreuung ausdrücklich genannt ist. Vor der Bewerbung würde ich vor allem klären, wie viel eigener Gestaltungsspielraum du bei diesen Prototypen und Verbesserungsvorschlägen im Alltag wirklich hast.

61 Wörter · 453 Zeichen

### C_custom

Ja, die würde ich empfehlen. Sie trifft deinen Wunsch nach praktischer Datenanalyse sehr direkt: Python- und SQL-Auswertungen plus kleine Prototypen im Produktteam. Für den Einstieg ist die feste Fachbetreuung ein starkes Plus. Vor der Bewerbung kläre vor allem, wie viel eigener Gestaltungsspielraum du bei den Prototypen wirklich hast und wie die Teamabstimmung konkret läuft.

54 Wörter · 378 Zeichen

## Reproduzieren

Das opt-in Skript `tools/evaluate_personality.py` liest die aktuellen UI-Vorlagen über Node. Ohne `--live` entstehen nur ein Plan und Offlineprüfungen. Live-Aufrufe benötigen den vorhandenen API-Key und verwenden ausschließlich die mitgelieferten synthetischen Daten. Die Modellantworten sind nicht deterministisch.

Promptgestaltung: [OpenAI – GPT-5.4 Model guidance](https://developers.openai.com/api/docs/guides/latest-model?model=gpt-5.4).
