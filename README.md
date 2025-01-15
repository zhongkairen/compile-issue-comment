# compile-issue-comment
A GitHub action that Gathers issue comments, compiles them into a cohesive paragraph, and posts the result in a discussion.

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
      uses: zhongkairen/compile-issue-comment@latest
      with:
        github-token: ${{ secrets.GITHUB_TOKEN }}
        label-name: "epic"
        comment-prefix: "[week3]"
        discussion-heading: "Weekly log - week 3"
```
More details can be found in `.github/workflows/example.yml`.
