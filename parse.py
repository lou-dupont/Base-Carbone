from bs4 import BeautifulSoup
from lxml import html
import numpy as np
import os
from os import listdir
from os.path import isfile, join
import pandas as pd
import re
import requests
import time

path = 'html/'

fiches = [f for f in listdir(path) if isfile(join(path, f))]

def siInfo(liste) :
    if liste is not None : 
        valeur = liste.text
        valeur = liste.text.strip()
        valeur = re.sub('\t', '', valeur)
        return(valeur)
    else :
        return('')

nom_col = ["Type Ligne", "Identifiant de l'élément", "Structure", "Type de l'élément", 
           "Statut de l'élément", "Nom base français", "Nom base anglais", "Nom attribut français", 
           "Nom attribut anglais", "Nom frontière français", "Nom frontière anglais", 
           "Code de la catégorie", "Tags français", "Tags anglais", "Unité français", 
           "Unité anglais", "Contributeur", "Programme", "Url du programme",
           "Source", "Localisation géographique", "Sous-localisation géographique français", 
           "Sous-localisation géographique anglais", "Date de création", "Date de modification",
           "Période de validité", "Incertitude", "Réglementations", "Transparence",
           "Qualité", "Qualité TeR", "Qualité GR", "Qualité TiR", "Qualité C", "Qualité P",
           "Qualité M", "Commentaire français", "Commentaire anglais", "Type poste",
           "Nom poste français", "Nom poste anglais", "Total poste non décomposé",
           "CO2f", "CH4f", "CH4b", "N2O", 
           "Code gaz supplémentaire 1", "Valeur gaz supplémentaire 1",
           "Code gaz supplémentaire 2", "Valeur gaz supplémentaire 2",
           "Code gaz supplémentaire 3", "Valeur gaz supplémentaire 3",
           "Code gaz supplémentaire 4", "Valeur gaz supplémentaire 4", 
           "Code gaz supplémentaire 5", "Valeur gaz supplémentaire 5", "Autres GES", "CO2b"]


def traiterFiche (page) :

    # Lecture de la page
    raw_page = open(path + page, encoding="utf-8")

    content = BeautifulSoup(raw_page, "lxml")

    # Parsing
    informations = {}
    informations["Identifiant de l'élément"] = re.sub('(.*).html', '\\1', page)
    informations["Type de l'élément"] = ""

    titre = siInfo(content.find("h2", {"class" : "bloctitle"}))
    if re.match(r"(.*) - (.*) - (.*)", titre) :
        informations['Nom base français'] = re.sub("(.*) - (.*) - (.*)", '\\1', titre)
        informations['Nom attribut français'] = re.sub("(.*) - (.*) - (.*)", '\\2', titre)
        informations['Nom frontière français'] = re.sub("(.*) - (.*) - (.*)", '\\3', titre)
    elif re.match(r"(.*) - (.*)", titre) :
        informations['Nom base français'] = re.sub("(.*) - (.*)", '\\1', titre)
        informations['Nom attribut français'] = re.sub("(.*) - (.*)", '\\2', titre)
    else : 
        informations['Nom base français'] = titre

        
    synthese = siInfo(content.find("div", {"class" : "synthese"}))
    informations['Total poste non décomposé'] = re.sub('([^ ]*) (.*)', '\\1', synthese)
    informations['Unité français'] = re.sub('([^ ]*) (.*)', '\\2', synthese)

    baliseZoneGeoAuteur = content.find('div', {"class" : "button-right"}).findPrevious('p')
    zoneGeo = re.sub('<p>(.*)<br/>(.*)</p>', '\\1', str(baliseZoneGeoAuteur))
    informations['Localisation géographique'] = re.sub('([^,]*), (.*)', '\\1', str(zoneGeo))
    informations["Sous-localisation géographique français"] = re.sub('([^,]*), (.*)', '\\2', str(zoneGeo))

    try : 
        informations["Url du programme"] = [x for x in content.findAll("div") if x.text.startswith("Programme")][0].findNext("a")['href']
    except : 
        informations["Url du programme"] =''
        

    # Informations administratives
    try : 
        for elem in content.find('div', {"class" : "info-admin"}).findAll("div", {"class" : "label"})  :
            valeur = elem.findNext("div", {"class" : "value"}).text
            elem = re.sub('\s+', ' ', elem.text).strip()
            valeur = re.sub('\s+', ' ', valeur).strip()
            informations[elem] = valeur.replace('baseCarbone.detailElement.detailQualite.', '')
    except : 
        print("Pas d'infos administratives : ", page)

    # Commentaire
    commentaires = [x.findNext("p") for x in content.findAll("h3") if x.text == "Commentaires"]
    if len(commentaires) > 0 : 
        informations['Commentaire français'] = commentaires[0]

    # Informations générales
    try : 
        for elem in content.find('div', {"class" : "info-gen"}).findAll("div", {"class" : "label"})  :
            valeur = elem.findNext("div", {"class" : "value"}).text
            elem = re.sub('\s+', ' ', elem.text).strip()
            valeur = re.sub('\s+', ' ', valeur).strip()
            informations[elem] = valeur
    except : 
        print("Pas d'infos générales : ", page)

    ### Tableau de décomposition
    
    table = content.find("div", {"class" : "table-decomposition"})
    decomposition = []

    # Non décomposé
    if table is None :
        informations['Structure'] = 'élément non décomposé'
        informations['Type Ligne'] = 'Elément'
        return([informations])
    
    # Par poste
    elif table.findNext('th', {"id" : "header1"}).text == "Type Poste" :
        informations['Structure'] = "élément décomposé par poste"
         
        if table.findNext('tbody') is not None : 
            for ligne in table.findNext('tbody').findAll('tr') :
                decomp = informations.copy()
                decomp["Type Ligne"] = "Poste"
                decomp["Type poste"] = re.sub("(.*) \((.*)\)$", '\\1', ligne.find("th").text)
                decomp['Nom poste français'] = re.sub("(.*) \((.*)\)$", '\\2', ligne.find("th").text)
                if decomp["Type poste"] == decomp['Nom poste français'] :
                    decomp['Nom poste français'] = ''
                decomp["Total poste non décomposé"] = ligne.find("td").text
                decomposition.append(decomp)
        
        if table.findNext('tfoot') is not None : 
            decomp = informations.copy()
            decomp["Type Ligne"] = "Elément"
            decomp["Total poste non décomposé"] = table.findNext('tfoot').find("tr").find("td").text
            decomposition.append(decomp)
            
    # Par poste et par gaz ou par gaz --> deux cas
    else : 
        entete = [x.text for x in table.find('thead').findAll('th')]
        entete = [w.replace('Total', 'Total poste non décomposé') for w in entete]
        entete = [w.replace('TOTAL', 'Total poste non décomposé') for w in entete]

        lignes = table.findAll(['tbody', 'tfoot'])
        
        if len(entete)>6 and len(lignes)>1 : 
            informations['Structure'] = "élément décomposé par poste et par gaz"
        elif len(entete)>6 and len(lignes) == 1 : 
            informations['Structure'] = "élément décomposé par gaz"
        
        lignes = [x.findAll('tr') for x in lignes]
        lignes = [item for sublist in lignes for item in sublist]
        for ligne in lignes :
            valeurs = [x.text for x in ligne.findChildren()]
            nomLigne = valeurs[0]
            valeurs = valeurs[1:]
            
            decomp = informations.copy()

            if nomLigne in ('Total poste non décomposé', 'Total') :
                    decomp["Type Ligne"] = "Elément"
            else : 
                decomp["Type Ligne"] = "Poste"
                decomp["Type poste"] = re.sub("(.*) \((.*)\)$", '\\1', nomLigne)
                decomp['Nom poste français'] = re.sub("(.*) \((.*)\)$", '\\2', nomLigne)
                if decomp["Type poste"] == decomp['Nom poste français'] :
                    decomp['Nom poste français'] = ''

            for i in range(len(entete)) :
                decomp[entete[i]] = valeurs[i]
            decomposition.append(decomp)
    return(decomposition)

