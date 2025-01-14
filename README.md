# github-weekly-tool

# Aggregate Comments Action

This GitHub Action aggregates issue comments with a specific prefix and updates/creates a discussion thread.

## Inputs

| Name                  | Description                      | Default               |
| --------------------- | -------------------------------- | --------------------- |
| `github-token`        | GitHub token for API access.     | **Required**          |
| `repository`          | Repository name (owner/repo).    | `{github.repository}` |
| `label-name`          | Issue label to filter by.        | `bug`                 |
| `comment-prefix`      | Prefix to filter issue comments. | `DISCUSSION:`         |
| `discussion-heading`  | Title of the discussion thread.  | `Aggregated Comments` |
| `discussion-category` | Category for the discussion.     | `General`             |

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
      uses: zhongkairen/github-weekly-tool@v1
      with:
        github-token: ${{ secrets.GITHUB_TOKEN }}
        repo-name: your-org/your-repo
        label-name: "epic"
        comment-prefix: "[week03]"
        discussion-heading: "Weekly log - week 3"
```
More can be found from `.github/workflows/test.yml`.
