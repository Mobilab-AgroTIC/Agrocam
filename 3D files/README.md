# 1. Imprimer le boitier
Tous les fichiers .stl se situent dans le dossier [3D files](https://github.com/Mobilab-AgroTIC/Agrocam/tree/main/3D%20files). Lancer l'impression avec une epaisseur de 0,2 mm. Pour lancer l'impression il existe de nombreux tutoriel sur internet.

# 2. Monter le boitier
Une fois les impressions terminées il faut assembler les pièces.

## 2.1 Insérer les écrous
Dans le boitier principal insérer les écrous dans les éncoches prévues. Il se peut que les écrous ne se piositionnent pas correctement dans les encoches à cause de défaut d'impression. Pour remédier à cela, un fer à souder peut permettre de pousser l'écrou dans l'encoche en faisant fondre les bordures.

<img src="https://user-images.githubusercontent.com/93132152/177131236-29effc2a-853d-4e9d-817c-d7e0ef8d1aed.png" width=20% height=20%>

## 2.2 Coller les supports
La caméra, le rasperry et le servomoteur sont vissés sur des supports qu'il faut coller (n'importe quelle colle forte du commerce fonctionnera) sur le couvercle du boitier. L'emplacement des supports est indiqué par un très léger manque d'épaisseur dans le couvercle. 
Attention pour le support du raspberry, il faudra ajuster la distance avec la caméra en fonction de la longueur de la nappe de cable les reliant.

## 2.2 Monter le servomoteur
Une fois le support du servomoteur collé, on peut insérer la partie rotative du servo dans le trou prévu.

<img src="https://user-images.githubusercontent.com/93132152/177153537-299992fb-9e69-4b5e-b79e-9f4946b5726b.jpg" width=20% height=20%>

De l'autre côté on emboite l'obturateur sur l'axe du servomoteur, puis on le visse :

<img src="https://user-images.githubusercontent.com/93132152/177153162-b6fa3ee8-4c61-4d92-9260-bce10f50fb50.png" width=20% height=20%>

Enfin clipser la casquette par simple pression :

## 2.3 Disposer les composants
Visser le raspberry, la caméra et le servomoteur à leurs supports respectifs avec des vis de taille adaptées.

La breadboard se fixe grace à sa bande adhésive sur la face gauche du boitier. Les câbles peuvent être fixés avec du scotch d'électricien, de la colle chaude, de la patafix pour éviter qu'il ne gènent la fermeture.

Voici la disposition finale pour optimiser le passage des câbles et la fermeture du boitier.

<img src="https://user-images.githubusercontent.com/93132152/177155317-2e7abd36-11fe-4593-95f9-a53e407cbca0.png" width=20% height=20%>

# 3. Fixer le boitier
Dans le cas d'une installation en vigne, le plus simple est de se servir des piquets de palissage en place et des trous disponible. Une seule fixation en point haut du boitier suffit. Dans notre cas, le boitier repose contre le palissage en partie basse à l'aide d'une vis. La photo ci-dessous le montre bien :

<img src="https://user-images.githubusercontent.com/93132152/177156635-e237a4aa-b2d8-4435-810d-a5f9378548d6.png" width=20% height=20%>

En cas de vibration, le boitier retombe le long du piquet dans la même position. Cette technique permet surtout de ne pas avoir à percer un trou dans le palissage (ce qui pourrait être un bonne solution également).

# 4. Démarrer l'Agrocam et fermer le boitier
Une fois l'arduino mis sous tension, l'Agrocam est démarrée. Cependant il peut être nécessaire de la démarrer à la main pour prendre une photo et vérifier le cadrage. Pour cela appuyer sur le bouton "reset" de l'arduino et refermer le couvercle (voir vidéo ci-dessous). Cette étape peut être compliquée, le boitier doit être refermé avant que l'acquisition de photo ne démarre (environ 30 secondes).

![giffermeture](https://user-images.githubusercontent.com/93132152/177158643-3b7930db-b18a-4ef6-adc9-c8a81a75e403.gif)

L'Agrocam fonctionne et prend des photo régulièrement (en fonction du paramétrage de l'arduino, 8h par défaut)

![gif agrocam](https://user-images.githubusercontent.com/93132152/177159419-08baae95-1023-4ff4-9a43-09a855c19ae0.gif)

