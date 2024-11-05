Ce Readme vous accompagne sur les étapes à accomplir pour paramétrer le Raspberry et la carte Witty Pi 4. 

Vous devriez avoir le matériel suivant : 

<img src="https://user-images.githubusercontent.com/93132152/190139861-a0678fe1-11a7-469f-9545-627c0b963aad.png" width=30% height=30%>

Pour commencez ce tutoriel et si vous souhaitez envoyer vos images sur agrocam.agroti.org afin de les visualiser vous devez déclarer votre Agrocam. Pour l'instant, il n'y a pas de procédure automatisée pour la déclaration de votre Agrocam. Il faudra donc envoyer un mail à basile.ploteau@supagro.fr en indiquant que vous souhaitez créer une Agrocam. Il vous renverra une chaine de 8 caractères qui sera le nom de votre Agrocam ainsi que le fichiers credentials.py utile dans la suite du tutoriel. Il faudra conserver ce nom car il sera utile à différents moments du tutoriel.

# 1. Préparer le dongle 4G
## 1.1. La carte SIM
Pour fonctionner de manière connectée l'Agrocam a besoin de connexion Wifi. Dans ce tutoriel vous suiverez des étapes qui permettent d'intégrer une clé 4G dans l'Agrocam qui produit directement un réseau Wifi. Pour fonctionner, cette clé 4G a besoin d'une carte SIM (les mêmes qu'il y a dans les téléphones). Un forfait de 5 Go/mois sera largement suffisant pour envoyer une photo par jour, il existe maintenant des forfaits abordables. Vous pouvez choisir de passer par n'importe quel opérateurs. Jusqu'à maintenant l'Agrocam a été testée avec les réseaux de Orange et de Bouygues.

## 1.2. Paramétrer le dongle 4G
Avant d'insérer la carte SIM dans le Dongle 4G, assurez vous d'avoir supprimer le code PIN. Pour retirer le code PIN de la carte SIM il faut insérer la carte dans un téléphone et se rendre dans les paramètres de ce dernier pour désactiver la sécurité.

Vous pouvez essayer d'insérer la carte SIM dans le Dongle 4G et de brancher la clé 4G à une alimentation USB. Ensuite connectez vous à votre clé 4G en wifi avec un ordinateur ou un smartphone (le nom de la clé (son SSID) et son mot de passe d'usine (souvent : "1234567890" sont indiqués sur le dos de la clé 4G). 
Vous devriez avoir accès à internet, faite une recherche sur Google pour vérifier que c'est bien le cas. Si tout fonctionne vous pouvez passer à la partie 2. Il est possible que malgré une carte SIM fonctionnelle la connection à internet ne se fasse pas. Cela est du à un problème d'APN mal configuré sur la clé 4G.
Pour modifier les paramètres d'APN vous devrez :

- Vous connecter au réseau Wifi du dongle 4G avec votre PC
- Vous connecter à l'interface de paramétrage du dongle. Pour cela vous devez taper dans un navigateur quelconque l'adresse IP locale de votre Dongle. Elle est souvent indiquée au dos du Dongle et ressembe à quelque chose comme : 192.168.100.1
- Le dongle vous demande des identifiants, par défaut Username : "admin" et Password : "admin"

<img src="https://github.com/user-attachments/assets/52e9c820-1c3b-47da-aa35-3775949c7060" width=30% height=30%>

- Une fois connecté vous pouvez aller dans Advanced>APN Setting

<img src="https://github.com/user-attachments/assets/2017d0d3-d322-47d1-9a12-6fb6dc42b77a" width=30% height=30%>

- Vous cochez "profile 1" à la place de "default". Ensuite le remplissage du formulaire dépend de chaque opérateur. En général chez Orange il n'y a qu'un seul APN donc rarement des problèmes mais chez leur concurents il faut souvent tester différents APN. Voici les paramètres qui ont fonctionné pour une carte SIM Bouygues. Attention l'APN peut différer en fonction du forfait que vous avez pris.

<img src="https://github.com/user-attachments/assets/11915d70-7c86-4cdb-b7a4-5b80e9e11013" width=30% height=30%>

- Une fois le formulaire créé cliquez sur "Save Configuration" puis "Execute"
- Attendez quelques secondes, ouvrez un nouvel onglet et faite une recherche pour vérifier si vous êtes bien connecté.

# 2. Préparer le Raspberry Pi Zero 
## 2.2. Initialiser le Raspberry Pi Zero
- Installer Raspberry Pi imager https://www.raspberrypi.com/software/
- Ouvrir Raspberry Pi imager
- Insérer la carte SD du raspberry dans le PC
- La fenêtre suivante s'affiche. Il faut passer dans les 3 menus pour préparer l'écriture de l'image sur le raspberry
<img src="https://github.com/Mobilab-AgroTIC/Agrocam/assets/93132152/0d2109b7-a593-48bd-8a5c-4dd2083974d9" width=30% height=30%>

1. Sélectionner le modèle du Raspberry **Raspberry pi zero**
2. Sélectionner l'OS **Raspberry Pi OS Lite (32-bit)**
3. Sélectionner l'espace de stockage correspondant à la carte SD

- Puis en cliquant sur **Suivant** un message demande si vous souhaitez modifier les paramètres. Cliquez sur **Modifier réglages**, une fenêtre s'ouvre:

<img src="https://github.com/user-attachments/assets/c243cdb7-8e18-4eb2-b4d8-86c56330bb69" width=30% height=30%>

- **Dans General** : Vous pouvez indiquer un nom d'utilisateur et un mot de passe pour votre Raspberry, vous pouvez conserver "pi" pour les deux. Vous pouvez aussi donner comme mot de passe la chaine de 8 caractères qui vous a été attribué lors de la déclaration de l'Agrocam sur le serveur, cela sécurisera votre raspberry s'il devait tomber entre de mauvaises mains.
- **Dans General** : Définir les paramètres Wifi (SSID, Password, pays (FR)) du dongle 4G. Bien penser à vérifier que le "pays Wifi" est en "FR"
- **Dans Service** : Activez le SSH et sélectionnez "utiliser un mot de passe pour l'authentification"

<img src="https://github.com/user-attachments/assets/34c68aef-dbbf-4c92-9d02-3b70c565d704" width=30% height=30%>

4. Cliquez sur **enregistrer** puis sur **Oui** puis une dernière fois sur **Oui**
5. L'écriture peut prendre du temps, n'hésitez pas à faire les installations de la partie 2.3 en attendant

## 2.3. Installer les logiciels pour la suite
- Installer [WinSCP](https://winscp.net/eng/download.php) sur votre PC. Ce logiciel permet de se connecter au raspberry en SSH, de parcourir ses fichier et d'interagir avec le terminal de commandes.
- Installer [Network analyzer](https://play.google.com/store/apps/details?id=net.techet.netanalyzerlite.an&hl=fr&gl=US) sur votre smartphone. Cette application permet de scaner un réseau wifi et de trouver les appareils (leur adresse IP) qui y sont connectés.

## 2.4. Réaliser les branchements
- Insérer la carte SD dans le raspberry
- Brancher la Picam. Attention au sens de branchement de la nappe de cable _(cf. photo ci-dessous)_. Attention les connecteurs sont fragiles, à manipuler avec précautions.
<img src="https://www.raspberrypi.com/app/uploads/2016/05/2016-05-15-16.32.19-768x576.jpg" width=20% height=20%>

- Brancher le dongle 4G au Raspberry sur le port **"USB"** _cf. photo ci-dessous_ _Par la suite il est possible que le dongle se déconnecte de temps à autre, ce qui va poser problème. Cela est du au Raspberry qui en fonction des modèle de dongle 4G ne fournit pas une intensité suffisante. Si cela se présente, veuillez brancher le dongle sur une autre source de courant par exemple un chargeur rapide 2 ampères de téléphone portable_
- Brancher l'alimentation sur le port **"PWR IN"** _cf. photo ci-dessous_
<img src="https://user-images.githubusercontent.com/93132152/169502193-72963340-17c8-46ee-b322-8d32348ea31f.png"  width=30% height=30%>

## 1.5. Se connecter au Raspberry depuis un PC

- Connecter un smartphone au réseau du dongle 4G (avec SSID et mot de passe précédemment paramétrés)
- Avec l'application mobile Network Analyzer cliquer sur "Scan" et identifier l'adresse IP du raspberry Pi:
<img src="https://user-images.githubusercontent.com/93132152/170043338-0604e7d1-208b-4c6d-9920-a58e33a77620.png"  width=20% height=20%>

- Sur PC, ouvrir WinSCP et créer une nouvelle session de connexion au Raspberry <img src="https://user-images.githubusercontent.com/93132152/170044340-fa6d77ba-f569-444e-ae02-0d12b61ad0e1.png"  width=10% height=10%>. Saisir les informations suivantes : Protocole de fichier : **SFTP**; Nom d'hôte : **IP obtenue sur Network analyzer**; Nom d'utilisateur : **pi** (sauf changement); Mot de passe : **défini partie 2**
- Depuis WinSCP ouvrir Putty <img src="https://user-images.githubusercontent.com/93132152/170045029-048df6d8-c55e-4bcc-b4fd-a2b8707ec859.png"  width=2% height=2%>
- Un terminal de commande s'ouvre et vous demande un mot de passe. Il s'agit toujours du même défini à la partie 2. Le mot de passe ne s'affiche pas mais appuyer su r "entrer" et ça marche.

## 2.6. Installer les librairies 

### 2.6.1 Installer smbus
```
sudo apt-get install python3-pip
pip install smbus
```

### 2.6.2 Activer le bus I2C (à vérifier si necessaire)
Ouvrir les paramètres ```sudo raspi-config``` puis suivre les étapes :```3 Interface Options/I2C/YES/Finish```
  
# 3 Ajouter les fichiers sur le raspberry pi
Cette opération peut se faire depuis WinSCP en glissant et déposant les fichiers
## 3.1 Créer le répertoire pour les photo (à vérifier si necessaire)
```
sudo mkdir Agrocam
```
## 3.2 Choisir votre fréquence d'allumage
Vous avez normalement reçu un fichier "credentials.py" de la part de Basile Ploteau lorsque vous avez demandez la création de votre Agrocam. Ouvrez ce fichier avec n'importe quel editeur de text comme Notepad++ ou un simple bloc note. Il y a une liste qui s'appelle ```trigger_times``` et qui contient les heures (GMT) à laquelle vous souhaitez que l'Agrocam se déclenche. Par exemple ```trigger_times=[time(6,30,00),time(8,40,00),time(12,0,0)]``` déclenchera une acquisition de photo à 6:30:00, 8:40:00 et 12:00:00; ```trigger_times=[time(12,0,0)]``` déclenchera une acquisition de photo à 12:00:00.

## 3.3 Ajouter les fichiers
Depuis l'interface de WinSCP déplasser les fichiers suivants. Le fichier agrocam.py se trouve sur ce repertoire Github. Le fichier credentials.py vous a été envoyé par Basile Ploteau.
- Glisser déposer agrocam.py dans /home/pi
- Glisser déposer credentials.py dans /home/pi
Donner tous les droits au script _(première ligne ci-dessous)_ et effacer les "\r" et "r" de fin de ligne _(2e ligne ci-dessous, cela n'est pas toujours nécessaire mais ces caractère spéciaux on pu être ajouté si le script a été édité sur un outil Windows, Visual Studio Code par exemple)_
```
chmod 644 Agrocam
sed -i -e 's/\r$//' agrocam.py
sed -i -e 's/\r$//' credentials.py
```
**NB :** Le script agrocam.py envoie la commande ```sudo shutdown -h now``` à la fin de son exécution ce qui éteint l'Agrocam. Pour débugger le script (c'est-à-dire reprendre la main dessus) il est recommandé de commenter cette ligne _cf. partie 7_

# 4. Programmer l'allumage de l'Agrocam avec la carte WittyPi
## 4.1 Installer WittyPi
Installer WittyPi avec les lignes de commandes suivantes.
```
wget http://www.uugear.com/repo/WittyPi4/install.sh
sudo sh install.sh
```
Puis éteindre le raspberry avec ```sudo shutdown -h now``` puis passer à l'étape d'après.
Une fois le raspberry éteint, débrancher l'alimentation électrique.

## 4.2 Connecter la carte WittyPi 4 au Raspberry
Insérer une pile 3V (si possible rechargeable et fourni avec la carte WittyPi 3) dans l'emplacement prévu à cette effet sur la carte Witty Pi

Les broches s'emboitent de la manière suivante.

<img src="https://user-images.githubusercontent.com/93132152/197517482-6a5a1459-3894-4c51-946a-7dcf6b49754d.jpg" width=30% height=30%>


## 4.3 Paramétrer le WittyPi
Brancher l'alimentation électrique directement sur la carte Witty Pi 4(l'alimentation du raspberry a été débranché en 3.1), c'est cette carte qui va ensuite gérer l'alimentation du raspberry. Pour que le raspberry démarre (en attendant qu'on lui donne un planing de mise en route), il faut appuyer sur le bouton poussoir de la carte Witty Pi. Lors de cette première mise en route, il est possible que le Dongle 4G ne s'allume pas. Il suffit de le débrancher et rebrancher.

<img src="https://user-images.githubusercontent.com/93132152/197518071-94065c91-ed4a-4cee-8cfb-99ead7fd86a6.jpg" width=30% height=30%>

Se connecter au Raspberry comme dans la partie 1.5, ouvrir le terminal de commande et démarrer WittyPi avec la commande suivante :
```
sudo ./wittypi/wittyPi.sh
```
Une liste de paramètre et de fonctionnalités s'affichent. Dans l'ordre nous allons procéder ainsi :
1. ```3.Synchronize time``` taper 3 et entrer
2. ```7. Set low voltage threshold``` taper 7 et entrer puis saisir 7V et entrer
3. ```8. Set recovery voltage threshold``` taper 8 et entrer puis saisir 0 et entrer (sinon quand on change la batterie la camera pourrait redemarrer)
4. ```11. View/change other settings...``` taper 11 et entrer. Ensuite suivre les instructions pour chaque paramètre. Attention lorsqu'un paramètre est validé on revient au menu initial, il faut donc revenir dans ```11. View/change other settings...```

| Paramètre  | Valeur |
| ------------- | ------------- |
| Default state when powered  | OFF  |
| Power cut delay after shutdown  | Inchangé  |
| Pulsing interval during sleep  | 20 |
| White LED duration  | 0  |
| Dummy load duration  | 0  |
| Vin adjustment | Inchangé  |
| Vout adjustment  | Inchangé  |
| Iout adjustment  | Inchangé  |

6. ```13. Exit``` taper 13 et entrer

# 5 Démarrer le script au reboot avec systemd
Pour l'instant, si vous éteignez et rallumez votre raspberry il ne se passera rien. Pour que l'Agrocam prenne une photo lorsqu'elle démarre, il faut le lui indiquer en suivant ces étapes.
```
sudo nano /lib/systemd/system/agrocam.service
```

Le fichier agrocam.service s'ouvre, pour l'instant il est vide. Il faut donc coller ce qui suit dedans :

```
[Unit]
Description=My Script Service
After=multi-user.target

[Service]
Type=idle
ExecStart=/usr/bin/python3 /home/pi/agrocam.py > /home/pi/myscript.log 2>&1
WorkingDirectory=/home/pi
User=pi

[Install]
WantedBy=multi-user.target
```

Puis on quitte le mode édition avec Ctrl+X puis on accepte en tapant "y" puis "entrée"

```
sudo chmod 644 /lib/systemd/system/agrocam.service

sudo systemctl daemon-reload
sudo systemctl enable agrocam.service
```

Si vous souhaitez savoir quel est l'état de votre service :
```
sudo systemctl status agrocam.service
```
Enfin éteindre l'Agrocam avec : ```sudo shutdown -h now```


# 6 Finaliser les branchements
- Brancher le servo moteur sur les broches du WittyPi. Le fil rouge du servo est relié à une **broche 5V**, le fil noir à une **broche GND**, et le fil restant (blanc, jaune) à la **broche GPIO 18** _cf.figures ci-dessous_
- Connecter les **broches GPIO 24 et GND** à l'aide d'un [cavalier](https://fr.rs-online.com/web/p/cavaliers-et-shunts/2518682?cm_mmc=FR-PLA-DS3A-_-google-_-CSS_FR_FR_Connecteurs_Whoop-_-(FR:Whoop!)+Cavaliers+et+Shunts+(2)-_-2518682&matchtype=&pla-321137858785&gclid=Cj0KCQjwhLKUBhDiARIsAMaTLnFPSjXNxxk7wiwrSQBFsIqT5VfPuMc_Ay4DvPVhzphmNF9wRRBNoIkaAl6-EALw_wcB&gclsrc=aw.ds)_(cf.figures ci-dessous_). Dans cette position l'Agrocam fonctionnera normalement, c'est à dire qu'elle s'éteindra après avoir pris une photo. Pour empêcher cela on peut basculer le cavalier entre la **broche 3,3V** et la **broche GPIO 24** ainsi l'Agrocam ne s'éteint pas et il est possible d'en prendre le contrôle (partie 7).

<img src="https://user-images.githubusercontent.com/93132152/170041886-8d5a046a-65c0-40ad-a286-e73cacb53113.png" width=20% height=20%>   <img src="https://user-images.githubusercontent.com/93132152/197519706-921a3b5f-f67a-4390-966c-3d595dfbf825.jpg" width=30% height=30%>

# 7 Demarrer l'Agrocam
## 7.1 Passer sur l'alimentation batterie
Insérer deux cellules Lithium 3,7V dans le boitier de pile et connecter le boitier à l'aide d'un connecteur JST à la carte WittyPi (Attention à la polarité). Si votre boitier n'a pas de connecteur (uniquement des fils dénudés), de nombreuses ressources sont disponibles en ligne ou dans le Fablab le plus proche de chez vous pour apprendre à faire ces connectiques.

Voici le montage que vous devriez obtenir

<img src="https://user-images.githubusercontent.com/93132152/197561986-99a13911-00bd-4a40-ad8d-847a19d2ca52.jpg" width=30% height=30%><img src="https://user-images.githubusercontent.com/93132152/197562094-93a74b95-9b66-4f5f-930a-35c74eec1e54.jpg" width=30% height=30%>


## 7.2 Relancer l'Agrocam
Pour relancer l'Agrocam, appuyer sur le bouton poussoir : elle devrait s'allumer, actionner le servomoteur, prendre une photo, réactionner le servomoteur, envoyer la photo sur le serveur et enfin s'éteindre.

# 8 Debugger l'Agrocam
Le script ```agrocam.py``` éteint l'Agrocam à la fin de son exécution, une fois cette partie 1 terminée il serait donc impossible de se connecter au raspberry en SSH car le script ```agrocam.py``` est lancé à chaque démarrage _(cf. partie 1.8)_. La solution consiste donc à empêcher que le script n'aille jusqu'au bout lorsqu'on le désire. Pour celà il y a une boucle en python à la fin du script qui tourne indéfiniement si le port GPIO 24 est "TRUE" donc connecté au 3,3V **(à l'aide du cavalier)**:
```
i=1
while (GPIO.input(controlPin) == 1) :
	time.sleep(5)
	print("ControlPin is not LOW. i = ", i)
	i += 1
```
Ci-dessous la position du cavalier pour que le script n'éteigne pas l'Agrocam à la fin de son exécution :
<img src="https://user-images.githubusercontent.com/93132152/197520127-1235e3c9-2c6c-40fe-a818-20d08dc6f98e.jpg" width=30% height=30%>


## 2.4 Tester l'Agrocam
Une fois ces étapes terminées. Eteindre l'Agrocam ```sudo shutdown -h now ``` puis repositionner le cavalier en position initiale.
Vous pouvez débrancher l'alimentation et connecter les cellules Li-ion comme sur la photo ci-dessous. Cette [vidéo](https://www.youtube.com/watch?v=nqwYTafg8Z0) vous explique comment réaliser la connectique mâle du XH2.54 sur les fils du boitier d'alimentation.


<img src="https://user-images.githubusercontent.com/93132152/190140109-795cd432-3d9a-4398-b5f2-6af661773ff9.png" width=30% height=30%>


Enfin pour tester le cadrage vous pouvez appuyer à n'importe quel moment sur le bouton poussoir de la Witty Pi 4 pour faire une photo. La caméra démarrera automatiquement à l'heure prédéfinie.
