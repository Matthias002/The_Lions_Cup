#!/usr/bin/env python
# coding: utf-8

# # Import Libraries

import pandas as pd
import numpy as np
from bs4 import BeautifulSoup as bs
import requests
import re
import xlwings as xw
import excel2img
import random
import EZM_Functions as ezm


# # Functions and Settings

lion_file_path = 'C:\Daten\Projekte\Eiszeit_Manager\Lions_Cup\Ablage\\'

filename = lion_file_path+'Lions Cup Tabellen.xlsx'

url_login_post = 'https://www.eiszeit-manager.de/login.php'
url_login_get = 'https://www.eiszeit-manager.de/buero/index.php?content=buero'

url_fs_post = 'https://www.eiszeit-manager.de/buero/index.php?content=friendly'

url_match_1 = 'https://www.eiszeit-manager.de/buero/index.php?content=match_detail&match_id='
url_match_2 = '&art=friendly'


spieltage = {
    1 :'3',
    2 :'6',
    3 :'9',
    4 :'12',
    5 :'15',
    6 :'18',
    7 :'22'
    }

schedule_templates = {
    7 : [
    [[2,7], [3,6], [4,5], [1,'S']],
    [[3,1], [4,7], [5,6], [2,'S']],
    [[4,2], [5,1], [6,7], [3,'S']],
    [[5,3], [6,2], [7,1], [4,'S']],
    [[6,4], [7,3], [1,2], [5,'S']],
    [[7,5], [1,4], [2,3], [6,'S']],
    [[1,6], [2,5], [3,4], [7,'S']]
    ],
    
    8 : [
    [[1,2],[3,4],[5,6],[7,8]],
    [[4,1],[2,3],[8,5],[6,7]],
    [[5,4],[1,3],[2,7],[6,8]],
    [[4,2],[7,5],[8,1],[3,6]],
    [[4,7],[2,8],[1,6],[5,3]],
    [[8,4],[6,2],[7,3],[5,1]],
    [[4,6],[3,8],[2,5],[1,7]]
    ]
}

cols_erg = ['Match_ID', 'Liga', 'Spieltag', 'Heimteam', 'SEFheim', 'Auswärtsteam', 'SEFausw',
            'Theim', 'Tausw', 'OT/SO', 'Pheim', 'Pausw', 'Sheim', 'Nheim', 'OTSheim', 'OTNheim',
            'Sausw', 'Nausw', 'OTSausw', 'OTNausw', 'Spiele']

int_cols_erg =['Match_ID', 'Theim', 'Tausw', 'Pheim', 'Pausw', 'Spiele', 'Sheim', 'Nheim', 'OTSheim',
               'OTNheim', 'Sausw', 'Nausw', 'OTSausw', 'OTNausw']

cols_liga = ['Team', 'ID', 'GP', 'P', 'T', 'GT', 'D', 'S', 'N', 'OTS', 'OTN']

cols_stat = ['ID', 'Spieltag', 'Spielername', 'Team', 'Pos', 'GP', 'Tore', 'Ass', 'Pkt', '+/-', 'PIM', 'TS', 'Chks',
             'BKS', 'GVA', 'TKA', 'Bul%', 'SOG', 'SAV', 'SV%', 'Min', 'Liga', 'Match_IDs']

cols_G = ['Spielername', 'Team', 'GP', 'SOG', 'SAV', 'SV%', 'Min']

cols_C = ['Spielername', 'Team', 'GP', 'Tore', 'Ass', 'Pkt', '+/-', 'PIM', 'TS', 'Chks',
           'BKS', 'GVA', 'TKA', 'Bul%', 'Min']

cols_V = ['Spielername', 'Team', 'GP', 'Tore', 'Ass', 'Pkt', '+/-', 'PIM', 'TS', 'Chks',
           'BKS', 'GVA', 'TKA', 'Min']

cols_S = ['Spielername', 'Team', 'GP', 'Tore', 'Ass', 'Pkt', '+/-', 'PIM', 'TS', 'Chks',
           'BKS', 'GVA', 'TKA', 'Min']

