"""Render the local feasibility probe. Requires matplotlib; no inferred wire data."""
import json
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

HERE = Path(__file__).resolve().parent
data = json.loads((HERE / 'analysis.json').read_text())
keys = ('small_full', 'small_segment', 'target_full', 'target_segment')
labels = ('0.5B / full collection', '0.5B / relevant record',
          '1.5B / full collection', '1.5B / relevant record')
colors = ('#8196ac', '#1ec8be', '#8196ac', '#1ec8be')
plt.rcParams.update({'font.family': 'DejaVu Sans', 'font.size': 11,
                     'axes.spines.top': False, 'axes.spines.right': False})
fig, axes = plt.subplots(2, 2, figsize=(14, 9))
fig.suptitle('Resident models: smaller task context, unqualified output contract', fontsize=17, fontweight='bold', y=.98)
panels = (
    ('median_request_payload_bytes', 'Serialized request size', 'Bytes; excludes transport overhead', None),
    ('median_completed_task_ms', 'Raw task completion time', 'Milliseconds; includes invalid outputs', None),
    ('correct', 'Primary result: strict output contract', 'Passing attempts out of 12', 12),
    ('posthoc_correct_after_fence_removal', 'Post-hoc diagnostic: remove Markdown fence', 'Correct fields and shape out of 12; not the original contract', 12),
)
for ax, (metric, title, xlabel, limit) in zip(axes.flat, panels):
    values = [data['cells'][k][metric] for k in keys]
    bars = ax.barh(labels, values, color=colors, height=.6)
    ax.invert_yaxis()
    ax.set_title(title, loc='left', fontsize=12, fontweight='bold', pad=12)
    ax.set_xlabel(xlabel, fontsize=9)
    ax.set_axisbelow(True)
    ax.grid(axis='x', alpha=.2)
    maxval = limit if limit else max(values) * 1.17
    ax.set_xlim(0, maxval * (1.12 if limit else 1))
    if limit:
        ax.set_xticks((0, 3, 6, 9, 12))
    for bar, value in zip(bars, values):
        label = str(int(value)) if limit else f'{value:,.0f}'
        ax.text(value + maxval * .02, bar.get_y() + bar.get_height() / 2, label, va='center')
fig.text(.025, .025,
         'Same Mac, real Qwen2.5 weights, 6 synthetic records x 2 repetitions per cell. Models resident; KV reset per task.\n'
         'No phones, network transfer, parallel scheduling or energy measurement. All 48 raw outputs fail the strict contract.\n'
         'Post-hoc parsing is diagnostic only. Completion lengths differ. No usable workflow or distributed speedup is established.',
         fontsize=10, color='#394856')
fig.tight_layout(rect=(0, .11, 1, .94), h_pad=2.5, w_pad=2.5)
fig.savefig(HERE / 'resident-task-pilot.png', dpi=160, facecolor='white')
plt.close(fig)
