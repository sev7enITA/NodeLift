#!/usr/bin/env python3
"""Run explicitly informed follow-ups, preserving the first-pass responses."""
import shutil
from pathlib import Path
import run_review

if __name__=='__main__':
    base=Path(__file__).resolve().parent
    if not (base/'completion.json').exists():
        raise SystemExit('Complete the initial review first.')
    folder=base/'followup'
    if (folder/'run-manifest.json').exists():
        raise SystemExit('Follow-up evidence already exists; use a new evidence folder.')
    artifact=run_review.ROOT/'artifacts/qwen-review-2026-11-03'
    shutil.copyfile(artifact/'server.log',artifact/'server-initial.log')
    run_review.OUT=folder
    run_review.main()
