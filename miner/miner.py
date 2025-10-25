import os
import ast
import re
from github import Github, Auth

#Read GitHub token 
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

#Explore files of the top repository
if top_repo:
    print(f"Now exploring repository: {top_repo.full_name}")
    try:
        contents = top_repo.get_contents("")
        files_to_check = []

        while contents:
            file_content = contents.pop(0)
            if file_content.type == "dir":
                contents.extend(top_repo.get_contents(file_content.path))
            else:
                files_to_check.append(file_content.path)

        #Filter only .py and .java files
        code_files = [f for f in files_to_check if f.endswith(".py") or f.endswith(".java")]

        print(f"Found {len(code_files)} code files (.py/.java) in {top_repo.full_name}")
        for f in code_files[:10]:
            print("  -", f)

        #extract function/method names
        for file_path in code_files[:3]:
            print(f"\nReading file: {file_path}")
            file_content = top_repo.get_contents(file_path)
            code = file_content.decoded_content.decode("utf-8")

            #Python file extraction
            if file_path.endswith(".py"):
                print("Language detected: Python")
                try:
                    tree = ast.parse(code)
                    func_names = [node.name for node in ast.walk(tree) if isinstance(node, ast.FunctionDef)]
                    if func_names:
                        print("Extracted functions:")
                        for name in func_names:
                            print("  -", name)
                    else:
                        print("No functions found.")
                except Exception as parse_error:
                    print("Error parsing Python file:", parse_error)

            #Java file extraction
            elif file_path.endswith(".java"):
                print("Language detected: Java")
                #Simple regex 
                java_methods = re.findall(r'\b(?:public|private|protected)\s+\w+\s+(\w+)\s*\(', code)
                if java_methods:
                    print("Extracted methods:")
                    for method in java_methods:
                        print("  -", method)
                else:
                    print("No methods found.")

    except Exception as e:
        print("Error while accessing repository contents:", e)
else:
    print("No repository found to explore.")
