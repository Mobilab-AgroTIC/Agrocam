Ce Readme vous accompagne sur les étapes à accomplir pour paramétrer le Raspberry et l'Arduino promini 3,3 V. Le tutoriel est découpé en 3 grandes étapes : 

**1. Programmer l'Agrocam**

**2. Programmer l'allumage de l'Agrocam**

**3. Réaliser le montage électronique**

# 1. Programmer l'Agrocam 
## 1.1. Paramétrer le dongle 4G
Suivre la notice d'utilisation du dongle pour éditer son SSID et son mot de passe. Ces deux informations sont à conserver pour établir la connexion entre le Raspberry et le dongle.
## 1.2. Initialiser le Raspberry Pi
- Installer Raspberry Pi imager https://www.raspberrypi.com/software/
- Ouvrir Raspberry Pi imager
- Insérer la carte SD du raspberry dans le PC
- Sélectionner l'espace de stockage correspondant à la carte SD et sélectionner l'OS : **Raspberry Pi OS Lite (32-bit)**
<img src="https://user-images.githubusercontent.com/93132152/169273540-02b78e90-f551-4a8f-ac33-b90f7be4cffa.png" width=30% height=30%>  <img src="https://user-images.githubusercontent.com/93132152/169275055-28434132-3a4c-42e0-8752-84e8525d4922.png" width=30% height=30%>

- Dans les paramètres <img src="https://user-images.githubusercontent.com/93132152/169275716-50c48613-8d7e-4b10-8681-f49c881cf00c.png" width=4% height=4%>:
    - Activer le SSH
    - Définir un mot de passe pour le Raspberry et un nom d'utilisateur (conserver "pi")
    - Définir les paramètres Wifi (SSID, Password, pays (FR)) du dongle 4G. ** Bien penser à au paramètre "FR"**
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

