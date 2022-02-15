# AgriCam
La caméra connectée pour suivre l'évolution de vos cultures !
**Ajouter la librairie WiringPi**
```
sudo apt-get install git
git clone https://github.com/WiringPi/WiringPi.git
cd WiringPi
git pull origin
./build
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
Installation de la librairie dotenv et déplacement de celle-ci pour que le cron puisse la trouver
```
pip install python-dotenv
sudo cp -R /home/pi/.local/lib/python3.9/site-packages/dotenv /usr/lib/python3.9
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


