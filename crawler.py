import asyncio
from playwright.async_api import async_playwright
from parser import HTMLParser
from utils import is_same_domain
import config
import json
from datetime import datetime
from urllib.parse import urlparse, parse_qs
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
            
            if depth > self.max_depth or url in self.visited_urls:
                queue.task_done()
                continue

            self.visited_urls.add(url)
            print(f"[*] Crawling: {url} (Depth: {depth})")

            # Shared collection container for dynamic API endpoints discovered over the wire
            js_discovered_endpoints = []

            try:
                page = await context.new_page()
                
                # Dynamic Interception: Listen to live Fetch/XHR background API requests
                def handle_request(request):
                    if request.resource_type in ["xhr", "fetch"]:
                        js_discovered_endpoints.append({
                            "url": request.url,
                            "method": request.method,
                            "resource_type": request.resource_type
                        })
                
                page.on("request", handle_request)

                try:
                    # Changed wait_until to "networkidle" so background JS API requests complete
                    response = await page.goto(url, wait_until="networkidle", timeout=30000)
                    
                    if response and response.status == 200:
                        html = await page.content()
                        discovered_links, intel = HTMLParser.parse_page(html, url)
                        
                        # Extract static query parameters directly from the URL itself
                        query_parameters = []
                        parsed_url = urlparse(url)
                        if parsed_url.query:
                            for param, values in parse_qs(parsed_url.query).items():
                                query_parameters.append({
                                    "name": param,
                                    "location": "query",
                                    "example_value": values[0]
                                })

                        headers = response.headers
                        content_type = headers.get("content-type", "text/html").split(";")[0]
                        
                        page_intel = {
                            "url": url,
                            "method": "GET",
                            "status_code": response.status,
                            "content_type": content_type,
                            "parameters": query_parameters if query_parameters else intel.get("parameters", []),
                            "forms": intel.get("forms", []),
                            "links": discovered_links,
                            "endpoints_discovered_via_js": js_discovered_endpoints,
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
                    raise
                except Exception as page_err:
                    print(f"[!] Timeout or render error on {url}: {page_err}")
                finally:
                    await page.close()

            except asyncio.CancelledError:
                queue.task_done()
                raise
            except Exception as worker_err:
                print(f"[!] Worker level critical fault: {worker_err}")
                queue.task_done()
            else:
                queue.task_done()
                
        await context.close()
    
    def save_results(self):
        """Compiles collected crawler intelligence records into the final schema file."""
        if not self.collected_intel:
            print("[!] No data collected to export.")
            return

        # Use the root landing domain context to define top-level profile structures
        target_profile = self.collected_intel[0]

        # Aggregate all unique forms found across the entire run
        all_forms = []
        for intel in self.collected_intel:
            if intel.get("forms"):
                all_forms.extend(intel["forms"])

        # Aggregate all JS network endpoints discovered across pages
        all_js_endpoints = []
        for intel in self.collected_intel:
            if intel.get("endpoints_discovered_via_js"):
                all_js_endpoints.extend(intel["endpoints_discovered_via_js"])

        # Detect potential Authentication frameworks based on landing/discovered URLs
        auth_keywords = ["login", "signup", "auth", "register", "token"]
        detected_auth_flows = [
            link for link in self.visited_urls 
            if any(kw in link.lower() for kw in auth_keywords)
        ]

        final_output = {
            "url": self.start_url,
            "method": "GET",
            "status_code": target_profile.get("status_code", 200),
            "content_type": target_profile.get("content_type", "text/html"),
            "discovered_at": datetime.utcnow().isoformat() + "Z", 
            "authentication": {
                "requires_auth_gateway_detected": len(detected_auth_flows) > 0,
                "detected_auth_flows": detected_auth_flows
            },
            "parameters": target_profile.get("parameters", []),
            "forms": all_forms,
            "endpoints_discovered_via_js": all_js_endpoints,
            "links": list(self.visited_urls),  
            "technologies": target_profile.get("technologies", [])
        }

        os.makedirs("output", exist_ok=True)

        # Output to crawler_output.json to match your smart crawler expectations
        with open("output/crawler_output.json", "w") as f:
            json.dump(final_output, f, indent=4)

        print("[*] Successfully generated output/crawler_output.json.")
        
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