- Brancher le servo moteur sur les broches du Raspberry. Le fil rouge du servo est relié à une **broche 5V**, le fil noir à une **broche GND**, et le fil restant (blanc, jaune) à la **broche GPIO 18** _cf.figures ci-dessous_
- Connecter les **broches GPIO 24 et GND** à l'aide d'un [cavalier](https://fr.rs-online.com/web/p/cavaliers-et-shunts/2518682?cm_mmc=FR-PLA-DS3A-_-google-_-CSS_FR_FR_Connecteurs_Whoop-_-(FR:Whoop!)+Cavaliers+et+Shunts+(2)-_-2518682&matchtype=&pla-321137858785&gclid=Cj0KCQjwhLKUBhDiARIsAMaTLnFPSjXNxxk7wiwrSQBFsIqT5VfPuMc_Ay4DvPVhzphmNF9wRRBNoIkaAl6-EALw_wcB&gclsrc=aw.ds)_(cf.figures ci-dessous_). Dans cette position l'Agrocam fonctionnera normalement, c'est à dire qu'elle s'éteindra après avoir pris une photo. Pour empêcher cela on peut basculer le cavalier entre la **broche 3,3V** et la **broche GPIO 24** ainsi l'Agrocam ne s'éteint pas et il est possible d'en prendre le contrôle (partie 1.5.). Dans la suite du tutoriel nous pouvons laisser le cavalier en position "normale" (entre GPIO 24 et GND) car la procédure d'exctinction n'a pa encore été implémentée à ce stade.

<img src="https://user-images.githubusercontent.com/93132152/170041886-8d5a046a-65c0-40ad-a286-e73cacb53113.png" width=20% height=20%>   <img src="https://user-images.githubusercontent.com/93132152/170041244-7e861340-61f8-4499-b359-bddf76874c6b.jpg" width=30% height=30%>

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

## 1.6. Configurer le raspberry 
Les parties ci-dessous ne sont pas nécessaires mais il est possible que si le reste ne fonctionne pas, le problème vienne de là.
**Si la caméra ne marche pas**, ouvrir les paramètres ```sudo raspi-config``` puis suivre les étapes : ```3 Interface Options/I1 Legacy Camera/YES/Finish/RebootYes```

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
## 1.7. Ajouter les fichiers sur le raspberry pi
Cette opération peut se faire depuis WinSCP en glissant et déposant les fichiers
### 1.7.1 Le script de l'Agrocam
Glisser déposer Agrocam_raspberry.sh dans /home/pi

Donner tous les droits au script _(première ligne ci-dessous)_ et effacer les "\r" et "r" de fin de ligne _(2e ligne ci-dessous, cela n'est pas toujours nécessaire mais ces caractère spéciaux on pu être ajouté si le script a été édité sur un outil Windows, Visual Studio Code par exemple)_
```
chmod 777 Agrocam_raspberry.sh
sed -i -e 's/\r$//' Agrocam_raspberry.sh
```
**Attention :** Le script Agrocam_raspberry.sh contient ```sudo shutdown -h now``` à la fin qui éteint l'Agrocam. Pour débugger le script (c'est-à-dire reprendre la main dessus) il est recommandé de commenter cette ligne _cf. partie 1.10_

### 1.7.2 Les variables d'environnement
Maintenant on va déposer dans un fichier séparé du script les variables qui permettent de se connecter au serveur FTP où seront envoyées et stockées les photos.

Depuis WinSCP, glisser déposer .env dans ```/home/pi``` une fois modifié avec les informations pertinentes entre les "" (hostname,user,password). Ce fichier contient les informations d'authentification pour accéder au serveur FTP sur lequel les photos seront sauvegardées. Attention le fichier peut être caché

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
```

## 1.8. Démarrer la script au reboot
Cette partie permet de démarrer le script ```Agrocam_raspberry.sh``` au démarrage. Attention, le script éteint le raspberry à la fin de son exécution. Cette extinction n'a pas lieu si ```controlPin==1```, il faut donc brancher le GPIO 24 au 3,3v pour que l'Agrocam reste allumée _cf. partie 1.10._

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

## 1.9. Tester le script
Pour relancer le raspberry : ```sudo reboot```, il devrait s'allumer, actionner le servomoteur, prendre une photo, réactionner le servomoteur, envoyer la photo sur le serveur et enfin s'éteindre.

## 1.10. Debugger l'Agrocam
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

# 2. Programmer l'allumage de l'Agrocam
On va se servir d'un arduino mini pour alimenter le Raspberry à intervalles régulier (et donc prendre une photo). L'arduino active un transistor qui lui même connecte le raspberry à une power bank _(cf. schéma en partie 3)_ 
- Installer le logiciel [Arduino](https://www.arduino.cc/en/software)
## 2.1 Brancher l'Arduino au PC
- Utiliser un FTDI pour relier l'Arduino mini au PC. S'il s'agit d'un Arduino mini 3,3 V penser à ce que le FTDI soit sur la position 3,3V (boutou ou cavalier selon les modèles)
<img src="https://user-images.githubusercontent.com/93132152/170056873-bf504cc6-de3e-4f86-b064-992f53fd7af1.png"  width=20% height=20%>

- Attention au sens de branchement du FTDI, les broches VCC, GND doivent coïncider. De même RX doit être branché sur TX et inversement :
<img src="https://user-images.githubusercontent.com/93132152/170057494-17264b12-1341-4d30-bbc1-56be233e0f04.jpg"  width=20% height=20%>

- Dans le logiciel Arduino, dans ```Outil > Type de carte``` sélectionner la carte **"Arduino Pro or Pro Mini"**
- Puis sélectionner le port qui s'est ajouté à la liste en branchant le cable USB (celui relié au FTDI) à l'ordinateur, dans ```Outil > Port```
<img src="https://user-images.githubusercontent.com/93132152/170059933-924f515d-7931-45b7-b47e-672c3da757bc.png"  width=20% height=20%>

## 2.2 Téléverser le script 
- Depuis Github copier le script Agrocam_arduino.ino et le coller dans le logiciel Arduino.
- Sauvegarder et téléverser le script :<img src="https://user-images.githubusercontent.com/93132152/170060569-35ab2f8e-8374-4a47-8603-4ba0fc10ead4.png" width=2% height=2%>

## 2.3 Modifier la fréquence d'acquisition d'image
Par défaut le script va lancer l'allumage approximativement toutes les 8h mais il est possible de modifier cette durée. Pour cela :
- ouvrir le script
- Trouver la boucle :
```
for (int i = 1; i <3600 ; i++){ //3600 pour 8h, 3150 avec le recalage
      LowPower.powerDown(SLEEP_8S, ADC_OFF, BOD_OFF);
  }
```

- Modifier 3600 par une autre valeur. La boucle permet de mettre l'Arduino en sommeil pour 8 secondes, la durée totale sera donc un multiple de 8 secondes.
- Téléverser une fois le script modifié

# 3. Réaliser le montage électronique
Nous avons maintenant un Raspberry qui fonctionne mais uniquement lorsqu'il est alimenté sur secteur. Cette partie vise à réaliser un montage pour permettre 
