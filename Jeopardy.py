# Libraries Used
import csv, requests
from bs4 import BeautifulSoup
import firebase_admin
from firebase_admin import credentials, firestore

# Variables To Write The SeasonsInfo.csv
seasonName = ''
seasonDate = ''
seasonGames = ''
seasonsInfo = []


def collectSeasonInfo(seasonSoup):
    seasonInfo = []
    seasonsLinks = []

    for row in seasonSoup.find_all('tr'):
        # Collect Info On A Season
        seasonName = row.find('a').text.strip()
        seasonDate = row.find_all('td')[1].text.strip()
        seasonGames = row.find_all('td')[2].text.strip()
        # Store the Info to one Row
        seasonsInfo.append((seasonName, seasonDate, seasonGames))

        # Collect Links To Travel To
        collectLinksToSeason = seasonSoup.find_all('a',
                                                   href=lambda href: href and href.startswith(
                                                       'showseason.php?season='))
        seasonsLinks.extend([link['href'] for link in collectLinksToSeason])

    return seasonsInfo, list(set(seasonsLinks))


def addSeason(seasonName, seasonDate, seasonGames):
    seasonCollection = theDB.collection('seasons')
    seasonsDocument = seasonCollection.document(seasonName)
    seasonsDocument.set({
        'date': seasonDate,
        'games': seasonGames
    })


def addEpisodeToSeason(seasonDocument, episodeNumber, episodeDate):
    episodeCollection = seasonDocument.collection('episodes')
    episodeDocument = episodeCollection.document(episodeNumber)
    episodeDocument.set({
        'date': episodeDate
    })


def addCategoryToEpisode(episodeDocument, categoryName):
    categoryCollection = episodeDocument.collection('categories')
    categoryDocument = categoryCollection.document(categoryName)
    categoryDocument.set({})


def addQuestionToCategory(categoryDocument, clue, answer, value):
    questionsCollection = categoryDocument.collection('questions')
    questionDocument = questionsCollection.document()
    questionDocument.set({
        'clue': clue,
        'answer': answer,
        'value': value
    })


def main():
    # A Starting Place To Gather Information
    seasonsURL = "https://j-archive.com/listseasons.php"
    seasonsResponse = requests.get(seasonsURL)
    seasonsSoup = BeautifulSoup(seasonsResponse.content, "html.parser")

    # Gather the info of all the Seasons and Their Links
    seasonsInfo, seasonsLinks = collectSeasonInfo(seasonsSoup)

    # Store the Seasons to the DB
    for seasonName, seasonDate, seasonGames in seasonsInfo:
        addSeason(seasonName, seasonDate, seasonGames)


if __name__ == '__main__':
    # Database Connections
    cred = credentials.Certificate('jeopardytraining-firebase-adminsdk-yswlk-16dacfaabf.json')
    firebase_admin.initialize_app(cred)
    theDB = firestore.client()

    main()
