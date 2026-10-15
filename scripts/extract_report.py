"""Builds reports/audit-project-N.md from a Phase 1-2 transcript.

Keeps the Phase 1 block, the endpoint inventory and the audit report through the
confirmation question, trimming the agent's narration around them.
Usage: python3 extract_report.py <transcript.md> <report.md> <title>
"""
import sys
from pathlib import Path

BANNER = "=" * 32
QUESTION = "Phase 2 complete. Proceed with refactoring (Phase 3)? [y/n]"


def extract(text):
    phase1_start = text.index(f"{BANNER}\nPHASE 1: PROJECT ANALYSIS")
    phase1_end = text.index(BANNER, text.index("PHASE 1: PROJECT ANALYSIS") + len(BANNER) * 2) + len(BANNER)
    endpoints_start = text.index("## Endpoints", phase1_end)
    endpoints_end = text.index(BANNER, endpoints_start)
    audit_start = text.index(f"{BANNER}\nARCHITECTURE AUDIT REPORT")
    audit_end = text.index(QUESTION, audit_start) + len(QUESTION)
    return "\n\n".join([
        text[phase1_start:phase1_end].strip(),
        text[endpoints_start:endpoints_end].strip(),
        text[audit_start:audit_end].strip(),
    ]) + "\n"


def main(transcript, report, title):
    body = extract(Path(transcript).read_text(encoding="utf-8"))
    link = Path(transcript).name
    header = (f"# {title}\n\nPhase 1 and Phase 2 output of `/refactor-arch`, as printed by the skill "
              f"(transcript: [`logs/{link}`](logs/{link})).\n\n")
    Path(report).write_text(header + body, encoding="utf-8")


if __name__ == "__main__":
    main(*sys.argv[1:4])
