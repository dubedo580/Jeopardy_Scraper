import requests
from bs4 import BeautifulSoup
import firebase_admin
from firebase_admin import credentials, firestore
import time

# Initialize Firebase
cred = credentials.Certificate('jeopardytraining-firebase-adminsdk-yswlk-16dacfaabf.json')
firebase_admin.initialize_app(cred)
db = firestore.client()


def fetch_page(url):
    try:
        response = requests.get(url)
        response.raise_for_status()
        return BeautifulSoup(response.content, 'html.parser')
    except requests.RequestException as e:
        print(f"Request failed: {e}")
        return None


def scrape_episode_details(base_url, episode_url):
    soup = fetch_page(episode_url)
    if not soup:
        return

    episode_id = episode_url.split('=')[-1]
    print(f"Scraping episode: {episode_id}")

    episode_doc = db.collection('episodes').document(episode_id)
    episode_doc.set({
        'url': episode_url
    })

    round_tables = soup.find_all('table', class_='round')
    for table in round_tables:
        round_name = table.find_previous('h2').text.strip()
        categories = table.find_all('td', class_='category_name')

        for category in categories:
            category_name = category.text.strip()
            category_doc = episode_doc.collection('categories').document(category_name)
            category_doc.set({
                'name': category_name
            })


def scrape_season(base_url, season_url):
    soup = fetch_page(season_url)
    if not soup:
        return

    episode_links = soup.find_all('a', href=lambda href: href and 'game_id' in href)
    for link in episode_links:
        episode_url = f"{base_url}/{link['href']}"
        scrape_episode_details(base_url, episode_url)


def scrape_all_seasons(base_url):
    url = f"{base_url}/listseasons.php"
    soup = fetch_page(url)
    if not soup:
        return

    season_links = soup.find_all('a', href=lambda href: href and 'season=' in href)
    for link in season_links:
        season_url = f"{base_url}/{link['href']}"
        print(f"Scraping season: {season_url}")
        scrape_season(base_url, season_url)


def main():
    base_url = "https://j-archive.com"
    scrape_all_seasons(base_url)


if __name__ == '__main__':
    main()
