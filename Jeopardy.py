import requests
from bs4 import BeautifulSoup
import firebase_admin
from firebase_admin import credentials, firestore
import time
import re

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


def sanitize_document_id(doc_id):
    # Remove leading and trailing whitespace
    doc_id = doc_id.strip()
    # Replace any sequence of non-alphanumeric characters with a single underscore
    doc_id = re.sub(r'[^a-zA-Z0-9]+', '_', doc_id)
    # Remove leading and trailing underscores to prevent empty document IDs
    doc_id = doc_id.strip('_')
    # Firestore document IDs should not be empty
    if not doc_id:
        doc_id = 'Unknown'
    return doc_id


def scrape_episode_details(base_url, season_doc, episode_url):
    soup = fetch_page(episode_url)
    if not soup:
        print(f"Failed to fetch or parse episode page: {episode_url}")
        return

    # Extract the episode number from the title tag using a regular expression
    title = soup.title.string if soup.title else ""
    match = re.search(r'Show #(\d+)', title)
    if match:
        episode_id = match.group(1)
    else:
        print(f"Failed to extract episode number from title: '{title}'")
        episode_id = 'Unknown'

    print(f"Scraping episode: {episode_id}")  # Debugging output

    # Sanitize the episode_id
    episode_id = sanitize_document_id(episode_id)
    if episode_id == 'Unknown':
        print(f"No valid episode ID found for URL: {episode_url}")
        return  # Skip setting data for episodes with unknown IDs

    episode_doc = season_doc.collection('episodes').document(episode_id)
    episode_doc.set({
        'url': episode_url
    })

    round_tables = soup.find_all('table', class_='round')
    for table in round_tables:
        categories = table.find_all('td', class_='category_name')
        for category in categories:
            category_name = category.text.strip()
            # Sanitize the category_name
            category_name = sanitize_document_id(category_name)
            category_doc = episode_doc.collection('categories').document(category_name)
            category_doc.set({
                'name': category_name
            })


def scrape_season(base_url, season_doc, season_url):
    soup = fetch_page(season_url)
    if not soup:
        return

    episode_links = soup.find_all('a', href=lambda href: href and 'game_id' in href)
    for link in episode_links:
        episode_url = f"{base_url}/{link['href']}"
        scrape_episode_details(base_url, season_doc, episode_url)


def scrape_all_seasons(base_url):
    url = f"{base_url}/listseasons.php"
    soup = fetch_page(url)
    if not soup:
        return

    seasons_collection = db.collection('seasons')
    season_links = soup.find_all('a', href=lambda href: href and 'season=' in href)
    for link in season_links:
        # Extract season number from the href attribute
        href = link['href']
        season_number = href.split('=')[-1].strip()  # Extracts the number after 'season='
        season_name = f"Season {season_number}"  # Constructs season name as 'Season 40', etc.

        season_url = f"{base_url}/{link['href']}"
        print(f"Scraping season: {season_name}")

        season_doc = seasons_collection.document(season_name)
        season_doc.set({
            'url': season_url
        })
        scrape_season(base_url, season_doc, season_url)


def main():
    base_url = "https://j-archive.com"
    scrape_all_seasons(base_url)


if __name__ == '__main__':
    main()
