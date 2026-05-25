#Yogiramsuratkumar Jaya Guru Raya!
import os

START_URL = "https://cyart.in/"
MAX_DEPTH = 2
CONCURRENT_REQUESTS = 5
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) SmartCrawler/13.0"

# Target Storage Configuration
OUTPUT_DIR = "output"
LINKS_JSON_FILE = os.path.join(OUTPUT_DIR, "links.json")
RESULTS_JSON_FILE = os.path.join(OUTPUT_DIR, "results.json")
GRAPH_JSON_FILE = os.path.join(OUTPUT_DIR, "graph_output.json")