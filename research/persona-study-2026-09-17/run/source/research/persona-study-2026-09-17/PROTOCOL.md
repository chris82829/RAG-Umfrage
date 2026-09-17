# Zwei-Personen-Pilot: dieselben fiktiven Nutzerinnen in A, B und C

Finaler Umfang vor den bezahlten Systemläufen am 17. September 2026: **zwei
fiktive Personen, sechs getrennte Sitzungen und 24 Messzeitpunkte**. Mara Seidel
(P01), Informatikstudentin am Anfang ihres Studiums, und Nora Peters (P06),
kaufmännisch erfahrene Berufsumsteigerin ins Personalmanagement, verwenden jeweils A, B und C einmal. Dies ist ein
deskriptiver technischer Pilot, keine Befragung realer Teilnehmer und keine
belastbare Wirksamkeitsstudie.

## Kanonische Eingaben und frühere Vorbereitung

`selected-personas.json` ist die einzige Eingabedatei für den auszuführenden
Piloten. Sie enthält die sechs Ausführungsfälle `P01-A`, `P01-B`, `P01-C`,
`P06-A`, `P06-B` und `P06-C`, mit `source_id: P01` beziehungsweise `source_id: P06`.
Initiales Profil, vollständiger Informationsbedarf, Qualifikationen, Grenzen,
Stellenarten und Informationsetappen sind innerhalb jeder Person über A/B/C identisch.
Die Rubrik und alle Fakten stehen vor der ersten Systemantwort fest.

Zwölf fiktive Personen wurden zunächst als Vorbereitung in
`personas/personas.json` und zwölf Markdown-Dossiers erstellt. Anschließend wurden
Entwürfe für zwölf C-Sitzungen, 36 Sitzungen über A/B/C und kurzzeitig drei
unterschiedliche Personen und nur eine Person erwogen. Diese Umfänge wurden auf
Nutzerwunsch **vor bezahlten Systemaufrufen dieses Piloten** durch den nun
festgelegten Pilot mit P01 und P06 ersetzt. Auch P03 als zweite Person wurde
vor dem Lauf durch das nichttechnische Profil P06 ersetzt. Die Vorbereitungsdateien
bleiben nachvollziehbar erhalten, gelten aber nicht als ausgeführte Tests.
Es werden keine Ergebnisse aus alten Evaluationen übernommen.

## Drei Beratungsvarianten

- **A:** unveränderte feste Standardberatung (`preset: standard`).
- **B:** unveränderte produktive Vorlage **Top-Berufsberater** (`career`) für
  beide Personen. Sie passt zu Maras erstem Berufseinstieg und Noras fachlichem
  Berufswechsel. Eine fachfremde Expertenvorlage wird nicht nur zur Variation
  erzwungen. Der Runner lädt die produktive Vorlage über `persona_mlds.py`
  aus `personas/career.mlds` und friert sie ein. Die ursprüngliche Vorbereitung
  verweist noch auf die entsprechende Frontend-Vorlage; maßgeblich für den Lauf
  ist die serverseitige MLDS-Konfiguration.
- **C:** vorab formulierte eigene Konfiguration **Mein Einstiegscoach** für Mara
  (ermutigend/strukturiert, Lernpotenzial) und **Meine Umstiegsberatung** für
  Nora (empathisch/direkt, Lernpotenzial). Keine Konfiguration
  wird nach Sichtung der Antworten optimiert. „Zielgerecht“ bedeutet passend
  entworfen, nicht wissenschaftlich als optimal oder perfekt belegt.

Die C-Beschreibung enthält weder die erst später genannten Stunden-/Ortswünsche
noch später offengelegte konkrete Kenntnisgrenzen. Der Gesprächsstil, die
Konfiguration und das initiale Suchziel sind zu Beginn festgelegt. Keine Variante
erhält den für die Bewertung bestimmten vollständigen Informationsbedarf als
zusätzliches verdecktes Suchprofil.

## Tatsächlicher Systemablauf

Pro Person und Variante wird in einer unabhängigen Sitzung das jeweilige identische initiale Profil
über `/api/onboard` verarbeitet. Danach folgen genau drei `/api/chat`-Nachrichten
im Modus `auto`. Der produktive Code entscheidet selbst zwischen Antwort,
Neubewertung und neuer Suche. Das System arbeitet gegen eine isolierte Datenbank
mit dem unveränderten originalen Bestand von 8.537 Stellenanzeigen. Echte
Umfrageantworten werden nicht angelegt oder verändert.

Das produktive Modell `gpt-5.4-2026-03-05`, Denkaufwand `none`, Prompts,
Bewertungskomponenten und Ausgabelimits bleiben erhalten. Der Transport muss
nicht als UI-Stream erfolgen; die finalen Zustände kommen aus denselben
Anwendungsendpunkten. Die konkreten Softwareversionen, Eingaben und Quelltexte
werden beim Vorbereiten mit Prüfsummen eingefroren.

