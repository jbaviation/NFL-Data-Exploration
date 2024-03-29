import pandas as pd
import numpy as np
from bs4 import BeautifulSoup
import requests
import re
import time
import datetime


def get_all_game_score_links(soup=None):
    """Open game scores page and retrieve appropriate links"""
    
    # Check if soup object is provided, if not generate one
    if soup is None:
        url = 'https://www.pro-football-reference.com/boxscores/game-scores.htm'

        # Get page content
        page = requests.get(url)
        soup = BeautifulSoup(page.content, 'html.parser')
    
    # Find table and all rows
    table = soup.find('table', attrs={'class': 'sortable stats_table'})
    trs = table.find_all('tr')  # each tr contains a link to each score

    # Use trs that have data
    trs = trs[1:]  # trs[0] contains only header info

    # Get all links
    links = []
    prefix = 'https://www.pro-football-reference.com'
    for td in trs:
        hrefs = [link.get('href') for link in td.find_all('a')]
        links.append(prefix + str(hrefs[0]))

    return links


def get_games_per_score(url, existing=None):
    """This function is meant to be iterated over each of the links returned
       from the get_all_game_score_links() function."""

    # Get page content
    page = requests.get(url)
    soup = BeautifulSoup(page.content, 'html.parser')

    # Find the table
    table = soup.find('table', attrs={'id': 'games'})  

    # Raise error if existing is wrong type
    if not isinstance(existing, (list, type(None))):
        raise TypeError('The existing input must be either a list or NoneType')

    # Get the games data
    games = {}
    site_stub = 'https://www.pro-football-reference.com'
    for i, row in enumerate(table.find_all('tr')[1:]):
        row_dict = {}  # re-initialize row_dict

        # TODO Skip this row if boxscore is in the existing list
        if existing is not None:
            site = row.find('td', attrs={'data-stat': 'boxscore_word'}).find('a').get('href')
            site = site_stub + site
            game_exists = site in existing

            if game_exists:
                continue

        # Otherwise, loop thru all values
        for col in row.find_all('td'):
            # Set row dictionary values
            col_name = col['data-stat']
            
            # Determine special columns
            if col_name=='winner':
                # winner_id
                try:
                    site = col.find('a').get('href')
                    row_dict['winner_id'] = re.search(r'/teams/([A-Za-z0-9]+)/', site).group(1)
                except:
                    row_dict['winner_id'] = None
            elif col_name=='loser':
                # loser_id
                try:
                    site = col.find('a').get('href')
                    row_dict['loser_id'] = re.search(r'/teams/([A-Za-z0-9]+)/', site).group(1)
                except:
                    row_dict['loser_id'] = None
            elif col_name=='game_location':
                # home_win
                row_dict['home_win'] = 0 if r'@' in col.text else 1
                continue
            elif col_name=='boxscore_word':
                # box_score
                try:
                    site = col.find('a').get('href')
                    row_dict['boxscore'] = site_stub + site
                except:
                    row_dict['boxscore'] = None
                continue
            elif col_name=='game_outcome':
                continue

            row_dict[col_name] = col.text

        # Add to games dictionary
        games[i] = row_dict

    return games
    
def add_stats(games):
    # Give a half point to ties
    def ties(row):
        return 0.5 if row['pts_win']==row['pts_lose'] else row['home_win']
    games['home_win'] = games.apply(ties, axis=1)

    # Set game_date to datetime
    games['game_date'] = pd.to_datetime(games['game_date'], format='%Y-%m-%d')

    #------- Break into seasons -----------
    # Get unique years to generate seasons
    years = games['game_date'].dt.year.unique()
    seasons = [(datetime.date(yr,8,1), datetime.date(yr+1,3,1)) for yr in years]

    # Organize games by date
    games = games.sort_values('game_date')
    games.insert(2, 'season', np.nan)  # initialize season column

    # Set season and type
    for season in seasons:
        games.loc[games.game_date.dt.date.between(season[0], season[1]),'season'] = season[0].year
    games['season'] = games['season'].astype('int')
    #---------------------------------------

    return games


def get_data(wait_time=2, all_games=None):
    """Iterate over all links in get_all_game_score_links() function
        to retrieve all basic NFL game data since 1920"""

    # If all_games is a Dataframe, this function adds to that frame, otherwise this is an initial data pull
    if isinstance(all_games, pd.DataFrame):
        data_exists = True
        boxscore_links = list(all_games.boxscore.unique())  # this is a unique id for each row

        # Prepopulate games dict with all_games
        games = all_games.reset_index(drop=True).to_dict(orient='index')

    elif isinstance(all_games, type(None)):
        data_exists = False
        boxscore_links = None
    else:
        raise TypeError('The all_games input must be None if this is an initial data pull, '+
                        'otherwise, all_games should be a pd.DataFrame type.')

    # Look thru game score links
    links = get_all_game_score_links()
    games = {}
    for i, link in enumerate(links):
        # Print Status Update
        win, loss = re.search(r'pts_win=(\d+)\&pts_lose=(\d+)', link).groups()
        print(f'Retrieving {win}-{loss} Score....{i+1} of {len(links)}', end='\r')

        # Dictionary for each score
        new_games_raw = get_games_per_score(link, existing=boxscore_links)

        # Rename keys so that no dupes exist
        if not data_exists:
            key_prefix = f'{i:04}'
            new_games = {(key_prefix+str(k)): new_games_raw[k] 
                            for k in new_games_raw.keys()}
        # TODO: Determine how to work with indexes for both with and without all_games

        # Combine old games and new games
        games = {**games, **new_games}
        time.sleep(wait_time)

    df = pd.DataFrame.from_dict(games, orient='index')
    return df

if __name__=='__main__':
    df = add_stats(get_data())

    # Write to csv
    today = datetime.datetime.now()
    df.to_csv(f'data/all_nfl_games{today.year}_{today.month}_{today.day}.csv')
