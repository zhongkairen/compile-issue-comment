import os
from github import Github
import requests


def get_issues_and_comments(repo, label, comment_prefix):
    issues = repo.get_issues(state="open", labels=[label])
    aggregated_content = ""

    for issue in issues:
        relevant_comments = [
            comment for comment in issue.get_comments() if comment.body.startswith(comment_prefix)
        ]
        if relevant_comments:
            aggregated_content += f"### Issue #{issue.number}: {issue.title} - "
            comments = [comment.body.replace(
                comment_prefix, "").lstrip() for comment in relevant_comments]
            aggregated_content += " ".join(comments)
            print(f"Aggregated content: '{comments}'")

    return aggregated_content


def fetch_discussions(owner, repo_name, graphql_schema, token):
    """Fetch discussions from the repository using a GraphQL query."""
    headers = {"Authorization": f"Bearer {token}"}
    query = {
        "query": graphql_schema,
        "variables": {
            "owner": owner,
            "repo": repo_name,
        },
    }
    response = requests.post(
        "https://api.github.com/graphql", json=query, headers=headers
    )
    response.raise_for_status()  # Raise an error for HTTP failures
    result = response.json()
    print(f"GraphQL Response: {result}")  # Add this line to debug
    if "data" not in result:
        raise ValueError(f"Unexpected GraphQL response format: {result}")
    return result["data"]["repository"]["discussions"]["nodes"]


def edit_discussion(discussion_id, new_content, token):
    """
    Edit an existing discussion using the GitHub GraphQL API.
    """
    mutation = """
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
    headers = {"Authorization": f"Bearer {token}"}
    variables = {"discussionId": discussion_id, "body": new_content}
    response = requests.post(
        "https://api.github.com/graphql",
        json={"query": mutation, "variables": variables},
        headers=headers,
    )
    response.raise_for_status()
    data = response.json()

    # Debug the response
    print(f"Edit Discussion Response: {data}")
    if "errors" in data:
        raise ValueError(f"Failed to update discussion: {data['errors']}")
    return data["data"]["updateDiscussion"]["discussion"]


def create_or_update_discussion(repo, discussion_heading, comment_prefix, content, graphql_schema, owner, repo_name, token, category_id):
    content = f"# {discussion_heading}\n\n" + content
    discussion_title = comment_prefix.strip("[]").strip()
    discussions = fetch_discussions(owner, repo_name, graphql_schema, token)

    # Check for existing discussion
    for discussion in discussions:
        if discussion["title"] == discussion_title:
            # Edit the discussion if found
            # repo.get_discussion(discussion["id"]).edit(body=content)
            edit_discussion(discussion["id"], content, token)
            return

    # If not found, create a new discussion using the GraphQL mutation
    mutation = """
    mutation($title: String!, $body: String!, $repoId: ID!, $categoryId: ID!) {
    createDiscussion(input: {repositoryId: $repoId, categoryId: $categoryId, title: $title, body: $body}) {
            discussion {
                id
                title
            }
        }
    }
    """
    # Make sure to fetch the repository ID here
    repo_id_query = """
    query($owner: String!, $repo: String!) {
        repository(owner: $owner, name: $repo) {
            id
        }
    }
    """
    # Get repository ID
    headers = {"Authorization": f"Bearer {token}"}
    repo_query = {
        "query": repo_id_query,
        "variables": {"owner": owner, "repo": repo_name},
    }
    repo_response = requests.post(
        "https://api.github.com/graphql", json=repo_query, headers=headers
    )
    repo_response.raise_for_status()
    repo_data = repo_response.json()
    repo_id = repo_data["data"]["repository"]["id"]

    # Now create the discussion using the mutation
    mutation_query = {
        "query": mutation,
        "variables": {
            "owner": owner,
            "repo": repo_name,
            "title": discussion_title,
            "body": content,
            "repoId": repo_id,
            "categoryId": category_id,
        },
    }

    # todo: add usage of discussion category

    mutation_response = requests.post(
        "https://api.github.com/graphql", json=mutation_query, headers=headers
    )
    mutation_response.raise_for_status()
    mutation_result = mutation_response.json()
    # Add this line to debug
    print(f"Create discussion Response: {mutation_result}")

    if mutation_result.get("errors"):
        raise ValueError(
            f"Failed to create discussion: {mutation_result['errors']}")

    print(
        f"Created discussion with title: {mutation_result['data']['createDiscussion']['discussion']['title']}")


def get_category_id(owner, repo_name, category_name, token):
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
    headers = {"Authorization": f"Bearer {token}"}
    variables = {"owner": owner, "repo": repo_name}
    response = requests.post(
        "https://api.github.com/graphql",
        json={"query": query, "variables": variables},
        headers=headers,
    )
    response.raise_for_status()
    data = response.json()

    # Extract categories
    categories = data["data"]["repository"]["discussionCategories"]["nodes"]
    for category in categories:
        if category["name"] == category_name:
            return category["id"]
    return None


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

    owner = repository.split("/")[0]  # Extract owner from 'owner/repo'
    repo_name = repository.split("/")[1]  # Extract repo name from 'owner/re

    # Debug line
    print(f"Fetching discussions for owner: {owner} and repo: {repo_name}")

    g = Github(token)
    repo = g.get_repo(repository)

    # Fetch category ID if it's provided
    category_id = None
    if discussion_category:
        category_id = get_category_id(
            owner, repo_name, discussion_category, token)
        if category_id:
            print(
                f"Found discussion category ID: {category_id} for '{discussion_category}'")
        else:
            print(f"discussion category '{discussion_category}' not found!")
            exit(1)

    graphql_schema = """
    query ($owner: String!, $repo: String!) {
      repository(owner: $owner, name: $repo) {
        discussions(first: 100) {
          nodes {
            id
            title
            body
          }
        }
      }
    }
    """

    aggregated_content = get_issues_and_comments(
        repo, label_name, comment_prefix)
    create_or_update_discussion(
        repo, discussion_heading, comment_prefix, aggregated_content, graphql_schema, owner, repo_name, token, category_id)


if __name__ == "__main__":
    main()
