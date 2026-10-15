"""Turns a `claude --output-format stream-json` log into a readable Markdown transcript.

Usage: python3 render_transcript.py <log.jsonl> <transcript.md>
Prints the session id to stdout. The raw log is rewritten without the details of the
local Claude Code setup (plugins, MCP servers, memory paths), since logs are published.
"""
import json
import sys
from pathlib import Path

MAX_COMMAND_CHARS = 300
INIT_FIELDS = ("type", "subtype", "session_id", "model", "permissionMode", "claude_code_version", "cwd", "tools", "uuid")
DROPPED_SUBTYPES = {"plugin", "ui_status"}


def sanitize(events):
    kept = []
    for event in events:
        if event.get("type") == "system" and event.get("subtype") in DROPPED_SUBTYPES:
            continue
        if event.get("type") == "system" and event.get("subtype") == "init":
            event = {key: event[key] for key in INIT_FIELDS if key in event}
        kept.append(event)
    return kept


def tool_summary(block):
    name = block.get("name", "tool")
    data = block.get("input", {})
    detail = data.get("command") or data.get("file_path") or data.get("pattern") or data.get("skill") or ""
    detail = " ".join(str(detail).split())
    if len(detail) > MAX_COMMAND_CHARS:
        detail = detail[:MAX_COMMAND_CHARS] + " ..."
    return f"> `{name}` {detail}".rstrip()


def render(events):
    session_id, model, lines = "", "", []
    for event in events:
        kind = event.get("type")
        if kind == "system" and event.get("subtype") == "init":
            session_id = event.get("session_id", session_id)
            model = event.get("model", model)
        elif kind == "assistant":
            for block in event.get("message", {}).get("content", []):
                if block.get("type") == "text" and block.get("text", "").strip():
                    lines += [block["text"].strip(), ""]
                elif block.get("type") == "tool_use":
                    lines += [tool_summary(block), ""]
        elif kind == "result":
            lines += [
                "---",
                f"Result: {event.get('subtype')} | turns: {event.get('num_turns')} | "
                f"duration: {round(event.get('duration_ms', 0) / 1000)}s",
            ]
    header = [f"# Skill run transcript", "", f"- Session: `{session_id}`", f"- Model: `{model}`", ""]
    return session_id, "\n".join(header + lines) + "\n"


def main(log_path, transcript_path):
    events = []
    for line in Path(log_path).read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line:
            events.append(json.loads(line))
    events = sanitize(events)
    Path(log_path).write_text("".join(json.dumps(e, ensure_ascii=False) + "\n" for e in events), encoding="utf-8")
    session_id, text = render(events)
    Path(transcript_path).write_text(text, encoding="utf-8")
    print(session_id)


if __name__ == "__main__":
    main(*sys.argv[1:3])
