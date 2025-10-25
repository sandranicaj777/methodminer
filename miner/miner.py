import os
from github import Github, Auth

#Read GitHub token from environment variable
token = os.getenv("GITHUB_TOKEN")

#Connect to GitHub (authenticated if token is available)
if token:
    print("Using authenticated GitHub connection")
    g = Github(auth=Auth.Token(token))
else:
    print("No token found, using anonymous connection (limited requests)")
    g = Github()

print("Fetching 5 top Python repositories")

#Searching for repositories written in Python, sorted by stars
repos = g.search_repositories(query="language:python", sort="stars", order="desc")

#Print out the first 5 repos as a test
count = 0
for repo in repos:
    print(f"{repo.full_name} - {repo.stargazers_count}")
    count += 1
    if count == 5:
        break

print("Fetched 5 repositories.")
