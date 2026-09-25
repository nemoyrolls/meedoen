import re
import threading
import urllib.request
import ipaddress
from urllib.parse import urljoin, urlparse
from concurrent.futures import ThreadPoolExecutor


def ipaddress_is_public(host):
    """False for a private or local IP address. Hostnames pass."""
    try:
        return ipaddress.ip_address(host).is_global
    except ValueError:
        return True


# The picture a page shows when you share it on WhatsApp or Instagram.
# Fetching it ourselves costs no tokens and shows the real event, not a stock photo.
META_IMAGE = re.compile(
    r'<meta[^>]+(?:property|name)=["\'](?:og:image|twitter:image)(?::src)?["\'][^>]*>',
    re.IGNORECASE,
)
CONTENT = re.compile(r'content=["\']([^"\']+)["\']', re.IGNORECASE)

_cache = {}
_lock = threading.Lock()


def page_image(url):
    """Return the share picture of a page, or None. Never raises."""
    with _lock:
        if url in _cache:
            return _cache[url]

    image = None
    try:
        # Only public web pages, never something on this computer or network.
        host = urlparse(url).hostname or ""
        if not url.startswith(("http://", "https://")) or host == "localhost" \
                or not ipaddress_is_public(host):
            raise ValueError("not a public page")
        request = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 TagAlong"})
        with urllib.request.urlopen(request, timeout=4) as response:
            head = response.read(300_000).decode("utf-8", errors="ignore")
        tag = META_IMAGE.search(head)
        if tag:
            content = CONTENT.search(tag.group(0))
            if content:
                image = urljoin(url, content.group(1).strip())
    except Exception:
        image = None

    # Only https pictures: an http one would be blocked or insecure on the page.
    if image and not image.startswith("https://"):
        image = None

    with _lock:
        _cache[url] = image
    return image


def add_images(activities):
    """Fill in activity["image"] for every activity that has none, all pages at once."""
    missing = [a for a in activities if not a.get("image")]
    if not missing:
        return activities
    with ThreadPoolExecutor(max_workers=min(12, len(missing))) as pool:
        for activity, image in zip(missing, pool.map(page_image, [a.get("source") for a in missing])):
            activity["image"] = image
    return activities
