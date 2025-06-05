from bs4 import BeautifulSoup
from core.network import fetch_url

def github_find(user, verbose):
    url = f'https://github.com/{user}'
    headers = {
        'User-Agent': 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:129.0) Gecko/20100101 Firefox/129.0'
    }
    response = fetch_url(url, headers, verbose)

    if not response:
        return {'GitHub': 'User not found or private'}

    soup = BeautifulSoup(response.content, 'html.parser')
    user_profile = soup.find('div', class_='js-profile-editable-replace')

    if not user_profile:
        return {'GitHub': 'User not found or private'}

    # Extract user information
    user_info = {}
    user_info['username'] = user
    user_info['display_name'] = user_profile.find('span', class_='p-name').text.strip() if user_profile.find('span', class_='p-name') else 'No display name'
    user_info['bio'] = user_profile.find('div', class_='p-note').text.strip() if user_profile.find('div', class_='p-note') else 'No bio'
    user_info['location'] = user_profile.find('span', class_='p-label').text.strip() if user_profile.find('span', class_='p-label') else 'No location'

    return {'GitHub': user_info}
