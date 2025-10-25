import os
from github import Github, Auth

#Read GitHub token from environment variable
token = os.getenv("GITHUB_TOKEN")

#Connect to GitHub 
if token:
    print("Using authenticated GitHub connection")
    g = Github(auth=Auth.Token(token))
else:
    print("No token found, using anonymous connection (limited requests)")
    g = Github()

print("Fetching 5 top Python repositories")

#Searching for repositories written in Python, sorted by stars
repos = g.search_repositories(query="language:python", sort="stars", order="desc")

#Store the first repo 
top_repo = None
count = 0
for repo in repos:
    print(f"{repo.full_name} - {repo.stargazers_count}")
    count += 1
    if count == 1:  # take the first repo only
        top_repo = repo
    if count == 5:
        break

print("Fetched 5 repositories.\n")

#Access the files of the top repository
if top_repo:
    print(f"Now exploring repository: {top_repo.full_name}")
    try:
     
        contents = top_repo.get_contents("")

        #explore subfolders too with stack
        files_to_check = []

        while contents:
            file_content = contents.pop(0)
            if file_content.type == "dir":
                #if it's a folder - add its contents to our list
                contents.extend(top_repo.get_contents(file_content.path))
            else:
                #if it's a file - save its path
                files_to_check.append(file_content.path)

        #Filter only .py and .java files!!
        code_files = [f for f in files_to_check if f.endswith(".py") or f.endswith(".java")]

        print(f"Found {len(code_files)} code files (.py/.java) in {top_repo.full_name}")
        #Show the first few for confirmation
        for f in code_files[:10]:
            print("  -", f)

    except Exception as e:
        print("Error while accessing repository contents:", e)
else:
    print("No repository found to explore.")
