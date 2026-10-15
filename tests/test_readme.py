import re
from pathlib import Path

import pytest

README = Path(__file__).resolve().parent.parent / "README.md"
PROJECTS = ["code-smells-project", "ecommerce-api-legacy", "task-manager-api"]
SEVERITY_RANK = {"CRITICAL": 0, "HIGH": 1, "MEDIUM": 2, "LOW": 3}


def section(text, heading):
    match = re.search(rf"^## {re.escape(heading)}\n(.*?)(?=^## |\Z)", text, re.M | re.S)
    assert match, f"missing section: {heading}"
    return match.group(1)


def manual_analysis_severities(project):
    body = section(README.read_text(encoding="utf-8"), "Análise Manual")
    match = re.search(rf"^### {re.escape(project)}\b.*?\n(.*?)(?=^### |\Z)", body, re.M | re.S)
    assert match, f"missing subsection: {project}"
    return re.findall(r"^\|\s*(CRITICAL|HIGH|MEDIUM|LOW)\s*\|", match.group(1), re.M)


@pytest.mark.parametrize("project", PROJECTS)
def test_manual_analysis_has_minimum_findings_in_severity_order(project):
    severities = manual_analysis_severities(project)

    assert len(severities) >= 5
    assert sum(s in ("CRITICAL", "HIGH") for s in severities) >= 1
    assert severities.count("MEDIUM") >= 2
    assert severities.count("LOW") >= 2
    ranks = [SEVERITY_RANK[s] for s in severities]
    assert ranks == sorted(ranks)


RESULTS_ROWS = {
    "code-smells-project": "audit-project-1.md",
    "ecommerce-api-legacy": "audit-project-2.md",
    "task-manager-api": "audit-project-3.md",
}


def test_readme_has_every_required_section():
    text = README.read_text(encoding="utf-8")

    for heading in ["Análise Manual", "Construção da Skill", "Resultados", "Como Executar"]:
        assert re.search(rf"^## {heading}$", text, re.M), heading


@pytest.mark.parametrize("project,report", RESULTS_ROWS.items())
def test_results_table_matches_the_report_summary(project, report):
    results = section(README.read_text(encoding="utf-8"), "Resultados")
    row = re.search(rf"^\| {re.escape(project)} \|[^|]*\| (\d+) \| (\d+) \| (\d+) \| (\d+) \| (\d+) \|", results, re.M)
    assert row, project
    summary_text = (README.parent / "reports" / report).read_text(encoding="utf-8")
    summary = re.search(r"CRITICAL: (\d+) \| HIGH: (\d+) \| MEDIUM: (\d+) \| LOW: (\d+)", summary_text)

    counts = [int(n) for n in row.groups()]
    assert counts[:4] == [int(n) for n in summary.groups()]
    assert counts[4] == sum(counts[:4])