Zunächst galt eine gemeinsame harte Grenze von **3,00 USD**. Nach Abschluss
von T0 und T1 (12 Messpunkten, 1,943655 USD Tokenkosten) genehmigte der Nutzer
am 17.09.2026 ausdrücklich **4,50 USD insgesamt**, um T2 und T3 fortzusetzen.
Die ursprünglichen Dateien bleiben unter `run/amendments/01-budget-authorization`
erhalten. Es gelten weiterhin konservative Tokenreservierung und höchstens
**80 kostenpflichtige POST-Anfragen**. Die Grenze
ist kein garantierter tatsächlicher Preis. Es gibt keine gesonderten
Nutzersimulator- oder Bewertungs-API-Aufrufe und keine automatischen bezahlten
Wiederholungen fehlgeschlagener Aufrufe. Bei Budget-, API- oder Laufproblemen
werden fehlende Messpunkte offen ausgewiesen, niemals durch erfundene Werte oder
heimliche Ersatzläufe ergänzt.

## Adaptive Unterhaltung mit gleichen Informationsetappen

Codex liest vor jeder Nachricht die tatsächlich erhaltene Antwort der jeweiligen
Sitzung. Es darf daran sprachlich anknüpfen, etwa eine konkret genannte Aufgabe
aufgreifen. Innerhalb jeder Person erhalten alle Varianten dieselben Fakten in
derselben Etappe. Für Mara sind das:

1. Betreuten Einstieg, Einarbeitung und eine feste fachliche Ansprechperson
   priorisieren; um Anpassung der Webentwicklungs-Rangfolge bitten.
2. Etwa 10–12 Wochenstunden, Wunsch nach Nürnberg/Erlangen und fehlende
   React-Erfahrung nennen; um erneute Anpassung bitten. Webentwicklung und
   Werkstudententätigkeit bleiben als Ziel und Stellenart unverändert.
3. Die tatsächlich erste angezeigte Stelle anhand des nun bekannten Bedarfs
   besprechen: zugängliche Aufgaben, Einarbeitung sowie offene Angaben zu
   Arbeitszeit und Betreuung. Keine neuen Wünsche oder Fähigkeiten hinzufügen.

Für Nora gelten entsprechend diese drei vorab festgelegten Etappen:

1. Interne Personaladministration, Mitarbeitendenbetreuung und Onboarding
   gegenüber vertriebsorientierter Personalvermittlung priorisieren; neu
   sortieren lassen.
2. Etwa 20–25 planbare Wochenstunden, fehlende eigenständige
   Entgeltabrechnungspraxis und fehlende SAP-HCM-Kenntnisse nennen; nötige
   Einarbeitung berücksichtigen und Rangfolge anpassen lassen.
3. Bei der tatsächlich ersten Stelle einen realistischen HR-Einstieg und den
   Nutzen vorhandener kaufmännischer Erfahrung prüfen. Keine neuen Fakten ergänzen.

`planned_messages`/`messages` sind vorab formulierte sprachliche Grundlagen,
keine vorgetäuschten tatsächlichen Interaktionen. `adaptive_message_stages`
legt das Informationsbudget fest. Tatsächlich gesendete Nachrichten,
Assistentenantworten und Gründe für sprachliche Anpassungen werden protokolliert.
Es werden weder spätere Etappen vorgezogen noch zusätzliche Nutzerfakten zur
Beantwortung unerwarteter Rückfragen erfunden. Die Formulierung wird nicht nach
erwarteten Metrikergebnissen ausgewählt. Bei fehlendem sinnvollen Gesprächsbezug
kann die vorgegebene Formulierung unverändert verwendet werden.

## Vier Messzeitpunkte je Variante

- T0: nach Profilerstellung und erster Suche, vor der ersten Nutzernachricht
- T1: nach der Systemantwort auf Nutzernachricht 1
- T2: nach der Systemantwort auf Nutzernachricht 2
- T3: nach der Systemantwort auf Nutzernachricht 3

Für A, B und C ergeben sich je Person zwölf, insgesamt 24 geplante Ranglistensnapshots. Zu jedem
werden tatsächliche Reihenfolge, Scores, Profilstand, Aktion, Antwort und
Kostenprotokoll gespeichert. Eine reine Gesprächsantwort ohne Änderung der
Rangfolge bleibt ein unveränderter Messzeitpunkt; sie wird nicht künstlich in
eine neue Suche umgewandelt.

## Gemeinsame Referenzbewertung durch Codex

Codex bewertet die Stellen selbst im bestehenden Auftrag ohne zusätzliche
Bewertungs-API. Der gemeinsame Bewertungspool enthält die Vereinigung aller
Stellen aus sämtlichen zwölf tatsächlich erhaltenen Snapshots derselben Person.
Für jede der beiden Personen wird ein eigener gemeinsamer Pool gebildet. Jedes
Person-Job-Paar erhält genau **ein** Relevanzurteil, das für diese Person in allen
Varianten und Zeitpunkten unverändert verwendet wird. Die Bewertungspakete enthalten den
vorab eingefrorenen vollständigen Informationsbedarf und die Originalanzeigen,
jedoch keine Systemscore-, Begründungs-, Rang-, Varianten- oder Zeitangaben.
Die Stellen werden in vorab festgelegter zufälliger Reihenfolge beurteilt.

