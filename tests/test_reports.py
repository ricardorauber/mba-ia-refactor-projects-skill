import re
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
REPORTS = sorted((ROOT / "reports").glob("audit-project-*.md"))
PROJECTS = {"1": "code-smells-project", "2": "ecommerce-api-legacy", "3": "task-manager-api"}
ORIGINAL_COMMIT = "6d1ce62"
SEVERITY_RANK = {"CRITICAL": 0, "HIGH": 1, "MEDIUM": 2, "LOW": 3}
LOCATION = re.compile(r"^(?P<path>[\w./-]+):(?P<start>\d+)(?:-(?P<end>\d+))?$")


def parse_report(path):
    text = path.read_text(encoding="utf-8")
    findings = []
    for match in re.finditer(r"^### \[(CRITICAL|HIGH|MEDIUM|LOW)\] (.+?)\n(.*?)(?=^### |^=+$|\Z)", text, re.M | re.S):
        file_line = re.search(r"^File: (.+)$", match.group(3), re.M)
        findings.append({
            "severity": match.group(1),
            "title": match.group(2),
            "body": match.group(3),
            "locations": file_line.group(1) if file_line else "",
        })
    summary = re.search(r"CRITICAL: (\d+) \| HIGH: (\d+) \| MEDIUM: (\d+) \| LOW: (\d+)", text)
    return text, findings, summary


def locations(raw):
    cleaned = re.sub(r"\s*\(\+\d+ more\)", "", raw)
    return [item.strip() for item in cleaned.split(",") if item.strip()]


def original_line_count(project, relative_path):
    result = subprocess.run(
        ["git", "show", f"{ORIGINAL_COMMIT}:{project}/{relative_path}"],
        cwd=ROOT, capture_output=True, text=True,
    )
    assert result.returncode == 0, f"{relative_path} does not exist in the original {project}"
    return len(result.stdout.splitlines())


def report_number(path):
    return re.search(r"audit-project-(\d)", path.name).group(1)


@pytest.mark.parametrize("report", REPORTS, ids=lambda path: path.name)
def test_report_follows_the_template(report):
    text, findings, summary = parse_report(report)

    assert "## Summary" in text
    assert "## Findings" in text
    assert len(findings) >= 5
    assert any(f["severity"] in ("CRITICAL", "HIGH") for f in findings)
    ranks = [SEVERITY_RANK[f["severity"]] for f in findings]
    assert ranks == sorted(ranks)
    for finding in findings:
        assert finding["locations"], finding["title"]
        for location in locations(finding["locations"]):
            assert LOCATION.match(location), location
    assert summary, "missing summary counts"
    counted = [sum(f["severity"] == s for f in findings) for s in SEVERITY_RANK]
    assert [int(n) for n in summary.groups()] == counted


@pytest.mark.parametrize("report", REPORTS, ids=lambda path: path.name)
def test_report_locations_exist_in_the_original_code(report):
    project = PROJECTS[report_number(report)]
    _, findings, _ = parse_report(report)

    for finding in findings:
        for location in locations(finding["locations"]):
            match = LOCATION.match(location)
            last_line = int(match.group("end") or match.group("start"))
            assert last_line <= original_line_count(project, match.group("path")), location
