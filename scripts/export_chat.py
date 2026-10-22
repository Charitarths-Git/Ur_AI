"""Export conversation transcripts from Antigravity IDE into chat_logs/.

Produces:
1. chat_logs/transcript_full.jsonl - raw machine-readable JSONL transcript
2. chat_logs/chat_log.md           - clean, human-readable Markdown transcript
"""

import json
import pathlib
import re
import shutil
import sys

from _console import configure_utf8

DEFAULT_LOG_PATH = pathlib.Path(
    r"C:\Users\gagan\.gemini\antigravity-ide\brain\04dc995e-54b1-483e-8d66-964372b8491e\.system_generated\logs\transcript_full.jsonl"
)
OUTPUT_DIR = pathlib.Path("chat_logs")


def clean_user_text(text: str) -> str:
    # Extract content inside <USER_REQUEST> if present
    match = re.search(r"<USER_REQUEST>\s*(.*?)\s*</USER_REQUEST>", text, re.DOTALL)
    if match:
        text = match.group(1)
    # Strip any remaining system XML tags
    text = re.sub(r"<ADDITIONAL_METADATA>.*?</ADDITIONAL_METADATA>", "", text, flags=re.DOTALL)
    text = re.sub(r"<USER_SETTINGS_CHANGE>.*?</USER_SETTINGS_CHANGE>", "", text, flags=re.DOTALL)
    return text.strip()


def export(log_path: pathlib.Path = DEFAULT_LOG_PATH, out_dir: pathlib.Path = OUTPUT_DIR) -> None:
    if not log_path.exists():
        print(f"Error: transcript file not found at {log_path}", file=sys.stderr)
        sys.exit(1)

    out_dir.mkdir(parents=True, exist_ok=True)

    # 1. Copy raw JSONL
    raw_dest = out_dir / "transcript_full.jsonl"
    shutil.copy2(log_path, raw_dest)
    print(f"Copied raw JSONL to {raw_dest}")

    # 2. Parse and format Markdown
    md_dest = out_dir / "chat_log.md"
    with open(log_path, "r", encoding="utf-8") as f_in, open(md_dest, "w", encoding="utf-8") as f_out:
        f_out.write("# Ur AI Internship Project — AI Interaction Log\n\n")
        f_out.write("> **Source:** Antigravity IDE session logs (`transcript_full.jsonl`)\n")
        f_out.write("> **Task:** Document Intelligence & VLM R&D take-home (Japanese Balance Sheet PDF parsing)\n\n")
        f_out.write("---\n\n")

        step_num = 0
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
            source = item.get("source")
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

    print(f"Generated Markdown log at {md_dest}")


if __name__ == "__main__":
    configure_utf8()
    export()
