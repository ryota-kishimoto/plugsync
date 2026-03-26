# plugsync

Sync skills, agents, and commands from GitHub repositories to a local target directory.

## Install

```bash
uv tool install git+https://github.com/ryota-kishimoto/plugsync
```

## Usage

```bash
plugsync                        # auto-detect ./plugsync.yaml or ~/.plugsync.yaml
plugsync --config ~/my.yaml     # explicit config
plugsync --dry-run              # preview without copying
```

## Configuration

Copy `plugsync.yaml.example` to `./plugsync.yaml` or `~/.plugsync.yaml`:

```yaml
target: ~/.claude   # destination root (~ expanded)

repos:
  - url: https://github.com/example/repo
    skills:
      - skills/my-skill        # → $target/skills/my-skill
    agents:
      - agents/my-agent.md     # → $target/agents/my-agent.md
    commands:
      - commands/my-cmd.md     # → $target/commands/my-cmd.md
```

## Multiple targets

Use separate configs per tool:

```bash
plugsync --config ~/.claude/plugsync.yaml    # → ~/.claude
plugsync --config ~/.cursor/plugsync.yaml    # → ~/.cursor
```

## Update

```bash
uv tool upgrade plugsync
```
