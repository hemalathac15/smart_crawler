from urllib.parse import urlparse, urljoin

class Colors:
    BLUE = "\033[94m"
    GREEN = "\033[92m"
    ORANGE = "\033[93m"
    RED = "\033[91m"
    BOLD = "\033[1m"
    END = "\033[0m"

def normalize_url(url, base):
    """Joins relative paths and sanitizes fragment strings."""
    try:
        joined = urljoin(base, url)
        parsed = urlparse(joined)
        #Drop url fragments (#)
        return f"{parsed.scheme}://{parsed.netloc}{parsed.path}"
    except Exception:
        return None

def is_same_domain(url, base_url):
    """Enforces scope boundaries, allowing primary domains and their subdomains."""
    try:
        target_netloc = urlparse(url).netloc.lower()
        base_netloc = urlparse(base_url).netloc.lower()
        
        # Strip 'www.' to get clean base comparisons
        base_domain = base_netloc.replace("www.", "")
        
        # Check if the target netloc matches or ends with the base domain
        return target_netloc == base_netloc or target_netloc.endswith("." + base_domain)
    except Exception:
        return False