import asyncio
from playwright.async_api import async_playwright
from parser import HTMLParser
from utils import is_same_domain
import config
import json
from datetime import datetime
import os

class AsyncEngine:
    def __init__(self, start_url):
        self.start_url = start_url
        self.visited_urls = set()
        self.collected_intel = []
        self.relationship_links = []
        self.max_depth = config.MAX_DEPTH
        self.concurrent_limit = config.CONCURRENT_REQUESTS

    async def worker(self, queue, browser):
        """Workers fetch tasks from the queue and interact with live DOM elements headless."""
        context = await browser.new_context(user_agent=config.USER_AGENT)
        
        while True:
            url, depth = await queue.get()
            
            # FIXED: Avoid the outer try/finally entirely for skipped links 
            # to prevent task_done() from firing twice on a single item.
            if depth > self.max_depth or url in self.visited_urls:
                queue.task_done()
                continue

            self.visited_urls.add(url)
            print(f"[*] Crawling: {url} (Depth: {depth})")

            # Isolate browser interactions safely
            try:
                page = await context.new_page()
                try:
                    response = await page.goto(url, wait_until="domcontentloaded", timeout=30000)
                    
                    if response and response.status == 200:
                        html = await page.content()
                        discovered_links, intel = HTMLParser.parse_page(html, url)
                        headers = response.headers
                        content_type = headers.get("content-type", "text/html").split(";")[0]
                        page_intel = {
                                    "url": url,
                                    "method": "GET",  # Base automated request configuration
                                    "status_code": response.status,
                                    "content_type": content_type,
                                    "parameters": intel.get("parameters", []),
                                    "forms": intel.get("forms", []),
                                    "links": discovered_links,
                                    "technologies": intel.get("technologies", [])
                             }
                        self.collected_intel.append(page_intel)

                        for next_link in discovered_links:
                            self.relationship_links.append({"source": url, "target": next_link})
                            
                            if is_same_domain(next_link, self.start_url) and next_link not in self.visited_urls:
                                await queue.put((next_link, depth + 1))
                    else:
                        status = response.status if response else "No Response"
                        print(f"[!] Target skipped due to bad HTTP status: {status} on {url}")

                except asyncio.CancelledError:
                    # Capture cancellation context gracefully without letting it fall into generic blocks
                    raise
                except Exception as page_err:
                    print(f"[!] Timeout or render error on {url}: {page_err}")
                finally:
                    await page.close()

            except asyncio.CancelledError:
                # If the main script tells the worker to stop, bubble the cancel upward cleanly
                queue.task_done()
                raise
            except Exception as worker_err:
                print(f"[!] Worker level critical fault: {worker_err}")
                queue.task_done()
            else:
                # Task completed successfully without errors
                queue.task_done()
                
        await context.close()
    
    def save_results(self):
        """Compiles collected crawler intelligence records into the final schema file."""
        if not self.collected_intel:
            print("[!] No data collected to export.")
            return

        target_profile = self.collected_intel[0]

        final_output = {
            "url": target_profile.get("url", self.start_url),
            "method": target_profile.get("method", "GET"),
            "status_code": target_profile.get("status_code", 200),
            "content_type": target_profile.get("content_type", "text/html"),
            "discovered_at": datetime.utcnow().isoformat() + "Z", 
            "parameters": target_profile.get("parameters", [
                {"name": "user", "type": "query", "value": ""},
                {"name": "redirect", "type": "query", "value": ""}
            ]),
            "forms": target_profile.get("forms", []),
            "links": list(self.visited_urls),  
            "technologies": target_profile.get("technologies", [])
        }

        os.makedirs("output", exist_ok=True)

        with open("output/crawler_output.json", "w") as f:
            json.dump(final_output, f, indent=4)

        print("[*] Successfully generated output/results.json.")
        
    #  FIXED: Indented properly inside the AsyncEngine class structure
    async def run(self):
        """Main orchestrator utilizing Playwright context environments."""
        queue = asyncio.Queue()
        await queue.put((self.start_url, 0))

        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            
            workers = [
                asyncio.create_task(self.worker(queue, browser))
                for _ in range(self.concurrent_limit)
            ]

            await queue.join()

            for worker_task in workers:
                worker_task.cancel()
            
            await asyncio.gather(*workers, return_exceptions=True)
            await browser.close()
            
            self.save_results()

        return self.collected_intel, self.relationship_links