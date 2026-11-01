#!/usr/bin/env python3
"""Validate and export the canonical, source-backed NodeLift comparison atlas."""
import csv
import hashlib
import json
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "site/NodeLift/data"
FIELDS = {
    "name": "Project", "category": "Category", "ecosystem": "Ecosystem",
    "origin": "Documented origin", "stage": "Readiness", "license": "License",
    "architecture": "Architecture", "host": "Host", "android": "Android",
    "ios": "iOS", "mobile_compute": "Mobile compute", "capacity": "Memory / capacity",
    "single_chat": "Single-chat latency", "transport": "Transport", "api": "Integration",
    "security": "Security / trust", "evidence": "Evidence", "limitations": "Limits",
    "lesson": "Lesson for NodeLift", "revision": "Source revision", "checked": "Checked",
}

def cell(value):
    value = str(value)
    return "'" + value if value.startswith(("=", "+", "-", "@", "\t", "\r")) else value

def main():
    dataset = json.loads((DATA / "comparison.json").read_text())
    projects = dataset["projects"]
    assert len({p["id"] for p in projects}) == len(projects), "Duplicate IDs"
    categories = {"distributed", "mobile", "runtime", "serving", "research", "baseline"}
    for project in projects:
        assert project["category"] in categories
        assert project["ecosystem"] in {"western", "asia", "international", "unverified"}
        assert all(isinstance(project[k], str) and project[k].strip() for k in FIELDS)
        assert project["sources"], project["id"]
        assert project["checked"] == dataset["updated"]
        for source in project["sources"]:
            url = urlparse(source["url"])
            assert url.scheme == "https" and url.hostname in {
                "github.com", "arxiv.org", "aclanthology.org", "lmstudio.ai", "www.mindspore.cn"
            }, source
            assert not url.username and not url.password and not url.query, source
    columns = ["id", *FIELDS, "tags", "sources"]
    with (DATA / "comparison.csv").open("w", encoding="utf-8-sig", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=columns, lineterminator="\n")
        writer.writeheader()
        for project in projects:
            row = {key: cell(project[key]) for key in ["id", *FIELDS]}
            row["tags"] = "; ".join(project["tags"])
            row["sources"] = " | ".join(f"{s['label']}: {s['url']}" for s in project["sources"])
            writer.writerow(row)
    text = ["# NodeLift: Detailed comparison atlas", "",
            f"**{dataset['updated']} · {len(projects)} selected entries · Dataset v{dataset['schema_version']}**", "",
            dataset["scope"]["en"], "", "[Method / Metodo](methodology.md)", "",
            "Technical descriptions are canonical English. Upstream results are not NodeLift replications.", "",
            "| Project | Category | Mobile compute | Memory / capacity |",
            "|---|---|---|---|"]
    for project in projects:
        values = [project[k].replace("|", "\\|").replace("\n", " ") for k in
                  ("name", "category", "mobile_compute", "capacity")]
        text.append("| " + " | ".join(values) + " |")
    for project in projects:
        text += ["", f"## {project['name']}", "", f"ID: `{project['id']}`", "",
                 "| Criterion | Assessment |", "|---|---|"]
        for key, label in FIELDS.items():
            if key == "name":
                continue
            value = project[key].replace("|", "\\|").replace("\n", " ")
            text.append(f"| {label} | {value} |")
        text += ["", "Sources: " + "; ".join(f"[{s['label']}]({s['url']})" for s in project["sources"])]
    (DATA / "comparison.md").write_text("\n".join(text) + "\n")
    inventory = ROOT / "research/comparison-2026-10-31/source-inventory.json"
    (DATA / "source-inventory.json").write_bytes(inventory.read_bytes())
    assessment = (ROOT / "research/comparison-2026-10-31/ASSESSMENT.md").read_text()
    assessment = assessment.replace("../../site/NodeLift/data/", "").replace(
        "../measurements/ENGINE_RESULTS.md",
        "https://github.com/sev7enITA/NodeLift/blob/c7a41e25aaa6a9bea52ab27a12a652c7a5e71054/research/measurements/ENGINE_RESULTS.md")
    (DATA / "assessment.md").write_text(assessment)
    files = ["comparison.json", "comparison.csv", "comparison.md", "methodology.md", "source-inventory.json", "assessment.md"]
    manifest = {"updated": dataset["updated"], "entries": len(projects), "files": {
        name: {"bytes": (DATA / name).stat().st_size,
               "sha256": hashlib.sha256((DATA / name).read_bytes()).hexdigest()} for name in files}}
    (DATA / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    print(json.dumps({"entries": len(projects), "categories": {
        key: sum(p["category"] == key for p in projects) for key in sorted(categories)},
        "exports": files}, indent=2))

if __name__ == "__main__":
    main()
