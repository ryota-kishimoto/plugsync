import yaml

from plugsync.main import save_lock

REPOS = [{"url": "https://github.com/foo/bar", "commit": "abc123"}]


def read(path):
    with open(path) as f:
        return yaml.safe_load(f)


def test_writes_lock_when_absent(tmp_path):
    lock = tmp_path / ".plugsync.lock"
    save_lock(lock, REPOS)

    data = read(lock)
    assert data["version"] == 1
    assert data["repos"] == REPOS
    assert data["locked_at"]


def test_keeps_locked_at_when_repos_unchanged(tmp_path):
    # 修正前は現在時刻で上書きされていた。過去の時刻を置くことで、引き継ぎが
    # 効いているかを同一秒問題に邪魔されずに判定する
    lock = tmp_path / ".plugsync.lock"
    stale = "2000-01-01T00:00:00Z"
    lock.write_text(yaml.dump({"version": 1, "locked_at": stale, "repos": REPOS}))

    save_lock(lock, REPOS)

    assert read(lock)["locked_at"] == stale


def test_writes_identical_bytes_when_repos_unchanged(tmp_path):
    """同じ内容で sync し直しても git 差分が出ないこと（この修正の目的）。"""
    lock = tmp_path / ".plugsync.lock"
    save_lock(lock, REPOS)
    before = lock.read_bytes()

    save_lock(lock, REPOS)

    assert lock.read_bytes() == before


def test_restamps_locked_at_when_commit_changes(tmp_path):
    # 引き継ぎ対象になりえない過去の時刻を置き、書き換わったことを判定できるようにする
    # （現在時刻同士だと同一秒に収まって差が出ない）
    lock = tmp_path / ".plugsync.lock"
    stale = "2000-01-01T00:00:00Z"
    lock.write_text(yaml.dump({"version": 1, "locked_at": stale, "repos": REPOS}))

    save_lock(lock, [{"url": "https://github.com/foo/bar", "commit": "def456"}])

    data = read(lock)
    assert data["repos"][0]["commit"] == "def456"
    assert data["locked_at"] != stale


def test_advances_locked_at_when_repo_added(tmp_path):
    lock = tmp_path / ".plugsync.lock"
    save_lock(lock, REPOS)

    grown = REPOS + [{"url": "https://github.com/foo/baz", "commit": "999"}]
    save_lock(lock, grown)

    assert read(lock)["repos"] == grown


def test_recovers_when_existing_lock_has_no_locked_at(tmp_path):
    lock = tmp_path / ".plugsync.lock"
    lock.write_text(yaml.dump({"version": 1, "repos": REPOS}))

    save_lock(lock, REPOS)

    assert read(lock)["locked_at"]
