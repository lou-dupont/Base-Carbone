# Base Carbone

Base Carbone gérée par l'ADEME

## Utilisation

Les données sont accessibles après création d'un compte utilisateur à cette adresse : http://www.bilans-ges.ademe.fr/fr/accueil/authentification.

Pour indiquer au script les paramètres de connexion à utiliser, créer un fichier `params.py` avec le contenu suivant

```
username = "adresse_electronique@fournisseur.fr"
password = "mot_de_passe_choisi_sur_le_site"
```

Ensuite, exécuter le script de téléchargement `download.py` et celui de lecture et consolidation `parse.py`.
