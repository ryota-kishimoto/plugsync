---
name: plugsync
description: ~/.plugsync.yaml に定義されたGitHubリポジトリからskills/agents/commandsを取得して~/.claudeに配置する。「skillを同期して」「plugin-sync実行して」「スキルを更新して」と言われたら使うこと。
---

## 実行方法

```bash
plugsync
```

## ~/.plugsync.yaml の管理

`~/.plugsync.yaml` でリポジトリとパスを管理している。

```yaml
target: ~/.claude

repos:
  - url: https://github.com/example/repo
    skills:
      - skills/my-skill
    agents:
      - agents/my-agent.md
    commands:
      - commands/my-command.md
```

新しいスキルを追加するときは `~/.plugsync.yaml` に追記して `plugsync` を実行する。

## paths: で任意パスに配置

`skills:` などの予約語以外に、`paths:` で任意のパスに配置できる。

```yaml
target: ~

repos:
  - url: https://github.com/someone/dotfiles
    paths:
      - path: .editorconfig
        src:
          - .editorconfig
      - path: .github
        src:
          - PULL_REQUEST_TEMPLATE.md
```
