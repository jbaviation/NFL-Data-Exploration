import pandas as pd
import numpy as np
from bs4 import BeautifulSoup
import requests
import re
import time
import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions
from selenium.webdriver.chrome.service import Service


class GetData:
    """
    This class facilitates the retrieval of data necessary to perform projections.
    """
    def __init__(self, season=None, year_soup=None, def_soup=None) -> None:
        # Set season
        self.season = get_current_season() if season is None else season

        # Get soups
        self.year_soup = year_soup if year_soup is not None else self.get_year_soup()
        self.def_soup = def_soup if def_soup is not None else self.get_defense_soup()


    ## ----------- Get soups ------------ ##
    def get_year_soup(self):
        """Get soup associated with yearly season stats."""
        url = f'https://www.pro-football-reference.com/years/{self.season}/'
        page = requests.get(url)
        return BeautifulSoup(page.content, 'html.parser')
    
    def get_defense_soup(self):
        """Get soup associated with yearly team defensive stats."""
        url = f'https://www.pro-football-reference.com/years/{self.season}/opp.htm'
        # page = requests.get(url)
        # soup = BeautifulSoup(page.content, 'html.parser')

        ## I think javascript is used to render this page, need to use selenium
        # Initiate webdriver and get site
        s = Service('/opt/homebrew/bin/chromedriver')
        driver = webdriver.Chrome(service=s)
        driver.get(url)

        # Wait for the critical elements of page to load
        try:
            WebDriverWait(driver, 5).until(expected_conditions.visibility_of_element_located((By.ID, 'all_passing')))
        except:
            driver.quit()
            raise LookupError('Unable to retrieve the defense page.')
        
        # Turn into soup
        # time.sleep(0.5)
        soup = BeautifulSoup(driver.page_source, 'lxml')
        driver.quit()

        return soup


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

    def team_offense_stats(self, soup=None, season=None):
        """
        Get the nfl team offensive stats.

        Parameters
        ----------
        soup : bs4.BeautifulSoup, optional
            Soup object from 'https://www.pro-football-reference.com/years/{season}/' request. If no 
            input is entered, the soup object is created.
        season : str, int, float, optional
            Season (year) that is desired to be used if soup is None. Defaults to current year.

        Returns
        -------
        list of pd.DataFrame
            List of length=10 pertaining to the various team defensive stat categories.
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

        # Fetch the correct div
        div_id = ['all_team_stats', 'all_passing', 'all_rushing', 'all_returns', 'all_kicking', 'all_punting',
                  'all_team_scoring', 'all_team_conversions', 'all_drives']
        div_tbls = self.year_soup.find_all('div', attrs={'class': 'table_wrapper'})

        stat_list = []  # Initiate list of dataframes
        for div_tbl in div_tbls:
            # Skip if table not part of the list of ids
            if div_tbl.get('id') not in div_id:
                continue

            tbl = div_tbl.find('table')
            if tbl is None: continue  # Some table are None, skip them
            tbl_name = tbl.find('caption').text

            # Get the tables
            non_std_tables = []
            if tbl_name in non_std_tables:
                stat_list.append(self.__scrape_offense_nonstd(tbl))
            else:
                stat_list.append(self.__scrape_offense_standard(tbl))


        # # Uses def_soup
        # div_tbls = self.def_soup.find_all('div', attrs={'class': 'table_wrapper'})
        
        # stat_list = []   # Initiate list of dataframes
        # for div_tbl in div_tbls:
        #     tbl = div_tbl.find('table')
        #     if tbl is None: continue  # Some tables are None, skip them
        #     try:
        #         tbl_name = tbl.find('caption').text
        #     except:
        #         tbl_name = "UNKNOWN"
        #         print('Excepted')

        #     # Get the tables
        #     non_std_tables = ['Team Advanced Defense Table']
        #     if tbl_name in non_std_tables:
        #         stat_list.append(self.__scrape_defense_nonstd(tbl))
        #     else:
        #         stat_list.append(self.__scrape_defense_standard(tbl))

        # return stat_list

    def team_defense_stats(self, soup=None, season=None):
        """
        Get the nfl team defensive stats.

        Parameters
        ----------
        soup : bs4.BeautifulSoup, optional
            Soup object from 'https://www.pro-football-reference.com/years/{season}/' request. If no 
            input is entered, the soup object is created.
        season : str, int, float, optional
            Season (year) that is desired to be used if soup is None. Defaults to current year.

        Returns
        -------
        list of pd.DataFrame
            List of length=10 pertaining to the various team defensive stat categories.
        """
        # Consider inputted season
        is_season_change = False
        if season is not None:
            is_season_change = (int(season) != int(self.season))
            self.season = season
            
        # Generate soup if not inputted
        if soup is not None:
            self.def_soup = soup
        elif is_season_change:
            self.def_soup = self.get_defense_soup()

        # Uses def_soup
        div_tbls = self.def_soup.find_all('div', attrs={'class': 'table_wrapper'})
        
        stat_list = []   # Initiate list of dataframes
        for div_tbl in div_tbls:
            tbl = div_tbl.find('table')
            if tbl is None: continue  # Some tables are None, skip them
            try:
                tbl_name = tbl.find('caption').text
            except:
                tbl_name = "UNKNOWN"
                print('Excepted')

            # Get the tables
            non_std_tables = ['Team Advanced Defense Table']
            if tbl_name in non_std_tables:
                stat_list.append(self.__scrape_defense_nonstd(tbl))
            else:
                stat_list.append(self.__scrape_defense_standard(tbl))

        return stat_list

    @staticmethod
    def __scrape_defense_standard(tbl):
        """Standard method of scraping defenses.
        
        Params
        ------
        tbl : html table
            Div table that is looped thru in team_defense_stats().
        """
        # Set name of table
        tbl_name = tbl.find('caption').text
        print(tbl_name)

        # Get each row
        teams = {}
        for td in tbl.find_all('td'):
            stat = td.get('data-stat')
            value = td.text

            if td.name=='th': 
                if stat != 'team':
                    continue  # Only use th if data-stat is team
            if stat=='team':
                team = re.sub(r'[^A-Za-z0-9 ]', '', str(value))  # Strip unnecessary characters

                # Sometimes summary rows exist, break the for loop if this is true
                if (team == 'Avg Team') or (team == 'League Total'):
                    break

                # Get link and extract team_id
                local_link = td.find('a')['href']
                team_id = ''
                if local_link is not None:
                    find_id = re.search(r'teams/([^/]+)/', local_link)  # Get team page link
                    if find_id is not None: team_id = find_id.groups()[0]
                
                # Set id and division
                teams[team] = {'id': team_id}
                continue

            # Apply each stat to the team dict
            teams[team][stat] = value

        # Turn into dataframe
        df = pd.DataFrame(teams).T
        df.name = tbl_name

        return df

    @staticmethod
    def __scrape_defense_nonstd(tbl):
        """
        Non-standard method of scraping defenses. Currently only applies to "Team Advanced Defense Table".

        Params
        ------
        tbl : html table
            Div table that is looped thru in team_defense_stats().
        """
        # Set name of table
        tbl_name = tbl.find('caption').text
        print(tbl_name)

        # Get each row
        teams = {}
        for tr in tbl.find_all('tr'):
            row = tr.get('data-row')   # Get data row

            # Skip if data-row doesn't exist
            if row is None:
                continue

            for td in tr.find_all(['td', 'th']):
                stat = td.get('data-stat')
                value = td.text

                # if td.name=='th': 
                #     if stat != 'team':
                #         continue  # Only use th if data-stat is team
                if stat=='team':
                    team = re.sub(r'[^A-Za-z0-9 ]', '', str(value))  # Strip unnecessary characters

                    # Sometimes summary rows exist, break the for loop if this is true
                    if (team == 'Avg Team') or (team == 'League Total'):
                        break

                    # Get link and extract team_id
                    local_link = td.find('a')['href']
                    team_id = ''
                    if local_link is not None:
                        find_id = re.search(r'teams/([^/]+)/', local_link)  # Get team page link
                        if find_id is not None: team_id = find_id.groups()[0]
                    
                    # Set id and division
                    teams[team] = {'id': team_id}
                    continue

                # Apply each stat to the team dict
                teams[team][stat] = value

        # Turn into dataframe
        df = pd.DataFrame(teams).T
        df.name = tbl_name

        return df

    ## ----------- END Team Level Data Section ------------- ##



def get_current_season():
    """Return the current season that is either active or has passed."""
    today = datetime.date.today()
    if int(today.month) < 9:
        return int(today.year) - 1
    return int(today.year)


