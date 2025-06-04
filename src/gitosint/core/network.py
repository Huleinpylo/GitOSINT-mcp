import requests

def fetch_url(url, headers, verbose):
    if verbose:
        print(f"Fetching URL: {url}")
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        if verbose:
            print(f"Request successful: {response.status_code}")
        return response
    except requests.RequestException as e:
        if verbose:
            print(f"Request failed: {e}")
        return None