def create_schedule(leagues_and_sizes):
    df = pd.DataFrame(columns=cols_erg)
    index = 1
    
    for c, league in enumerate(leagues_and_sizes, start=1):
        los = random.sample(list(league[0].values()),league[1])
        spielplan_vorlage = schedule_templates[league[1]]
        spieltag_nr = 1

        for spieltag in spielplan_vorlage:
            for paarung in spieltag:                
                df.loc[index] = 0
                df.loc[index, 'Liga'] = c
                df.loc[index, 'Spieltag'] = spieltag_nr
                df.loc[index, 'Heimteam'] = los[paarung[0]-1]
                if 'S' in paarung:
                    df.loc[index, 'Auswärtsteam'] = '**spielfrei**'
                else:
                    df.loc[index, 'Auswärtsteam'] = los[paarung[1]-1]
                index += 1
            spieltag_nr += 1
    df['OT/SO'] = ''    
    
    df.to_pickle(lion_file_path+'Ergebnisse Spieltag 0')
    schedule_to_excel(df)
    
    return df


def all_away(team):
    df = pd.read_pickle(lion_file_path+'Ergebnisse Spieltag 0')
    
    for i in df.iterrows():
        if i[1][3] == team:
            df.loc[i[0], 'Heimteam'], df.loc[i[0], 'Auswärtsteam'] =            df.loc[i[0], 'Auswärtsteam'], df.loc[i[0], 'Heimteam']
            
    schedule_to_excel(df)
    df.to_pickle(lion_file_path+'Ergebnisse Spieltag 0')
    return df


def update_results(spieltag):
    cancelled = []
    df = pd.read_pickle(lion_file_path + 'Ergebnisse Spieltag ' + str(spieltag-1))
    regex = r'\d+'
    
    if df.loc[df.Spieltag == spieltag].Spiele.sum() != 0:
        pass
    else:        
        for spiel in df.loc[(df.Spieltag == spieltag) & (df.Auswärtsteam != '**spielfrei**')].index: 
            heimteam_id = ezm.lions_teams_dict_rev[df.loc[spiel, 'Heimteam']]

            r = session.post(url_fs_post, data={
            'filter': 'offen',
            'mode': 'filter',
            'team': heimteam_id,
            'seite': '0'
            })

            soup = bs(r.text, 'html.parser')
            table_rows = soup.find_all('table')[2].find_all('tr')

            for row in table_rows:
                if row.find_all('td')[0].text == spieltage[spieltag]:
                    hteam = row.find_all('td')[2].text.strip().rpartition(' ')[0]
                    hsef = row.find_all('td')[2].text.strip().rpartition(' ')[-1]
                    ateam = row.find_all('td')[4].text.strip().rpartition(' ')[0]
                    asef = row.find_all('td')[4].text.strip().rpartition(' ')[-1]
                    htore = row.find_all('td')[5].text.split(' ')[0]                    
                    atore = row.find_all('td')[5].text.split(' ')[2]
                    overtime = row.find_all('td')[5].text.split(' ')[-1]
                    match_id = int(re.search(regex, row.find_all('td')[6].find('a')['href']).group())                    

                    df.loc[spiel, 'Match_ID'] = match_id
                    df.loc[spiel, 'Heimteam'] = hteam
                    df.loc[spiel, 'SEFheim'] = hsef
                    df.loc[spiel, 'Auswärtsteam'] = ateam
                    df.loc[spiel, 'SEFausw'] = asef
                    try:
                        htore = int(htore)
                        atore = int(atore)
                        df.loc[spiel, 'Theim'] = htore
                        df.loc[spiel, 'Tausw'] = atore
                    except:
                        df.loc[spiel, 'Theim'] = 0
                        df.loc[spiel, 'Tausw'] = 0
                        print('Spieltag '+ str(spieltag) + ' / ' + 'Spielnummer ' + str(spiel) + ':')
                        print(hteam + ' vs. ' + ateam + ' hat nicht stattgefunden!')
                        cancelled.append([spieltag, spiel, match_id, hteam, ateam])
                    
                    df.loc[spiel, 'Spiele'] += 1
                    if overtime in ['(SO)', '(OT)']:
                        df.loc[spiel, 'OT/SO'] = overtime
                        if htore > atore:
                            df.loc[spiel, 'Pheim'] = 2
                            df.loc[spiel, 'Pausw'] = 1
                            df.loc[spiel, 'OTSheim'] += 1
                            df.loc[spiel, 'OTNausw'] += 1
                        else:
                            df.loc[spiel, 'Pheim'] = 1
                            df.loc[spiel, 'Pausw'] = 2
                            df.loc[spiel, 'OTSausw'] += 1
                            df.loc[spiel, 'OTNheim'] += 1
                    else:
                        df.loc[spiel, 'OT/SO'] = ''
                        if htore > atore:
                            df.loc[spiel, 'Pheim'] = 3
                            df.loc[spiel, 'Pausw'] = 0
                            df.loc[spiel, 'Sheim'] += 1
                            df.loc[spiel, 'Nausw'] += 1
                        else:
                            df.loc[spiel, 'Pheim'] = 0
                            df.loc[spiel, 'Pausw'] = 3
                            df.loc[spiel, 'Sausw'] += 1
                            df.loc[spiel, 'Nheim'] += 1
                            
                else:
                    continue                    
            
        df[int_cols_erg] = df[int_cols_erg].astype(int)
        df.to_pickle(lion_file_path+'Ergebnisse Spieltag '+str(spieltag))
        schedule_to_excel(df)
        
    return cancelled, df
        
                
