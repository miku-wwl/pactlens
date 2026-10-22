"""Source-consistent review archive; no credentials, environments, private state or raw traces."""

import hashlib
import json
import re
import tempfile
import zipfile
from pathlib import Path

from pactlens.agents.deepseek_provider import configured_key

ROOT = Path(__file__).resolve().parents[1]
TARGET = ROOT.parent / "pactlens-phase5a1-review.zip"
FORBIDDEN = {".git", ".venv", ".runtime", "__pycache__", ".pytest_cache", ".ruff_cache"}
SECRET = re.compile(
    rb"(?:sk-(?:proj-)?[A-Za-z0-9_-]{24,}|gh[pousr]_[A-Za-z0-9]{30,}|github_pat_[A-Za-z0-9_]{40,}|AKIA[0-9A-Z]{16}|-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----)"
)


def sha(data):
    return hashlib.sha256(data).hexdigest()


def serialized(body):
    return (json.dumps(body, ensure_ascii=False, sort_keys=True, indent=2) + "\n").encode("utf-8")


def main():
    if TARGET.exists() or Path(str(TARGET) + ".verification.json").exists():
        raise ValueError("EXISTING_ARCHIVE_PRESERVED")
    verification = json.loads(
        (ROOT / "review/phase5a1/verification.json").read_text(encoding="utf-8")
    )
    if verification.get("all_required_passed") is not True:
        raise ValueError("FINAL_VERIFICATION_REQUIRED")
    paths = [
        ROOT / n
        for n in (
            "AGENTS.md",
            "README.md",
            "LICENSE",
            "pyproject.toml",
            "uv.lock",
            ".python-version",
            ".gitignore",
            "PACTLENS_HACKATHON_DESIGN.md",
        )
    ]
    for name in (
        "src",
        "tests",
        "scripts",
        "docs",
        "datasets/fixtures",
        "research/phase4d",
        "research/phase5a",
        "research/phase5a1",
        "review/phase4d",
        "review/phase4e5a",
        "review/phase5a1",
    ):
        paths.extend(p for p in (ROOT / name).rglob("*") if p.is_file())
    payload = {}
    for path in sorted(set(paths)):
        relative = path.relative_to(ROOT)
        # A caller may redirect this command's output into review/logs. Such
        # terminal sealing logs mutate after validation and cannot be payload.
        if relative.as_posix().startswith(
            ("review/phase4e5a/logs/package", "review/phase5a1/logs/package")
        ):
            continue
        if (
            FORBIDDEN & set(relative.parts)
            or any(p.lower().startswith(".env") for p in relative.parts)
            or path.suffix.lower()
            in (".pyc", ".zip", ".sqlite3", ".db", ".wal", ".shm", ".bin", ".safetensors")
        ):
            continue
        if path.is_symlink():
            raise ValueError("NO_SYMLINKS")
        payload[relative.as_posix()] = path.read_bytes()
    # Exact values remain only in memory. They are never printed, hashed or exported.
    sensitive = [configured_key().encode("utf-8")]
    for directory in (ROOT / ".runtime").glob("phase*"):
        if directory.is_dir():
            sensitive.extend(
                p.read_bytes().strip() for p in directory.rglob("capability") if p.is_file()
            )
    for name, data in payload.items():
        if SECRET.search(data) or any(len(s) >= 24 and s in data for s in sensitive):
            raise ValueError("SECRET_MATERIAL_REJECTED_IN_" + name)
    for name, digest in verification["source_sha256"].items():
        if sha((ROOT / name).read_bytes()) != digest:
            raise ValueError("TESTED_SOURCE_CHANGED_" + name)
    with tempfile.TemporaryFile() as temporary:
        with zipfile.ZipFile(temporary, "w", zipfile.ZIP_DEFLATED) as archive:
            for name, data in payload.items():
                archive.writestr(name, data)
        temporary.seek(0)
        with zipfile.ZipFile(temporary) as archive:
            assert archive.testzip() is None and all(
                archive.read(n) == d for n, d in payload.items()
            )
    embedded = {
        "scope": "PAYLOAD_VALIDATED_BEFORE_FINAL_SEAL; FINAL_SHA_IN_ADJACENT_RECEIPT",
        "payload_members": len(payload),
        "crc": "PASS",
        "member_hashes": "PASS",
        "source_consistency": "PASS",
        "secret_pattern_and_exact_value_scan": "PASS",
        "excluded": sorted(
            FORBIDDEN
            | {
                ".env*",
                "runtime databases",
                "raw private traces",
                "weights",
                "authorization headers",
                "previous ZIPs",
            }
        ),
        "formal_executions": 0,
        "research_ready": False,
        "sealing_stdout_logs_excluded": True,
    }
    members = {**payload, "ARCHIVE_VERIFICATION.json": serialized(embedded)}
    manifest = {name: sha(data) for name, data in members.items()}
    members["SHA256SUMS.json"] = serialized(
        {
            "algorithm": "SHA-256",
            "members": manifest,
            "self_exclusion": "SHA256SUMS.json hash is in external receipt",
        }
    )
    with zipfile.ZipFile(TARGET, "x", zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for name, data in members.items():
            archive.writestr(name, data)
    with zipfile.ZipFile(TARGET) as archive:
        assert archive.testzip() is None
        assert len(archive.namelist()) == len(set(archive.namelist())) == len(members)
        hashes = {n: sha(archive.read(n)) for n in archive.namelist()}
        assert all(hashes[n] == sha(d) for n, d in members.items())
        assert all(hashes[n] == h for n, h in manifest.items())
        assert all((ROOT / n).read_bytes() == archive.read(n) for n in payload)
        assert not any(
            FORBIDDEN & set(Path(n).parts) or any(p.startswith(".env") for p in Path(n).parts)
            for n in archive.namelist()
        )
    receipt = {
        "archive": str(TARGET),
        "archive_sha256": sha(TARGET.read_bytes()),
        "archive_bytes": TARGET.stat().st_size,
        "member_count": len(members),
        "crc": "PASS",
        "every_member_hash": "PASS",
        "source_consistency": "PASS",
        "secret_checks": "PASS",
        "members_sha256": hashes,
    }
    Path(str(TARGET) + ".verification.json").write_bytes(serialized(receipt))
    print(json.dumps({k: v for k, v in receipt.items() if k != "members_sha256"}, indent=2))


if __name__ == "__main__":
    main()
