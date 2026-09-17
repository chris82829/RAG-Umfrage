"""Create descriptive scientific figures from validated metrics; no API calls."""
from pathlib import Path
import json
import os
import tempfile

os.environ.setdefault('MPLCONFIGDIR', str(Path(tempfile.gettempdir()) / 'diana-persona-mpl-cache'))

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

HERE = Path(__file__).resolve().parent
OUT = HERE / 'run' / 'analysis'


def main():
    report = json.loads((OUT / 'report.json').read_text())
    colors = {'A': '#52647b', 'B': '#007e87', 'C': '#7352b5'}
    metrics = [('ndcg_10', 'nDCG@10'), ('ndcg_5', 'nDCG@5'),
               ('precision_5', 'Precision@5'), ('mrr_10', 'MRR@10')]
    fig, axes = plt.subplots(2, 2, figsize=(10.2, 7.1), sharex=True, sharey=True)
    for ax, (key, label) in zip(axes.flat, metrics):
        for arm, color in colors.items():
            rows = [r for r in report['arm_turn_means'] if r['arm'] == arm]
            rows.sort(key=lambda r: r['turn'])
            points = [(r['turn'], r['metrics'][key]) for r in rows]
            # Undefined or missing metrics remain gaps; never fill with zero.
            ax.plot([x for x, y in points], [float('nan') if y is None else y for x, y in points],
                    marker={'A': 'o', 'B': 's', 'C': '^'}[arm], markersize=6,
                    linewidth=1.7, color=color, label=f'System {arm}', alpha=.9)
        ax.set_title(label, loc='left', fontsize=12, fontweight='bold')
        ax.set_ylim(-.025, 1.055)
        ax.set_xticks(range(4), ['Vor Chat', 'Nach N1', 'Nach N2', 'Nach N3'])
        ax.grid(axis='y', color='#e2e6ec', linewidth=.7)
        ax.spines[['top', 'right']].set_visible(False)
        ax.set_axisbelow(True)
        pair = ('A', 'B') if key == 'precision_5' else ('B', 'C') if key == 'mrr_10' else None
        if pair:
            curves = [[r['metrics'][key] for r in report['arm_turn_means'] if r['arm'] == arm] for arm in pair]
            if curves[0] == curves[1] and curves[0] and all(v is not None for v in curves[0]):
                ax.text(2.9, min(1.025, max(curves[0]) + .035), ' = '.join(pair),
                        ha='right', color='#52647b', fontsize=9)
    fig.suptitle('Ranking im Gespräch · A/B/C', x=.08, ha='left', fontsize=18, fontweight='bold')
    fig.legend(*axes[0, 0].get_legend_handles_labels(), loc='upper right', ncol=3,
               bbox_to_anchor=(.94, .965), frameon=False)
    fig.text(.08, .02, 'Zwei synthetische Personas; Mittelwerte ohne Signifikanzbehauptung.\n'
             'Alle Zeitpunkte gegen den vollständigen, unveränderten Persona-Bedarf; nDCG relativ zum gemeinsamen Ergebnispool.\n'
             'Nachricht 3: reine Passungsfrage ohne Neusortierung; deshalb unveränderte Kennzahlen.',
             fontsize=9, color='#52647b')
    fig.tight_layout(rect=(.04, .075, .98, .92), h_pad=2.3)
    fig.savefig(OUT / 'ranking-verlauf.png', dpi=190, facecolor='white')
    fig.savefig(OUT / 'ranking-verlauf.svg', facecolor='white')
    plt.close(fig)


if __name__ == '__main__':
    main()
