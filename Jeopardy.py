# Libraries Used
import csv, requests
from bs4 import BeautifulSoup


# A Starting Place To Gather Information
seasonsURL = "https://j-archive.com/listseasons.php"
seasonsResponse = requests.get(seasonsURL)
seasonsSoup = BeautifulSoup(seasonsResponse.content, "html.parser")
seasonsTable = seasonsSoup.find('table')

# Variables To Write The SeasonsInfo.csv
seasonName = ''
seasonDate = ''
seasonGames = ''
seasonsInfo = []

# Variables To Traverse To A Particular Season
collectLinksToSeason = ''
seasonsLinks = []

# For Every Row (Season) In The seasonsTable, Grab Relevant Info
for row in seasonsTable.find_all('tr'):
    # Collect Info On A Season
    seasonName = row.find('a').text.strip()
    seasonDate = row.find_all('td')[1].text.strip()
    seasonGames = row.find_all('td')[2].text.strip()
    # Store the Info to one Row
    seasonsInfo = [seasonName, seasonDate, seasonGames]
   
    # Collect Links To Travel To
    collectLinksToSeason = seasonsSoup.find_all('a', href=lambda href: href and href.startswith('showseason.php?season='))
    seasonsLinks = [link['href'] for link in collectLinksToSeason]

# Variables To Set Up The Scrape Of A Particual Season
seasonURL = ''
seasonResponse = ''
seasonSoup = ''

# Variables to Grab Each Episode ID In A Particular Season
collectLinksToGames = ''
seasonalGameLinks = []
gameLinks = []

# Traverse A Season At A Time
for season in seasonsLinks:
    # A Starting Place To Gather Info On A Season
    seasonUrl = f"https://j-archive.com/{season}"
    seasonResponse = requests.get(seasonUrl)
    seasonSoup = BeautifulSoup(seasonResponse.content, "html.parser")
    
    # Collect Links To Travel To
    collectLinksToGames = seasonSoup.find_all("a", href=lambda href: href and "showgame.php?game_id=" in href)
    seasonalGameLinks = [link["href"].split("=")[1] for link in collectLinksToGames]
    gameLinks = gameLinks + seasonalGameLinks

# Variables To Set Up The Scrape Of A Game
gameURL = ''
gameResponse = ''
gameSoup = ''

for game in gameLinks:
    gameURL = f"https://j-archive.com/showgame.php?game_id={game}"
    gameResponse = requests.get(gameURL)
    gameSoup = BeautifulSoup(gameResponse.content, "html.parser")

    # Variables To Write The Game's Info Into A CSV File
    jCategories = []
    djCategories = []
    fjCategory = []

    gameClues = []
    clueValues = []
    clueAnswers = []
    theCategories = []

    theInfo = []

    # Populate Arrays For Categories
    # Find Jeopardy Round
    jeopardyRound = gameSoup.find(id='jeopardy_round')
    if jeopardyRound is not None:
        jCategoryElements = jeopardyRound.select('.category')
    else:
        print("No Jeopardy Found")
    for element in jCategoryElements:
        jCategories.append(element.select('.category_name')[0].text)

    # Find Double Jeopardy Round
    doubleJeopardyRound = gameSoup.find(id='double_jeopardy_round')
    if doubleJeopardyRound is not None:
        djCategoryElements = doubleJeopardyRound.select('.category')
    else:
        print("No Double Found")
    for element in djCategoryElements:
        djCategories.append(element.select('.category_name')[0].text)

    # Find Final Jeopardy Round
    finalJeopardyRound = gameSoup.find(class_='final_round')
    if finalJeopardyRound is not None:
        fjCategoryE = finalJeopardyRound.find(class_='category_name').text
        fjCategory.append(fjCategoryE)
    else:
        print("No Final Found")

    # Populate Arrays for Clues
    # Find Jeopardy/Double Jeopardy Rounds
    clueElements = gameSoup.find_all(class_='clue_unstuck')
    clueIds = [element.get('id') for element in clueElements]
    jClueLocations = []
    djClueLocations = []

    # For Every Clue Find Out the Category It Will Be 
    # Based On It's Location
    for clueId in clueIds:
        # Figure Out The Category It Needs To Be In
        # By Figuring Out Where It's Located
        if clueId.startswith('clue_J'):
            startingIndex = len('clue_J_')
            endingIndex = clueId.find('_', startingIndex)
            numberAsString = clueId[startingIndex:endingIndex]
            jClueLocations.append(int(numberAsString))
        elif clueId.startswith('clue_DJ'):
            startingIndex = len('clue_DJ_')
            endingIndex = clueId.find('_', startingIndex)
            numberAsString = clueId[startingIndex:endingIndex]
            djClueLocations.append(int(numberAsString))

    # Correct Categories For A Whole Game In An Array
    for value in jClueLocations:
        theCategories.append(jCategories[value - 1])
    for value in djClueLocations:
        theCategories.append(djCategories[value - 1])
    theCategories.append(fjCategoryE)


    # Correct Clues For A Whole Game In An Array
    gameClues = [element.get_text() for element in gameSoup.find_all(class_='clue_text')]
    gameClues = gameClues[::2]

    # Correct Answers For A Whole Game In An Array
    clueAnswers = [element.get_text() for element in gameSoup.find_all(class_='correct_response')]

    # Correct Clue Values For A Whole Game In An Array
    for element in gameSoup.find_all(class_='clue'):

        if element.find(class_='clue_value') is not None:
            element = element.find(class_='clue_value').get_text()
        elif element.find(class_='clue_value_daily_double') is not None:
            element = element.find(class_='clue_value_daily_double').get_text()
        else:
            continue

        clueValues.append(element)

    clueValues.append("No Specific Value")

    list_length = min(len(theCategories), len(gameClues), len(clueAnswers), len(clueValues))

    # Populate One Array With All Relevant Info For One Question
    for i in range(list_length):
        theInfo.append([theCategories[i], gameClues[i], clueAnswers[i], clueValues[i]])

    # Write That Array To A CSV File
    with open('TheQuestions.csv', 'a', newline='', encoding='utf-8') as csvfile:

        writer = csv.writer(csvfile)

        for info in theInfo:
            writer.writerow(info)