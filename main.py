import asyncio
import sys
import config
from crawler import AsyncEngine
from store import DataStore
from graph_builder import SecurityGraphBuilder
from utils import Colors

def main():
    print(f"{Colors.BLUE}{Colors.BOLD}=== Starting Smart Crawler Engine Pipeline ==={Colors.END}\n")

    #Start the Asynchronous Web Crawling Matrix
    engine = AsyncEngine(config.START_URL)
    intelligence_feed, structural_links = asyncio.run(engine.run())

    print(f"\n{Colors.GREEN}[✔] Exploration Complete. Found {len(intelligence_feed)} accessible nodes.{Colors.END}")

    #Export Raw Core Data Blueprints
    DataStore.save_json(config.LINKS_JSON_FILE, structural_links)
    DataStore.save_json(config.RESULTS_JSON_FILE, intelligence_feed)

    #Initialize Graph Processing Matrices
    print(f"\n{Colors.BLUE}[*] Launching Topology Architecture Map Assembly...{Colors.END}")
    builder = SecurityGraphBuilder()
    builder.process_crawled_data(intelligence_feed)

    # Generate structured nodes/links format file output
    builder.export_graph_json()

    # Trigger graph window view modal
    print(f"{Colors.GREEN}[✔] Visual Canvas Prepared. Rendering layout window...{Colors.END}")
    builder.draw_graph()

# ==========================================
# DEPLOYED RUNTIME DEBUG SCOPE (SOFT-CODED ENTRY)
# ==========================================
print("\n[DEBUG 1] Python has loaded main.py and is reading the global scope!")

if __name__ == "__main__":
    print("[DEBUG 2] Python successfully entered the __main__ block!")
    
    if sys.platform == 'win32':
        import warnings
        # Silence the 3.16 deprecation warning noise
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", DeprecationWarning)
            asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
    
    print("[DEBUG 3] Now jumping into main()...")
    main()