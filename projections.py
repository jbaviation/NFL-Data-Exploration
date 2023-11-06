import pandas as pd
import numpy as np
from bs4 import BeautifulSoup
import requests
import re
import time
import datetime


class GetData:
    """
    This class facilitates the retrieval of data necessary to perform projections.
    """
    def __init__(self, season=None, year_soup=None) -> None:
        # Set season
        self.season = get_current_season() if season is None else season

        # Get soups
        self.year_soup = year_soup if year_soup is not None else self.get_year_soup()


    ## ----------- Get soups ------------ ##
    def get_year_soup(self):
        """Get soup associated with yearly season stats."""
        url = f'https://www.pro-football-reference.com/years/{self.season}/'
        page = requests.get(url)
        return BeautifulSoup(page.content, 'html.parser')


    ## ----------- Team Level Data Section ------------- ##
    def team_links(self, soup=None, season=None):
        """
        Get the webpage links for all teams.

        Parameters
        ----------
        soup : bs4.BeautifulSoup, optional
            Soup object from 'https://www.pro-football-reference.com/years/{season}/' request.
        season : str, int, float, optional
            Season (year) that is desired to be used if soup is None. Defaults to current year.
        """
        # Consider inputted season
        is_season_change = False
        if season is not None:
            is_season_change = (int(season) == int(self.season))
            self.season = season
            
        # Generate soup if not inputted
        if soup is not None:
            self.year_soup = soup
        elif is_season_change:
            self.year_soup = self.get_year_soup()
            
        # Save base url for creating links
        base_url = 'https://www.pro-football-reference.com'

        # Create afc and nfc tables
        afc = self.year_soup.find('table', attrs={'id': 'AFC'})
        nfc = self.year_soup.find('table', attrs={'id': 'NFC'})

        # Look thru tables for items
        teams = {}  # Initialize dict
        for conf in [afc, nfc]:
            for tr in conf.find_all('tr'):
                # Skip line if first th='Tm'
                try:
                    tr_text = tr.find('th').text
                    if tr_text=='Tm': continue
                except:
                    pass  # Ignore and proceed
                
                # Loop thru each row
                team = ''  # Initialize team
                for td in tr.find_all(['th', 'td'], attrs={'data-stat': 'team'}):
                    value = td.text

                    link = base_url + td.find('a')['href']  # Get team page link
                    team = re.sub(r'[^A-Za-z0-9 ]', '', str(value))  # Strip unnecessary characters
                    teams[team] = link

        # Make dataframe
        teams = pd.Series(teams).to_frame().rename({0: 'team_link'}, axis=1)

        # Get team id
        t_id = teams['team_link'].str.extract(r'teams/([^/]+)/')
        teams.insert(0, 'team_id', t_id)

        return teams
    
    def team_standings(self, soup=None, season=None):
        """
        Get the nfl standings.

        Parameters
        ----------
        soup : bs4.BeautifulSoup, optional
            Soup object from 'https://www.pro-football-reference.com/years/{season}/' request. If no 
            input is entered, the soup object is created.
        season : str, int, float, optional
            Season (year) that is desired to be used if soup is None. Defaults to current year.
        """
        # Consider inputted season
        is_season_change = False
        if season is not None:
            is_season_change = (int(season) != int(self.season))
            self.season = season
            
        # Generate soup if not inputted
        if soup is not None:
            self.year_soup = soup
        elif is_season_change:
            self.year_soup = self.get_year_soup()

        # Create afc and nfc tables
        afc = self.year_soup.find('table', attrs={'id': 'AFC'})
        nfc = self.year_soup.find('table', attrs={'id': 'NFC'})

        # Look thru tables for items
        teams = {}  # Initialize dict
        division = ''  # Initialize division
        for conf in [afc, nfc]:
            for tr in conf.find_all('tr'):
                
                # Skip line if first th='Tm'
                try:
                    tr_text = tr.find('th').text
                    if tr_text=='Tm': continue
                except:
                    pass  # Ignore and proceed
                
                # Loop thru each row
                team = ''  # Initialize team
                for td in tr.find_all(['th', 'td']):
                    stat = td.get('data-stat')
                    value = td.text

                    # If 'onecell' this is division header
                    if stat=='onecell':
                        division = value
                        continue

                    # If team, get link, division, and set as key in teams dict
                    if stat=='team':
                        team = re.sub(r'[^A-Za-z0-9 ]', '', str(value))  # Strip unnecessary characters

                        # Get link and extract team_id
                        local_link = td.find('a')['href']
                        team_id = ''
                        if local_link is not None:
                            find_id = re.search(r'teams/([^/]+)/', local_link)  # Get team page link
                            if find_id is not None: team_id = find_id.groups()[0]
                        
                        # Set id and division
                        teams[team] = { 'id': team_id, 'division': division}
                        continue

                    # Apply each stat to the team dict
                    teams[team][stat] = value

        return pd.DataFrame(teams).T
    

     ## ----------- END Team Level Data Section ------------- ##



def get_current_season():
    """Return the current season that is either active or has passed."""
    today = datetime.date.today()
    if int(today.month) < 9:
        return int(today.year) - 1
    return int(today.year)