def update_league_table(liga, df_Ergebnisse):
    df = pd.DataFrame(columns=cols_liga)
    df['Team'] = sorted(ezm.ligen[liga-1].values())
    df.set_index('Team', drop=True, inplace=True)
    
    for team in df.index:
        werte_heim = df_Ergebnisse.loc[df_Ergebnisse.Heimteam==team][int_cols_erg].sum()    
        df.loc[team] = 0
        df.loc[team, 'ID'] = int(ezm.lions_teams_dict_rev[team])
        df.loc[team, 'GP'] += werte_heim['Spiele']
        df.loc[team, 'P'] += werte_heim['Pheim']
        df.loc[team, 'T'] += werte_heim['Theim']
        df.loc[team, 'GT'] += werte_heim['Tausw']    
        df.loc[team, 'S'] += werte_heim['Sheim']
        df.loc[team, 'N'] += werte_heim['Nheim']
        df.loc[team, 'OTS'] += werte_heim['OTSheim']
        df.loc[team, 'OTN'] += werte_heim['OTNheim']

        werte_ausw = df_Ergebnisse.loc[df_Ergebnisse.Auswärtsteam==team][int_cols_erg].sum()
        df.loc[team, 'GP'] += werte_ausw['Spiele']
        df.loc[team, 'P'] += werte_ausw['Pausw']
        df.loc[team, 'T'] += werte_ausw['Tausw']
        df.loc[team, 'GT'] += werte_ausw['Theim']    
        df.loc[team, 'S'] += werte_ausw['Sausw']
        df.loc[team, 'N'] += werte_ausw['Nausw']
        df.loc[team, 'OTS'] += werte_ausw['OTSausw']
        df.loc[team, 'OTN'] += werte_ausw['OTNausw']

        df.loc[team, 'D'] = df.loc[team, 'T'] - df.loc[team, 'GT']  
        
    df.sort_values(['P', 'D', 'T'], ascending=[False, False, False], inplace=True)
    df['Pl'] = list(range(1, len(ezm.ligen[liga-1])+1))
    df = df.reset_index().set_index('Pl')    
    df.to_pickle(lion_file_path+'Tabelle Liga '+str(liga))
    
    return df


