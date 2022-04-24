#!/usr/bin/env python
# coding: utf-8

# # Import Libraries

import requests
from IPython.display import clear_output


# Lions Cup League Set up

liga1 = {
    '19113': 'Hinode Hokkeyido',
    '28631': 'T Rex Swerdlowsk',
    '27448': 'Stavanger Sturmschwalben',
    '26620': 'Fredrikstad Ducks',
    '11440': 'San Marcos Rhinos',
    '21678': 'EC Frankonia',
    '23103': 'Costa Mesa Violent Gents',
    '10202': 'Halifax Moose',
}

liga1_rev = {val:key for key, val in liga1.items()}

liga2 = { 
    '23635': 'Chickenmountain Gamecocks',
    '13052': 'Broad Street Bullies',
    '29385': 'Genuesische Edelfighter',
    '31547': 'SüdtondernEishockeySylt',
    '24181': 'Hanover Knights',
    '16738': 'Htown Pelican',    
    '25082': 'Dynamo City Thunder',
    '28495': 'Flagstaff Broncos',
}

liga2_rev = {val:key for key, val in liga2.items()}

liga3 = {
    '28378': 'Düsseldorf Penguins',
    '26524': 'Hornets de Marseille',    
    '32102': 'Don Camillo Yellow Hunter',    
    '33165': 'Saporischschja Atomics',
    '18566': 'HC Ladeburger Oilers',
    '25115': 'Valaskjalf Vikings',
    '30021': 'ESC Wedemark Scorpions',
    '23232': 'Boston Lynxes',
}

liga3_rev = {val:key for key, val in liga3.items()}

ligen = [liga1, liga2, liga3]

lions_teams_dict = {key:val for d in ligen for key,val in d.items()}
lions_teams_dict_rev = {val:key for d in ligen for key,val in d.items()}


#Login to EZM

url_login_post = 'https://www.eiszeit-manager.de/login.php'

login_data = {
    'benutzername' : 'XXX',
    'passwort' : 'XXX'
}

def login():
        
    session=requests.Session()
    session.post(url_login_post, data=login_data)
    
    page = session.get(url_ligatabelle)
    soup = bs(page.text, 'html.parser')
    
    headline = soup.find_all('b')[0].find_parent().get_text().split()
    
    print(f'Saison {headline[1]}, Spieltag {headline[3]}')
    
    return session, headline[1], headline[3]