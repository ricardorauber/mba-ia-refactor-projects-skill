# 0002 - Fast-forward the default branch after each spec

- Date: 2026-10-14
- Spec: 0001-repository-setup-and-conventions
- Status: accepted

## Context
The build process never commits to the default branch, but the delivery requires the default branch of the public fork to contain the skill, the refactored projects and the reports. The same decision was taken in the previous challenges.

## Options considered
- A: Open one pull request per spec and merge them in order at the end.
- B: Open pull requests and let the user merge them.
- C: Fast-forward `main` to each spec branch once it is green.

## Decision
"Commit direto na main" (Commit straight to main) — option C, carried over from the previous challenges.

## Consequences
Each spec is still built in its own worktree and branch. Once a spec is green, committed and pushed, `main` is fast-forwarded to that spec branch and pushed, and the next spec branches from the updated `main`.
