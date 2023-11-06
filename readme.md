# NFL Data Exploration
Initial goal of this repository is to explore how NFL Combine data relates to NFL success.  Additionally, drawing conclusions on game-level data is another interest of this project. Continuing on to project winners/losers and gambling interests are also being considered in this project

## Installation

Required dependencies (currently):

- Python (>=3.6)
- Numpy
- Pandas
- BeautifulSoup

## Project Motivation

Discovering hidden correlations between statistics in various sports has always been interesting to me. I especially am interested in motivations of NFL front offices regarding QB draft picks. This project will perform a deep dive into understanding why certain players are picked and which drafting methods yield the highest success rate.

While investigating draft picks, it has become increasingly important to retreive additional game-level statistics to find correlated winners, losers and various other stats that revolve around betting.  This project has shifted from a narrow focus on QB draft picks and their successes (or failures) to a repository for retrieving a multitude of NFL statistics.

Since a lot of data is being retrieved for a variety of specific research interests, game gambling considerations are also taking place by retrieving standings, team offensive, and defensive data.

## Files

**explore_data.ipynb**: This file is currently being used to test webscraping and data wrangling methods to grab NFL data pertinent to investigating how combine stats relate to NFL performance. Eventually, when the data is properly wrangled, this notebook will perform EDA, generate visuals, and test models.

**all_game_data.ipynb**: The goal of this notebook is the setup the webscraper for retrieving scores from all games throughout the history of the NFL.  The only realized way to get this data (at least for free) is to start by getting all game scores (i.e. 20-17, 24-7, etc.) and scraping links to the list of all games at that score.  The scraping starts at this [pro football reference](https://www.pro-football-reference.com/boxscores/game-scores.htm) page and stores data from all the linked pages.

**game_data.py**: This is the webscraper that pulls all game data and puts it into a dataframe and csv.  Running the file will create the csv while simply calling the get_data() function from another file will return a dataframe.

**projections.py**: Allows the user to get all data necessary for creating game projections.

## Examples

```python
data = projections.GetData()

data.team_standings(season=1999)  # View standings from 1999
data.team_links()  # View the team weblinks for each team from 1999

## Licensing and Acknowledgements

Data currently comes from multiple sources:

- [NFL Combine.com](https://nflcombineresults.com/)
- [Wikipedia](https://en.wikipedia.org/wiki/2021_NFL_Draft)
- [Next Gen Stats](https://nextgenstats.nfl.com/)
- [pro football reference](https://www.pro-football-reference.com)

