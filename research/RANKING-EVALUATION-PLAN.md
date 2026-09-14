# Geplanter technischer Check der Prioritäten und Rangfolge

**Status: ausschließlich ein Plan.** Noch nicht ausgeführt, nicht terminiert und
keine Automation eingerichtet. Es wurden dafür keine Stellen bewertet, keine
LLM-Anfragen gestellt und keine neuen Nutzerinhalte aufgezeichnet. Umfang und
Bewertungskriterien sollen vor einer späteren Durchführung festgelegt werden.

## Fragestellung

Verändert eine andere Beratungspriorität die Reihenfolge der Stellen in einer
inhaltlich nachvollziehbaren Richtung, ohne fachliche Anforderungen zu übergehen?
Wie groß ist dieser beabsichtigte Unterschied im Vergleich zur Variation bei
unveränderten Eingaben?

Ein anderes Ranking allein ist kein Qualitätsnachweis. Ein unverändertes Ranking
kann ebenfalls richtig sein, etwa wenn fachliche Passung die Kandidaten klar
trennt oder die Anzeigen keine Unterschiede beim geänderten Wunsch enthalten.
Der Check ergänzt die V10-Nutzungsstudie; er misst weder subjektiven Mehrwert
noch Bewerbungserfolg.

## Vergleich kontrolliert aufbauen

1. Eine kleine, fachlich begründete Sammlung **synthetischer** Suchprofile und
   Prüffälle vorab festlegen. Verschiedene Fachrichtungen und Stellenarten abdecken.
   Klare fachliche Fehlpassungen ebenso berücksichtigen wie fachlich ähnlich
   geeignete Stellen mit unterschiedlichen Lern-, Vertiefungs- oder Gestaltungsangeboten.
   Profile nicht nachträglich danach auswählen, ob das System gut abschneidet.
2. Je Prüffall Nutzerprofil, Suchwünsche, harte Stellenartfilter, Datensatz,
   Stellenbeschreibungen und denselben Kandidatenpool unverändert halten.
   Für den isolierten Reranking-Test dieselben bis zu 20 Anzeigen verwenden.
   Das prüft die Nachsortierung, nicht die Vollständigkeit der vorgeschalteten Suche.
3. Nur die untersuchte Priorität ändern, beispielsweise ausgewogen gegenüber
   fachlicher Vertiefung oder Lernen. Alle anderen beeinflussenden Einstellungen
   einschließlich Gesprächseigenschaften konstant halten. Vorher festhalten,
   welche dokumentierten Anzeigenmerkmale eine höhere Priorität rechtfertigen.
4. Kontrollfälle mit unveränderten Eingaben wiederholen. Zusätzlich reine
   Namensänderungen und Änderungen des Gesprächsstils gezielt getrennt betrachten:
   Ein Name allein soll keine fachlichen Vorteile erzeugen. Wenn eine Eigenschaft
   laut Implementierung auch Gewichte verändert, ist sie kein reiner Stiltest.

## Deterministische Gewichtung und Modellvariation trennen

Zwei Ebenen getrennt prüfen und berichten:

- **Gewichtungslogik:** Mit festgehaltenen Teilbewertungen nachvollziehen, ob
  Gewichtung, Rundung, fachliche Score-Grenzen und Gleichstandsregeln korrekt
  angewendet werden. Erwartete Ergebnisse unabhängig von der getesteten
  Berechnungsfunktion bestimmen. Das ist eine Implementierungsprüfung, noch kein
  Nachweis, dass die Teilbewertungen inhaltlich stimmen.
- **LLM-Bewertungen:** Mit gleichem Modell-Snapshot, Prompt, Profil, Anzeigen und
  Parametern wiederholte unabhängige Bewertungen vorsehen. Zahl der Wiederholungen
  und Umgang mit Fehlern vorab festlegen. Dokumentieren, wann ein Cache verwendet
  wird: Wiederverwendete Teilwerte messen keine neue Modellvariation. Fehler und
  Wiederholungen nicht still aus der Auswertung entfernen.

