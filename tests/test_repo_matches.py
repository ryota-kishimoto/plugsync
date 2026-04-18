from plugsync.main import repo_matches


def test_matches_full_url():
    assert repo_matches("https://github.com/foo/bar", "https://github.com/foo/bar")


def test_matches_org_name():
    assert repo_matches("https://github.com/foo/bar", "foo/bar")


def test_matches_strips_dot_git():
    assert repo_matches("https://github.com/foo/bar.git", "foo/bar")
    assert repo_matches("https://github.com/foo/bar", "foo/bar.git")
    assert repo_matches(
        "https://github.com/foo/bar.git", "https://github.com/foo/bar"
    )
    assert repo_matches(
        "https://github.com/foo/bar", "https://github.com/foo/bar.git"
    )


def test_no_match():
    assert not repo_matches("https://github.com/foo/bar", "foo/baz")
    assert not repo_matches("https://github.com/foo/bar", "other/bar")


def test_partial_name_does_not_match():
    assert not repo_matches("https://github.com/foo/bar", "bar")
