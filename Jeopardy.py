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
    seasonsLinks = {}

    for row in seasonSoup.find_all('tr'):
        # Collect Info On A Season
        seasonName = row.find('a').text.strip()
        seasonDate = row.find_all('td')[1].text.strip()
        seasonGames = row.find_all('td')[2].text.strip()
        # Store the Info to one Row
        seasonsInfo.append((seasonName, seasonDate, seasonGames))

        # Collect Links To Travel To
        # Collect Links To Travel To
        seasonLink = row.find('a', href=lambda href: href and href.startswith('showseason.php?season='))
        if seasonLink:
            seasonsLinks[seasonName] = seasonLink['href']

    return seasonsInfo, seasonsLinks


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
        'date': episodeDate,
    })


def collectEpisodeInfo(seasonSoup):
    episodeInfo = []
    episodeRows = seasonSoup.find_all('tr')

    for row in episodeRows:
        episodeDetails = {}
        episodeLink = row.find('a')
        if episodeLink and 'game_id' in episodeLink['href']:
            gameID = episodeLink['href'].split('game_id=')[-1]
            airedText = episodeLink.text  # e.g., "#9075, aired 2024-04-05"
            gameNumber = airedText.split(',')[0].strip('#')  # Extracts "9075" from "#9075, aired 2024-04-05"
            airDate = airedText.split('aired ')[-1].strip()  # Extracts "2024-04-05"

            episodeDetails['game_id'] = gameID
            episodeDetails['game_number'] = gameNumber
            episodeDetails['air_date'] = airDate

            episodeInfo.append(episodeDetails)

    return episodeInfo


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
        seasonReference = addSeason(seasonName, seasonDate, seasonGames)

        seasonURL = "https://j-archive.com/" + seasonsLinks[seasonName]
        seasonResponse = requests.get(seasonURL)
        seasonSoup = BeautifulSoup(seasonResponse.content, "html.parser")
        episodeInfo = collectEpisodeInfo(seasonSoup)

        for episode in episodeInfo:
            gameNumber = episode['game_number']
            episodeDate = episode['air_date']

            addEpisodeToSeason(theDB.collection('seasons').document(seasonName), gameNumber, episodeDate)


if __name__ == '__main__':
    # Database Connections
    cred = credentials.Certificate('jeopardytraining-firebase-adminsdk-yswlk-16dacfaabf.json')
    firebase_admin.initialize_app(cred)
    theDB = firestore.client()

    main()
