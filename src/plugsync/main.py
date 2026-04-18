#!/usr/bin/env python3
"""plugsync — sync skills/agents/commands from GitHub repos to a local target."""

import argparse
import concurrent.futures
import os
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

import yaml


CONFIG_SEARCH_PATHS = [
    Path("./.plugsync.yaml"),
    Path("./.plugsync.yml"),
]

LOCK_FILENAME = "plugsync.lock"


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


def lock_path_for(config_path: Path) -> Path:
    return config_path.absolute().parent / LOCK_FILENAME


def load_lock(path: Path) -> dict | None:
    if not path.exists():
        return None
    with open(path) as f:
        return yaml.safe_load(f)


def save_lock(path: Path, repos: list[dict]) -> None:
    data = {
        "version": 1,
        "locked_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "repos": repos,
    }
    with open(path, "w") as f:
        yaml.dump(data, f, default_flow_style=False, sort_keys=False)


def get_head_sha(clone_dir: Path) -> str:
    result = subprocess.run(
        ["git", "-C", str(clone_dir), "rev-parse", "HEAD"],
        capture_output=True, text=True,
    )
    return result.stdout.strip()


def get_locked_sha(lock_data: dict | None, url: str) -> str | None:
    if lock_data is None:
        return None
    for repo in lock_data.get("repos", []):
        if repo["url"] == url:
            return repo.get("commit")
    return None


def repo_matches(url: str, target: str) -> bool:
    """Match a repo url against a user-supplied target (full url or org/name)."""
    if url == target:
        return True
    name = url.removesuffix(".git")
    org_name = "/".join(name.rsplit("/", 2)[-2:])
    return org_name == target.removesuffix(".git")


CACHE_DIR = Path(os.environ.get("PLUGSYNC_CACHE", "~/.cache/plugsync")).expanduser()


def fetch_repo(
    url: str, ref: str | None, locked_sha: str | None = None,
) -> tuple[Path | None, str, str | None]:
    """Fetch a repo and return (clone_dir, message, sha)."""
    org = os.path.basename(os.path.dirname(url))
    name = os.path.basename(url).removesuffix(".git")
    clone_dir = CACHE_DIR / org / name / (ref or "_default")

    ref_label = f" (ref: {ref})" if ref else ""

    if clone_dir.exists():
        if locked_sha:
            current_sha = get_head_sha(clone_dir)
            if current_sha == locked_sha:
                return clone_dir, f"→ {url}{ref_label} (locked)", locked_sha

        result = subprocess.run(
            ["git", "-C", str(clone_dir), "pull", "--depth=1", "--quiet"],
        )
        if result.returncode == 0:
            sha = get_head_sha(clone_dir)
            return clone_dir, f"→ Pulling {url}{ref_label} ... (cached)", sha
        # Cache is broken — delete and re-clone
        shutil.rmtree(clone_dir)

    clone_dir.parent.mkdir(parents=True, exist_ok=True)
    clone_cmd = ["git", "clone", "--depth=1", "--quiet"]
    if ref:
        clone_cmd += ["--branch", ref]
    clone_cmd += [url, str(clone_dir)]
    result = subprocess.run(clone_cmd)
    if result.returncode != 0:
        return None, f"  ⚠ Failed to clone {url}, skipping.\n", None
    sha = get_head_sha(clone_dir)
    return clone_dir, f"→ Cloning {url}{ref_label} ...", sha


def sync(
    config: dict, config_path: Path, *, dry_run: bool = False,
    update: bool | str = False, frozen: bool = False,
) -> None:
    target = resolve_target(config["target"], config_path)
    lock_file = lock_path_for(config_path)
    lock_data = load_lock(lock_file)

    if frozen and lock_data is None:
        print("Error: --frozen requires a lock file, but plugsync.lock was not found.", file=sys.stderr)
        sys.exit(1)

    repos = config.get("repos", [])

    if isinstance(update, str):
        matched = [r for r in repos if repo_matches(r["url"], update)]
        if not matched:
            print(f"Error: no repo matches '{update}'.", file=sys.stderr)
            sys.exit(1)
        if len(matched) > 1:
            urls = ", ".join(r["url"] for r in matched)
            print(f"Error: '{update}' matches multiple repos: {urls}", file=sys.stderr)
            sys.exit(1)
        update_targets = {matched[0]["url"]}
    else:
        update_targets = None

    def locked_sha_for(url: str) -> str | None:
        if lock_data is None:
            return None
        if update is True:
            return None
        if update_targets is not None and url in update_targets:
            return None
        return get_locked_sha(lock_data, url)

    print(f"Target: {target}")
    if lock_data is not None and update is not True:
        print(f"Lock:   {lock_file}")
    print()

    total_repos = 0
    synced_files = 0
    warnings = 0

    with concurrent.futures.ThreadPoolExecutor() as pool:
        futures = {
            pool.submit(
                fetch_repo, repo["url"], repo.get("ref"),
                locked_sha_for(repo["url"]),
            ): repo
            for repo in repos
        }
        fetch_results: dict[tuple[str, str | None], tuple[Path | None, str, str | None]] = {}
        for future in concurrent.futures.as_completed(futures):
            repo = futures[future]
            fetch_results[(repo["url"], repo.get("ref"))] = future.result()

    lock_entries: list[dict] = []

    for repo in repos:
        url = repo["url"]
        clone_dir, message, sha = fetch_results[(url, repo.get("ref"))]
        print(message)
        if clone_dir is None:
            warnings += 1
            continue

        total_repos += 1
        if sha:
            lock_entries.append({"url": url, "commit": sha})

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

    if not dry_run and lock_entries:
        save_lock(lock_file, lock_entries)


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
    parser.add_argument(
        "--update", "-u",
        nargs="?",
        const=True,
        default=False,
        metavar="URL|NAME",
        help="Update lock. Without arg: all repos. With arg (full url or org/name): that repo only.",
    )
    parser.add_argument(
        "--frozen",
        action="store_true",
        help="Use locked SHAs only; fail if lock file is missing",
    )
    args = parser.parse_args()

    if args.update and args.frozen:
        print("Error: --update and --frozen are mutually exclusive.", file=sys.stderr)
        sys.exit(1)

    config_path = args.config or find_config()
    if config_path is None:
        print(
            "Error: no config found. Create .plugsync.yaml, or use --config to specify a path.",
            file=sys.stderr,
        )
        sys.exit(1)

    config = load_config(config_path)
    sync(config, config_path=config_path, dry_run=args.dry_run, update=args.update, frozen=args.frozen)
