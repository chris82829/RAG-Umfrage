# Deskriptive Rankingauswertung: zwei fiktive Personen in A/B/C

**24 von 24 Messpunkten vorhanden.** Zwei synthetische Personen, je eine Sitzung in A, B und C. Pro Sitzung initiale Suche und drei Nachrichten. Die 24 geplanten Messpunkte sind keine 24 unabhängigen Teilnehmer.

nDCG ist relativ zum gemeinsamen bewerteten Stellenpool der jeweiligen Person. Relevanz 2 und 3 zählt für Precision/RR als relevant. Pro Person wird RR@10 berichtet; der Mittelwert über Personen heißt MRR@10. **NA** bedeutet fehlender Messpunkt oder undefinierte Kennzahl. Alle Änderungen beziehen sich auf die gleiche Person und Variante bei T0. Es wurden keine zusätzlichen Modellaufrufe für diese Berechnung ausgeführt.

## Bewertungspools

| Person | Bewertete Stellen | Vorhandene Messpunkte | Relevanz 0 / 1 / 2 / 3 |
|---|---:|---:|---|
| P01 · Mara Seidel | 23 | 12/12 | 4 / 10 / 7 / 2 |
| P06 · Nora Peters | 24 | 12/12 | 7 / 9 / 7 / 1 |

## P01 · Mara Seidel

Je Zelle: Kennzahl **(Änderung gegenüber T0)**.

| Variante | Zeitpunkt | Stellen | nDCG@10 (ΔT0) | nDCG@5 (ΔT0) | Precision@5 (ΔT0) | RR@10 (ΔT0) |
|---|---|---:|---:|---:|---:|---:|
| A | T0 | 20 | 0.657 (+0.000) | 0.583 (+0.000) | 0.800 (+0.000) | 1.000 (+0.000) |
| A | T1 | 20 | 0.601 (-0.057) | 0.510 (-0.072) | 0.800 (+0.000) | 0.500 (-0.500) |
| A | T2 | 20 | 0.685 (+0.028) | 0.664 (+0.082) | 0.800 (+0.000) | 1.000 (+0.000) |
| A | T3 | 20 | 0.685 (+0.028) | 0.664 (+0.082) | 0.800 (+0.000) | 1.000 (+0.000) |
| B | T0 | 20 | 0.892 (+0.000) | 0.738 (+0.000) | 0.800 (+0.000) | 1.000 (+0.000) |
| B | T1 | 20 | 0.872 (-0.020) | 0.713 (-0.026) | 0.800 (+0.000) | 1.000 (+0.000) |
| B | T2 | 20 | 0.877 (-0.015) | 0.713 (-0.026) | 0.800 (+0.000) | 1.000 (+0.000) |
| B | T3 | 20 | 0.877 (-0.015) | 0.713 (-0.026) | 0.800 (+0.000) | 1.000 (+0.000) |
| C | T0 | 20 | 0.710 (+0.000) | 0.580 (+0.000) | 0.600 (+0.000) | 1.000 (+0.000) |
| C | T1 | 20 | 0.691 (-0.018) | 0.483 (-0.098) | 0.400 (-0.200) | 1.000 (+0.000) |
| C | T2 | 20 | 0.696 (-0.014) | 0.654 (+0.074) | 0.600 (+0.000) | 1.000 (+0.000) |
| C | T3 | 20 | 0.696 (-0.014) | 0.654 (+0.074) | 0.600 (+0.000) | 1.000 (+0.000) |

## P06 · Nora Peters

Je Zelle: Kennzahl **(Änderung gegenüber T0)**.

| Variante | Zeitpunkt | Stellen | nDCG@10 (ΔT0) | nDCG@5 (ΔT0) | Precision@5 (ΔT0) | RR@10 (ΔT0) |
|---|---|---:|---:|---:|---:|---:|
| A | T0 | 20 | 0.860 (+0.000) | 0.823 (+0.000) | 1.000 (+0.000) | 1.000 (+0.000) |
| A | T1 | 20 | 0.998 (+0.138) | 1.000 (+0.177) | 1.000 (+0.000) | 1.000 (+0.000) |
| A | T2 | 20 | 0.996 (+0.136) | 1.000 (+0.177) | 1.000 (+0.000) | 1.000 (+0.000) |
| A | T3 | 20 | 0.996 (+0.136) | 1.000 (+0.177) | 1.000 (+0.000) | 1.000 (+0.000) |
| B | T0 | 20 | 0.810 (+0.000) | 0.809 (+0.000) | 1.000 (+0.000) | 1.000 (+0.000) |
| B | T1 | 20 | 0.962 (+0.151) | 1.000 (+0.191) | 1.000 (+0.000) | 1.000 (+0.000) |
| B | T2 | 20 | 0.872 (+0.062) | 0.885 (+0.076) | 1.000 (+0.000) | 1.000 (+0.000) |
| B | T3 | 20 | 0.872 (+0.062) | 0.885 (+0.076) | 1.000 (+0.000) | 1.000 (+0.000) |
| C | T0 | 20 | 0.865 (+0.000) | 0.885 (+0.000) | 1.000 (+0.000) | 1.000 (+0.000) |
| C | T1 | 20 | 0.870 (+0.005) | 0.885 (+0.000) | 1.000 (+0.000) | 1.000 (+0.000) |
| C | T2 | 20 | 0.919 (+0.054) | 0.902 (+0.017) | 0.800 (-0.200) | 1.000 (+0.000) |
| C | T3 | 20 | 0.919 (+0.054) | 0.902 (+0.017) | 0.800 (-0.200) | 1.000 (+0.000) |

