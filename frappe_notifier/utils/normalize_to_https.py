from urllib.parse import urlparse, urlunparse

def normalize_url_to_https(url: str) -> str:
    parsed = urlparse(url)

    # Ensure scheme is 'https'
    scheme = 'https'

    # Remove port if present
    netloc = parsed.hostname or ''
    path = parsed.path or ''
    params = parsed.params or ''
    query = parsed.query or ''
    fragment = parsed.fragment or ''

    # Reconstruct the URL
    normalized_url = urlunparse((
        scheme,
        netloc,
        path,
        params,
        query,
        fragment
    ))
    
    return normalized_url
