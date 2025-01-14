import os
from github import Github
import requests


class IssueComment:
    """Data class for GitHub comments."""

    def __init__(self, issue, comment_prefix):
        self.issue = issue
        self.comment_prefix = comment_prefix

    def __str__(self):
        aggregated_content = f"**{self.issue.title}** (#{self.issue.number}) - "
        comments = [comment.body.replace(
            self.comment_prefix, "").lstrip() for comment in self.comments]
        aggregated_content += " ".join(comments)
        return aggregated_content

    @property
    def comments(self):
        return [
            comment for comment in self.issue.get_comments() if comment.body.startswith(self.comment_prefix)
        ]


class Repository:
    """Wrapper class for the GitHub repository."""

    def __init__(self, repository, token):
        g = Github(token)
        self.repo = g.get_repo(repository)
        self.owner = self.repo.owner.login
        self.name = self.repo.name
        self.token = token

    @property
    def id(self):
        if not hasattr(self, "_id"):
            self._id = self.query_id()
        return self._id

    def get_aggregated_comment(self, label, comment_prefix):
        issues = self.repo.get_issues(state="open", labels=[label])
        return "\n".join(str(IssueComment(issue, comment_prefix)) for issue in issues)

    def post(self, query, variables):
        headers = {"Authorization": f"Bearer {self.token}"}
        response = requests.post(
            "https://api.github.com/graphql", json={"query": query, "variables": variables}, headers=headers
        )
        response.raise_for_status()
        return response.json()

    def query_id(self):
        query = """
            query($owner: String!, $repo: String!) {
                repository(owner: $owner, name: $repo) {
                    id
                }
            }
        """
        headers = {"Authorization": f"Bearer {self.token}"}
        variables = {"owner": self.owner, "repo": self.name}
        data = self.post(query, variables)
        return data["data"]["repository"]["id"]

    def query_discussion_category_ids(self):
        """
        Fetch the category ID for a discussion category using the GitHub GraphQL API.
        """
        query = """
        query($owner: String!, $repo: String!) {
        repository(owner: $owner, name: $repo) {
            discussionCategories(first: 100) {
            nodes {
                id
                name
            }
            }
        }
        }
        """
        variables = {"owner": self.owner, "repo": self.name}
        data = self.post(query, variables)

        # Extract categories
        categories = data["data"]["repository"]["discussionCategories"]["nodes"]
        return {category["name"]: category["id"] for category in categories}


class Discussion:
    """Wrapper class for the GitHub discussion."""

    def __init__(self, repo):
        self.repo = repo
        # self._title = None
        self.category_map = None

    def get_category_id(self, category_name):
        if not self.category_map:
            self.category_map = self.repo.query_discussion_category_ids()
        return self.category_map.get(category_name)

    def get_discussion_id(self, title: str):
        discussion_schema = """
            id
            title
        """
        discussions_pages = self.repo.repo.get_discussions(discussion_schema)
        discussions = list(discussions_pages)
        for discussion in discussions:
            if discussion.title == title:
                return discussion.id

    def edit(self, discussion_id, body):
        update_discussion_mutation = """
        mutation($discussionId: ID!, $body: String!) {
            updateDiscussion(input: {discussionId: $discussionId, body: $body}) {
                discussion {
                    id
                    title
                    body
                }
            }
        }
        """
        variables = {"discussionId": discussion_id, "body": body}
        data = self.repo.post(update_discussion_mutation, variables)

        if "errors" in data:
            raise ValueError(f"Failed to update discussion: {data['errors']}")
        return data["data"]["updateDiscussion"]["discussion"]

    def create(self, category_id, title, body):
        # If not found, create a new discussion using the GraphQL mutation
        create_discussion_mutation = """
        mutation($title: String!, $body: String!, $repoId: ID!, $categoryId: ID!) {
        createDiscussion(input: {repositoryId: $repoId, categoryId: $categoryId, title: $title, body: $body}) {
                discussion {
                    id
                    title
                }
            }
        }
        """
        # Now create the discussion using the mutation
        mutation_result = self.repo.post(create_discussion_mutation, {
            "title": title,
            "body": body,
            "repoId": self.repo.id,
            "categoryId": category_id,
        })

        # Add this line to debug
        print(f"Create discussion Response: {mutation_result}")

        if mutation_result.get("errors"):
            raise ValueError(
                f"Failed to create discussion: {mutation_result['errors']}")

        print(
            f"Created discussion with title: {mutation_result['data']['createDiscussion']['discussion']['title']}")


def main():
    token = os.getenv("GITHUB_TOKEN")
    repository = os.getenv("REPOSITORY")
    label_name = os.getenv("LABEL_NAME")
    comment_prefix = os.getenv("COMMENT_PREFIX")
    discussion_heading = os.getenv("DISCUSSION_HEADING")
    discussion_category = os.getenv("DISCUSSION_CATEGORY")

    # Debug prints for all variables
    print(f"GITHUB_TOKEN: {token}")
    print(f"REPOSITORY: {repository}")
    print(f"LABEL_NAME: {label_name}")
    print(f"COMMENT_PREFIX: {comment_prefix}")
    print(f"DISCUSSION_HEADING: {discussion_heading}")
    print(f"DISCUSSION_CATEGORY: {discussion_category}")

    repo = Repository(repository, token)

    # Fetch category ID if it's provided
    discussion = Discussion(repo)

    category_id = discussion.get_category_id(discussion_category)

    if category_id:
        print(
            f"Found discussion category ID: {category_id} for '{discussion_category}'")
    else:
        print(f"discussion category '{discussion_category}' not found!")
        exit(1)

    aggregated_content = repo.get_aggregated_comment(
        label_name, comment_prefix)

    discussion_id = discussion.get_discussion_id(title=discussion_heading)
    if discussion_id:
        print(f"Discussion found: {discussion_heading}, {discussion_id}")
        discussion.edit(discussion_id, body=aggregated_content)
    else:
        print(f"Discussion not found: {discussion_heading}")
        # create new discussion
        discussion.get_category_id(discussion_category)
        discussion.create(category_id, title=discussion_heading,
                          body=aggregated_content)


if __name__ == "__main__":
    main()
