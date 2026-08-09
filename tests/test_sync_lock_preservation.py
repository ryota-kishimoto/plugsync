"""fetch に失敗した repo の記録を lock から落とさないこと。

一時的なネットワーク断でピン留めが消えると lock が再現性を失うため、
sync() を fetch_repo だけ差し替えて確認する。
"""

import yaml

from plugsync import main

CONFIG = {
    "target": "./out",
    "repos": [
        {"url": "https://github.com/foo/ok"},
        {"url": "https://github.com/foo/broken"},
    ],
}

EXISTING_LOCK = {
    "version": 1,
    "locked_at": "2020-01-01T00:00:00Z",
    "repos": [
        {"url": "https://github.com/foo/ok", "commit": "aaa"},
        {"url": "https://github.com/foo/broken", "commit": "bbb"},
    ],
}


def write(path, data):
    path.write_text(yaml.dump(data, default_flow_style=False, sort_keys=False))


def read(path):
    with open(path) as f:
        return yaml.safe_load(f)


def fake_fetch(monkeypatch, tmp_path):
    """ok は成功、broken は失敗を返す fetch_repo。"""
    clone_dir = tmp_path / "clone"
    clone_dir.mkdir(exist_ok=True)

    def _fetch(url, ref, locked_sha=None):
        if url.endswith("/broken"):
            return None, f"  ⚠ Failed to clone {url}, skipping.", None
        return clone_dir, f"→ {url}", "aaa"

    monkeypatch.setattr(main, "fetch_repo", _fetch)


def test_keeps_entry_for_repo_that_failed_to_fetch(tmp_path, monkeypatch):
    config_path = tmp_path / ".plugsync.yaml"
    write(config_path, CONFIG)
    lock_path = tmp_path / ".plugsync.lock"
    write(lock_path, EXISTING_LOCK)
    fake_fetch(monkeypatch, tmp_path)

    main.sync(CONFIG, config_path)

    urls = [r["url"] for r in read(lock_path)["repos"]]
    assert "https://github.com/foo/broken" in urls


def test_unchanged_lock_is_untouched_despite_fetch_failure(tmp_path, monkeypatch):
    config_path = tmp_path / ".plugsync.yaml"
    write(config_path, CONFIG)
    lock_path = tmp_path / ".plugsync.lock"
    write(lock_path, EXISTING_LOCK)
    fake_fetch(monkeypatch, tmp_path)
    before = lock_path.read_bytes()

    main.sync(CONFIG, config_path)

    assert lock_path.read_bytes() == before


def test_drops_entry_when_repo_left_the_config(tmp_path, monkeypatch):
    """設定から外れた repo は引き継がず、記録も消えること。"""
    shrunk = {"target": "./out", "repos": [{"url": "https://github.com/foo/ok"}]}
    config_path = tmp_path / ".plugsync.yaml"
    write(config_path, shrunk)
    lock_path = tmp_path / ".plugsync.lock"
    write(lock_path, EXISTING_LOCK)
    fake_fetch(monkeypatch, tmp_path)

    main.sync(shrunk, config_path)

    data = read(lock_path)
    urls = [r["url"] for r in data["repos"]]
    assert urls == ["https://github.com/foo/ok"]
    assert data["locked_at"] != EXISTING_LOCK["locked_at"]
