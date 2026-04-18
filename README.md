# plugsync

Sync skills, agents, and commands from GitHub repositories to a local directory.

## Install

```bash
# uv (recommended)
uv tool install git+https://github.com/ryota-kishimoto/plugsync

# pipx
pipx install git+https://github.com/ryota-kishimoto/plugsync
```

## Usage

Create `.plugsync.yaml` in any directory and run:

```bash
plugsync                         # auto-discovers .plugsync.yaml or .plugsync.yml
plugsync --dry-run               # preview without copying
plugsync --config /path/to/file  # explicit config path
plugsync --update                # fetch latest for all repos
plugsync --update foo/bar        # fetch latest for one repo (url or org/name)
plugsync --frozen                # use locked SHAs only; fail if no lock file
```

## Configuration

See [examples/plugsync.yaml](examples/plugsync.yaml).

```yaml
target: ~/.claude  # ~ paths are expanded; other paths are relative to this file

repos:
  - url: https://github.com/anthropics/skills
    skills:
      - skills/skill-creator
      - skills/frontend-design

  - url: https://github.com/obra/superpowers
    ref: main  # optional: pin to a specific branch or tag
    skills:
      - skills/brainstorming
      - src: skills/using-superpowers  # optional: rename with "name"
        name: superpowers
    agents:
      - agents/code-reviewer.md
    commands:
      - commands/brainstorm.md
```

After running `plugsync`, files are placed under `target`:

```
~/.claude/
├── skills/
│   ├── skill-creator
│   ├── frontend-design
│   └── brainstorming
├── agents/
│   └── code-reviewer.md
└── commands/
    └── brainstorm.md
```

### Lock file

plugsync generates a `plugsync.lock` file next to your config to pin exact commit SHAs for reproducible syncs.

| Command | Lock exists | Lock absent |
|---------|------------|-------------|
| `plugsync` | Sync at locked SHAs | Fetch latest, generate lock |
| `plugsync --update` (`-u`) | Fetch latest for all, regenerate lock | Same |
| `plugsync --update foo/bar` | Fetch latest for `foo/bar` only, others stay locked | Same (others unlocked) |
| `plugsync --frozen` | Sync at locked SHAs | Error |

When a lock file is present, repos whose cached SHA already matches the lock are not fetched at all, making warm runs faster.

### Custom paths

Use `paths:` to place files anywhere under `target`.

See [examples/dotfiles/plugsync.yaml](examples/dotfiles/plugsync.yaml).

```yaml
# target: "." means the same directory as this config file
target: .

repos:
  - url: https://github.com/mathiasbynens/dotfiles
    paths:
      - path: .
        src:
          - .editorconfig

  - url: https://github.com/stevemao/github-issue-templates
    paths:
      - path: .github
        src:
          - PULL_REQUEST_TEMPLATE.md
          - src: PULL_REQUEST_TEMPLATE.md  # optional: rename (subdirs allowed)
            name: pull_request_template/feature.md
```

## Skill

A skill that lets your AI agent understand and run plugsync for you.

[skills/plugsync/SKILL.md](skills/plugsync/SKILL.md)
