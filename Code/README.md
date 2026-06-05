**Ce readme permet de recréer le fichier agrocam.img à destination des développeurs. Si vous souhaitez simplement assembler une agrocam rendez vous sur https://mobilab.agrotic.org/2025/02/18/agrocam/**
Ce Readme a pour objectif de détailler les étapes de création du fichier agrocam.img. Il a pour but de servir de base à la reproduction du fichier agrocam.img s'il venait à être perdu ou si de nouvelle fonctionnalités devaient être ajoutées.

Pour réaliser ces étapes vous avez besoin de :
- Une carte Raspberry Pi Zero 2
- Une carte SD 16Go
- Un PC idealement sous une distribution Linux pour créer le fichier .img et le compresser. Pour ma part j'ai un windows 11 dont la virtualisation est bloquée (machine professionnelle), c'est un peu plus long mais ça se fait bien.
- Un smartphone dont vous pouvez changer le nom de l'acces point (ou partage de connexion) donc idéalement un Android

# 1. Ecriture de L'OS
On va utiliser le logiciel Raspberry Pi Imager disponible ici 

https://www.raspberrypi.com/software/

Insérez une carte SD de 16Go et suivez les étapes de raspberry pi imager
- Appareil : *Raspberry Pi Zero*
- OS : *Raspberry Pi OS Lite (32-bit)* (disponible dans Raspberry Pi OS (other))
- Stockage : Sélectionnez votre carte SD. Chez moi elle s'appelle *Mass Storage Device USB Device* avec 14,6 Go
- Personnalisation : Suivez les étapes du tableau ci-dessous

|Onglet|Action|
|------|------|
|Nom d'hôte|agrocam|
|Localisation|Ville capitale : Paris <br> Fuseau horaire : Europe/Paris <br> Type de clavier : fr|
|Utilisateur|Nom d'utilisateur : pi <br> Mot de passe : *à définir et ne surtout pas perdre pour vous connecter en ssh par la suite* |
|Wi-Fi|SSID : agrocam <br> Mot de passe :  <br> *Vous permettra de vous connecter au raspberry en générant un hotspot wifi du même nom avec un smartphone. Servira ensuite régulièrement pour assurer la maintenance des Agrocams.* |
|Accès à distance|Activer le SSH <br> Mécanisme d'authentification : utiliser le mot de passe pour l'authentification |
|Raspberry Pi Connect|Ne pas activer|

- Enfin lancez l'écriture. Cela peut prendre une dizaine de minutes


# 2. Accéder en ssh au raspberry
Installer WinSCP
hostname *agrocam.local*
Login : pi
Mot de passe : définit à l'étape 1 dans l'onglet utilisateur
Ouvrir Putty

# 3. Installation de librairies

```
sudo apt-get update
sudo apt upgrade
sudo apt install python3-flask python3-piexif
```

