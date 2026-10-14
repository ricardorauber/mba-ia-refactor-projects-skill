import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
SKILL_DIR = ROOT / "code-smells-project" / ".claude" / "skills" / "refactor-arch"
SKILL_MD = SKILL_DIR / "SKILL.md"
REFERENCES_DIR = SKILL_DIR / "references"
CONFIRMATION = "Phase 2 complete. Proceed with refactoring (Phase 3)? [y/n]"
PROJECT_SPECIFIC_TOKENS = [
    "produtos",
    "AppManager",
    "loja.db",
    "tasks.db",
    "code-smells-project",
    "ecommerce-api-legacy",
    "task-manager-api",
]


def frontmatter(text):
    match = re.match(r"^---\n(.*?)\n---\n", text, re.S)
    assert match, "SKILL.md has no YAML frontmatter"
    fields = {}
    for line in match.group(1).splitlines():
        key, _, value = line.partition(":")
        fields[key.strip()] = value.strip()
    return fields


def skill_text():
    return SKILL_MD.read_text(encoding="utf-8")


def test_frontmatter_declares_name_and_description():
    fields = frontmatter(skill_text())

    assert fields.get("name") == "refactor-arch"
    assert fields.get("description")


def test_skill_mentions_exactly_the_existing_reference_files():
    mentioned = set(re.findall(r"references/[\w.-]+\.md", skill_text()))
    existing = {f"references/{path.name}" for path in REFERENCES_DIR.glob("*.md")}

    assert mentioned == existing


def test_skill_ends_phase_two_with_the_confirmation_question():
    assert CONFIRMATION in skill_text()


def test_skill_is_project_agnostic_and_concise():
    text = skill_text()

    for token in PROJECT_SPECIFIC_TOKENS:
        assert token not in text, token
    assert len(text.splitlines()) < 500


def reference_text(name):
    return (REFERENCES_DIR / name).read_text(encoding="utf-8")


def test_report_template_defines_every_report_field():
    text = reference_text("report-template.md")

    for marker in ["## Summary", "## Findings", "File:", "Description:", "Impact:", "Recommendation:", CONFIRMATION]:
        assert marker in text, marker


def test_project_analysis_covers_the_manifests_of_each_stack():
    text = reference_text("project-analysis.md")

    for manifest in ["requirements.txt", "package.json", "pom.xml", "go.mod", "composer.json", "Gemfile", ".csproj"]:
        assert manifest in text, manifest


def catalog_entries():
    text = reference_text("anti-patterns.md")
    blocks = re.split(r"^### (?=AP-\d{2})", text, flags=re.M)[1:]
    entries = {}
    for block in blocks:
        entry_id = block[:5]
        severity = re.search(r"^- Severity: (CRITICAL|HIGH|MEDIUM|LOW)$", block, re.M)
        fix = re.search(r"^- Fix: (PB-\d{2})$", block, re.M)
        entries[entry_id] = {
            "severity": severity.group(1) if severity else None,
            "fix": fix.group(1) if fix else None,
        }
    return entries


def playbook_ids():
    return set(re.findall(r"^### (PB-\d{2})", reference_text("refactoring-playbook.md"), re.M))


def test_catalog_has_enough_entries_with_distributed_severities():
    severities = [entry["severity"] for entry in catalog_entries().values()]

    assert len(severities) >= 14
    for severity in ["CRITICAL", "HIGH", "MEDIUM", "LOW"]:
        assert severities.count(severity) >= 3, severity


def test_catalog_covers_the_deprecated_apis():
    text = reference_text("anti-patterns.md")
    deprecated = text[text.index("Deprecated APIs"):]

    for api in ["Query.get", "utcnow", "new Buffer", "bodyParser", "req.param", "before_first_request", "md5"]:
        assert api in deprecated, api


@pytest.mark.skipif(not playbook_ids(), reason="refactoring playbook has no patterns yet")
def test_every_catalog_entry_points_to_an_existing_playbook_pattern():
    known = playbook_ids()

    for entry_id, entry in catalog_entries().items():
        assert entry["fix"] in known, entry_id
