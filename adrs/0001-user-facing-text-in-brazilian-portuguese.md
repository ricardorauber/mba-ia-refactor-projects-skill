# 0001 - README in Brazilian Portuguese; skill, specs and code in English; audit reports mixed

- Date: 2026-10-14
- Spec: 0001-repository-setup-and-conventions
- Status: accepted

## Context
The challenge statement and the three legacy projects are in Brazilian Portuguese, the build process requires produced files in American English, and the challenge example of the audit report uses English headings (`## Summary`, `File:`, `Impact:`) with Portuguese descriptions. The previous challenges kept user-facing text in Brazilian Portuguese and everything else in English.

## Options considered
- A: Skill files (SKILL.md and references), specs, ADRs, code and commits in English; README in Brazilian Portuguese; audit reports with English headings/labels and Brazilian Portuguese descriptions — matches the challenge example and the previous challenges.
- B: Everything in Brazilian Portuguese, including the skill — diverges from the build process.
- C: Everything in English except the README — diverges from the challenge example of the report.

## Decision
"Skill EN, relatório misto" (Skill in English, mixed report) — option A.

## Consequences
SKILL.md, every reference file, specs, ADRs, scripts, tests and commit messages are written in American English. The README is written in Brazilian Portuguese. The report template keeps headings, labels and phase banners in English and instructs the agent to write finding descriptions, impacts and recommendations in Brazilian Portuguese.
