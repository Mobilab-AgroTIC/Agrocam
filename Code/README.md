# Initialiser le Raspberry Pi #
- Installer Raspberry Pi imager https://www.raspberrypi.com/software/
- Insérer la carte SD dans le PC
- Ouvrir Raspberry Pi imager
- Sélectionner espace de stockage correspondant à la carte SD et sélectionner l'OS : raspi lite 32 bit
- Dans les paramètres (ajouter des photos) :
    - Activer le SSH
    - Définir un mot de passe 
    - Définir les paramètres Wifi (SSID, Password, pays (FR)) du dongle 4G --> détailler la procédure de paramétrage du dongle 4G

# Se connecter au Raspberry depuis un PC #
- Mettre le raspberry Pi sous tension avec le dongle 4G branché
- Connecter un smartphone au réseau du dongle 4G
- Avec l'application mobile Net analyzer identifier l'adresse IP du raspberry Pi
- Sur PC, installer WinSCP et se connecter au rasperry : protocole de fichier : SFTP; Nom d'hôte : IP; Nom d'utilisateur : pi; Mot de passe : défini précédemment
- Depuis WinSCP ouvrir Putty

# Configurer le raspberry #
## Activer la camera ##
Ouvrir les paramètres ```sudo raspi-config``` puis ```3 Interface Options/I1 Legacy Camera/YES/Finish/RebootYes``` puis il faut refaire la même opération pour désactiver la caméra legacy
## Activer les ports GPIO ##
Ouvrir les paramètres ```sudo raspi-config``` puis ```3 Interface Options/``` A priori pas besoin de ça
# Installer les librairies #
## Installer git ##
```
sudo apt-get install git
```
## Installer WiringPi ##
```
git clone https://github.com/WiringPi/WiringPi.git
cd WiringPi
git pull origin
./build
```
## Installer pip et python-dotenv ##
```
sudo apt-get install python3-pip
pip install python-dotenv
sudo cp -R /home/pi/.local/lib/python3.9/site-packages/dotenv /usr/lib/python3.9 
```
*On déplace la librairie pour qu'elle soit trouvée en démarrage automatique*
# Ajouter les fichiers sur le raspberry pi #
Cette opération peut se faire depuis WinSCP en glissant et déposant les fichiers

- Glisser déposer Viticam_raspberry.sh dans /home/pi
- Glisser déposer .env dans /home/pi une fois modifié (hostname,user,password). Ce fichier contient les informations d'authentification pour accéder au serveur FTP sur lequel les photos seront sauvegardées. Attention le fichier peut être caché
    Ou alors créer ce fichier depuis le terminal
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
Donner tous les droits au script et effacer les "\r" et "r" de fin de ligne en cas d'édition du script sur Windows :
```
chmod 777 Agrocam_raspberry.sh
sed -i -e 's/\r$//' Agrocam_raspberry.sh
```
**Attention :** Le script Agrocam_raspberry.sh contient ```sudo shutdown -h now``` à la fin, pour débugger le script il est donc recommandé de commenter cette ligne pour éviter d'éteindre le script

# Démarrer la script au reboot : #
Cette partie permet de démarrer le script ```Agrocam_raspberry.sh``` au démarrage. Attention, le script éteint le raspberry à la fin de son exécution. Cette extinction n'a pas lieu si ```controlPin==1```, il faut donc brancher le GPIO 24 au 3,3v pour que l'Agrocam reste allumée.

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

# Tester le script #
Pour relancer le raspberry : ```sudo reboot```, il devrait s'allumer, actionner le servomoteur, prendre une photo, réactionner le servomoteur, envoyer la photo sur le serveur, puis il s'éteint

Pour empêcher l'extinction, connecter le GPIO 24 au 3,3v

# Arduino #
- Téléverser le script Arduino sur un Arduino promini 3,3v
- Suivre le schéma de montage pour le transistor (à faire)
