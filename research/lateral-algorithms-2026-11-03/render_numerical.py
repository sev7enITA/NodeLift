"""Render a targeted numerical diagnostic, never a throughput chart."""
import json
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle

ROOT = Path(__file__).resolve().parent
names = [('metal-fa', 'Metal / flash attention'),
         ('metal-no-fa', 'Metal / conventional attention'),
         ('cpu-fa', 'CPU / flash attention'),
         ('cpu-no-fa', 'CPU / conventional attention')]
plt.rcParams.update({'font.family': 'DejaVu Sans', 'font.size': 11, 'svg.fonttype': 'none'})
fig, ax = plt.subplots(figsize=(13, 6.6))
fig.patch.set_facecolor('#f5f8fc'); ax.set_facecolor('#f5f8fc')
for y, (name, label) in enumerate(names):
    value = json.loads((ROOT / (name + '.json')).read_text())
    for x, window in enumerate(value['windows']):
        flips = [p for p in window['positions'] if p['top1_flipped']]
        assert all(p['max_abs_serial_control'] == 0 for p in window['positions'])
        ax.add_patch(Rectangle((x, y), .93, .85, color='#bd403a' if flips else '#dce8ef', lw=0))
        text = '6104 → 5810' if flips else 'No flip'
        ax.text(x + .465, y + .425, text, ha='center', va='center',
                color='white' if flips else '#173349', fontsize=10, fontweight='bold')
ax.set_xlim(0, 6); ax.set_ylim(4, -.05)
ax.set_yticks([i + .425 for i in range(4)], [label for _, label in names])
ax.set_xticks([i + .465 for i in range(6)], ['H2 / W1', 'H2 / W5', 'H3 / W1', 'H3 / W5', 'H5 / W1', 'H5 / W5'])
ax.xaxis.tick_top(); ax.tick_params(length=0, pad=12)
for spine in ax.spines.values(): spine.set_visible(False)
fig.suptitle('One recorded prefix: batch-shape sensitivity extends beyond Metal',
             x=.51, y=.98, fontsize=16, fontweight='bold', color='#173349')
fig.text(.51, .91, 'Llama 3.1 8B Q4_K_M | H = history batch width | W = current evaluation width',
         ha='center', fontsize=11, color='#45586a')
fig.text(.51, .075, 'Red: at least one argmax differs from that profile\'s serial reference. Every observed flip is at the first position.\n'
         '24 windows / 72 compared positions, one known prefix. Serial-repeat logits match in all profiles.\n'
         'No flip in a tested window is not a general correctness guarantee. This is not a performance benchmark.',
         ha='center', va='center', fontsize=10, color='#45586a')
fig.subplots_adjust(left=.27, right=.98, top=.81, bottom=.2)
fig.savefig(ROOT / 'numerical-isolation.png', dpi=170)
fig.savefig(ROOT / 'numerical-isolation.svg')
