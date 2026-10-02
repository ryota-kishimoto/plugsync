"""locked SHA があるときは、共有キャッシュの HEAD がどこにあってもその SHA で同期すること。

キャッシュは全プロジェクト共有なので、別プロジェクトが同じ repo を先に進めている状況を
ローカルの git repo で再現して確認する。
"""

import subprocess

from plugsync import main


def git(cwd, *args):
    return subprocess.run(
        ["git", "-C", str(cwd), *args], check=True, capture_output=True, text=True,
    ).stdout.strip()


def make_origin(tmp_path):
    """2 commit ある origin を作り、(url, 古い SHA, 新しい SHA) を返す。"""
    origin = tmp_path / "org" / "repo"
    origin.mkdir(parents=True)
    git(origin, "init", "--quiet")
    # GitHub と同じく、任意の SHA を fetch できるようにする
    git(origin, "config", "uploadpack.allowAnySHA1InWant", "true")
    shas = []
    for content in ("old", "new"):
        (origin / "file.txt").write_text(content)
        git(origin, "add", ".")
        git(origin, "-c", "user.name=t", "-c", "user.email=t@t", "commit", "--quiet", "-m", content)
        shas.append(git(origin, "rev-parse", "HEAD"))
    return f"file://{origin}", shas[0], shas[1]


def test_checks_out_locked_sha_even_if_cache_moved_ahead(tmp_path, monkeypatch):
    monkeypatch.setattr(main, "CACHE_DIR", tmp_path / "cache")
    url, old, new = make_origin(tmp_path)
    # 別プロジェクトが最新まで進めたキャッシュ
    main.fetch_repo(url, None)

    clone_dir, _, sha = main.fetch_repo(url, None, locked_sha=old)

    assert sha == old
    assert (clone_dir / "file.txt").read_text() == "old"


def test_checks_out_locked_sha_on_fresh_clone(tmp_path, monkeypatch):
    monkeypatch.setattr(main, "CACHE_DIR", tmp_path / "cache")
    url, old, _ = make_origin(tmp_path)

    clone_dir, _, sha = main.fetch_repo(url, None, locked_sha=old)

    assert sha == old
    assert (clone_dir / "file.txt").read_text() == "old"


def test_returns_to_latest_without_lock(tmp_path, monkeypatch):
    monkeypatch.setattr(main, "CACHE_DIR", tmp_path / "cache")
    url, old, new = make_origin(tmp_path)
    main.fetch_repo(url, None, locked_sha=old)

    _, _, sha = main.fetch_repo(url, None)

    assert sha == new


def test_fails_when_locked_sha_is_unreachable(tmp_path, monkeypatch):
    monkeypatch.setattr(main, "CACHE_DIR", tmp_path / "cache")
    url, _, _ = make_origin(tmp_path)

    clone_dir, _, sha = main.fetch_repo(url, None, locked_sha="0" * 40)

    assert clone_dir is None
    assert sha is None