# 4. Téléverser les scripts depuis Winscp
Depuis WinSCP téléverser les scripts suivant dans */home/pi/*

*agrocam.py*
*usb_storage*
*wittypi.py*
*credentials_web.py*
*crendentials.json*

Dans *credentials.json* un paramètre "debug_mode":false peut être passer en true pour éviter que l'Agrocam n'active pas son hotspot et qu'elle soit ainsi accessible sur votre SSID (partage de connexion "agrocam")



# 5. Création et activation des services systemctl
Depuis WinSCP vous ne pouvez pas téléverser les fichiers .service dans leur lieu de destination (/lib/systemd/system) car il faut être en mode admin
On va donc créer les fichiers agrocam.service, agrocam-wifi.service,agrocam-flask.service à la main
```
sudo nano /lib/systemd/system/agrocam.service
```
 puis collez le contenu du fichier agrocam.service dedans

```
sudo nano /lib/systemd/system/agrocam-flask.service
```
puis collez le contenu du fichier agrocam-flask.service dedans

Puis on permet la lecture de ces fichiers
```
sudo chmod 644 /lib/systemd/system/agrocam.service
sudo chmod 644 /lib/systemd/system/agrocam-flask.service
```
644 signifie que vous pouvez lire et écrire le fichier ou le répertoire et que les autres utilisateurs peuvent seulement le lire.

On redemarre daemon
```
sudo systemctl daemon-reload
```
On peut enfin activer l'ensemble des services
```
sudo systemctl enable agrocam.service
sudo systemctl disable agrocam-flask.service
```

Créer la connexion Hotspot persistante avec un SSID temporaire
```sudo nmcli con add type wifi ifname wlan0 con-name Hotspot autoconnect no ssid Agrocam-init```

Configurer le mode AP et le partage réseau
```sudo nmcli connection modify Hotspot 802-11-wireless.mode ap 802-11-wireless.band bg ipv4.method shared```

# 6. Installation wittyPi
```
wget http://www.uugear.com/repo/WittyPi4/install.sh
sudo sh install.sh
```
Le script vous demande de rebooter, On le fera plus tard


# 7. Suppression des services inutiles (valabe sur raspberry pi zero 2)

sudo systemctl disable \
  cloud-final.service \
  cloud-init-main.service \
  cloud-init-local.service \
  cloud-config.service \
  cloud-init-network.service \
  apt-daily.service \
  apt-daily-upgrade.service \
  bluetooth.service

sudo systemctl disable --now apt-daily.timer
sudo systemctl disable --now apt-daily-upgrade.timer
sudo systemctl disable --now fstrim.timer

** Amélioration possibles **
```sudo nano /boot/firmware/config.txt```
Ajouter ceci
\# Désactive le Bluetooth
dtoverlay=disable-bt
\# Désactive l'HDMI (gain de conso et de temps)
hdmi_blanking=2

# 8. Finalisation des installation
Pour finaliser l'installation de wittypi :

``` 
sudo reboot
```
Une fois l'Agrocam redémarrée plusieurs comportement sont possible en fonction de l'état du jumper de maintenance et de la variable "debug_mode" :
|   |debug_mode=false|debug_mode=true|
|---|----------------|---------------|
|Jumper position normale|**Fonctionnement normal :** L'Agrocam démarre, prend une photo, essaye de se connecter aux wifi connus, d'envoyer les photos en pending, et s'éteint|L'Agrocam démarre, essaye de se connecter au wifi, d'envoyer des photos, mais ne s'éteint pas|
|Jumper position maintenance|**Fonctionnement maintenance**: l'Agrocam crée un hotspot wifi, affiche une interface de paramétrage sur agrocam.local:5000||
# 8. Dernière petites étapes avant extinction
Pour eviter d'embarquer trop de trace de notre intervention. vous pouvez faire les étapes suivantes
Videz le cache APT : ```sudo apt clean```
Supprimez l'historique bash : 

```sudo cat /dev/null > ~/.bash_history```

```history -c```


Eteignez le raspberry avec
```sudo shutdown -h now```


# 9. Récupérer la carte SD et créer une image
Une fois le raspberry éteint (LED verte éteinte et qui ne clignote plus), récupérez la carte SD et insérez là dans votre PC. A ce stade je donne la procédure sur Windows 11.

Installez le logiciel Win32DiskImager
Ouvrez le
Il y a deux champ à remplir 
fichier image : correspond à l'emplacement où vous allez écrire votre image (attention il vous faut de la place sur votre disque, équivalente à la taille de la carte SD). On pourra nommer le fichier agrocam.img
Périphérique : correspond à l'emplacement de votre carte SD. [:\D] dans mon cas

Il n'y a plus qu'à cliquer sur "Lire" cela peut prendre 10 minutes

# 10. Réduire la taille de votre fichier *agrocam.img*
L'image fait maintenant environ 16 Go qui correspond à la taille de la carte SD. Or l'OS et les scripts que nous avons rajouté ne prennent pas toute cette place. On va donc évacuer de l'image tous les octets qui ne "servent à rien" en utilisant PiShrink grace à WSL2 sur Windows 11.
```
wget https://raw.githubusercontent.com/Drewsif/PiShrink/master/pishrink.sh
```
pour télécharger Pishrink
```
chmod +x pishrink.sh
```
Pour le rendre activable
```
sudo ./pishrink.sh /mnt/c/Mon/Chemin/vers/agrocam.img
```
Puis compression de l'image :
```
xz -vk /mnt/c/Mon/Chemin/vers/agrocam.img
```


# 12. Quelques commandes utiles
synchroniser l'heure avec le réseau :
```
sudo timedatectl set-ntp true
```

Analyser ce qui prend du temps au boot

```
systemd-analyze
systemd-analyze blame
```

sudo journalctl -u agrocam
