# Fragebogen V13: Umsetzung und Prüfung

Stand: 21. September 2026. Die Sicherung vor dieser Änderung liegt auf dem Branch `sicherung-vor-framework-fragebogen-2026-09-21` (Commit `efad58958af4d86e4a36f5158819bc71e33fa065`).

## Forschungsbezug

Der Fragebogen wurde aus der Forschungsfrage neu abgeleitet: C–B untersucht den zusätzlichen wahrgenommenen Nutzen selbst gestaltbarer Beratung; B–A untersucht das Beratungspaket gegenüber dem Basissystem. Die alten Fragen waren keine Vorgabe. Originalquellen, genaue Auswahl und Anpassungen stehen in [QUESTIONNAIRE.md](QUESTIONNAIRE.md). Verbindliche Definition ist [survey_definition_v13.json](survey_definition_v13.json).

14 adaptierte ResQue-/CRS-Que-Aussagen und zwei eigene Studienaussagen verwenden eine einheitliche Skala von 1 bis 7. Mit Kontextangaben und freiwilligem Freitext sind es 22 Fragen für A/B und 23 für C. Die deutsche Auswahl und die Vereinheitlichung der Antwortskalen erfordern noch einen Pretest; sie sind keine bereits validierte deutsche Gesamtskala.

## Produkt und Daten

- Nur V13 wird im Studienablauf, in der Verwaltung und in deren Exporten verwendet. Es gibt keine Fragebogenauswahl. Veraltete Browserentwürfe werden verworfen, alte öffentliche Schreibrequests abgelehnt.
- Nutzen, Suchkontrolle und Nachvollziehbarkeit werden als drei getrennte Mittelwerte aus jeweils drei vollständig numerisch beantworteten Items ausgewertet. Nichtbeurteilbarkeit und fehlende Antworten werden nicht als null gewertet.
- CSV, Codebuch und Auswertungspaket enthalten verständliche Variablennamen, Quellenzuordnungen und die drei Mittelwerte. Historische Parser bleiben nur für technische Kompatibilität und Tests erhalten; alte Antworten werden nicht umgerechnet.
- Modell, Rankinggewichte, Systemprompts und Chatbudget wurden durch diese Fragebogenänderung nicht geändert.

## Ausgeführte Prüfungen

- Gesamte Python-Testsuite: **114 Tests bestanden**. Enthalten sind sechs neue V13-Tests zu Antwortgrenzen, Gruppensichtbarkeit, Datenbankspalten, fehlenden Werten, Exporten und Ablehnung alter Anfragen.
- Frontend-Tests: **31 Tests bestanden**.
- Produktionsbuild mit Vite erfolgreich.
- Browserprüfung gegen die echten Flask-Routen mit isolierter Testdatenbank und simuliertem Modell: A und B bei 1440 Pixel Breite, C bei 390 Pixel Breite; jeweils vollständiger Abschluss und Speicherung aller 16 Bewertungen, Zusatzfrage nur in C. Keine JavaScript-Fehler und kein horizontaler Überlauf.
- Verwaltung bei 390 Pixel Breite: drei getrennte Auswertungsbereiche, keine Fragebogenauswahl, CSV- und ZIP-Download erfolgreich. CSV enthält V13-Mittelwerte und keine V12-Antwortspalten.
- Quellenzuordnung und Wortlaut aller Fragen unabhängig mit den Originaltabellen und der JSON-Definition abgeglichen.

Die Browserdaten waren ausschließlich synthetische lokale Testdaten. Für diese Prüfungen wurden keine kostenpflichtigen Modellanfragen ausgeführt. Diese technischen Prüfungen ersetzen weder eine Nutzerstudie noch die psychometrische Prüfung des Fragebogens.
