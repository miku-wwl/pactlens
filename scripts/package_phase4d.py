"""Create a scoped review ZIP; verify CRC, every member/source hash and secret exclusions."""

import hashlib
import json
import re
import tempfile
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TARGET = ROOT.parent / "pactlens-phase4d-review.zip"
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
        raise ValueError("EXISTING_REVIEW_ARCHIVE_PRESERVED")
    paths = [
        ROOT / name
        for name in (
            "AGENTS.md",
            "README.md",
            "LICENSE",
            "pyproject.toml",
            "uv.lock",
            ".python-version",
            ".env.example",
            ".gitignore",
            "PACTLENS_HACKATHON_DESIGN.md",
        )
    ]
    for directory in (
        "src",
        "tests",
        "docs",
        "datasets/fixtures",
        "scripts",
        "research/phase4d",
        "review/phase4d",
    ):
        paths.extend(p for p in (ROOT / directory).rglob("*") if p.is_file())
    payload = {}
    for path in sorted(set(paths)):
        relative = path.relative_to(ROOT)
        if FORBIDDEN & set(relative.parts) or path.suffix.lower() in (
            ".pyc",
            ".zip",
            ".sqlite3",
            ".db",
            ".wal",
        ):
            continue
        if path.is_symlink():
            raise ValueError("NO_REVIEW_SYMLINKS")
        payload[relative.as_posix()] = path.read_bytes()
    # Also check exact capability values from this phase, without printing them.
    capabilities = []
    for directory in (ROOT / ".runtime").glob("phase4d*"):
        if directory.is_dir():
            capabilities.extend(
                p.read_bytes().strip() for p in directory.rglob("capability") if p.is_file()
            )
    for name, data in payload.items():
        if SECRET.search(data) or any(len(token) >= 24 and token in data for token in capabilities):
            raise ValueError("SECRET_MATERIAL_REJECTED_IN_" + name)
    checks = json.loads((ROOT / "review/phase4d/verification.json").read_text(encoding="utf-8"))
    if not checks["all_required_passed"]:
        raise ValueError("FINAL_VERIFICATION_REQUIRED")
    # Validate a temporary payload archive before issuing its embedded receipt.
    with tempfile.TemporaryFile() as temporary:
        with zipfile.ZipFile(temporary, "w", zipfile.ZIP_DEFLATED) as archive:
            for name, data in payload.items():
                archive.writestr(name, data)
        temporary.seek(0)
        with zipfile.ZipFile(temporary) as archive:
            assert archive.testzip() is None
            assert all(archive.read(name) == data for name, data in payload.items())
    embedded = {
        "version": "pactlens-review-payload-receipt-v1",
        "scope": "payload bytes verified in temporary archive before final sealing; final archive receipt is adjacent external file",
        "payload_members": len(payload),
        "payload_crc": "PASS",
        "payload_hashes": "PASS",
        "secret_pattern_and_exact_phase_capability_checks": "PASS",
        "phase_capability_values_checked": len(capabilities),
        "exclusions": sorted(FORBIDDEN),
        "final_archive_sha256_location": "pactlens-phase4d-review.zip.verification.json (external; avoids recursive self-hash)",
    }
    members = {**payload, "ARCHIVE_VERIFICATION.json": serialized(embedded)}
    manifest = {name: sha(data) for name, data in members.items()}
    members["SHA256SUMS.json"] = serialized(
        {
            "algorithm": "SHA-256",
            "members": manifest,
            "self_exclusion": "SHA256SUMS.json is hashed by the external final receipt",
        }
    )
    with zipfile.ZipFile(TARGET, "x", zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for name, data in members.items():
            archive.writestr(name, data)
    with zipfile.ZipFile(TARGET) as archive:
        assert archive.testzip() is None
        assert len(archive.namelist()) == len(set(archive.namelist())) == len(members)
        final_hashes = {name: sha(archive.read(name)) for name in archive.namelist()}
        assert all(final_hashes[name] == sha(data) for name, data in members.items())
        assert all(final_hashes[name] == value for name, value in manifest.items())
        assert all((ROOT / name).read_bytes() == archive.read(name) for name in payload)
        assert not any(FORBIDDEN & set(Path(name).parts) for name in archive.namelist())
    receipt = {
        "archive": str(TARGET),
        "archive_sha256": sha(TARGET.read_bytes()),
        "archive_bytes": TARGET.stat().st_size,
        "crc": "PASS",
        "every_member_hash": "PASS",
        "source_consistency": "PASS",
        "secret_checks": "PASS",
        "member_count": len(members),
        "members_sha256": final_hashes,
        "scope": "FINAL_ARCHIVE_AND_ALL_MEMBERS",
        "embedded_receipt_scope": embedded["scope"],
    }
    Path(str(TARGET) + ".verification.json").write_bytes(serialized(receipt))
    print(json.dumps({k: v for k, v in receipt.items() if k != "members_sha256"}, indent=2))


if __name__ == "__main__":
    main()
