"""Fresh-process post-seal verification; never edits the archive or its payload."""

import hashlib
import json
import zipfile
from pathlib import Path

from pactlens.agents.deepseek_provider import configured_key

ROOT = Path(__file__).resolve().parents[1]
ARCHIVE = ROOT.parent / "pactlens-phase5a1-review.zip"


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def main():
    receipt_path = Path(str(ARCHIVE) + ".verification.json")
    receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
    raw = ARCHIVE.read_bytes()
    assert digest(raw) == receipt["archive_sha256"]
    key = configured_key().encode("utf-8")
    with zipfile.ZipFile(ARCHIVE) as archive:
        assert archive.testzip() is None
        names = archive.namelist()
        assert len(names) == len(set(names)) == receipt["member_count"]
        manifest = json.loads(archive.read("SHA256SUMS.json"))["members"]
        assert set(manifest) == set(names) - {"SHA256SUMS.json"}
        source_members = 0
        for name in names:
            parts = Path(name).parts
            assert not set(parts) & {".git", ".venv", ".runtime", "__pycache__"}
            assert not any(p.startswith(".env") for p in parts)
            assert Path(name).suffix.lower() not in (
                ".sqlite3",
                ".db",
                ".zip",
                ".safetensors",
                ".bin",
            )
            content = archive.read(name)
            assert key not in content
            assert digest(content) == receipt["members_sha256"][name]
            if name in manifest:
                assert digest(content) == manifest[name]
            if name not in ("SHA256SUMS.json", "ARCHIVE_VERIFICATION.json"):
                assert (ROOT / name).is_file() and (ROOT / name).read_bytes() == content
                source_members += 1
    receipt["independent_post_process_verification"] = {
        "status": "PASS",
        "crc": "PASS",
        "every_member_sha256": "PASS",
        "current_source_bytes": "PASS",
        "source_members": source_members,
        "secret_exact_value_scan": "PASS",
        "excluded_private_paths": "PASS",
        "packaging_process_already_exited": True,
        "archive_unchanged": True,
    }
    receipt_path.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    assert ARCHIVE.read_bytes() == raw
    print(json.dumps({k: v for k, v in receipt.items() if k != "members_sha256"}, indent=2))


if __name__ == "__main__":
    main()
