"""
Attribution d'inscription : pays (géolocalisation IP) + source de trafic
(referrer HTTP / UTM). Capté une seule fois à l'inscription — l'IP brute
n'est jamais conservée, seul le pays qui en est déduit l'est.
"""
import json
import urllib.error
import urllib.parse
import urllib.request

# IANA/RFC : plages privées, jamais géolocalisables (dev local, LAN, proxy interne).
_PRIVATE_PREFIXES = ("127.", "10.", "192.168.", "::1")


def get_client_ip(request) -> str | None:
    """Adresse IP du client, en tenant compte d'un éventuel proxy inverse
    (Render, nginx...) qui pose X-Forwarded-For."""
    forwarded = request.META.get("HTTP_X_FORWARDED_FOR")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.META.get("REMOTE_ADDR")


def lookup_country_code(ip: str | None) -> str:
    """Code pays ISO à deux lettres, ou chaîne vide si indisponible.
    Best effort : toute erreur réseau/timeout est silencieuse — l'inscription
    ne doit jamais échouer à cause d'un service de géolocalisation externe."""
    if not ip or ip.startswith(_PRIVATE_PREFIXES) or ip.startswith("172."):
        return ""
    try:
        url = f"http://ip-api.com/json/{urllib.parse.quote(ip)}?fields=status,countryCode"
        with urllib.request.urlopen(url, timeout=2) as response:
            data = json.loads(response.read())
        if data.get("status") == "success":
            return (data.get("countryCode") or "")[:2]
    except (urllib.error.URLError, TimeoutError, ValueError, OSError):
        pass
    return ""


def extract_referrer_domain(referrer_url: str) -> str:
    if not referrer_url:
        return ""
    try:
        domain = urllib.parse.urlparse(referrer_url).netloc
        return domain.removeprefix("www.")[:255]
    except ValueError:
        return ""
