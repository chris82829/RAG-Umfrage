# Quellenprüfung und methodische Entscheidungen zu V14

Prüfung: 22. September 2026, Originalpublikationen gelesen; Tabellen 2 (ResQue) und 4 (CRS-Que) zusätzlich als gerenderte PDF-Seiten visuell abgeglichen. Die Veröffentlichungen wurden nicht als Repositorykopien übernommen.

| Quelle | Primärbeleg | Bedeutung für DIANA |
| --- | --- | --- |
| Pu, Chen & Hu (2011), *A User-Centric Evaluation Framework for Recommender Systems*, RecSys, S. 157–164 | [DOI](https://doi.org/10.1145/2043932.2043962), [Autoren-PDF](https://www.comp.hkbu.edu.hk/~lichen/download/p157-pu.pdf), Tabelle 2 S. 161; §5.1 S. 163 | Nutzen enthält drei Items; Zufriedenheit ein Item. Confidence & Trust enthält vier Items. Die verkürzte Auswahl wird nicht als validierte Vollskala bezeichnet. |
| Jin, Chen, Cai & Zhao (2024), *CRS-Que: A User-centric Evaluation Framework for Conversational Recommender Systems*, TORS 2(1), Artikel 2 | [DOI](https://doi.org/10.1145/3631534), [Autoren-PDF](https://yucheng.gold/file/tors23.pdf), Tabelle 4 S. 2:20, Tabelle 5 S. 2:27, §5.3 S. 2:23 | User Control und Transparency jeweils drei Items; Trust & Confidence sechs. Die offizielle Kurzform enthält einzelne Vertreter der Konstrukte, nicht das neue DIANA-Vertrauenspaar. |

## Neue Items und ihre Abgrenzung

`trust_fit` verbindet Vertrauen in Empfehlungen mit erwarteter eigener Passung. Inhaltlicher Bezug besteht zu Vertrauen in Empfehlungen und Zuversicht, die empfohlenen Gegenstände zu mögen. `trust_credibility` richtet sich auf Glaubwürdigkeit der DIANA-Passungseinschätzung. Keines der beiden Items ist eine wortgetreue deutsche Übertragung eines vollständigen Originalkonstrukts. Der userseitig vorgeschlagene Wortlaut bleibt erhalten; Codebuch und Protokoll kennzeichnen die beiden Aussagen als **an ResQue/CRS-Que angelehntes, eigenständig adaptiertes Vertrauenspaar**.

`perceived_character` ist ein DIANA-Manipulationscheck. Ein erkennbarer Charakter ist nicht gleich „menschlich wirken“, Sympathie oder wahrgenommene Kontrolle. Das Item deshalb nicht als CRS-Que-Humanness-Item ausgeben. Die zusätzliche Screening-Frage ist ebenfalls eine Eigenentwicklung.

Die bisher vorhandenen 14 Framework-Aussagen werden nicht umformuliert. Die zwei bestehenden DIANA-Ratings zu Aufwand und Stilkontrolle sind weiterhin Einzelitems. Die Herkunftstypen müssen im Codebuch sichtbar bleiben; eine gemeinsame 1–7-Skala macht nicht jede Aussage zu einer validierten Framework-Skala. ResQue verwendete fünf Zustimmungskategorien, CRS-Que sieben; die einheitliche Skala sowie Übersetzung und Jobkontext benötigen einen Pretest.

## Festgelegte methodische Auflösungen des Vorschlags

- **Welch fest vorgeben**; Levene entscheidet nicht nachträglich zwischen zwei Tests. Die Varianzdiagnose bleibt informativ. Mann–Whitney wird stets als Sensitivität ergänzt.
- **Vier vollständige Skalenwerte:** drei Items für Nutzen/Kontrolle/Transparenz; zwei für Vertrauen. Die pauschale Regel „weniger als drei gültige Antworten ausschließen“ gilt nicht für das neue Zweierpaar.
- **Holm über genau drei Tests**, nicht über alle explorativen Ausgaben und nicht nur über erfolgreich berechenbare Tests.
- **M1 ist kein Gate für H1.** Fehlende Signifikanz kann mangelnde Power bedeuten. Keine Negativaussage „Personas wirken nicht“ aus dem Manipulationscheck ableiten.
- **Keine automatische Fehler-Ausschlussregel:** wiederhergestellte Fehler sind kein Grund, gültige Antworten zu entfernen. Dokumentierte terminale Ausschlüsse werden vor Entblindung gesondert begründet.
- **Fallzahlbeispiel statt fingiertem Freeze:** d = 0,35 und 72 Stunden sind noch nicht bestätigt. Rechner und Entwurfsprotokoll sind vorbereitet; Forschungsentscheidungen werden nicht als erledigt behauptet.
- **26/27 Fragen statt 25/26**, wenn das im Plan zusätzlich verlangte Screening mitgezählt wird. E1 wird nicht ergänzt.
- **Pseudonymisierte Metadaten bleiben verknüpfbar.** Aus technischen Änderungen allein folgt weder Anonymität noch eine abschließende datenschutzrechtliche Bewertung.

## Statistikimplementierung

Die zweiseitigen Welch-Werte wurden mit `scipy.stats.ttest_ind(equal_var=False)` geprüft. Die Fallzahlrechnung verwendet eine nichtzentrale t-Verteilung und wird unabhängig mit `statsmodels.stats.power.TTestIndPower` gegengeprüft. Das ist die übliche balancierte t-Planung unter Gleichvarianz, kein exakter allgemeiner Welch-Powertest. Primäre Quelle für die verwendete API: [SciPy ttest_ind](https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.ttest_ind.html), [statsmodels TTestIndPower](https://www.statsmodels.org/stable/generated/statsmodels.stats.power.TTestIndPower.html).

Hedges g verwendet die Gamma-basierte Bias-Korrektur J mit df = n₁+n₂−2. Das 95%-Intervall ist ein unabhängiger, gruppenweiser Perzentil-Bootstrap; es ist bei kleinen Stichproben und heterogenen Varianzen nur näherungsweise belastbar. Der Mittelwertunterschied wird zusätzlich mit seinem Welch-Intervall berichtet. Alle Richtungen sind konsistent „zuerst genannte Gruppe minus zweite Gruppe“. Nicht schätzbare Koeffizienten bleiben `null`, keine erfundenen Nullen.

Cronbach-α wird aus vollständigen Itemvektoren berechnet. Das Vertrauenspaar erhält zusätzlich Interitemkorrelation und Spearman–Brown; beide ersetzen keine Inhalts- oder Konstruktvalidität. Gruppenwerte und gepoolte Reliabilität werden getrennt ausgewiesen. Ohne Varianz ist ein Koeffizient nicht definiert. Rater-Belegtreue wird getrennt mit ungewichtetem Cohen-κ analysiert; perfekte Übereinstimmung nur in einer Kategorie erzeugt kein definiertes κ.
