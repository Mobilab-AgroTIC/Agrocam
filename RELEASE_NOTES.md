# Agrocam v2.1.0

## Nouveautés

- **Configuration en mode « maintenance » via un point d'accès** : lorsque le jumper est en position maintenance au démarrage, l'Agrocam crée son propre réseau Wi-Fi `Agrocam-XXXX` (les 4 derniers caractères du numéro de série du Raspberry). Il suffit de s'y connecter pour la configurer sur le terrain, sans autre réseau. Retirer le jumper met fin à ce mode et redémarre l'Agrocam.
- **Formulaire de paramétrage** : une interface web, accessible sur `http://10.42.0.1:5000` en mode maintenance, permet de modifier les paramètres de l'Agrocam depuis un navigateur.
- **Choix de la destination des photos** : le formulaire permet d'envoyer les photos soit sur Immich (`immich.agrotic-dev.org`), soit sur la plateforme Agrocam (`agrocam.agrotic-app.org`).
