from bs4 import BeautifulSoup
from core.network import fetch_url

def gitea_find(user, verbose):
    url = f'https://gitea.com/{user}'
    headers = {
        'User-Agent': 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:129.0) Gecko/20100101 Firefox/129.0'
    }
    response = fetch_url(url, headers, verbose)

    if not response:
        return {'Gitea': 'User not found or private'}

    soup = BeautifulSoup(response.content, 'html.parser')
    main = soup.find('div', attrs={'aria-label': user})
    if not main:
        return {'Gitea': 'User not found or private'}

    username = main.find('span', attrs={'class': 'username text center'})
    join_date = main.find('li').find('absolute-date')

    user_info = {
        'username': username.text if username else 'N/A',
        'register': join_date.attrs['date'] if join_date else 'N/A'
    }
    return {'Gitea': user_info}
