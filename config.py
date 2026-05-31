import os

START_URL = "https://cyart.in/"
MAX_DEPTH = 2
CONCURRENT_REQUESTS = 5
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) SmartCrawler/13.0"

# Target Storage Configuration
OUTPUT_DIR = "output"
RESULTS_JSON_FILE = os.path.join(OUTPUT_DIR, "crawler_output.json")
GRAPH_JSON_FILE = os.path.join(OUTPUT_DIR, "graph_output.json")