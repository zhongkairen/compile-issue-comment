import os
from github import Github


def get_issues_and_comments(repo, label, comment_prefix):
    issues = repo.get_issues(state="open", labels=[label])
    aggregated_content = "# Aggregated Comments\n\n"

    for issue in issues:
        relevant_comments = [
            comment for comment in issue.get_comments() if comment.body.startswith(comment_prefix)
        ]
        if relevant_comments:
            aggregated_content += f"### Issue #{issue.number}: {issue.title}\n"
            for comment in relevant_comments:
                aggregated_content += f"- {comment.body}\n\n"

    return aggregated_content


def create_or_update_discussion(repo, discussion_title, content):
    discussions = repo.get_discussions()
    for discussion in discussions:
        if discussion.title == discussion_title:
            discussion.edit(body=content)
            return

    # Create new discussion if not found
    repo.create_discussion(title=discussion_title, body=content)


def main():
    token = os.getenv("GITHUB_TOKEN")
    repo_name = os.getenv("REPO_NAME")
    label_name = os.getenv("LABEL_NAME")
    comment_prefix = os.getenv("COMMENT_PREFIX")
    discussion_title = os.getenv("DISCUSSION_TITLE")

    g = Github(token)
    repo = g.get_repo(repo_name)

    aggregated_content = get_issues_and_comments(
        repo, label_name, comment_prefix)
    create_or_update_discussion(repo, discussion_title, aggregated_content)


if __name__ == "__main__":
    main()