Der gewünschte Prioritätseffekt wird mit der Streuung innerhalb unveränderter
Bedingungen verglichen. Einzelne besonders anschauliche Läufe nicht als Beweis
für einen stabilen Effekt darstellen.

## Unabhängige inhaltliche Bewertung

Vor Modellaufrufen eine kurze Bewertungsanleitung festlegen. Unabhängige fachkundige
Beurteilende prüfen Profil und originale Stellenbeschreibung, möglichst ohne die
Systemrangfolge, Variante oder LLM-Scores zu sehen. Fachliche Eignung und die
relevanten Zusatzdimensionen getrennt beurteilen. Unterschiede zwischen
Beurteilenden sichtbar machen und nach einer zuvor festgelegten Regel klären.

Prüfpunkte für Begründungen:

- Lassen sich Aussagen über verlangte Kenntnisse, Aufgaben und Rahmenbedingungen
  tatsächlich in Anzeige oder Profil belegen?
- Werden fehlende Angaben als unbekannt behandelt, statt Vorteile zu erfinden?
- Bleibt eine klare fachliche Fehlpassung auch bei einer attraktiven weichen
  Priorität erkennbar?
- Passt die genannte Begründung zur tatsächlich geänderten Priorität?

LLM-eigene Scores oder Begründungen sind nicht die unabhängige Referenz, mit der
sich dasselbe LLM seinen Erfolg bestätigt. Für unterschiedliche legitime
Prioritäten kann es mehrere sinnvolle Rangfolgen geben; eine einzige starre
Referenzliste darf diese Unterschiede nicht unbegründet als Fehler zählen.

## Geplante Auswertung

Vor Durchführung wenige Kennwerte auswählen und festschreiben:

- Richtung und Größenordnung der Score-/Rangänderung bei unabhängig belegten
  Prioritätsmerkmalen, einschließlich fachlicher Fehlpassungen.
- Rangstabilität und Überschneidung der oberen Ergebnisse bei identischen Eingaben;
  gewünschte Änderungen separat von dieser Grundvariation berichten.
- Falls abgestufte unabhängige Relevanzurteile vorliegen: beispielsweise NDCG@5
  und NDCG@20, mit einer vorab begründeten, zur jeweiligen Suchpriorität passenden
  Relevanzdefinition. Diese Kennzahlen nicht mit dem LLM-Score gleichsetzen.
- Anteil belegter, unbelegter und widersprüchlicher Aussagen in den Begründungen.
- Unterschiede zwischen Beurteilenden, unvollständige Bewertungen und technische
  Fehler; bei zusammengefassten Ergebnissen Prüffälle/Profile als Einheiten beachten.
  Mehrere Anzeigen und Wiederholungen desselben Profils sind keine unabhängigen Personen.

Ein separater späterer Retrieval-Test könnte untersuchen, ob passende Anzeigen
überhaupt in den Kandidatenpool gelangen. Aus einem festen Top-20-Reranking-Test
lässt sich das nicht ableiten.

## Nachvollziehbarkeit und Abschluss

Commit, Modell-Snapshot, Prompt-/MLDS-Dateien, synthetische Profile, Datensatz- und
Kandidatenprüfsummen, Cachezustand, Parameter, Wiederholungsanzahl, unabhängige
Urteile und Auswerteschritte gemeinsam archivieren. Lizenz- und Zugangsbedingungen
der verwendeten Anzeigen vor einer Veröffentlichung berücksichtigen.

Erst nach der späteren Durchführung Ergebnisse, Grenzen und notwendige Änderungen
beurteilen. Falls der produktive Rankingablauf für die Hauptstudie geändert wird,
den neuen Systemstand dokumentieren und nicht ungeprüft mit früheren Teilnahmen
zusammen auswerten. Dieser Plan startet keine Prüfung und setzt keinen Termin.
