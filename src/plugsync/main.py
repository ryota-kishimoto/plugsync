#!/usr/bin/env python3
"""plugsync — sync skills/agents/commands from GitHub repos to a local target."""

import argparse
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

import yaml


CONFIG_SEARCH_PATHS = [
    Path("./.plugsync.yaml"),
    Path("./.plugsync.yml"),
]


def find_config() -> Path | None:
    for path in CONFIG_SEARCH_PATHS:
        if path.exists():
            return path
    return None


def load_config(path: Path) -> dict:
    with open(path) as f:
        return yaml.safe_load(f)


def resolve_target(raw: str, root: Path | None) -> Path:
    if root is not None:
        if raw.startswith("~/"):
            rel = raw[2:]
        elif raw == "~":
            rel = ""
        elif raw.startswith("/"):
            rel = raw.lstrip("/")
        else:
            rel = raw
        return root / rel if rel else root
    return Path(os.path.expanduser(raw))


def sync(config: dict, dry_run: bool = False, root: Path | None = None) -> None:
    target = resolve_target(config["target"], root)
    print(f"Target: {target}")
    print()

    total_repos = 0
    synced_files = 0
    warnings = 0

    with tempfile.TemporaryDirectory() as tmpdir:
        for repo in config.get("repos", []):
            url = repo["url"]
            org = os.path.basename(os.path.dirname(url))
            name = os.path.basename(url).removesuffix(".git")
            clone_dir = Path(tmpdir) / org / name

            ref = repo.get("ref")
            clone_cmd = ["git", "clone", "--depth=1", "--quiet"]
            if ref:
                clone_cmd += ["--branch", ref]
            clone_cmd += [url, str(clone_dir)]

            ref_label = f" (ref: {ref})" if ref else ""
            print(f"→ Cloning {url}{ref_label} ...")
            result = subprocess.run(clone_cmd)
            if result.returncode != 0:
                print(f"  ⚠ Failed to clone {url}, skipping.\n")
                warnings += 1
                continue

            total_repos += 1

            for kind in ("skills", "agents", "commands"):
                paths = repo.get(kind, [])
                if not paths:
                    continue

                dest_base = target / kind
                if not dry_run:
                    dest_base.mkdir(parents=True, exist_ok=True)

                for src_path in paths:
                    src = clone_dir / src_path
                    dest = dest_base / src.name

                    if not src.exists():
                        print(f"  ⚠ Not found: {src_path}")
                        warnings += 1
                        continue

                    if dry_run:
                        print(f"  (dry) [{kind}] {src.name} → {dest}")
                    else:
                        if dest.exists():
                            shutil.rmtree(dest) if dest.is_dir() else dest.unlink()
                        if src.is_dir():
                            shutil.copytree(src, dest)
                        else:
                            shutil.copy2(src, dest)
                        print(f"  ✓ [{kind}] {src.name}")
                        synced_files += 1

            for entry in repo.get("paths", []):
                dest_base = target / entry["path"]
                if not dry_run:
                    dest_base.mkdir(parents=True, exist_ok=True)

                for src_path in entry.get("src", []):
                    src = clone_dir / src_path
                    dest = dest_base / src.name

                    if not src.exists():
                        print(f"  ⚠ Not found: {src_path}")
                        warnings += 1
                        continue

                    if dry_run:
                        print(f"  (dry) [paths] {src.name} → {dest}")
                    else:
                        if dest.exists():
                            shutil.rmtree(dest) if dest.is_dir() else dest.unlink()
                        if src.is_dir():
                            shutil.copytree(src, dest)
                        else:
                            shutil.copy2(src, dest)
                        print(f"  ✓ [paths] {src.name} → {dest_base}")
                        synced_files += 1

            print()

    warn_label = f", {warnings} warning{'s' if warnings != 1 else ''}" if warnings else ""
    print(f"{total_repos} repo{'s' if total_repos != 1 else ''}, {synced_files} file{'s' if synced_files != 1 else ''} synced{warn_label}")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Sync skills/agents/commands from GitHub repos to a local target."
    )
    parser.add_argument(
        "--config", "-c",
        type=Path,
        help="Path to config file (default: .plugsync.yaml or ~/.plugsync.yaml)",
    )
    parser.add_argument(
        "--dry-run", "-n",
        action="store_true",
        help="Show what would be copied without actually copying",
    )
    parser.add_argument(
        "--root",
        type=Path,
        metavar="DIR",
        help="Root directory to prepend to the target path (overrides the home-directory part of target)",
    )
    args = parser.parse_args()

    config_path = args.config or find_config()
    if config_path is None:
        print(
            "Error: no config found. Create .plugsync.yaml, or use --config to specify a path.",
            file=sys.stderr,
        )
        sys.exit(1)

    config = load_config(config_path)
    sync(config, dry_run=args.dry_run, root=args.root)
