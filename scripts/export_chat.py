"""Export one legacy Antigravity transcript to a separate destination by default.

Produces:
1. outputs/chat_export/transcript_full.jsonl - redacted machine-readable JSONL transcript
2. outputs/chat_export/chat_log.md           - clean, human-readable Markdown transcript
"""

import argparse
import json
import pathlib
import re
import shutil
import sys
import tempfile
import uuid

from _console import configure_utf8

DEFAULT_LOG_PATH = pathlib.Path.home() / (
    ".gemini/antigravity-ide/brain/04dc995e-54b1-483e-8d66-964372b8491e/"
    ".system_generated/logs/transcript_full.jsonl"
)
OUTPUT_DIR = pathlib.Path("outputs/chat_export")


def redact_text(text: str) -> str:
    """Remove local identities while retaining repository-relative path tails."""
    root = (
        r"(?<![A-Za-z0-9])[a-z]:[\\/]+(?:[^\\/\r\n\"'<>`|]*[\\/]+)*"
        + re.escape(pathlib.Path(__file__).resolve().parents[1].name)
        + r"(?:[\\/]+|(?=$|[\s\"'<>`|),;]))"
    )
    text = re.sub(root, "<path>/", text, flags=re.IGNORECASE)
    text = re.sub(
        r"(?i)(?<![A-Za-z0-9])[a-z]:[\\/]+[^\s\"'<>`|;,()\[\]{}]*",
        "<path>",
        text,
    )
    text = re.sub(
        r"(?<![\w/:])/(?:home|Users|tmp|var/tmp|mnt|private)/[^\s\"'<>`|;,()\[\]{}]*",
        "<path>",
        text,
    )
    text = re.sub(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}", "<email>", text)
    username = pathlib.Path.home().name
    if username:
        text = re.sub(re.escape(username), "<user>", text, flags=re.IGNORECASE)
    text = re.sub(
        r"(?i)(?:sk-[A-Za-z0-9_-]{16,}|ghp_[A-Za-z0-9]{20,}|AIza[A-Za-z0-9_-]{20,}|Bearer\s+[A-Za-z0-9._~-]{16,})",
        "<credential>",
        text,
    )
    return text


def redact_value(value):
    if isinstance(value, str):
        return redact_text(value)
    if isinstance(value, list):
        return [redact_value(item) for item in value]
    if isinstance(value, dict):
        return {redact_text(key): redact_value(item) for key, item in value.items()}
    return value


def clean_user_text(text: str) -> str:
    # Extract content inside <USER_REQUEST> if present
    match = re.search(r"<USER_REQUEST>\s*(.*?)\s*</USER_REQUEST>", text, re.DOTALL)
    if match:
        text = match.group(1)
    # Strip any remaining system XML tags
    text = re.sub(r"<ADDITIONAL_METADATA>.*?</ADDITIONAL_METADATA>", "", text, flags=re.DOTALL)
    text = re.sub(r"<USER_SETTINGS_CHANGE>.*?</USER_SETTINGS_CHANGE>", "", text, flags=re.DOTALL)
    return text.strip()


