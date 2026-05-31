import asyncio
import sys
import config
import warnings
from crawler import AsyncEngine
from graph_builder import SecurityGraphBuilder
from utils import Colors

def main():
    print(f"{Colors.BLUE}{Colors.BOLD}=== Starting Smart Crawler Engine Pipeline ==={Colors.END}\n")

    # 1. Initialize and launch the Asynchronous Web Crawling Matrix
    engine = AsyncEngine(config.START_URL)
    
    # Run the async engine execution loop cleanly using the verified policy handler
    intelligence_feed, structural_links = asyncio.run(engine.run())

    print(f"\n{Colors.GREEN}[✔] Exploration Complete. Found {len(intelligence_feed)} accessible nodes.{Colors.END}")

    # Note: crawler.py automatically outputs output/crawler_output.json at the end of engine.run()

    # 2. Initialize Graph Processing Matrices
    print(f"\n{Colors.BLUE}[*] Launching Topology Architecture Map Assembly...{Colors.END}")
    builder = SecurityGraphBuilder()
    
    # Pass the collected data into our rebuilt graph engine
    builder.process_crawled_data(intelligence_feed)

    # 3. Generate structured nodes/edges format file output (graph_output.json)
    builder.export_graph_json()

    # 4. Trigger graph window view modal and save static PNG canvas snapshot
    print(f"{Colors.GREEN}[✔] Visual Canvas Prepared. Rendering layout window...{Colors.END}")
    builder.draw_graph()


# ==========================================
# DEPLOYED RUNTIME DEBUG SCOPE (SOFT-CODED ENTRY)
# ==========================================
print("\n[DEBUG 1] Python has loaded main.py and is reading the global scope!")

if __name__ == "__main__":
    print("[DEBUG 2] Python successfully entered the __main__ block!")
    
    # Windows-specific event loop adjustments must occur BEFORE asyncio.run() executes
    if sys.platform == 'win32':
        print("[DEBUG] Windows OS detected. Applying Proactor event loop policy optimization...")
        # Silence the Windows-specific event loop deprecation warning noise
        warnings.filterwarnings("ignore", category=DeprecationWarning)
        asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
    
    print("[DEBUG 3] Now jumping into main()...")
    main()