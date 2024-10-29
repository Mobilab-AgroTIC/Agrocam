Ce Readme vous accompagne sur les étapes à accomplir pour paramétrer le Raspberry et la carte Witty Pi 3. 

Vous devriez avoir le matériel suivant : 

<img src="https://user-images.githubusercontent.com/93132152/190139861-a0678fe1-11a7-469f-9545-627c0b963aad.png" width=30% height=30%>

# 1. Préparer le raspberry l'Agrocam 
## 1.1. Paramétrer le dongle 4G
Avant d'insérer la carte SIM dans le Dongle 4G, assurez vous d'avoir supprimer le code PIN. Pour retirer le code PIN de la carte SIM il faut insérer la carte dans un téléphone et se rendre dans les paramètres de ce dernier pour désactiver la sécurité.

Ensuite, suivre la notice d'utilisation du dongle pour éditer son SSID et son mot de passe. Le SSID et mot de passe par défaut peuvent aussi être laissé tels quels. Ces deux informations (SSID et mot de passe) sont à conserver pour établir la connexion entre le Raspberry et le dongle par la suite.

## 1.2. Initialiser le Raspberry Pi
- Installer Raspberry Pi imager https://www.raspberrypi.com/software/
- Ouvrir Raspberry Pi imager
- Insérer la carte SD du raspberry dans le PC
- La fenêtre suivante s'affiche. Il faut passer dans les 3 menus pour préparer l'écriture de l'image sur le raspberry
<img src="https://github.com/Mobilab-AgroTIC/Agrocam/assets/93132152/0d2109b7-a593-48bd-8a5c-4dd2083974d9" width=30% height=30%>

1. Sélectionner le modèle du Raspberry **Raspberry pi zero**
2. Sélectionner l'OS **Raspberry Pi OS Lite (32-bit)**
3. Sélectionner l'espace de stockage correspondant à la carte SD


- Puis en cliquant sur **Suivant** un message demande si nous souhaitons modifier les paramètres. Cliquez sur **Modifier réglages**, une fenêtre s'ouvre:
    - Activer le SSH
    - Définir un mot de passe pour le Raspberry et un nom d'utilisateur (conserver "pi" pour les deux). Vous pouvez aussi donner comme mot de passe la chaine de 8 caractères qui vous a été attribué lors de la déclaration de l'Agrocam sur le serveur.
    - Définir les paramètres Wifi (SSID, Password, pays (FR)) du dongle 4G. ** Bien penser à modifier le paramètre Wireless LAN country avec "FR"**
<img src="https://user-images.githubusercontent.com/93132152/169276815-ce32ffe7-997c-40b8-b6e8-bc613ae2f673.png" width=30% height=30%>
- Cliquez sur **enregistrer** puis sur **Oui**
- L'écriture peut prendre du temps, n'hésitez pas à faire les installations de la partie 1.3 en attendant

