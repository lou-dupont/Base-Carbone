from bs4 import BeautifulSoup
from lxml import html
import os
from os import listdir
from os.path import isfile, join
import pandas as pd
import params
import re
import requests
import time

log_url = "http://www.bilans-ges.ademe.fr/fr/accueil/authentification/save"
scrap_url = "http://www.bilans-ges.ademe.fr"

payload = {
    "UTI_EMAIL": params.username,
    "UTI_MOT_DE_PASSE": params.password,
}

if not os.path.exists("html"):
    os.makedirs("html")

with requests.Session() as session:
    r = session.post(log_url, data=payload)
    url = session.get(scrap_url + "/fr/basecarbone/donnees-consulter/choix-categorie/")
    soup = BeautifulSoup(url.content, 'html.parser')
    categories = soup.find_all('a', {'class' : 'bloc-categorie'}, href=True)
    categories = [a['href'] for a in categories]
    categories_parcourues = []
    categories_finales = []
    categories_terminales = []
    while len(categories)> 0 :
        for categorie in categories :
            print('INFO: ' + categorie)
            url = session.get(scrap_url + categorie)
            soup = BeautifulSoup(url.content, 'html.parser')
            categories.remove(categorie)
            categories_parcourues.append(categorie)
            categories_nouvelles = soup.find_all('a', {'class' : 'bloc-categorie'}, href=True)
            categories_nouvelles = [a['href'] for a in categories_nouvelles]
            for categorie_nouvelle in categories_nouvelles : 
                if categorie_nouvelle in (categories, categories_parcourues) :
                    continue
                else : 
                    categories.append(categorie_nouvelle)
            # Si on est sur une page avec une liste de produits
            if len(soup.find_all('div', {"class" : "nbres"}))>0 : 
                categories_terminales.append(categorie)

print("Nombre de noeuds", len(categories_parcourues))
print("Categories finales", len(categories_terminales))

ids = []
with requests.Session() as session:
    r = session.post(log_url, data=payload)
    for categorie in categories_terminales : 
        print('INFO: ' + categorie)
        url = session.get(scrap_url + categorie)
        soup = BeautifulSoup(url.content, 'html.parser')
        blocs = soup.find('div', {'id' : "page-elements"}).select("div[class*=bloc]")
        for bloc in blocs : 
            detail_id = bloc.select("a[id*=detail-element]")
            if len(detail_id) == 0 : 
                detail_id = bloc.select("div[id*=detail-element]")
            detail_id = re.search('.*element-(.*)', detail_id[0]['id']).group(1)
            ids.append(detail_id)
            with open("html/%s.html"%detail_id, "w", encoding='utf-8') as file:
                file.write(bloc.encode('utf-8').decode('utf-8'))
                file.write('\n')
        time.sleep(.5)

xhr_url = scrap_url + "/fr/basecarbone/donnees-consulter/xhr-detail-element?element=%s&regle="
with requests.Session() as session:
    r = session.post(log_url, data=payload)
    headers = session.headers.update({"X-Requested-With": "XMLHttpRequest"})
    for detail_id in ids : 
        print('INFO: ' + detail_id)
        url = session.get(xhr_url % detail_id)
        soup = BeautifulSoup(url.content, 'html.parser')
        soup = str(soup.encode('utf-8').decode('utf-8'))
        soup = re.sub('<img([^>]*)>', '', soup)
        with open("html/%s.html"%detail_id, "a", encoding='utf-8') as file:
            file.write(soup)