def update_player_stats(spieltag):    
    df_Ergebnisse = pd.read_pickle(lion_file_path + 'Ergebnisse Spieltag ' + str(spieltag))
    df = pd.read_pickle(lion_file_path + 'Spieler Stats')
    
    match_ids_to_scrape = list(df_Ergebnisse.loc[df_Ergebnisse.Spieltag == spieltag].Match_ID)
    
    if df.Match_IDs.sum() == 0:
        matches_already_scraped = []
    else:
        matches_already_scraped = df.Match_IDs.sum()
        
    if len(df.index) == 0:
        index = 0
    else:
        index = df.index[-1] + 1
        
    for match_id in match_ids_to_scrape:
        if (match_id in matches_already_scraped) or (match_id == 0):
            continue
        else:            
            r = session.get(url_match_1+str(match_id)+url_match_2)
            soup = bs(r.text, 'html.parser')

            team_home = soup.find_all('b')[0].get_text()
            team_away = soup.find_all('b')[1].get_text()

            result = soup.find_all('h2')
            goals_home = int(result[0].get_text())
            goals_away = int(result[1].get_text())

            shots = soup.find('td', text='Torschüsse').find_next_siblings('td')
            shots_home = int(shots[0].get_text())
            shots_away = int(shots[1].get_text())

            rows = soup.find_all('table')[-1].find_all('tr')[1:]
            
            for row in rows:
                try:
                    if row.find('th').get_text() != 'Spieler':
                        teamname = row.find('th').get_text()
                except:
                    pass     

                try:                   
                    cells = row.find_all('td')
                    df.loc[index] = 0
                    df.loc[index, 'ID'] = row.find('td').find('a')['href'].split('=')[-1]
                    df.at[index, 'Match_IDs'] = ''
                    df.at[index, 'Match_IDs'] = []
                    df.loc[index, 'Spielername'] = cells[0].get_text()
                    df.loc[index, 'Team'] = teamname
                    df.loc[index, 'Pos'] = cells[1].get_text()
                    df.loc[index, 'Spieltag'] = spieltag
                    df.loc[index, 'Tore'] += int(cells[2].get_text())
                    df.loc[index, 'Ass'] += int(cells[3].get_text())
                    df.loc[index, 'Pkt'] += int(cells[4].get_text())
                    df.loc[index, '+/-'] += int(cells[5].get_text())
                    df.loc[index, 'PIM'] += int(cells[6].get_text())
                    df.loc[index, 'TS'] += int(cells[7].get_text())
                    df.loc[index, 'Chks'] += int(cells[8].get_text())
                    df.loc[index, 'BKS'] += int(cells[9].get_text())
                    df.loc[index, 'GVA'] += int(cells[10].get_text())
                    df.loc[index, 'TKA'] += int(cells[11].get_text())
                    if cells[12].get_text() != '':
                        df.loc[index, 'Bul%'] += int(cells[12].get_text())
                    if df.loc[index, 'Pos'] == 'G':
                        if df.loc[index, 'Team'] == team_home:
                            df.loc[index, 'SOG'] += shots_away
                            df.loc[index, 'SAV'] += shots_away - goals_away
                        else:
                            df.loc[index, 'SOG'] += shots_home
                            df.loc[index, 'SAV'] += shots_home - goals_home
                        try:
                            df.loc[index, 'SV%'] = int(100*df.loc[index, 'SAV']/df.loc[index, 'SOG'])
                        except ZeroDivisionError:
                            df.loc[index, 'SV%'] = 0
                    df.loc[index, 'Min'] += int(cells[15].get_text().split(':')[0])
                    df.loc[index, 'Match_IDs'].append(match_id)
                    df.loc[index, 'GP'] = 1
                    
                    if df.loc[index, 'Team'] in ezm.liga1.values():
                        df.loc[index, 'Liga'] = 1
                    elif df.loc[index, 'Team'] in ezm.liga2.values():
                        df.loc[index, 'Liga'] = 2
                    else:
                        df.loc[index, 'Liga'] = 3
                    index += 1

                except AttributeError: 
                    pass
                
    df.to_pickle(lion_file_path+'Spieler Stats')
    return df


def index_ranking(df, drop):
    df.reset_index(drop=drop, inplace=True)
    df.set_index(keys=pd.Index(range(1, df.shape[0]+1)),inplace=True)
    return df 