## 1.3. Installer les logiciels pour la suite
- Installer [WinSCP](https://winscp.net/eng/download.php) sur votre PC. Ce logiciel permet de se connecter au raspberry en SSH, de parcourir ses fichier et d'interagir avec le terminal de commandes.
- Installer [Network analyzer](https://play.google.com/store/apps/details?id=net.techet.netanalyzerlite.an&hl=fr&gl=US) sur votre smartphone. Cette application permet de scaner un réseau wifi et de trouver les appareils (leur adresse IP) qui y sont connectés.

## 1.4. Réaliser les branchements
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

## 1.6. Installer les librairies 

### 1.6.1 Installer smbus
```
sudo apt-get install python3-pip
pip install smbus
```

### 1.6.2 Activer le bus I2C
Ouvrir les paramètres ```sudo raspi-config``` puis suivre les étapes :```3 Interface Options/I2C/YES/Finish```
  
# 2 Ajouter les fichiers sur le raspberry pi
Cette opération peut se faire depuis WinSCP en glissant et déposant les fichiers
## 2.1 Créer le répertoire pour les photo
```
sudo mkdir Agrocam
```

## 2.1 Le script de l'Agrocam
Glisser déposer agrocam.py dans /home/pi
Glisser déposer credentials.py dans /home/pi
Glisser déposer agrocam_schedule.wp dans /home/pi/wittypi/schedules
Glisser déposer sync_network_time.sh dans /home/pi/wittypi
Donner tous les droits au script _(première ligne ci-dessous)_ et effacer les "\r" et "r" de fin de ligne _(2e ligne ci-dessous, cela n'est pas toujours nécessaire mais ces caractère spéciaux on pu être ajouté si le script a été édité sur un outil Windows, Visual Studio Code par exemple)_
```
chmod 777 Agrocam
sudo chmod 777 /home/pi/wittypi/sync_network_time.sh
sed -i -e 's/\r$//' agrocam.py
sed -i -e 's/\r$//' credentials.py
sed -i -e 's/\r$//' agrocam_schedule.wpi
sed -i -e 's/\r$//' sync_network_time.sh
```
**Attention :** Le script agrocam.py envoie la commande ```sudo shutdown -h now``` à la fin qui éteint l'Agrocam. Pour débugger le script (c'est-à-dire reprendre la main dessus) il est recommandé de commenter cette ligne _cf. partie 7_

## 2.2 Les credentials
Maintenant on va déposer envoyer au Raspberry un fichier séparé du script et qui contient les variables qui permettent de se connecter au serveur FTP où seront envoyées et stockées les photos. Le fichier disponible sur le repository est donné comme exemple. Si vous souhaitez envoyer vos photos sur agrocam.agrotic.org pour les visualiser, contactez Basile Ploteau (basile.ploteau@supagro.fr) pour vous fournir un fichier credentials pour votre Agrocam.

Depuis WinSCP, glisser déposer credentials.py dans ```/home/pi```. 

# 3. Programmer l'allumage de l'Agrocam avec la carte WittyPi
A partir de cette étape, cette branche diffère fortement de la branche main. On va pouvoir paramétrer l'allumage du raspberry grâce à la carte Witty Pi 4

## 3.1 Installer WittyPi
Installer WittyPi avec les lignes de commandes suivantes.
```
wget http://www.uugear.com/repo/WittyPi4/install.sh
sudo sh install.sh
```
Puis éteindre le raspberry avec ```sudo shutdown -h now``` puis passer à l'étape d'après.
Une fois le raspberry éteint, débrancher l'alimentation électrique.

## 3.2 Connecter la carte WittyPi 4 au Raspberry
Insérer une pile 3V (si possible rechargeable et fourni avec la carte WittyPi 3) dans l'emplacement prévu à cette effet sur la carte Witty Pi

Les broches s'emboitent de la manière suivante.

<img src="https://user-images.githubusercontent.com/93132152/197517482-6a5a1459-3894-4c51-946a-7dcf6b49754d.jpg" width=30% height=30%>


## 3.4 Paramétrer le WittyPi
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

## 3.5 Verser le planning d'allumage
Pour savoir à quelle heure démarrer, la carte WittyPi a besoin du script ```agrocam_schedule.wpi```. La version disponible sur le repository permet de déclencher l'allumage du raspberry à 11h (heure d'hiver, 12h en été) chaque jour. Si vous souhaitez modifier le planning d'allumage et savoir comment modifier le script, référez vous à la [documentation de la carte WittyPi 4](https://www.uugear.com/doc/WittyPi4_UserManual.pdf).

Le script doit être déposé dans le dossier (à l'aide de WinSCP par exemple) /home/pi/wittypi/schedules.

## 3.6 Lancer le planning d'allumage
Rouvrir wittyPi ```sudo ./wittypi/wittyPi.sh```. Puis tapez 6 pour ```6. Choose schedule script```puis tapez le chiffre qui correspond au script ```agrocam_schedule.wpi``` ici c'est 1.

Maintenant il devrait être écrit la prochaine date à laquelle l'Agrocam va démarrer à la ligne 5 des paramètres de la carte WittyPi. Si vous faites l'étape précédente à 12h. L'Agrocam démarrera pour la première fois le lendemain à 12h. Si vous la faites après 12h, l'Agrocam démarrera le surlendemain à la même heure.

Une fois le script d'allumage pris en compte, le prochain allumage aura lieu que le surlendemain. Pour éviter de perde un jour de photo on peut paramétrer le prochain allumage en tapant 5 ```5. Schedule next startup```. Ici suivez ce que dit le programme pour programmer le prochain allumage. Cela devrait ressembler à XX 11:00:30 où XX est la date du prochain allumage souhaité.

Puis quittez wittyPi : ```13. Exit``` taper 13 et entrer
# 4 Démarrer le script au reboot avec systemd
```
sudo nano /lib/systemd/system/agrocam.service
```

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


# 5 Finaliser les branchements
- Brancher le servo moteur sur les broches du WittyPi. Le fil rouge du servo est relié à une **broche 5V**, le fil noir à une **broche GND**, et le fil restant (blanc, jaune) à la **broche GPIO 18** _cf.figures ci-dessous_
- Connecter les **broches GPIO 24 et GND** à l'aide d'un [cavalier](https://fr.rs-online.com/web/p/cavaliers-et-shunts/2518682?cm_mmc=FR-PLA-DS3A-_-google-_-CSS_FR_FR_Connecteurs_Whoop-_-(FR:Whoop!)+Cavaliers+et+Shunts+(2)-_-2518682&matchtype=&pla-321137858785&gclid=Cj0KCQjwhLKUBhDiARIsAMaTLnFPSjXNxxk7wiwrSQBFsIqT5VfPuMc_Ay4DvPVhzphmNF9wRRBNoIkaAl6-EALw_wcB&gclsrc=aw.ds)_(cf.figures ci-dessous_). Dans cette position l'Agrocam fonctionnera normalement, c'est à dire qu'elle s'éteindra après avoir pris une photo. Pour empêcher cela on peut basculer le cavalier entre la **broche 3,3V** et la **broche GPIO 24** ainsi l'Agrocam ne s'éteint pas et il est possible d'en prendre le contrôle (partie 7).

<img src="https://user-images.githubusercontent.com/93132152/170041886-8d5a046a-65c0-40ad-a286-e73cacb53113.png" width=20% height=20%>   <img src="https://user-images.githubusercontent.com/93132152/197519706-921a3b5f-f67a-4390-966c-3d595dfbf825.jpg" width=30% height=30%>

# 6 Demarrer l'Agrocam
## 6.1 Passer sur l'alimentation batterie
Insérer deux cellules Lithium 3,7V dans le boitier de pile et connecter le boitier à l'aide d'un connecteur JST à la carte WittyPi (Attention à la polarité). Si votre boitier n'a pas de connecteur (uniquement des fils dénudés), de nombreuses ressources sont disponibles en ligne ou dans le Fablab le plus proche de chez vous pour apprendre à faire ces connectiques.

Voici le montage que vous devriez obtenir

<img src="https://user-images.githubusercontent.com/93132152/197561986-99a13911-00bd-4a40-ad8d-847a19d2ca52.jpg" width=30% height=30%><img src="https://user-images.githubusercontent.com/93132152/197562094-93a74b95-9b66-4f5f-930a-35c74eec1e54.jpg" width=30% height=30%>


## 6.2 Relancer l'Agrocam
Pour relancer l'Agrocam, appuyer sur le bouton poussoir : elle devrait s'allumer, actionner le servomoteur, prendre une photo, réactionner le servomoteur, envoyer la photo sur le serveur et enfin s'éteindre.

# 7 Debugger l'Agrocam
Le script ```agrocam.py``` éteint l'Agrocam à la fin de son exécution, une fois cette partie 1 terminée il serait donc impossible de se connecter au raspberry en SSH car le script ```agrocam.py``` est lancé à chaque démarrage _(cf. partie 1.8)_. La solution consiste donc à empêcher que le script n'aille jusqu'au bout lorsqu'on le désire. Pour celà il y a une boucle en python à la fin du script qui tourne indéfiniement si le port GPIO 24 est "TRUE" donc connecté au 3,3V **(à l'aide du cavalier)**:
```
python << END_OF_PYTHON
import time
import RPi.GPIO as GPIO
controlPin=24
GPIO.setmode(GPIO.BCM)
GPIO.setup(controlPin, GPIO.IN)
i=1
while (GPIO.input(controlPin) == 1) :
	time.sleep(5)
	print("ControlPin is not LOW. i = ", i)
	i += 1
END_OF_PYTHON
```
Ci-dessous la position du cavalier pour que le script n'éteigne pas l'Agrocam à la fin de son exécution :
<img src="https://user-images.githubusercontent.com/93132152/197520127-1235e3c9-2c6c-40fe-a818-20d08dc6f98e.jpg" width=30% height=30%>


## 2.4 Tester l'Agrocam
Une fois ces étapes terminées. Eteindre l'Agrocam ```sudo shutdown -h now ``` puis repositionner le cavalier en position initiale.
Vous pouvez débrancher l'alimentation et connecter les cellules Li-ion comme sur la photo ci-dessous. Cette [vidéo](https://www.youtube.com/watch?v=nqwYTafg8Z0) vous explique comment réaliser la connectique mâle du XH2.54 sur les fils du boitier d'alimentation.


<img src="https://user-images.githubusercontent.com/93132152/190140109-795cd432-3d9a-4398-b5f2-6af661773ff9.png" width=30% height=30%>


Enfin pour tester le cadrage vous pouvez appuyer à n'importe quel moment sur le bouton poussoir de la Witty Pi 4 pour faire une photo. La caméra démarrera automatiquement à l'heure prédéfinie.
