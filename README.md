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

See [examples/plugsync.yaml](examples/plugsync.yaml) for a full example.

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

## Claude Code skill

`skills/plugsync/SKILL.md` is a Claude Code skill that lets Claude run `plugsync` for you.

Add it to your `~/.plugsync.yaml`:

```yaml
repos:
  - url: https://github.com/ryota-kishimoto/plugsync
    skills:
      - skills/plugsync
```