base_ges = []
for index, fiche in enumerate(fiches):
    if index % 100 == 0:
        print('INFO: %d fiches traitées.' % index)
    if fiche == "15333.html" : continue
    base_ges.append(traiterFiche(fiche))
base_ges = [item for sublist in base_ges for item in sublist]
base_ges2 = pd.DataFrame(base_ges)    

base_ges2.rename(columns={'Statut': "Statut de l'élément", 
                        'Catégorie': 'Code de la catégorie',
                        'Tags': 'Tags français',
                        'Création' : "Date de création",
                        'Mise à jour': 'Date de modification',
                        "Représentativité technique" : "Qualité TeR",
                        "Représentativité géographique" : "Qualité GR",
                        "Représentation temporelle" : "Qualité TiR",
                        "Complétude" : "Qualité C",
                        "Précision" : "Qualité P",
                        "Homogénéité" : "Qualité M",
                        "Autre gaz" : "Autres GES"}, inplace=True)

for c in list(set(nom_col) - set(base_ges2.columns)) :
    base_ges2[c] = ''
    

# Conversion des colonnes en plus en code/valeur gaz supp
for index, row in base_ges2.iterrows():
    i = 0
    for col_supp in list(set(base_ges2.columns)-set(nom_col)) : # Colonnes en plus
        if str(row[col_supp]) != 'nan':
            i = i+1
            base_ges2.loc[index]['Code gaz supplémentaire ' + str(i)] = col_supp
            base_ges2.loc[index]['Valeur gaz supplémentaire ' + str(i)] = row[col_supp]

base_ges2[ 'baseCarbone.detailElement.detailQualite.'] = ''

base_ges2 = base_ges2[nom_col]
pd.DataFrame.to_csv(base_ges2, "BaseCarbone.csv", encoding='UTF-8', index=False)

base_ges2.groupby(['Contributeur'], sort=False).size().reset_index(name='Count')

base_ges2_filtree = base_ges2[base_ges2['Contributeur'].isin(('ADEME', 'AGRIBALYSE', 'MEEM'))]
base_ges2_filtree.to_csv("BaseCarbone_ActeursPublics.csv", encoding='UTF-8', index=False)
base_ges2_filtree.to_excel("BaseCarbone_ActeursPublics.xlsx", index=False)
