import os
import ast
import re
import time
import redis
import signal
from github import Github, Auth
from dotenv import load_dotenv

print("=== MINER STARTING ===")

# Load environment variables
load_dotenv()

# Connect to GitHub
token = os.getenv("GITHUB_TOKEN")
if token:
    g = Github(auth=Auth.Token(token))
    print("Using authenticated GitHub connection")
else:
    g = Github()
    print("WARNING: No GitHub token found, using anonymous connection (limited requests)")

# Connect to Redis
redis_host = os.getenv("REDIS_HOST", "redis_service")
try:
    r = redis.Redis(host=redis_host, port=6379, decode_responses=True)
    r.ping()
    print(f"Connected to Redis at {redis_host}")
except Exception as e:
    print(f"Redis connection failed: {e}")
    r = None

# Config
REPO_LIMIT = int(os.getenv("REPO_LIMIT", 5))
FILE_LIMIT = int(os.getenv("FILE_LIMIT", 5))

print(f"REPO_LIMIT: {REPO_LIMIT}, FILE_LIMIT: {FILE_LIMIT}")



def split_method_name(name):
    """Split method or function names into words."""
    name = name.replace("_", " ")
    name = re.sub(r'([a-z])([A-Z])', r'\1 \2', name)
    words = name.lower().split()
    return [w for w in words if w.isalpha() and len(w) > 1]

class TimeoutError(Exception):
    pass

def timeout_handler(signum, frame):
    raise TimeoutError("Repository processing timeout")

def extract_java_methods(code):
    """Extract Java method names using regex patterns."""
    methods = []
    patterns = [
        r'\b(?:public|private|protected|static|final|synchronized|abstract|\s)+[\w<>\[\],\s]+\s+(\w+)\s*\([^)]*\)\s*\{',
        r'@\w+(?:\([^)]*\))?\s*(?:public|private|protected|static|\s)+[\w<>\[\],\s]+\s+(\w+)\s*\(',
        r'\b(?:public|private|protected)\s+(\w+)\s*\([^)]*\)\s*\{',
        r'\b([a-z][a-zA-Z0-9]*)\s*\([^);]*\)\s*\{'
    ]
    for pattern in patterns:
        methods.extend(re.findall(pattern, code))
    false_positives = {
        'class','interface','enum','if','for','while','switch','catch','try','return',
        'new','throw','assert','synchronized','this','super','true','false','null',
        'void','boolean','int','long','double','float','char','byte','short',
        'String','Object','List','Set','Map','ArrayList','HashMap'
    }
    return list(set([m for m in methods if m not in false_positives and len(m) > 1]))

def extract_python_functions(code):
    """Extract Python function names using AST."""
    try:
        tree = ast.parse(code)
        return [n.name for n in ast.walk(tree) if isinstance(n, ast.FunctionDef)]
    except:
        return []

def process_file_content(code, language):
    """Extract words from methods or functions."""
    all_words = []
    names = extract_python_functions(code) if language == "python" else extract_java_methods(code)
    for name in names:
        all_words.extend(split_method_name(name))
    return all_words

def find_code_files(repo, language, max_files=100):
    """Recursively find code files in a repository."""
    code_files = []
    def search(path):
        try:
            contents = repo.get_contents(path)
            for c in contents:
                if c.type == "dir":
                    search(c.path)
                else:
                    if (language == "python" and c.path.endswith(".py")) or \
                       (language == "java" and c.path.endswith(".java")):
                        code_files.append(c.path)
                    if len(code_files) >= max_files:
                        return
        except Exception as e:
            print(f"Error searching path {path}: {e}")
    search("")
    return code_files[:max_files]

def process_repository(repo, language):
    """Process a single repository and push words to Redis."""
    print(f"Processing {language} repo: {repo.full_name}")
    try:
        signal.signal(signal.SIGALRM, timeout_handler)
        signal.alarm(120)
        files = find_code_files(repo, language, FILE_LIMIT * 2)
        total_words = 0
        for file_path in files[:FILE_LIMIT]:
            try:
                content = repo.get_contents(file_path)
                if content.size > 500000:
                    continue
                code = content.decoded_content.decode("utf-8")
                words = process_file_content(code, language)
                for word in words:
                    r.publish("word_stream", f"{repo.full_name}|{language}|{word}")
                total_words += len(words)
            except Exception:
                continue
        signal.alarm(0)
        print(f"✓ {repo.full_name}: {total_words} words extracted")
        return total_words
    except TimeoutError:
        print(f"Timeout processing {repo.full_name}")
        return 0
    except Exception as e:
        print(f"Error processing {repo.full_name}: {e}")
        return 0

def mine_repositories_by_language(language):
    """Mine top repositories for a given language."""
    print(f"\n=== MINING {language.upper()} REPOSITORIES ===")
    try:
        repos = g.search_repositories(query=f"language:{language} sort:stars")
        count = 0
        total = 0
        for repo in repos:
            if count >= REPO_LIMIT:
                break
            if r:
                r.set("last_repo", f"{repo.full_name} ({language})")
            total += process_repository(repo, language)
            count += 1
            time.sleep(2)
        print(f"✓ Completed {language}: {count} repos, {total} words extracted")
        return total
    except Exception as e:
        print(f"Error mining {language}: {e}")
        return 0

def main_mining_cycle():
    """Run one full mining cycle."""
    print("Starting mining cycle...")
    try:
        rate = g.get_rate_limit().core
        print(f"GitHub API rate limit: {rate.remaining}/{rate.limit}")
    except:
        print("Could not check rate limit")
    total_words = 0
    for lang in ["python", "java"]:
        total_words += mine_repositories_by_language(lang)
        print("Waiting 10 seconds before next language...")
        time.sleep(10)
    print(f"Cycle complete: {total_words} total words")
    return total_words


if __name__ == "__main__":
    cycle = 0
    while True:
        try:
            cycle += 1
            print(f"\n{'='*50}\nMINING CYCLE #{cycle}\n{'='*50}")
            main_mining_cycle()
            print("Waiting 60 seconds before next cycle...")
            time.sleep(60)
        except KeyboardInterrupt:
            print("\nStopping miner...")
            break
        except Exception as e:
            print(f"Unexpected error: {e}")
            time.sleep(60)
