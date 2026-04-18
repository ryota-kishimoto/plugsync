---
name: plugsync
description: ~/.plugsync.yaml に定義されたGitHubリポジトリからskills/agents/commandsを取得して~/.claudeに配置する。「skillを同期して」「plugin-sync実行して」「スキルを更新して」と言われたら使うこと。
---

## 実行方法

```bash
plugsync                   # lock があれば固定SHAで同期、なければ最新取得して lock 生成
plugsync --update          # 全repoを最新取得、lock 再生成
plugsync --update foo/bar  # 指定repoだけ最新取得（url または org/name）
plugsync --frozen          # lock 必須、なければエラー
plugsync --dry-run         # プレビューのみ（lock 書き出しなし）
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

## plugsync.lock

`plugsync` を実行すると、config と同じディレクトリに `plugsync.lock` が生成される。各リポジトリのコミットSHAを記録し、次回以降は同じバージョンで同期する。最新に更新したいときは `plugsync --update` を使う。特定のrepoだけ更新したいときは `plugsync --update foo/bar` のように url か `org/name` を渡す。

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
