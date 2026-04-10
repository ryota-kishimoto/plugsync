#!/usr/bin/env python3
"""plugsync — sync skills/agents/commands from GitHub repos to a local target."""

import argparse
import concurrent.futures
import os
import shutil
import subprocess
import sys
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


def resolve_target(raw: str, config_path: Path) -> Path:
    if raw.startswith("~"):
        return Path(os.path.expanduser(raw))
    return (config_path.absolute().parent / raw).absolute()


CACHE_DIR = Path(os.environ.get("PLUGSYNC_CACHE", "~/.cache/plugsync")).expanduser()


def fetch_repo(url: str, ref: str | None) -> tuple[Path | None, str]:
    org = os.path.basename(os.path.dirname(url))
    name = os.path.basename(url).removesuffix(".git")
    clone_dir = CACHE_DIR / org / name / (ref or "_default")

    ref_label = f" (ref: {ref})" if ref else ""

    if clone_dir.exists():
        result = subprocess.run(
            ["git", "-C", str(clone_dir), "pull", "--depth=1", "--quiet"],
        )
        if result.returncode == 0:
            return clone_dir, f"→ Pulling {url}{ref_label} ... (cached)"
        # Cache is broken — delete and re-clone
        shutil.rmtree(clone_dir)

    clone_dir.parent.mkdir(parents=True, exist_ok=True)
    clone_cmd = ["git", "clone", "--depth=1", "--quiet"]
    if ref:
        clone_cmd += ["--branch", ref]
    clone_cmd += [url, str(clone_dir)]
    result = subprocess.run(clone_cmd)
    if result.returncode != 0:
        return None, f"  ⚠ Failed to clone {url}, skipping.\n"
    return clone_dir, f"→ Cloning {url}{ref_label} ..."


def sync(config: dict, config_path: Path, dry_run: bool = False) -> None:
    target = resolve_target(config["target"], config_path)
    print(f"Target: {target}")
    print()

    total_repos = 0
    synced_files = 0
    warnings = 0

    repos = config.get("repos", [])
    with concurrent.futures.ThreadPoolExecutor() as pool:
        futures = {
            pool.submit(fetch_repo, repo["url"], repo.get("ref")): repo
            for repo in repos
        }
        fetch_results: dict[tuple[str, str | None], tuple[Path | None, str]] = {}
        for future in concurrent.futures.as_completed(futures):
            repo = futures[future]
            fetch_results[(repo["url"], repo.get("ref"))] = future.result()

    for repo in repos:
        url = repo["url"]
        clone_dir, message = fetch_results[(url, repo.get("ref"))]
        print(message)
        if clone_dir is None:
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

            for item in paths:
                if isinstance(item, dict):
                    src_path, dest_name = item["src"], item.get("name")
                else:
                    src_path, dest_name = item, None

                src = clone_dir / src_path
                dest = dest_base / (dest_name or src.name)

                if not src.exists():
                    print(f"  ⚠ Not found: {src_path}")
                    warnings += 1
                    continue

                label = f"{src.name} → {dest_name}" if dest_name else src.name
                if dry_run:
                    print(f"  (dry) [{kind}] {label}")
                else:
                    if dest.exists():
                        shutil.rmtree(dest) if dest.is_dir() else dest.unlink()
                    dest.parent.mkdir(parents=True, exist_ok=True)
                    if src.is_dir():
                        shutil.copytree(src, dest)
                    else:
                        shutil.copy2(src, dest)
                    print(f"  ✓ [{kind}] {label}")
                    synced_files += 1

        for entry in repo.get("paths", []):
            dest_base = target / entry["path"]
            if not dry_run:
                dest_base.mkdir(parents=True, exist_ok=True)

            for item in entry.get("src", []):
                if isinstance(item, dict):
                    src_path, dest_name = item["src"], item.get("name")
                else:
                    src_path, dest_name = item, None

                src = clone_dir / src_path
                dest = dest_base / (dest_name or src.name)

                if not src.exists():
                    print(f"  ⚠ Not found: {src_path}")
                    warnings += 1
                    continue

                label = f"{src.name} → {dest_name}" if dest_name else src.name
                if dry_run:
                    print(f"  (dry) [paths] {label} → {dest_base}")
                else:
                    if dest.exists():
                        shutil.rmtree(dest) if dest.is_dir() else dest.unlink()
                    dest.parent.mkdir(parents=True, exist_ok=True)
                    if src.is_dir():
                        shutil.copytree(src, dest)
                    else:
                        shutil.copy2(src, dest)
                    print(f"  ✓ [paths] {label} → {dest_base}")
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
        help="Path to config file (default: .plugsync.yaml or .plugsync.yml in current directory)",
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
            "Error: no config found. Create .plugsync.yaml, or use --config to specify a path.",
            file=sys.stderr,
        )
        sys.exit(1)

    config = load_config(config_path)
    sync(config, config_path=config_path, dry_run=args.dry_run)