## Mittelwerte je Variante und Zeitpunkt

Die Fallzahl steht je Kennzahl dabei. Ein Mittelwert mit n=1 ist kein vollständiger Mittelwert über beide geplanten Personen.

| Variante | Zeitpunkt | nDCG@10 | nDCG@5 | Precision@5 | MRR@10 |
|---|---|---:|---:|---:|---:|
| A | T0 | 0.759 (n=2) | 0.703 (n=2) | 0.900 (n=2) | 1.000 (n=2) |
| A | T1 | 0.800 (n=2) | 0.755 (n=2) | 0.900 (n=2) | 0.750 (n=2) |
| A | T2 | 0.841 (n=2) | 0.832 (n=2) | 0.900 (n=2) | 1.000 (n=2) |
| A | T3 | 0.841 (n=2) | 0.832 (n=2) | 0.900 (n=2) | 1.000 (n=2) |
| B | T0 | 0.851 (n=2) | 0.774 (n=2) | 0.900 (n=2) | 1.000 (n=2) |
| B | T1 | 0.917 (n=2) | 0.856 (n=2) | 0.900 (n=2) | 1.000 (n=2) |
| B | T2 | 0.874 (n=2) | 0.799 (n=2) | 0.900 (n=2) | 1.000 (n=2) |
| B | T3 | 0.874 (n=2) | 0.799 (n=2) | 0.900 (n=2) | 1.000 (n=2) |
| C | T0 | 0.787 (n=2) | 0.733 (n=2) | 0.800 (n=2) | 1.000 (n=2) |
| C | T1 | 0.781 (n=2) | 0.684 (n=2) | 0.700 (n=2) | 1.000 (n=2) |
| C | T2 | 0.808 (n=2) | 0.778 (n=2) | 0.700 (n=2) | 1.000 (n=2) |
| C | T3 | 0.808 (n=2) | 0.778 (n=2) | 0.700 (n=2) | 1.000 (n=2) |

## Mittlere gepaarte Veränderung gegenüber T0

Nur Personen mit definiertem Ausgangs- und Folgewert derselben Variante gehen ein.

| Variante | Zeitpunkt | Δ nDCG@10 | Δ nDCG@5 | Δ Precision@5 | Δ MRR@10 |
|---|---|---:|---:|---:|---:|
| A | T1 | +0.041 (n=2) | +0.053 (n=2) | +0.000 (n=2) | -0.250 (n=2) |
| A | T2 | +0.082 (n=2) | +0.130 (n=2) | +0.000 (n=2) | +0.000 (n=2) |
| A | T3 | +0.082 (n=2) | +0.130 (n=2) | +0.000 (n=2) | +0.000 (n=2) |
| B | T1 | +0.066 (n=2) | +0.083 (n=2) | +0.000 (n=2) | +0.000 (n=2) |
| B | T2 | +0.023 (n=2) | +0.025 (n=2) | +0.000 (n=2) | +0.000 (n=2) |
| B | T3 | +0.023 (n=2) | +0.025 (n=2) | +0.000 (n=2) | +0.000 (n=2) |
| C | T1 | -0.007 (n=2) | -0.049 (n=2) | -0.100 (n=2) | +0.000 (n=2) |
| C | T2 | +0.020 (n=2) | +0.045 (n=2) | -0.100 (n=2) | +0.000 (n=2) |
| C | T3 | +0.020 (n=2) | +0.045 (n=2) | -0.100 (n=2) | +0.000 (n=2) |

## Gepaarte Unterschiede zwischen Varianten

B−A, C−A und C−B verwenden je Zeitpunkt dieselben Personen auf beiden Seiten. Positive Werte sprechen in diesem konkreten Vergleich für die zuerst genannte Variante. Dies sind deskriptive Unterschiede, keine Signifikanznachweise.

