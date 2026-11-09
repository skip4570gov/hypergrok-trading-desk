#!/usr/bin/env python3
"""Check an installed tree against the reviewed file manifest.

Identity is the hashes in ``install-manifest.json``, not this commit's own
SHA. When the tree is a git checkout, HEAD must also contain the reviewed
ancestor named in ``install_pin.py``. A later commit on that history still
passes the ancestor check, and fails the hash check if a runtime file drifted.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys

from install_pin import ANCESTOR, REPOSITORY

MANIFEST = "install-manifest.json"


def file_hash(path: str) -> str:
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for chunk in iter(lambda: handle.read(65536), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_manifest(root: str) -> dict:
    with open(os.path.join(root, MANIFEST), encoding="utf-8") as handle:
        data = json.load(handle)
    files = data.get("files")
    if not isinstance(files, dict) or not files:
        raise SystemExit("install manifest has no files")
    return files


def check_hashes(root: str, files: dict) -> list[str]:
    errors = []
    for rel, expected in sorted(files.items()):
        path = os.path.join(root, rel)
        if not os.path.isfile(path):
            errors.append(f"missing {rel}")
            continue
        actual = file_hash(path)
        if actual != expected:
            errors.append(f"hash mismatch {rel}")
    return errors


def check_ancestor(root: str) -> list[str]:
    if not os.path.isdir(os.path.join(root, ".git")):
        return []
    result = subprocess.run(
        ["git", "-C", root, "merge-base", "--is-ancestor", ANCESTOR, "HEAD"],
        capture_output=True, text=True,
    )
    if result.returncode != 0:
        return [f"HEAD does not contain reviewed ancestor {ANCESTOR}"]
    return []


def verify(root: str) -> list[str]:
    root = os.path.abspath(root)
    errors = check_hashes(root, load_manifest(root))
    errors.extend(check_ancestor(root))
    return errors


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Verify an installed paper-only tree.")
    parser.add_argument("--root", default=os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    args = parser.parse_args(argv)
    errors = verify(args.root)
    if errors:
        print("\n".join(errors))
        print(f"{len(errors)} problem(s)")
        return 1
    print(f"ok: {REPOSITORY} runtime files match the manifest; ancestor {ANCESTOR} is contained")
    return 0


if __name__ == "__main__":
    sys.exit(main())
