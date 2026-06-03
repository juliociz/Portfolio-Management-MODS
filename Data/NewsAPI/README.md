#  Configuration de l'Environnement et de la Clé API

Pour faire fonctionner le pipeline de récupération des actualités financières (`NewsAPI.py`), chaque membre de l'équipe doit configurer son propre fichier d'environnement local. 

Les clés d'API étant strictement confidentielles et personnelles, **elles ne doivent jamais être partagées sur GitHub**. C'est pourquoi le système ci-dessous a été mis en place.

---

##  Procédure de configuration (À faire dès le premier clonage)

Suivez scrupuleusement ces 3 étapes pour configurer votre accès en moins de 2 minutes :

### Étape 1 : Dupliquer le fichier d'exemple
À la racine du projet, repérez le fichier nommé `.env.example`. 
* **Dupliquez-le** (copier-coller) au même endroit.
* **Renommez la copie** exactement de cette manière : `.env` (sans rien avant le point).

### Étape 2 : Ajouter votre clé NewsAPI
Ouvrez le nouveau fichier `.env` que vous venez de créer dans VS Code. Vous y trouverez ceci :
```text
MY_NEWS_API_KEY=votre_cle_news_api_ici