def all_stars(spieltag):
    df = pd.read_pickle(lion_file_path + 'Spieler Stats')
    df_stats = df[df.Spieltag == spieltag].drop('ID', axis=1)
    
    df_scorer = pd.concat([df.groupby('Pos').get_group(group) for group in ('C', 'V', 'S')]).groupby('Spielername').agg({
        'Team':'min',
        'Pos':'min',
        'Liga': 'min',
        'GP':'sum',
        'TS': 'sum',
        'Tore':'sum',
        'Ass':'sum',
        'Pkt':'sum',
        'Min': 'sum'
    })

    df_scorer = df_scorer.drop(df_scorer[(df_scorer.GP <= df.Spieltag.max()//2)|(df_scorer.TS==0)].index, axis=0)
    df_scorer['SC%'] = round(100 * df_scorer['Tore'] / df_scorer['TS'], 2)
    df_scorer.sort_values(['Pkt', 'Tore', 'Ass', 'SC%'], ascending=[False, False, False, False], inplace=True)
    df_scorer = index_ranking(df_scorer, drop=False)
    
    df_goalies = df.groupby('Pos').get_group('G').groupby('Spielername').agg({
        'Team':'min',
        'Liga': 'min',
        'GP':'sum',
        'SOG':'sum',
        'SAV':'sum',
    })
    df_goalies = df_goalies.drop(df_goalies[df_goalies.GP <= df.Spieltag.max()//2].index, axis=0)
    df_goalies['SV%'] = round(100 * df_goalies['SAV'] / df_goalies['SOG'], 2)
    df_goalies.sort_values('SV%', ascending=False, inplace=True)
    df_goalies = index_ranking(df_goalies, drop=False)

    all_stars = {}
    scorer_rankings = {}
    goalie_rankings = {}

    for liga in range(1, len(ezm.ligen)+1):
        temp = pd.DataFrame(columns=cols_stat, index=range(1,17)).drop('ID', axis=1)
        temp.loc[1] = df_stats.groupby(['Liga','Pos']).get_group((liga,'G'))\
            .sort_values(['SV%', 'SOG'],ascending=[False, False])[:1].values

        temp.loc[list(range(2,5))] = df_stats.groupby(['Liga','Pos']).get_group((liga,'C'))\
            .sort_values(['Bul%', 'Pkt', 'Chks'], ascending=[False, False, False])[:3].values

        temp.loc[list(range(5,11))] = df_stats.groupby(['Liga','Pos']).get_group((liga,'V'))\
            .sort_values(['BKS', '+/-', 'Chks'], ascending=[False, False, False])[:6].values

        temp.loc[list(range(11,17))] = df_stats.groupby(['Liga','Pos']).get_group((liga,'S'))\
            .sort_values(['Pkt', 'TS' , 'Chks'], ascending=[False, False, False])[:6].values

        all_stars[liga] = temp.drop(['GP', 'Min', 'Liga', 'Match_IDs', 'Spieltag'], axis=1)\
            .set_index('Pos', drop=True)
        
        scorer_rankings[liga] = index_ranking(df_scorer.groupby('Liga').get_group(liga), drop=True)[:20]\
            .drop('Liga', axis=1)
        
        goalie_rankings[liga] = index_ranking(df_goalies.groupby('Liga').get_group(liga), drop=True)[:8]\
            .drop('Liga', axis=1)
    
    return list(all_stars.values()), scorer_rankings, goalie_rankings


def schedule_to_excel(df):
    grouped_df = df.groupby(['Liga', 'Spieltag'])
    leagues_count = int(len(grouped_df) / 7)
    
    wb = xw.Book(filename)
    sht_erg = wb.sheets['Ergebnisse']
    columns = ('A', 'F', 'K', 'P')
    rows = list(range(4, 41, 6))
    
    for league in range(1, leagues_count+1):
        column = columns[league-1]
        for match_day in range(1,8):
            row = rows[match_day-1]
            df = grouped_df.get_group((league, match_day)).astype('str')
            df['home'] = df['Heimteam'] + ' ' + df['SEFheim'].replace('0','')
            df['vs'] = 'vs.'
            df['away'] = df['Auswärtsteam'] + ' ' + df['SEFausw'].replace('0','')    
            df['result'] = df['Theim'] + " – " + df['Tausw'] + ' ' + df['OT/SO']
            sht_erg.range((column+str(row))).value = df.iloc[:,-4:].values
            
    wb.save(filename)
    
    
def tables_to_excel():
    wb = xw.Book(filename)    
    sht_tab = wb.sheets['Tabellen']
    sht_tab.clear_contents()
    rows = (1, 12, 23, 34)
    
    for i in range(len(ezm.ligen)):
        df = pd.read_pickle(lion_file_path+'Tabelle Liga ' + str(i+1))
        sht_tab.range('A'+str(rows[i])).value = df
    wb.save(filename)
    

def all_stars_to_excel(all_stars_dfs):
    wb = xw.Book(filename)    
    sht_tab = wb.sheets['All Stars']
    sht_tab.clear_contents()
    rows = [1, 20, 39, 58]
    
    for c, df in enumerate(all_stars_dfs):
        sht_tab.range('A' + str(rows[c])).value = df
        
    wb.save(filename)
    
    
def top_players_to_excel(top_scorer, top_goalies):
    wb = xw.Book(filename)    
    sht_tab = wb.sheets['Top Players']
    sht_tab.clear_contents()
    rows = [1, 38, 75, 112]
    
    for liga in range(1, len(ezm.ligen)+1):
        sht_tab.range('A' + str(rows[liga-1])).value = 'Top Goalies'
        sht_tab.range('A' + str(rows[liga-1]+2)).value = top_goalies[liga]
        sht_tab.range('A' + str(rows[liga-1]+12)).value = 'Top Scorer'
        sht_tab.range('A' + str(rows[liga-1]+14)).value = top_scorer[liga]
        
    wb.save(filename)
    
    
def create_images():
    excel2img.export_img(
            lion_file_path+"Lions Cup Tabellen.xlsx", lion_file_path+"Ergebnisse Liga 1.png", "Ergebnisse", "A1:D43")
    excel2img.export_img(
            lion_file_path+"Lions Cup Tabellen.xlsx", lion_file_path+"Ergebnisse Liga 2.png", "Ergebnisse", "F1:I43")
    excel2img.export_img(
            lion_file_path+"Lions Cup Tabellen.xlsx", lion_file_path+"Ergebnisse Liga 3.png", "Ergebnisse", "K1:N43")
    excel2img.export_img(
            lion_file_path+"Lions Cup Tabellen.xlsx", lion_file_path+"Tabelle Liga 1.gif", "Tabellen", "A1:L9")
    excel2img.export_img(
            lion_file_path+"Lions Cup Tabellen.xlsx", lion_file_path+"Tabelle Liga 2.gif", "Tabellen", "A12:L20")
    excel2img.export_img(
            lion_file_path+"Lions Cup Tabellen.xlsx", lion_file_path+"Tabelle Liga 3.gif", "Tabellen", "A23:L31")
    excel2img.export_img(
            lion_file_path+"Lions Cup Tabellen.xlsx", lion_file_path+"All Stars Liga 1.gif", "All Stars", "A1:Q17")
    excel2img.export_img(
            lion_file_path+"Lions Cup Tabellen.xlsx", lion_file_path+"All Stars Liga 2.gif", "All Stars", "A20:Q36")
    excel2img.export_img(
            lion_file_path+"Lions Cup Tabellen.xlsx", lion_file_path+"All Stars Liga 3.gif", "All Stars", "A39:Q55")
    excel2img.export_img(
            lion_file_path+"Lions Cup Tabellen.xlsx", lion_file_path+"Top Players Liga 1.gif", "Top Players", "A1:K35")
    excel2img.export_img(
            lion_file_path+"Lions Cup Tabellen.xlsx", lion_file_path+"Top Players Liga 2.gif", "Top Players", "A38:K72")
    excel2img.export_img(
            lion_file_path+"Lions Cup Tabellen.xlsx", lion_file_path+"Top Players Liga 3.gif", "Top Players", "A75:K109")
    

def auswertung_ergebnisse(df_Ergebnisse, spieltag):
    ezm.clear_output()
    print('Schreibe Ergebnisse...')
    schedule_to_excel(df_Ergebnisse)
    ezm.clear_output()
    print('Erstelle Tabellen...')
    for i in range(len(ezm.ligen)):
            update_league_table(i+1, df_Ergebnisse)
    ezm.clear_output()
    print('Schreibe Tabellen...')
    tables_to_excel()
    ezm.clear_output()
    print('Erstelle All Star Teams und Top-Spieler Rankings...')
    update_player_stats(spieltag)
    all_stars_dfs, top_scorer, top_goalies = all_stars(spieltag)
    all_stars_to_excel(all_stars_dfs)
    top_players_to_excel(top_scorer, top_goalies)
    ezm.clear_output()
    print('Erstelle Grafiken...')
    create_images()
    ezm.clear_output()
    
    
def Spieltag(spieltag, df_Ergebnisse=None):
    
    if spieltag == 0:
        leagues_and_sizes = [(x, len(x)) for x in ezm.ligen]
        df_Ergebnisse = create_schedule(leagues_and_sizes)
        df_Stats = pd.DataFrame(columns=cols_stat)
        df_Stats.to_pickle(lion_file_path+'Spieler Stats')
        for i in range(len(ezm.ligen)):
            update_league_table(i+1, df_Ergebnisse)
        tables_to_excel()
        create_images()
        return 'Die neue Saison kann kommen!'
    
    if isinstance(df_Ergebnisse, pd.DataFrame):
        auswertung_ergebnisse(df_Ergebnisse, spieltag)
        return 'Erledigt!'
    
    print('Sammle Ergebnisse...')
    cancelled, df_Ergebnisse = update_results(spieltag)
    
    if len(cancelled) == 0:
        auswertung_ergebnisse(df_Ergebnisse, spieltag)
        return f'Spieltag {spieltag} erledigt!'
    
    cancelled_games = [x[2] for x in cancelled]
    df_Stats = pd.read_pickle(lion_file_path+'Spieler Stats')
    df_Stats.at[0, 'Match_IDs'] += cancelled_games
    df_Stats.to_pickle(lion_file_path+'Spieler Stats')
    

def hall_of_fame(min_games=7, goalies=20, attcker=50, defender=50, penalties=50):
    df = pd.read_pickle(lion_file_path+'hall_of_fame')
    df = df.groupby('Spielername').agg({
            'Team': 'min',
            'Pos': 'min',
            'GP': 'sum',
            'Min': 'sum',
            'TS': 'sum',
            'Tore': 'sum',
            'Ass': 'sum',
            'Pkt': 'sum',        
            'BKS': 'sum',
            '+/-': 'sum',
            'PIM': 'sum',
            'Chks': 'sum',
            'SOG': 'sum',
            'SAV': 'sum',
        })
    df = df[[int(x) >= min_games for x in df.GP]]

    df_field = pd.concat([df.groupby('Pos').get_group(group) for group in ('C', 'V', 'S')])\
        [['Team', 'Pos', 'GP', 'Min', 'TS', 'Tore', 'Ass', 'Pkt', 'BKS', 'Chks', 'PIM', '+/-']]
    df_field['SC%'] = 100 * df_field['Tore'] / df_field['TS']
    df_field['SC%'] = [round(i,2) for i in df_field['SC%'].values]
    df_field['P%'] = 100 * df_field['PIM'] / df_field['Min']
    df_field['P%'] = [round(i,2) for i in df_field['P%'].values]

    df_attacker = df_field.sort_values(['Tore', 'SC%', 'Ass'], ascending=[False, False, False])\
        .drop(['BKS', 'Chks', '+/-', 'P%', 'PIM'], axis=1)
    df_attacker = index_ranking(df_attacker, drop=False).loc[:attcker]

    df_defender = df_field.sort_values(['BKS', 'Chks', 'PIM'], ascending=[False, False, True])\
        .drop(['TS', 'Tore', 'Ass', 'Pkt', 'SC%', '+/-', 'P%'], axis=1)
    df_defender = index_ranking(df_defender, drop=False).loc[:defender]

    df_penalties = df_field.sort_values(['PIM', 'P%'], ascending=[False, False])\
        .drop(['TS', 'Tore', 'Ass', 'Pkt', 'SC%', '+/-', 'BKS', 'Chks'], axis=1)
    df_penalties = index_ranking(df_penalties, drop=False).loc[:penalties]
        
    df_goalies = df.groupby('Pos').get_group('G')[['Team', 'Pos', 'GP', 'Min', 'SOG', 'SAV']]
    df_goalies['SV%'] = 100 * df_goalies['SAV'] / df_goalies['SOG']
    df_goalies['SV%'] = [round(i,2) for i in df_goalies['SV%'].values]
    df_goalies.sort_values(['SV%', 'SAV'], ascending=[False, False], inplace=True)
    df_goalies = index_ranking(df_goalies, drop=False).loc[:goalies]

    wb = xw.Book(filename)    
    sht_hof = wb.sheets['Hall of Fame']
    sht_hof.clear_contents()
    sht_hof.range('A1').value = 'Die unüberwindbarsten Goalies'
    sht_hof.range('A25').value = 'Die gefährlichsten Torjäger'
    sht_hof.range('A79').value = 'Die härtesten Defensivspieler'
    sht_hof.range('A133').value = 'Die Strafbankkönige - zu Ehren von Erich Kühnhackl'

    sht_hof.range('A3').value = df_goalies
    sht_hof.range('A27').value = df_attacker
    sht_hof.range('A81').value = df_defender
    sht_hof.range('A135').value = df_penalties
    
    wb.save(filename)

    excel2img.export_img(
            lion_file_path+"Lions Cup Tabellen.xlsx", lion_file_path+"Hall of Fame.gif", "Hall of Fame", "A1:K185")