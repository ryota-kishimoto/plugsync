"""同じキャッシュを使う plugsync は、先に取った側が離すまで待つこと。"""

import threading

from plugsync import main


def test_second_holder_waits_until_first_releases(tmp_path):
    clone_dir = tmp_path / "org" / "repo" / "_default"
    acquired = threading.Event()

    def second():
        with main.cache_lock(clone_dir):
            acquired.set()

    with main.cache_lock(clone_dir):
        t = threading.Thread(target=second)
        t.start()
        assert not acquired.wait(0.3)

    assert acquired.wait(5)
    t.join()

