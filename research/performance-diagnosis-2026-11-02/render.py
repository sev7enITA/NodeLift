#!/usr/bin/env python3
"""Render retained physical pairs only; no confidence interval is inferred."""
import json
import statistics
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parent
fig, axes = plt.subplots(1, 2, figsize=(12, 5.5), layout='constrained')
colors = ['#007f99', '#6c4db4', '#c35d16']
for i, width in enumerate((1, 4, 8)):
    raw = json.loads((ROOT / f'iphone-width-{width}.json').read_text())
    ratios, delays = [], []
    for session in raw['sessions']:
        for pair in session['plan']:
            arms = {a['arm']: a for a in session['attempts'] if a['pair_id'] == pair['id']}
            h, c = arms['host'], arms['candidate']
            assert h['status'] == c['status'] == 'completed' and not c['fallback']
            assert all(h[f] == c[f] for f in ('tokens_sha256', 'token_count', 'finish_reason'))
            ratios.append(c['duration_ms'] / h['duration_ms'])
            delays.append(c['ttft_ms'] - h['ttft_ms'])
    for ax, values in zip(axes, (ratios, delays)):
        ax.scatter([i-.08, i, i+.08], values, color=colors[i], s=48, zorder=3)
        median = statistics.median(values)
        ax.plot([i-.25, i+.25], [median, median], color=colors[i], linewidth=3)
        ax.annotate(f'{median:.3f}', (i+.28, median), fontsize=10, va='center')
for ax in axes:
    ax.set_xticks(range(3), ['1 token', '4 tokens', '8 tokens'])
    ax.set_xlabel('Draft width (three paired prompts each)')
    ax.set_xlim(-.45, 2.65)
    ax.grid(axis='y', alpha=.2)
    ax.spines[['top', 'right']].set_visible(False)
axes[0].axhline(1, color='#252b33', linestyle='--', linewidth=1)
axes[0].set_ylim(0, max(7, axes[0].get_ylim()[1]+.5))
axes[0].set_ylabel('Paired duration / Mac-only duration')
axes[0].set_title('Total response: all measured pairs slower')
axes[0].text(-.35, 1.13, 'Mac-only = 1', fontsize=9)
axes[1].axhline(0, color='#252b33', linestyle='--', linewidth=1)
axes[1].set_ylim(bottom=0)
axes[1].set_ylabel('Candidate TTFT minus Mac TTFT (ms)')
axes[1].set_title('First token: added delay')
fig.suptitle('iPhone draft-width follow-up | 2 November 2026', fontsize=16)
fig.supxlabel('Dots: physical pairs. Lines: medians. 9/9 outputs match; no fallback.\nQwen2.5 1.5B / 0.5B Q4_K_M, 128-token budget. Fixed width order; no confidence or energy claim.', fontsize=10)
fig.savefig(ROOT/'iphone-width-comparison.png', dpi=160, facecolor='white')
