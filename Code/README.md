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

- Sélectionner l'espace de stockage correspondant à la carte SD et sélectionner l'OS : **Raspberry Pi OS Lite (32-bit)**
<img src="https://user-images.githubusercontent.com/93132152/169273540-02b78e90-f551-4a8f-ac33-b90f7be4cffa.png" width=30% height=30%>  <img src="https://user-images.githubusercontent.com/93132152/169275055-28434132-3a4c-42e0-8752-84e8525d4922.png" width=30% height=30%>

- Dans les paramètres <img src="https://user-images.githubusercontent.com/93132152/169275716-50c48613-8d7e-4b10-8681-f49c881cf00c.png" width=4% height=4%>:
    - Activer le SSH
    - Définir un mot de passe pour le Raspberry et un nom d'utilisateur (conserver "pi")
    - Définir les paramètres Wifi (SSID, Password, pays (FR)) du dongle 4G. ** Bien penser à modifier le paramètre Wireless LAN country avec "FR"**
<img src="https://user-images.githubusercontent.com/93132152/169276815-ce32ffe7-997c-40b8-b6e8-bc613ae2f673.png" width=30% height=30%>
- Cliquer sur "save" puis sur "écrire"
- L'écriture peut prendre du temps, n'hésitez pas à faire les installations de la partie 3 en attendant

