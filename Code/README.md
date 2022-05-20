Ce Readme vous accompagne sur les étapes à accomplir pour paramétrer le raspberry et l'arduino

# 1. Paramétrer le dongle 4G
Suivre la notice d'utilisation du dongle pour éditer son SSID et son mot de passe. Ces deux informations sont à conserver pour établir la connexion entre le Raspberry et le dongle.
# 2. Initialiser le Raspberry Pi
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

# 3. Installer les logiciels pour la suite
- Installer [WinSCP](https://winscp.net/eng/download.php) sur votre PC. Ce logiciel permet de se connecter au raspberry en SSH, de parcourir ses fichier et d'interagir avec le terminal de commandes.
- Installer [Network analyzer](https://play.google.com/store/apps/details?id=net.techet.netanalyzerlite.an&hl=fr&gl=US) sur votre smartphone. Cette application permet de scaner un réseau wifi et de trouver les appareils (leur adresse IP) qui y sont connectés.

# 4. Réaliser les branchements
- Insérer la carte SD dans le raspberry
- Brancher la Picam. Attention au sens de branchement de la nappe de cable. Attention les connecteurs sont fragiles, à manipuler avec précautions.
<img src="https://www.raspberrypi.com/app/uploads/2016/05/2016-05-15-16.32.19-768x576.jpg" width=20% height=20%>

- Brancher le servo moteur sur les broches du Raspberry. (photo !)
- Brancher le dongle 4G au Raspberry sur le port **"USB"** _cf. photo ci-dessous_
- Brancher l'alimentation sur le port **"PWR IN"** _cf. photo ci-dessous_
<img src="https://user-images.githubusercontent.com/93132152/169502193-72963340-17c8-46ee-b322-8d32348ea31f.png"  width=30% height=30%>

# 4. Se connecter au Raspberry depuis un PC #

- Connecter un smartphone au réseau du dongle 4G (avec SSID et mot de passe précédemment paramétrés)
- Avec l'application mobile Net analyzer identifier l'adresse IP du raspberry Pi
- Sur PC, installer WinSCP et se connecter au rasperry : protocole de fichier : SFTP; Nom d'hôte : IP; Nom d'utilisateur : pi; Mot de passe : défini précédemment
- Depuis WinSCP ouvrir Putty

# Configurer le raspberry #
Les parties ci-dessous ne sont pas nécessaires mais il est possible que si le reste ne fonctionne pas, le problème vienne de là.
## Activer la camera ##
Si la caméra ne marche pas, ouvrir les paramètres ```sudo raspi-config``` puis ```3 Interface Options/I1 Legacy Camera/YES/Finish/RebootYes```
## Activer les ports GPIO ##
Si le servomoteur ne marche pas, ouvrir les paramètres ```sudo raspi-config``` puis ```3 Interface Options/``` A priori pas besoin de ça
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
cd ..
```
## Installer pip et python-dotenv ##
Cela peut prendre un peu de temps 
```
sudo apt-get install python3-pip
pip install python-dotenv
sudo cp -R /home/pi/.local/lib/python3.9/site-packages/dotenv /usr/lib/python3.9 
```
*On déplace la librairie pour qu'elle soit trouvée en démarrage automatique*
# Ajouter les fichiers sur le raspberry pi #
Cette opération peut se faire depuis WinSCP en glissant et déposant les fichiers
## Le script de l'Agrocam ##
Glisser déposer Agrocam_raspberry.sh dans /home/pi

Donner tous les droits au script et effacer les "\r" et "r" de fin de ligne en cas d'édition du script sur Windows :
```
chmod 777 Agrocam_raspberry.sh
sed -i -e 's/\r$//' Agrocam_raspberry.sh
```
**Attention :** Le script Agrocam_raspberry.sh contient ```sudo shutdown -h now``` à la fin, pour débugger le script il est donc recommandé de commenter cette ligne pour éviter d'éteindre le script

## Les variables d'environnement ##
Maintenant on va déposer dans un fichier séparé du script les variables qui permettent de se connecter au serveur FTP où seront stockées les photos

Glisser déposer .env dans /home/pi une fois modifié (hostname,user,password). Ce fichier contient les informations d'authentification pour accéder au serveur FTP sur lequel les photos seront sauvegardées. Attention le fichier peut être caché
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
