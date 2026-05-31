from bs4 import BeautifulSoup
import re
from utils import normalize_url

class HTMLParser:
    @staticmethod
    def parse_page(html_content, base_url):
        """
        Parses raw HTML content to extract out-of-box links, dynamic form schemas,
        and hidden client-side API configurations.
        
        Completely soft-coded to dynamically map page payloads and interactive surfaces.
        """
        discovered_links = set()
        intel = {
            "url": base_url,
            "forms": [],
            "has_file_upload": False,
            "has_hidden_inputs": False,
            "discovered_api_patterns": []
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

        # 2. EXTRACT SECURITY INTEL & METRICS (Form & Parameter Mapping)
        forms = soup.find_all("form")
        for form in forms:
            # Dynamically normalize form destinations
            raw_action = form.get("action", "")
            normalized_action = normalize_url(raw_action, base_url) if raw_action else base_url
            
            form_data = {
                "action": normalized_action,
                "method": form.get("method", "get").lower(),
                "inputs": []
            }

            # Soft-coded extraction capturing ALL valid submission fields (inputs, textareas, drop-downs)
            interactive_elements = form.find_all(["input", "textarea", "select", "button"])
            for elem in interactive_elements:
                elem_name = elem.get("name", "").strip()
                
                # Determine element type profile
                if elem.name == "input":
                    elem_type = elem.get("type", "text").lower()
                else:
                    elem_type = elem.name  # 'textarea', 'select', or 'button'

                # Flag risk metrics automatically based on runtime features
                if elem_type == "hidden":
                    intel["has_hidden_inputs"] = True
                if elem_type == "file":
                    intel["has_file_upload"] = True

                # Only include parameters that carry functional submission weight
                if elem_name or elem_type == "button":
                    field_metadata = {
                        "name": elem_name if elem_name else f"unnamed_{elem_type}",
                        "type": elem_type
                    }
                    
                    # Track explicit overriding endpoints on HTML5 submit buttons
                    if elem_type == "button" and elem.get("formaction"):
                        field_metadata["overriding_action"] = normalize_url(elem.get("formaction"), base_url)

                    form_data["inputs"].append(field_metadata)

            intel["forms"].append(form_data)

        # 3. STATIC ENDPOINT FALLBACK SCANNING (Regex Analysis of Inline JS Elements)
        # Regex to parse potential API paths, routing configurations, or endpoints inside scripts
        api_pattern = re.compile(r'(?:href|src|url|path|api)\s*[:=]\s*["\'](/[^"\']+)["\']', re.IGNORECASE)
        
        for script in soup.find_all("script"):
            if script.string:
                matches = api_pattern.findall(script.string)
                for match in matches:
                    # Filter out noise like basic document queries and clean matches
                    if len(match) > 2 and not match.endswith(('.js', '.css', '.png', '.jpg')):
                        normalized_api = normalize_url(match, base_url)
                        if normalized_api and normalized_api not in discovered_links:
                            intel["discovered_api_patterns"].append(normalized_api)

        # Clean duplicate entries from the inline regex analyzer
        intel["discovered_api_patterns"] = list(set(intel["discovered_api_patterns"]))

        return list(discovered_links), intel