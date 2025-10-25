import os
import ast
import re
import redis
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

#Connect to Redis
try:
    r = redis.Redis(host="redis_service", port=6379, decode_responses=True)
    r.ping()
    print("Connected to Redis successfully")
except Exception as e:
    print("Redis connection failed:", e)
    r = None

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

#Helper function to split method names into words
def split_method_name(name):
    #Replace underscores with spaces
    name = name.replace("_", " ")
    #Add space before any capital letter (for camelCase)
    name = re.sub(r'([a-z])([A-Z])', r'\1 \2', name)
    #Split into words and lowercase them
    words = name.lower().split()
    return words

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

        #Extract function/method names and push to Redis
        for file_path in code_files[:3]:
            print(f"\nReading file: {file_path}")
            file_content = top_repo.get_contents(file_path)
            code = file_content.decoded_content.decode("utf-8")

            all_words = []

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
                            words = split_method_name(name)
                            all_words.extend(words)
                    else:
                        print("No functions found.")
                except Exception as parse_error:
                    print("Error parsing Python file:", parse_error)

            #Java file extraction
            elif file_path.endswith(".java"):
                print("Language detected: Java")
                java_methods = re.findall(r'\b(?:public|private|protected)\s+\w+\s+(\w+)\s*\(', code)
                if java_methods:
                    print("Extracted methods:")
                    for method in java_methods:
                        print("  -", method)
                        words = split_method_name(method)
                        all_words.extend(words)
                else:
                    print("No methods found.")

            #Push words to Redis
            if r and all_words:
                for w in all_words:
                    r.lpush("method_words", w)
                print(f"Pushed {len(all_words)} words to Redis from {file_path}")

    except Exception as e:
        print("Error while accessing repository contents:", e)
else:
    print("No repository found to explore.")