def _export_unchecked(log_path, out_dir):
    if not log_path.exists():
        print(redact_text(f"Error: transcript file not found at {log_path}"), file=sys.stderr)
        sys.exit(1)

    out_dir.mkdir(parents=True, exist_ok=True)

    # 1. Redact JSON values before serializing, preserving valid JSON escapes.
    raw_dest = out_dir / "transcript_full.jsonl"
    with (
        log_path.open("r", encoding="utf-8") as source,
        raw_dest.open("w", encoding="utf-8") as dest,
    ):
        for line in source:
            try:
                dest.write(json.dumps(redact_value(json.loads(line)), ensure_ascii=False) + "\n")
            except json.JSONDecodeError:
                dest.write(redact_text(line))
    print(redact_text(f"Copied raw JSONL to {raw_dest}"))

    # 2. Parse and format Markdown
    md_dest = out_dir / "chat_log.md"
    with (
        open(raw_dest, "r", encoding="utf-8") as f_in,
        open(md_dest, "w", encoding="utf-8") as f_out,
    ):
        f_out.write("# Ur AI Internship Project — AI Interaction Log\n\n")
        f_out.write("> **Source:** Antigravity IDE session logs (`transcript_full.jsonl`)\n")
        f_out.write(
            "> **Task:** Document Intelligence & VLM R&D take-home "
            "(Japanese Balance Sheet PDF parsing)\n\n"
        )
        f_out.write("---\n\n")

        current_user_step = 0

        for line in f_in:
            line = line.strip()
            if not line:
                continue
            try:
                item = json.loads(line)
            except Exception:
                continue

            stype = item.get("type")
            created_at = item.get("created_at", "")

            if stype == "USER_INPUT":
                current_user_step += 1
                raw_content = item.get("content", "")
                cleaned = clean_user_text(raw_content)
                if not cleaned:
                    continue
                f_out.write(f"## 👤 User Prompt #{current_user_step} ({created_at})\n\n")
                f_out.write(f"{cleaned}\n\n")
                f_out.write("---\n\n")

            elif stype == "PLANNER_RESPONSE":
                content = item.get("content", "")
                tool_calls = item.get("tool_calls", [])

                # Include response text if any
                if content and content.strip():
                    f_out.write(f"### 🤖 Assistant Response ({created_at})\n\n")
                    f_out.write(f"{content.strip()}\n\n")
                    f_out.write("---\n\n")

                # If there were tool actions, we can summarize them lightly
                if tool_calls:
                    call_summaries = []
                    for call in tool_calls:
                        name = call.get("name", "tool")
                        args = call.get("args", {})
                        summary = args.get("toolSummary", name)
                        call_summaries.append(f"`{name}` ({summary})")
                    if call_summaries:
                        f_out.write(f"*Tool Actions Executed: {', '.join(call_summaries)}*\n\n")

    print(redact_text(f"Generated Markdown log at {md_dest}"))


def export(log_path=DEFAULT_LOG_PATH, out_dir=OUTPUT_DIR, *, replace=False):
    """Default to a separate ignored destination; replacement requires a byte backup.

    Validate all input JSON before touching outputs. Stage both products before
    replacing either. A successful explicit replacement retains a UUID backup
    of both original products, including a consolidated multi-session export.
    """
    log_path, out_dir = pathlib.Path(log_path), pathlib.Path(out_dir)
    names = ("transcript_full.jsonl", "chat_log.md")
    existing = [out_dir / name for name in names if (out_dir / name).exists()]
    if existing and not replace:
        raise FileExistsError(
            "Refusing to overwrite existing logs; use a separate --out-dir "
            "or explicit --replace (creates recoverable backups)"
        )
    # Fail closed: malformed source cannot silently create an invalid JSONL export.
    with log_path.open(encoding="utf-8-sig") as source:
        for line in source:
            json.loads(line)
    out_dir.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="export-stage-", dir=out_dir) as temporary:
        stage = pathlib.Path(temporary)
        _export_unchecked(log_path, stage)
        if existing:
            backup = out_dir / ("backup-" + uuid.uuid4().hex)
            backup.mkdir()
            for path in existing:
                shutil.copy2(path, backup / path.name)
        for name in names:
            (stage / name).replace(out_dir / name)
    return tuple(out_dir / name for name in names)


if __name__ == "__main__":
    configure_utf8()
    cli = argparse.ArgumentParser(
        description="Export one legacy session safely; not a consolidation tool"
    )
    cli.add_argument("--source", type=pathlib.Path, default=DEFAULT_LOG_PATH)
    cli.add_argument("--out-dir", type=pathlib.Path, default=OUTPUT_DIR)
    cli.add_argument("--replace", action="store_true", help="replace with recoverable backups")
    args = cli.parse_args()
    try:
        export(args.source, args.out_dir, replace=args.replace)
    except (OSError, ValueError) as exc:
        print(redact_text(str(exc)), file=sys.stderr)
        sys.exit(2)
