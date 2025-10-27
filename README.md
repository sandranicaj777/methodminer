# Method Miner — GitHub Function Name Analyzer

## Overview

Method Miner is a containerized system that mines GitHub repositories to extract and analyze the most frequent words used in function and method names in Python and Java codebases.

It consists of two main components:

- Miner – collects data from GitHub and streams extracted words  
- Visualizer – receives live data, aggregates frequencies, and displays results in real time  

---

## System Architecture

Producer–Consumer model:
GitHub → Miner → Redis (pub/sub) → Visualizer (Socket.IO + Chart.js)


Each component runs in its own Docker container:
- `miner_service`: continuously crawls GitHub repositories  
- `redis_service`: message broker for word streaming  
- `visualizer_service`: interactive dashboard for real-time insights  

---

## Components

### Miner

- Interacts with the GitHub API (via PyGithub) to retrieve repositories ordered by stars  
- Extracts words from:
  - Python function names (using the `ast` module)
  - Java method names (using regex-based parsing)
- Streams extracted words through Redis Pub/Sub  
- Automatically handles:
  - API rate limits  
  - Repository timeouts  
  - Skipping large files  
  - Graceful error recovery  

### Visualizer

- Built with Flask and Socket.IO  
- Subscribes to Redis channels for live updates  
- Displays the top 10 most frequent words in an animated bar chart (Chart.js)  
- Allows filtering by:
  - Programming language (Python / Java / All)
  - Text search filter  
- Shows total word count and the last mined repository  

---

## Containers Setup

### Project Structure

.
├── miner/
│ ├── miner.py
│ ├── init.py
├── visualizer/
│ ├── app.py
│ ├── static/
│ │ ├── script.js
│ │ ├── favicon.png
│ ├── templates/
│ │ └── index.html
├── tests/
│ └── test_all.py
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
└── .env


### Docker Services

| Service | Description | Port |
|----------|--------------|------|
| redis_service | Message broker | 6379 |
| miner_service | Extracts words and streams data | — |
| visualizer_service | Web dashboard | 5050 |

---

## How to Run

### 1. Clone the repository
```bash
git clone https://github.com/<your-username>/methodminer.git
cd methodminer

2. Configure environment variables
Create a .env file in the project root:

bash
GITHUB_TOKEN=your_github_token
REPO_LIMIT=20
FILE_LIMIT=20
REDIS_HOST=redis_service

3. Build and start the containers
bash
docker-compose down
docker system prune -af --volumes
docker-compose build --no-cache
docker-compose up

Then open the dashboard at:
http://localhost:5050

Running Tests

bash
pytest -v

Tests cover:

Python and Java method extraction

Word splitting logic

File content processing

Logging and Resilience
All miner events are logged with timestamps and severity levels.

Timeouts prevent long-running repositories.

Faulty files are skipped without interrupting mining.

Automatic reconnection to Redis if disconnected.

Example log output:

yaml
2025-10-27 16:42:12 [INFO] MINING CYCLE #1
2025-10-27 16:42:15 [INFO] Processing python repo: pypa/pip
2025-10-27 16:42:48 [INFO] pypa/pip: 432 words extracted


Dashboard
Real-time bar chart of the top 10 most frequent words

Filter by language or substring

Displays total count and last processed repository

Smooth gradient bars and animated transitions for a modern, clean interface

Future Improvements
Add support for additional languages (C++, JavaScript, Go)

Parallelized mining with multithreading for faster performance

Semantic grouping of similar words

Historical trend visualization

