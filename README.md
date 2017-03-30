# projet-sysRes
Projet Système et Réseau 3A 2017 à l'INSA CVL

## Serveur
### Mise en place
- [X] Gestion de plusieurs clients (sans notion de concurrence) 
- [ ] Mise en place dictionnaire de données (BDD personnes + historique de connexion)
- [ ] Mise en place de la structure (reception des données entrantes, des arguments envoyés par le client etc...)

### Dictionnaire de données
- [ ] Personnes pouvant s'authentifier (login, mdp, poste?, droits, date de dernière co?)
- [ ] Personnes étant authentifiés actuellement sur le système
- [ ] ....

### Authentification
- [ ] Authentification simple (comparaison du couple login/mdp avec la BDD)
- [ ] Vérification d'une connexion possible (pas deux même personnes sur le serveur)
- [ ] Gestion déconnexion (retirer son login des personnes authentifiés sur le système)
- [ ]

### Fonctionnalités
- [ ] ls
- [ ] mv
- [ ] exe
- [ ] Gestion des droits (via ACLs)
- [ ] Connexion chiffrée (clés pas en clair sur le poste client + certificat coté serveur) SSL
- [ ] Flux graphiques ?
- [ ] Creer des logs sur les actions effectués ?



## Client
### Mise en place
- [X] Mise en place de l'interface de connexion
- [ ] Mise en place de l'interface pour les actions
- [ ] Chiffrement (clés)
- [ ] Flux graphiques ?
- [ ] Interface graphique ? 


## BDD / Dict
### Structure
- Data
    + Name
        + Password
        + Role
        + Last connexion

## Bilan 1ere séance
- Gestion des autentifications autre que en dur
- Posibilité d'avoir des actions supplémentaires pour certains roles pour ajouter ou modifier les personnes pouvant d'autentitfier
- Voir comment gerer les identifiants/mdp autre que ne dur (BDD ?)
- Gerer les outils et commandes dynamiques (ex vi) et comment gerer la relation client/serveur




# Notre version minimal : 

    - Elle comporte une interface graphique :
        - Qui permet:
            - Authentification des users
            - Stockage des mdp hashés sur le serveur
            - De sélectionner et visualiser un fichier
            - De se déplacer de fichier en fichier et de dossier en dossier
            - Qui permet d'éditer un fichier
    - Nous avons implémenté des droits pour chacun des dossiers afin que seuls les gens autorisés puissent voir ou modifier nu fichier.
    - Comme demandé elle possède une fonctionnalité additionelle :
        - Les communications utilisent le protocole SSL.