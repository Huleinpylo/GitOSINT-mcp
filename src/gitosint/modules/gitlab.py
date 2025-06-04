from bs4 import BeautifulSoup
from core.network import fetch_url

def extract_meta_tags(content, properties):
    soup = BeautifulSoup(content, 'html.parser')
    meta_info = {}
    for property_name in properties:
        meta_tag = soup.find('meta', attrs={'property': property_name})
        if meta_tag and 'content' in meta_tag.attrs:
            meta_info[property_name] = meta_tag.attrs['content']
    return meta_info

def gitlab_find(user, verbose):
    url = f'https://gitlab.com/{user}'
    headers = {
        'User-Agent': 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:129.0) Gecko/20100101 Firefox/129.0'
    }
    response = fetch_url(url, headers, verbose)

    if not response:
        return {'Gitlab': 'User not found or private'}

    properties_to_extract = [
        'og:title', 'og:description', 'og:image', 'og:url',
        'twitter:title', 'twitter:description', 'twitter:image'
    ]
    user_info = extract_meta_tags(response.content, properties_to_extract)
    return {'Gitlab': user_info}
