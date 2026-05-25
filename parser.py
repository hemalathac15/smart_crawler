from bs4 import BeautifulSoup
from utils import normalize_url

class HTMLParser:
    @staticmethod
    def parse_page(html_content, base_url):
        """
        Parses raw HTML content to extract out-of-box links and security risk indicators.
        Completely soft-coded to dynamically map page payloads.
        """
        discovered_links = set()
        intel = {
            "url": base_url,
            "forms": [],
            "has_file_upload": False,
            "has_hidden_inputs": False
        }

        if not html_content:
            return list(discovered_links), intel

        soup = BeautifulSoup(html_content, "lxml")

        # 1. EXTRACT ALL LINKS (The Relationship Builders)
        for anchor in soup.find_all("a", href=True):
            href = anchor.get("href").strip()
            
            # Normalize relative links (e.g., '/about' -> 'https://site.com/about')
            normalized = normalize_url(href, base_url)
            if normalized:
                # Avoid self-referencing fragments loops
                if normalized != base_url:
                    discovered_links.add(normalized)

        # 2. EXTRACT SECURITY INTEL & METRICS
        forms = soup.find_all("form")
        for form in forms:
            form_data = {
                "action": form.get("action", ""),
                "method": form.get("method", "get").lower(),
                "inputs": []
            }

            # Inspect form input fields
            inputs = form.find_all("input")
            for inp in inputs:
                inp_type = inp.get("type", "text").lower()
                inp_name = inp.get("name", "")
                
                form_data["inputs"].append({"name": inp_name, "type": inp_type})

                if inp_type == "hidden":
                    intel["has_hidden_inputs"] = True
                if inp_type == "file":
                    intel["has_file_upload"] = True

            intel["forms"].append(form_data)

        return list(discovered_links), intel