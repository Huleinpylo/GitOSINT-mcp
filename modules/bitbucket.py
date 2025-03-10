from core.network import fetch_url

def bitbucket_find(user, verbose):
    url = f'https://bitbucket.org/!api/2.0/workspaces/{user}'
    headers = {
        'User-Agent': 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:129.0) Gecko/20100101 Firefox/129.0'
    }
    response = fetch_url(url, headers, verbose)

    if not response:
        return {'Bitbucket': 'User not found or private'}

    return {'Bitbucket': response.json()}
