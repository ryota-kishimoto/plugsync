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
    Path("./plugsync.yaml"),
    Path("~/.plugsync.yaml").expanduser(),
]


def find_config() -> Path | None:
    for path in CONFIG_SEARCH_PATHS:
        if path.exists():
            return path
    return None


def load_config(path: Path) -> dict:
    with open(path) as f:
        return yaml.safe_load(f)


def sync(config: dict, dry_run: bool = False) -> None:
    target = Path(os.path.expanduser(config["target"]))
    print(f"Target: {target}")
    print()

    with tempfile.TemporaryDirectory() as tmpdir:
        for repo in config.get("repos", []):
            url = repo["url"]
            org = os.path.basename(os.path.dirname(url))
            name = os.path.basename(url).removesuffix(".git")
            clone_dir = Path(tmpdir) / org / name

            print(f"→ Cloning {url} ...")
            result = subprocess.run(
                ["git", "clone", "--depth=1", "--quiet", url, str(clone_dir)],
            )
            if result.returncode != 0:
                print(f"  ⚠ Failed to clone {url}, skipping.\n")
                continue

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

            print()

    print("Done.")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Sync skills/agents/commands from GitHub repos to a local target."
    )
    parser.add_argument(
        "--config", "-c",
        type=Path,
        help="Path to config file (default: ./plugsync.yaml or ~/.plugsync.yaml)",
    )
    parser.add_argument(
        "--dry-run", "-n",
        action="store_true",
        help="Show what would be copied without actually copying",
    )
    args = parser.parse_args()

    config_path = args.config or find_config()
    if config_path is None:
        print(
            "Error: no config found. Create ./plugsync.yaml or ~/.plugsync.yaml",
            file=sys.stderr,
        )
        sys.exit(1)

    config = load_config(config_path)
    sync(config, dry_run=args.dry_run)