| Vergleich | Zeitpunkt | Δ nDCG@10 | Δ nDCG@5 | Δ Precision@5 | Δ MRR@10 |
|---|---|---:|---:|---:|---:|
| B-A | T0 | +0.093 (n=2) | +0.071 (n=2) | +0.000 (n=2) | +0.000 (n=2) |
| B-A | T1 | +0.117 (n=2) | +0.101 (n=2) | +0.000 (n=2) | +0.250 (n=2) |
| B-A | T2 | +0.034 (n=2) | -0.033 (n=2) | +0.000 (n=2) | +0.000 (n=2) |
| B-A | T3 | +0.034 (n=2) | -0.033 (n=2) | +0.000 (n=2) | +0.000 (n=2) |
| C-A | T0 | +0.029 (n=2) | +0.030 (n=2) | -0.100 (n=2) | +0.000 (n=2) |
| C-A | T1 | -0.019 (n=2) | -0.071 (n=2) | -0.200 (n=2) | +0.250 (n=2) |
| C-A | T2 | -0.033 (n=2) | -0.054 (n=2) | -0.200 (n=2) | +0.000 (n=2) |
| C-A | T3 | -0.033 (n=2) | -0.054 (n=2) | -0.200 (n=2) | +0.000 (n=2) |
| C-B | T0 | -0.064 (n=2) | -0.041 (n=2) | -0.100 (n=2) | +0.000 (n=2) |
| C-B | T1 | -0.136 (n=2) | -0.173 (n=2) | -0.200 (n=2) | +0.000 (n=2) |
| C-B | T2 | -0.067 (n=2) | -0.021 (n=2) | -0.200 (n=2) | +0.000 (n=2) |
| C-B | T3 | -0.067 (n=2) | -0.021 (n=2) | -0.200 (n=2) | +0.000 (n=2) |

## Unterschied der Veränderungen seit T0

Verglichen wird (Variante X bei Tn − X bei T0) minus (Variante Y bei Tn − Y bei T0). Pro Person müssen alle vier Werte vorliegen.

| Vergleich | Zeitpunkt | ΔΔ nDCG@10 | ΔΔ nDCG@5 | ΔΔ Precision@5 | ΔΔ MRR@10 |
|---|---|---:|---:|---:|---:|
| B-A | T1 | +0.025 (n=2) | +0.030 (n=2) | +0.000 (n=2) | +0.250 (n=2) |
| B-A | T2 | -0.059 (n=2) | -0.104 (n=2) | +0.000 (n=2) | +0.000 (n=2) |
| B-A | T3 | -0.059 (n=2) | -0.104 (n=2) | +0.000 (n=2) | +0.000 (n=2) |
| C-A | T1 | -0.048 (n=2) | -0.101 (n=2) | -0.100 (n=2) | +0.250 (n=2) |
| C-A | T2 | -0.062 (n=2) | -0.084 (n=2) | -0.100 (n=2) | +0.000 (n=2) |
| C-A | T3 | -0.062 (n=2) | -0.084 (n=2) | -0.100 (n=2) | +0.000 (n=2) |
| C-B | T1 | -0.073 (n=2) | -0.131 (n=2) | -0.100 (n=2) | +0.000 (n=2) |
| C-B | T2 | -0.003 (n=2) | +0.020 (n=2) | -0.100 (n=2) | +0.000 (n=2) |
| C-B | T3 | -0.003 (n=2) | +0.020 (n=2) | -0.100 (n=2) | +0.000 (n=2) |

## Fehlende Messpunkte

Keine fehlenden Messpunkte.

## Aussagegrenzen

- Zwei konstruierte synthetische Personen; keine repräsentative Nutzerstichprobe.
- Ein stochastischer Lauf je Person/Variante; keine Signifikanztests oder Konfidenzintervalle.
- Codex erstellt Nutzerprofile und Relevanzurteile; keine unabhängige menschliche Referenz.
- Die ideale Rangfolge stammt aus dem gepoolten Ergebnisbestand, nicht aus einer vollständigen Bewertung aller 8.537 Stellen.
- Zusätzliche Informationen im Gespräch können Änderungen erklären. Ein Persönlichkeitseffekt ist damit nicht isoliert nachgewiesen.
- Rankingmetriken messen keine Chatqualität, Bedienbarkeit, Zufriedenheit oder tatsächliche Einstellungschancen.

## Nachvollziehbarkeit

Der JSON-Bericht enthält alle Eingabeprüfsummen, vollständige Einzelwerte, verwendete Personenpaare, Fallzahlen und die Definitionen. Vor der Berechnung wurden Bewertungsabdeckung, IDs, Relevanzgrade, Dopplungen, Poolhash und Übereinstimmung des Pools mit den gespeicherten Rangfolgen geprüft.
