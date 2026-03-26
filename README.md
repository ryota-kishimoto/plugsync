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

```
$ plugsync
Target: ~/.claude

→ Cloning https://github.com/anthropics/skills ...
  ✓ [skills] skill-creator
  ✓ [skills] frontend-design

→ Cloning https://github.com/obra/superpowers ...
  ✓ [skills] brainstorming
  ✓ [agents] code-reviewer.md
  ✓ [commands] brainstorm.md

Done.
```

```yaml
target: ~/.claude

repos:
  - url: https://github.com/anthropics/skills
    skills:
      - skills/skill-creator
      - skills/frontend-design

  - url: https://github.com/obra/superpowers
    skills:
      - skills/brainstorming
      - skills/systematic-debugging
      - skills/writing-plans
    agents:
      - agents/code-reviewer.md
    commands:
      - commands/brainstorm.md
      - commands/write-plan.md
      - commands/execute-plan.md
```