Für jedes Urteil werden Relevanzgrad und konkrete Belege dokumentiert:

- **0:** fachfremd oder aufgrund ausdrücklich zwingender zentraler Anforderungen
  eindeutig nicht zugänglich.
- **1:** nur schwacher fachlicher Anschluss oder größere belegte Lücken,
  beispielsweise zwingende mehrjährige React-Praxis ohne Einstiegspfad.
- **2:** sinnvolle fachliche Passung auf realistischem Einstiegsniveau mit
  erlernbaren Lücken oder noch offenen weichen Wünschen.
- **3:** starke fachliche Passung und konkrete Belege für die wesentlichen Ziele,
  beispielsweise zugängliche Webaufgaben mit Betreuung für Mara oder passende
  zugängliche interne Personalaufgaben mit Einarbeitung für Nora.

Es gelten die ausführlicheren, vorab gespeicherten personenbezogenen Regeln in
`selected-personas.json`. Ort, Arbeitsmodell und Stunden sind weiche Wünsche.
Unbekannte Angaben gelten weder als zugesagte Vorteile noch als nachgewiesene
Konflikte. Demografische Angaben begründen keine Fähigkeits- oder
Eignungsannahmen. Der komplette Bewertungsbedarf bleibt vom Anfang bis zum Ende
identisch, auch solange das System einen Teil der Wünsche noch nicht kennt.

## Metriken

Pro Person, Variante und Zeitpunkt werden **nDCG@10, nDCG@5, Precision@5 und RR@10**
berechnet. Precision zählt Relevanzgrade 2 und 3 als relevant und verwendet immer
fünf Plätze im Nenner. RR ist der Kehrwert des Rangs des ersten relevanten Treffers
unter den ersten zehn; fehlt dieser, ist RR null. Die gewünschte **MRR@10 ist je
Variante und Zeitpunkt der Mittelwert der beiden RR@10-Einzelfallwerte**. Auch
die anderen Kennzahlen können gleichgewichtet über beide Personen zusammengefasst
werden, stets mit tatsächlich verfügbarer Fallzahl. Fehlende Läufe werden nicht
als Nullwerte aufgefüllt. Die 24 Snapshots sind wiederholte Messungen zweier
Personen, keine 24 unabhängigen Fälle.

nDCG verwendet Gewinn `2^Relevanzgrad - 1` und Diskontierung `log2(Rang + 1)`.
Die ideale Rangfolge wird je Nutzerin aus ihrem gemeinsamen Pool über alle
Varianten und Zeitpunkte gebildet. Unbewertete Stellen führen zu einem Fehler.
Fehlt jeglicher positiver Gewinn im Pool, bleibt nDCG undefiniert und wird als
fehlend ausgewiesen. Für alle Kennzahlen zählen die tatsächlichen ersten fünf
beziehungsweise zehn gerankten Ergebnisse ohne Mindestscore.

Berichtet werden die 24 Einzelfall-Messpunkte sowie Veränderungen T1/T2/T3
gegenüber T0 innerhalb jeder Person und Variante. Der A/B/C-Vergleich ist über
dieselben zwei Personen gepaart, bleibt aber rein deskriptiv. Gepaarte Differenzen
verwenden nur vollständig vorliegende Paare und nennen deren Anzahl. Es gibt
keine Konfidenzintervalle, Signifikanztests oder Repräsentativitätsbehauptungen.

## Aussagegrenzen

Der Pilot zeigt mögliche Unterschiede und technische Auffälligkeiten an zwei
konkreten konstruierten Informationsbedarfen. Er beweist nicht, dass A, B oder C
allgemein besser ist. Ein einziger stochastischer Durchlauf pro Person und Variante erlaubt
keine Trennung von stabilem Systemeffekt, Modellvarianz und konkretem
Gesprächsverlauf. Verbesserungen können durch die zusätzlichen Suchinformationen
entstehen und lassen sich nicht allein dem Beratungsstil zuschreiben.

Nutzerprofil und Relevanzurteile sind KI-erstellt; unabhängige menschliche
Referenzurteile fehlen. Der gemeinsame Ergebnispool ist keine Vollbewertung des
gesamten Stellenkorpus. Chatqualität, tatsächlicher Nutzwert und Akzeptanz werden
von diesen Rankingmetriken nicht unmittelbar gemessen. Die Ergebnisse werden
nicht als repräsentativer Konferenznachweis oder als vorher geplante größere
Studie dargestellt.

## Entfernte frühere Tests und Quellen

Die früheren Forschungs- und Anwendungstests wurden auf ausdrücklichen
Nutzerwunsch entfernt und außerhalb des Projekts gesichert. Der unveränderte
Nachweis liegt in `old-tests-removed.json`; historische Ergebnisse werden nicht
in diesen Piloten eingerechnet.

- Stanford Introduction to Information Retrieval, Evaluation of ranked retrieval
  results: https://nlp.stanford.edu/IR-book/html/htmledition/evaluation-of-ranked-retrieval-results-1.html
- OpenAI GPT-5.4 Modell und Preise, im übergeordneten Auftrag am 17.09.2026 geprüft:
  https://developers.openai.com/api/docs/models/gpt-5.4
