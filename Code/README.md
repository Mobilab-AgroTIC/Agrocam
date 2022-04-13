#Initialiser le Raspberry Pi#
- Installer Raspberry Pi imager https://www.raspberrypi.com/software/
- Insérer la carte SD dans le PC
- Ouvrir Raspberry Pi imager
- Sélectionner espace de stockage correspondant à la carte SD et sélectionner l'OS : raspi lite 32 bit
- Dans les paramètres (ajouter des photos) :
    - Activer le SSH
    - Définir un mot de passe 
    - Définir les paramètres Wifi (SSID, Password) du dongle 4G

#Se connecter au Raspberry depuis un PC#
- Mettre le raspberry Pi sous tension avec le dongle 4G branché
- Connecter un smartphone au réseau du dongle 4G
- Avec l'application mobile Net analyzer identifier l'adresse IP du raspberry Pi
- Sur PC, installer WinSCP et se connecter au rasperry : protocole de fichier : SFTP; Nom d'hôte : IP; Nom d'utilisateur : pi; Mot de passe : défini précédemment
- Depuis WinSCP ouvrir Putty

#Installer les librairies#
##Installer git##
```
sudo apt-get install git
```
##Installer WiringPi##
```
git clone https://github.com/WiringPi/WiringPi.git
cd WiringPi
git pull origin
./build
```
##Installer pip et python-dotenv##
```
pip install python-dotenv
sudo cp -R /home/pi/.local/lib/python3.9/site-packages/dotenv /usr/lib/python3.9 //On déplace la librairie pour qu'elle soit trouvée en démarrage automatique
```

**Démarrer la script au boot :**
Dans le script, ajouter au début 
```
#! bin/sh
```

Donner tous les droits au script :
```
chmod 777 Viticam_raspberry.sh
```
Création d'un fichier .env dans home/pi/
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

Activer le script au reboot
Ouvrir le crontab 
```
sudo crontab -e
```
Ajouter une ligne au crontab :
```
@reboot sudo /home/pi/Viticam_raspberry.sh
```


