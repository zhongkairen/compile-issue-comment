# github-weekly-tool

# Aggregate Comments Action

This GitHub Action aggregates issue comments with a specific prefix and updates/creates a discussion thread.

## Inputs

| Name               | Description                      | Default               |
| ------------------ | -------------------------------- | --------------------- |
| `github-token`     | GitHub token for API access.     | **Required**          |
| `repo-name`        | Repository name (owner/repo).    | **Required**          |
| `label-name`       | Issue label to filter by.        | `bug`                 |
| `comment-prefix`   | Prefix to filter issue comments. | `DISCUSSION:`         |
| `discussion-title` | Title of the discussion thread.  | `Aggregated Comments` |

## Example Usage

```yaml
name: Aggregate Comments

on:
  schedule:
    - cron: '0 2 * * *'
  workflow_dispatch:

jobs:
  aggregate-comments:
    runs-on: ubuntu-latest
    steps:
    - name: Aggregate Comments
      uses: your-org/aggregate-comments-action@v1
      with:
        github-token: ${{ secrets.GITHUB_TOKEN }}
        repo-name: your-org/your-repo
        label-name: "enhancement"
        comment-prefix: "NOTE:"
        discussion-title: "Enhanced Notes"
```