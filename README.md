# plugsync

Sync skills, agents, and commands from GitHub repositories to a local directory.

## Install

```bash
uv tool install git+https://github.com/ryota-kishimoto/plugsync
```

## Usage

Create `~/.plugsync.yaml` and run:

```bash
plugsync                         # run with ~/.plugsync.yaml or ./plugsync.yaml
plugsync --dry-run               # preview without copying
plugsync --config ~/my.yaml      # explicit config path
```

## Configuration

See [examples/plugsync.yaml](examples/plugsync.yaml).

```yaml
target: ~/.claude  # change to your tool's directory
                   # e.g. skills → ~/.claude/skills/

repos:
  - url: https://github.com/anthropics/skills
    skills:
      - skills/skill-creator
      - skills/frontend-design

  - url: https://github.com/obra/superpowers
    skills:
      - skills/brainstorming
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

## Skill

A skill that lets your AI agent understand and run plugsync for you.

[skills/plugsync/SKILL.md](skills/plugsync/SKILL.md)