## 1.3. Installer les logiciels pour la suite
- Installer [WinSCP](https://winscp.net/eng/download.php) sur votre PC. Ce logiciel permet de se connecter au raspberry en SSH, de parcourir ses fichier et d'interagir avec le terminal de commandes.
- Installer [Network analyzer](https://play.google.com/store/apps/details?id=net.techet.netanalyzerlite.an&hl=fr&gl=US) sur votre smartphone. Cette application permet de scaner un réseau wifi et de trouver les appareils (leur adresse IP) qui y sont connectés.

## 1.4. Réaliser les branchements
- Insérer la carte SD dans le raspberry
- Brancher la Picam. Attention au sens de branchement de la nappe de cable _(cf. photo ci-dessous)_. Attention les connecteurs sont fragiles, à manipuler avec précautions.
<img src="https://www.raspberrypi.com/app/uploads/2016/05/2016-05-15-16.32.19-768x576.jpg" width=20% height=20%>

- Brancher le dongle 4G au Raspberry sur le port **"USB"** _cf. photo ci-dessous_
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
Les parties ci-dessous ne sont pas nécessaires mais il est possible que si le reste ne fonctionne pas, le problème vienne de là.

**Si le servomoteur ne marche pas**, les GPIO ne sont peut-être pas activés. Ouvrir les paramètres ```sudo raspi-config``` puis suivre les étapes :```3 Interface Options/RemoteGPIO/YES/Finish/RebootYes``` A priori pas besoin de ça

### 1.6.1 Installer git 
```
sudo apt-get install git
```
### 1.6.2 Installer WiringPi
```
git clone https://github.com/WiringPi/WiringPi.git
cd WiringPi
git pull origin
./build
cd ..
```
### 1.6.3 Installer pip et python-dotenv
Cela peut prendre un peu de temps 
```
sudo apt-get install python3-pip
pip install python-dotenv
sudo cp -R /home/pi/.local/lib/python3.9/site-packages/dotenv /usr/lib/python3.9 
```
*On déplace la librairie pour qu'elle soit trouvée en démarrage automatique*

### 1.6.4 Installer smbus
```
pip install smbus
sudo cp -R /home/pi/.local/lib/python3.9/site-packages/smbus.cpython-39-arm-linux-gnueabihf.so /usr/lib/python3.9
sudo cp -R /home/pi/.local/lib/python3.9/site-packages/smbus-1.1.post2.dist-info/ /usr/lib/python3.9
```
*On déplace la librairie pour qu'elle soit trouvée en démarrage automatique*

### 1.6.5 Activer le bus I2C
Ouvrir les paramètres ```sudo raspi-config``` puis suivre les étapes :```3 Interface Options/I2C/YES/Finish```

# 2. Programmer l'allumage de l'Agrocam avec la carte WittyPi
A partir de cette étape, cette branche diffère fortement de la branche main. On va pouvoir paramétrer l'allumage du raspberry grâce à la carte Witty Pi 3

## 2.1 Installer WittyPi
Installer WittyPi avec les lignes de commandes suivantes.
```
wget http://www.uugear.com/repo/WittyPi3/install.sh
sudo sh install.sh
```
Puis éteindre le raspberry avec ```sudo shutdown -h now``` puis passer à l'étape d'après.
Une fois le raspberry éteint, débrancher l'alimentation électrique.

## 2.2 Connecter la carte WittyPi 3 au Raspberry
Insérer une pile 3V (si possible rechargeable et fourni avec la carte WittyPi 3) dans l'emplacement prévu à cette effet sur la carte Witty Pi

Les broches s'emboitent de la manière suivante.

<img src="https://user-images.githubusercontent.com/93132152/197517482-6a5a1459-3894-4c51-946a-7dcf6b49754d.jpg" width=30% height=30%>

## 2.3 Paramétrer le WittyPi
Brancher l'alimentation électrique directement sur la carte Witty Pi (l'alimentation du raspberry a été débranché en 2.1), c'est cette carte qui va ensuite gérer l'alimentation du raspberry. Pour que le raspberry démarre (en attendant qu'on lui donne un planing de mise en route), il faut appuyer sur le bouton poussoir de la carte Witty Pi. Lors de cette première mise en route, il est possible que le Dongle 4G ne s'allume pas. Il suffit de le débrancher et rebrancher.

<img src="https://user-images.githubusercontent.com/93132152/197518071-94065c91-ed4a-4cee-8cfb-99ead7fd86a6.jpg" width=30% height=30%>

Se connecter au Raspberry comme dans la partie 1.5, ouvrir le terminal de commande et démarrer WittyPi avec la commande suivante :
```
sudo ./wittypi/wittyPi.sh
```
Une liste de paramètre et de fonctionnalités s'affichent. Dans l'ordre nous allons procéder ainsi :
1. ```3.Synchronize time``` taper 3 et entrer
2. ```7. Set low voltage threshold``` taper 7 et entrer puis saisir 6,5V et entrer
3. ```9. View/change other settings...``` taper 9 et entrer. Ensuite suivre les instructions pour chaque paramètre. Attention lorsqu'un paramètre est validé on revient au menu initial, il faut donc revenir dans ```9. View/change other settings...```

| Paramètre  | Valeur |
| ------------- | ------------- |
| Default state when powered  | OFF  |
| Power cut delay after shutdown  | Inchangé  |
| Pulsing interval during sleep  | 8  |
| White LED duration  | 0  |
| Dummy load duration  | 0  |
| Vin adjustment | Inchangé  |
| Vout adjustment  | Inchangé  |
| Iout adjustment  | Inchangé  |

4. ```5. Schedule next startup``` taper 5 et entrer. Ensuite taper la chaine de caractère correspondant à votre fréquence d'acquisition. Exemple ```?? 12:00:00``` pour déclencher tous les jours à midi ou ```?? ??:15:00``` pour tous les jours et toutes les heures à la 15e minute. Pour faire plusieurs démarrages en une journée il faudra faire un paramétrage plus complexe. Voir le [guide d'utilisateur](https://www.uugear.com/doc/WittyPi3_UserManual.pdf) de la carte qui est très bien fait.

5. ```11. Exit``` taper 11 et entrer

## 2.4 Récupérer l'adresse I2C de la carte WittyPi
Cette adresse est nécessaire pour la lecture de la tension de la batterie. Pour obtenir l'adresse, saisir la commande suivante :

```
i2cdetect -y 1
```

Il n'y a qu'une seule adresse qui est détectée, c'est celle du WittyPi, ici c'est l'adresse 0x08 :
```
0  1  2  3  4  5  6  7  8  9  a  b  c  d  e  f
00:                         08 -- -- -- -- -- -- --
10: -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- --
20: -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- --
30: -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- --
40: -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- --
50: -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- --
60: -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- --
70: -- -- -- -- -- -- -- --
```

# 3 Finaliser les branchements
- Brancher le servo moteur sur les broches du WittyPi. Le fil rouge du servo est relié à une **broche 5V**, le fil noir à une **broche GND**, et le fil restant (blanc, jaune) à la **broche GPIO 18** _cf.figures ci-dessous_
- Connecter les **broches GPIO 24 et GND** à l'aide d'un [cavalier](https://fr.rs-online.com/web/p/cavaliers-et-shunts/2518682?cm_mmc=FR-PLA-DS3A-_-google-_-CSS_FR_FR_Connecteurs_Whoop-_-(FR:Whoop!)+Cavaliers+et+Shunts+(2)-_-2518682&matchtype=&pla-321137858785&gclid=Cj0KCQjwhLKUBhDiARIsAMaTLnFPSjXNxxk7wiwrSQBFsIqT5VfPuMc_Ay4DvPVhzphmNF9wRRBNoIkaAl6-EALw_wcB&gclsrc=aw.ds)_(cf.figures ci-dessous_). Dans cette position l'Agrocam fonctionnera normalement, c'est à dire qu'elle s'éteindra après avoir pris une photo. Pour empêcher cela on peut basculer le cavalier entre la **broche 3,3V** et la **broche GPIO 24** ainsi l'Agrocam ne s'éteint pas et il est possible d'en prendre le contrôle (partie 7).

<img src="https://user-images.githubusercontent.com/93132152/170041886-8d5a046a-65c0-40ad-a286-e73cacb53113.png" width=20% height=20%>   <img src="https://user-images.githubusercontent.com/93132152/197519706-921a3b5f-f67a-4390-966c-3d595dfbf825.jpg" width=30% height=30%>


# 4 Ajouter les fichiers sur le raspberry pi
Cette opération peut se faire depuis WinSCP en glissant et déposant les fichiers
## 4.1 Le script de l'Agrocam
Glisser déposer Agrocam_raspberry.sh dans /home/pi

Donner tous les droits au script _(première ligne ci-dessous)_ et effacer les "\r" et "r" de fin de ligne _(2e ligne ci-dessous, cela n'est pas toujours nécessaire mais ces caractère spéciaux on pu être ajouté si le script a été édité sur un outil Windows, Visual Studio Code par exemple)_
```
chmod 777 Agrocam_raspberry.sh
sed -i -e 's/\r$//' Agrocam_raspberry.sh
```
**Attention :** Le script Agrocam_raspberry.sh contient ```sudo shutdown -h now``` à la fin qui éteint l'Agrocam. Pour débugger le script (c'est-à-dire reprendre la main dessus) il est recommandé de commenter cette ligne _cf. partie 7_

## 4.2 Les variables d'environnement
Maintenant on va déposer dans un fichier séparé du script les variables qui permettent de se connecter au serveur FTP où seront envoyées et stockées les photos.

Depuis WinSCP, glisser déposer .env dans ```/home/pi``` une fois modifié avec les informations pertinentes entre les "" (hostname,user,password) et la valeur de I2CAdress. Ce fichier contient les informations d'authentification pour accéder au serveur FTP sur lequel les photos seront sauvegardées. Ce fichier contient également l'adrese I2C de la carte WittyPi (obtenu en 2.4), cette variable est un entier. Par exemple si le port I2C est 0x08, taper simplement ```I2CAdress=8```. Attention le fichier peut être caché.

Le fichier peut aussi être crée depuis le terminal :
```
touch .env
sudo nano .env
```
Contenu de .env
```
hostname = ""
user = ""
password =""
I2CAdress=
```

# 5 Démarrer le script au reboot
Cette partie permet de démarrer le script ```Agrocam_raspberry.sh``` au démarrage. Attention, le script éteint le raspberry à la fin de son exécution. Cette extinction n'a pas lieu si ```controlPin==1```, il faut donc brancher le GPIO 24 au 3,3v pour que l'Agrocam reste allumée _cf. partie 7._

Ouvrir le crontab 
```
sudo crontab -e
```
Puis sélectionner ```1. /bin/nano``` en tapant ```1```
Ajouter une ligne à la fin du crontab :
```
@reboot sudo /home/pi/Agrocam_raspberry.sh 
```
Ajouter ```>> /var/log/Agrocam.log 2>&1``` à la ligne précédente pour créer un fichier de log pour débugger

Enfin éteindre l'Agrocam avec : ```sudo shutdown -h now```

# 6 Demarrer l'Agrocam
## 6.1 Passer sur l'alimentation batterie
Insérer deux cellules Lithium 3,7V dans le boitier de pile et connecter le boitier à l'aide d'un connecteur JST à la carte WittyPi (Attention à la polarité). Si votre boitier n'a pas de connecteur (uniquement des fils dénudés), de nombreuses ressources sont disponibles en ligne ou dans le Fablab le plus proche de chez vous pour apprendre à faire ces connectiques.

Voici le montage que vous devriez obtenir

<img src="https://user-images.githubusercontent.com/93132152/197561986-99a13911-00bd-4a40-ad8d-847a19d2ca52.jpg" width=30% height=30%><img src="https://user-images.githubusercontent.com/93132152/197562094-93a74b95-9b66-4f5f-930a-35c74eec1e54.jpg" width=30% height=30%>


## 6.2 Relancer l'Agrocam
Pour relancer l'Agrocam, appuyer sur le bouton poussoir : elle devrait s'allumer, actionner le servomoteur, prendre une photo, réactionner le servomoteur, envoyer la photo sur le serveur et enfin s'éteindre.

# 7 Debugger l'Agrocam
Le script ```Agrocam_raspberry.sh``` éteint l'Agrocam à la fin de son exécution, une fois cette partie 1 terminée il serait donc impossible de se connecter au raspberry en SSH car le script ```Agrocam_raspberry.sh``` est lancé à chaque démarrage _(cf. partie 1.8)_. La solution consiste donc à empêcher que le script n'aille jusqu'au bout lorsqu'on le désire. Pour celà il y a une boucle en python à la fin du script qui tourne indéfiniement si le port GPIO 24 est "TRUE" donc connecté au 3,3V **(à l'aide du cavalier)**:
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


Enfin pour tester le cadrage vous pouvez appuyer à n'importe quel moment sur le bouton poussoir de la Witty Pi 3 pour faire une photo. La caméra démarrera automatiquement à l'heure prédéfinie.
