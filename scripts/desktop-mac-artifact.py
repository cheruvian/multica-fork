#!/usr/bin/env python3
"""Verify a fork macOS package and write its immutable build receipt."""

import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys


def main() -> None:
    dist = Path(sys.argv[1])
    source_sha = os.environ["SOURCE_SHA"]
    signed = os.environ["SIGNED"] == "true"
    if len(source_sha) != 40 or any(c not in "0123456789abcdef" for c in source_sha):
        raise SystemExit("SOURCE_SHA must be a full lowercase commit SHA")
    if subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip() != source_sha:
        raise SystemExit("checkout differs from SOURCE_SHA")
    dmgs = list(dist.glob("multica-desktop-*-mac-arm64.dmg"))
    if len(dmgs) != 1:
        raise SystemExit("expected exactly one arm64 DMG")
    app = dist / "mac-arm64" / "Multica.app"
    if not app.is_dir():
        raise SystemExit("packaged Multica.app missing")
    if signed:
        for command in (["codesign", "--verify", "--deep", "--strict", str(app)],
                        ["spctl", "--assess", "--type", "execute", str(app)],
                        ["xcrun", "stapler", "validate", str(app)]):
            subprocess.run(command, check=True)
    with dmgs[0].open("rb") as stream:
        digest = hashlib.file_digest(stream, "sha256").hexdigest()
    receipt = {
        "schema": 1,
        "source_repository": "cheruvian/multica-fork",
        "source_sha": source_sha,
        "github_run_id": os.environ["RUN_ID"],
        "platform": "mac-arm64",
        "artifact": dmgs[0].name,
        "sha256": digest,
        "signed_notarized": signed,
        "state": "built",
    }
    (dist / "desktop-artifact.json").write_text(json.dumps(receipt, indent=2) + "\n")


if __name__ == "__main__":
    main()
