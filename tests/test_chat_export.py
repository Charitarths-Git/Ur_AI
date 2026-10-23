"""Protect consolidated logs and recoverability, using tiny synthetic input."""

import importlib.util
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
spec = importlib.util.spec_from_file_location("chat_export_test", ROOT / "scripts/export_chat.py")
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


def fixture(tmp_path):
    source = tmp_path / "source.jsonl"
    source.write_text(
        json.dumps({"type": "USER_INPUT", "content": "Hello"}) + "\n", encoding="utf-8"
    )
    out = tmp_path / "consolidated"
    out.mkdir()
    (out / "chat_log.md").write_bytes(b"MULTI SESSION historical text")
    (out / "transcript_full.jsonl").write_bytes(b'{"sessions": 3}\n')
    return source, out


def test_refuses_overwrite_and_preserves_both_products(tmp_path):
    source, out = fixture(tmp_path)
    before = {p.name: p.read_bytes() for p in out.iterdir()}
    with pytest.raises(FileExistsError):
        module.export(source, out)
    assert {p.name: p.read_bytes() for p in out.iterdir()} == before


def test_explicit_replace_keeps_byte_identical_backup(tmp_path):
    source, out = fixture(tmp_path)
    before = {p.name: p.read_bytes() for p in out.iterdir()}
    module.export(source, out, replace=True)
    (backup,) = out.glob("backup-*")
    assert {p.name: p.read_bytes() for p in backup.iterdir()} == before
    assert "Hello" in (out / "chat_log.md").read_text(encoding="utf-8")
    for line in (out / "transcript_full.jsonl").read_text(encoding="utf-8").splitlines():
        json.loads(line)


def test_bad_source_cannot_damage_existing_logs(tmp_path):
    source, out = fixture(tmp_path)
    source.write_text("{", encoding="utf-8")
    before = {p.name: p.read_bytes() for p in out.iterdir()}
    with pytest.raises(ValueError):
        module.export(source, out, replace=True)
    assert {p.name: p.read_bytes() for p in out.iterdir()} == before


def test_default_destination_is_not_consolidated_directory():
    assert module.OUTPUT_DIR.parts == ("outputs", "chat_export")
