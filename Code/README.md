**Ce readme permet de recréer le fichier agrocam.img à destination des développeurs. Si vous souhaitez simplement assembler une agrocam rendez vous sur https://mobilab.agrotic.org/2025/02/18/agrocam/**
Ce Readme a pour objectif de détailler les étapes de création du fichier agrocam.img. Ila pour but de servir de base à la reproduction du fichier agrocam.img s'il venait à être perdu ou si de nouvelle fonctionnalités devaient être ajoutées.

Pour réaliser ces étapes vous avez besoin de :
- Une carte Raspberry Pi Zero
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
|Wi-Fi|SSID : agrocam <br> Mot de passe : agrocam2026 <br> *Vous permettra de vous connecter au raspberry en générant un hotspot wifi du même nom avec un smartphone. Servira ensuite régulièrement pour assurer la maintenance des Agrocams* |
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
sudo apt install python3-flask 
```

# 4. Téléverser les scripts depuis Winscp
Depuis WinSCP téléverser les scripts suivant dans */home/pi/*

*agrocam.py*
*credentials_web.py*
*crendentials.json*

Puis dans putty on supprime les caractères spéciaux. Cette étapes est certainement à supprimer mais à une époque, le fait d'éditer des scripts dans VSC générait des retour de chariot dans le texte du script qui n'étaient pas compris par python une fois sur le Raspberry. Cette étapes est certainement facultative mais voici les informations au cas où :
```
sed -i -e 's/\r$//' agrocam.py
sed -i -e 's/\r$//' credentials_web.py
sed -i -e 's/\r$//' credentials.json
```

# 5. Création du répertoire pour les photos
```
sudo mkdir Agrocam
sudo chmod 777 Agrocam
```

# 6. Installation wittyPi
```
wget http://www.uugear.com/repo/WittyPi4/install.sh
sudo sh install.sh
```
Le script vous demande de rebooter, faites-le
``` 
sudo reboot
```
# 7. Création et activation des services systemctl
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
# 8. Dernière petites étapes avant extinction
Pour eviter d'embarquer trop de trace de notre intervention. vous pouvez faire les étapes suivantes
Videz le cache APT : ```sudo apt clean```
Supprimez l'historique bash : ```sudo cat /dev/null > ~/.bash_history```

On pourrait ici encore grandement améliorer la consommation du raspberry en optimisant ses services. Les chatbot Gemini et Chatgpt ont pu faire différentes recommandations mais pour l'instant rien n'a encore été implémentés car non testé. On peut lister parmis les services potentiellement désactivables : services autour du multimedia (hdmi), le bluetooth, une multitude de service avancé sur la gestion du réseau et des fichiers mais qui sont tous assez interdépendant donc risqué de les désactiver.

Attention à de pas rebooter le raspberry à ce stade. Rien de grave mais au démarrage le service agrocam va se lancer mais il ne pourra pas bien s'executer (cartes wittypi et camera absente), les conséquences n'ont pas encore été étudier. Il ne semble pas que cela pose un problème mais on ne sait jamais

Eteignez le raspberry avec
```sudo shutdown -h now```

** Amélioration possibles **
```sudo nano /boot/firmware/config.txt```
Ajouter ceci
\# Désactive le Bluetooth et le Wifi intégré (si vous utilisez un dongle 4G)
dtoverlay=disable-bt
\# dtoverlay=disable-wifi # Ne l'activez que si le dongle 4G suffit
\# Désactive l'HDMI (gain de conso et de temps)
hdmi_blanking=2


```sudo nano /etc/dhcpcd.conf```
interface wlan0
static ip_address=192.168.1.100/24
static routers=192.168.1.1
static domain_name_servers=1.1.1.1

**Eteindre des services inutiles**
Desactiver cloud-init qui est inutile (pour machines virtuelles)
```sudo apt-get purge cloud-init -y```
```sudo rm -rf /etc/cloud/ && sudo rm -rf /var/lib/cloud/```

Desactiver ModemManager car on communique tout le temps en wifi
Idem pour bluetooth car on s'en sert pas
networkmanager-wait-online.service car agrocam.py peut démarrer même si on n'a pas encore le wifi

sudo systemctl disable ModemManager bluetooth NetworkManager-wait-online.service



# 9. Récupérer la carte SD et créer une image
Une fois le raspberry éteint (LED verte éteinte et qui ne clignote plus), récupérez la carte SD et insérez là dans votre PC. A ce stade je donne la procédure sur Windows 11 mais sur Linux cela se fait bien avec la commande dd.

Installez le logiciel Win32DiskImager
Ouvrez le
Il y a deux champ à remplir 
fichier image : correspond à l'emplacement où vous allez écrire votre image (il faut au moins 16 Go de place). On pourra nommer le fichier agrocam.img
Périphérique : correspond à l'emplacement de votre carte SD. [:\D] dans mon cas

Il n'y a plus qu'à cliquer sur "Lire" cela peut prendre 10 minutes

# 10. Réduire la taille de votre fichier *agrocam.img*
L'image fait maintenant environ 16 Go qui correspond à la taille de la carte SD. Or l'OS et les scripts que nous avons rajouté ne prennent pas toute cette place. On va donc évacuer de l'image tous les octets qui ne "servent à rien" en utilisant PiShrink.
Vous pouvez utiliser ce logiciel sur Windows si vous arrivez à lancer WSL pour avoir une virtualisation d'un environnement linux. Ma machine ne le permet pas alors j'ai fait les étapes suivantes :
- Déplacement du fichier agrocam.img sur une clé USB de grande capacité
- Ecriture d'un OS Raspberry pi lite uniquement pour cette opération. Sur une autre carte SD vous pouvez reproduire l'étape 1
- Ouvrir une connexion SSH avec le raspberry et dans un invite de commande suivre les étapes suivante
- Avec un adapteur micro-USB mâle - USB A femelle branchez la clé USB qui contient agrocam.img au raspberry 
```
wget https://raw.githubusercontent.com/Drewsif/PiShrink/master/pishrink.sh
```
pour télécharger Pishrink
```
chmod +x pishrink.sh
```
Pour le rendre activable
```
sudo mount /dev/sda1 /mnt
```
Pour monter la clé USB
```
sudo ./pishrink.sh /mnt/agrocam.img
```
Pour lancer pishrink. Attention cela va écraser le fichier agrocam.img par une nouvelle version moins volumineuse (environ 4Go)

Actuellement Pishrink a conservé uniquement les parties utiles de la partition (qui correspondent réellement à des fichiers). Mais il est encore possible de compresser tout ce petit monde. La commande suivante est à exécuter sur le raspberry Pi Zero. Mais attention comme c'est pas une machine de guerre, cette simple commande peut facilement prendre plus d'une heure à s'executer.

```
xz -vk /mnt/agroocam.img
```
Si cela est trop long, vous pouvez récupérer le fichier agrocam.img de 4Go sur votre windows et dans Powershell lancer la commande suivante


Cela va créer un nouveau fichier d'environ 500 Mo agrocam.img.gz

C'est lui qui sera notre image officielle de l'Agrocam

# 11. Autre alternative pour réduire l'image (synthèse de gemini)

C'est un excellent réflexe de noter tout ça ! On a traversé pas mal d'embûches techniques, et ce tutoriel servira de "guide de survie" pour tes futures réplications.

Voici la synthèse complète de ta méthode, de la création de l'image à la compression finale.
🛠️ Tutoriel : Clonage et Optimisation d'Image Raspberry Pi
Pourquoi avons-nous dû ruser avec le Raspberry Pi ?

Le problème venait d'un conflit de génération entre les systèmes de fichiers :

    Ton PC (Ubuntu 22.04) : Utilise une version ancienne des outils (e2fsprogs v1.46).

    Raspberry Pi OS (Bookworm) : Utilise une version récente (v1.47).

    Le conflit : Les images récentes activent une option nommée orphan_file (FEATURE_C12). Ton Ubuntu, trop vieux, ne comprenait pas cette option et bloquait tout. Nous avons donc utilisé le Raspberry Pi (à jour) pour désactiver cette option et rendre l'image compatible avec ton PC.

Étape 1 : Création de l'image "Master" (Windows)

    Insère la carte SD de ton projet dans ton PC Windows.

    Lance Win32DiskImager.

    Sélectionne la lettre de ta carte SD (ex: D: ou E:).

    Choisis un nom de fichier sur ta clé USB de grande capacité (ex: agrocam_brut.img).

    Clique sur Read (Lire). Tu obtiens un fichier de 15 Go.

Étape 2 : Préparation sur le Raspberry Pi Zero (SSH)

Branche ta clé USB sur le Pi Zero (via un adaptateur micro-USB OTG) et connecte-toi en SSH.

1. Identifier et monter la clé USB :
Bash

```lsblk```                              # Repère ta clé (souvent sda1)
Crée un dossier de montage en remplaçant le X par le numéro sorti par lsblk
```sudo mount /dev/sdaX /mnt```
Monte la clé

2. Rendre l'image compatible (Le "Fix" tune2fs) : On utilise le Pi Zero pour "rétrograder" le système de fichiers de l'image.
Bash

**Crée un périphérique virtuel pour accéder aux partitions de l'image**
```sudo losetup -fP /mnt/agrocam.img```

```lsblk```                          Vérifie le nom du loop (ex: loop0p2)

# Répare les sommes de contrôle (checksums)
```sudo e2fsck -f -y /dev/loopXp2```

# Désactive l'option "orphan_file" qui faisait planter Ubuntu
sudo tune2fs -O ^orphan_file /dev/loopXp2

# Libère proprement le fichier
sudo losetup -d /dev/loopX
cd ~
sudo umount /mnt               # Éjecte virtuellement la clé

Étape 3 : Réduction sur le PC (Ubuntu)

Maintenant que l'image est compatible, on utilise la puissance de ton PC pour gagner du temps.

1. Lancement de PiShrink : Branche la clé sur ton PC Ubuntu et va dans le dossier de la clé :
Bash

# Télécharge le script si tu ne l'as pas
wget https://raw.githubusercontent.com/Drewsif/PiShrink/master/pishrink.sh
chmod +x pishrink.sh

# Lance la réduction (ton image va passer de 15 Go à ~4,2 Go)
sudo ./pishrink.sh agrocam_brut.img agrocam_shrinked.img

Étape 4 : Compression maximale (.img.xz)

Pour que ton fichier soit facile à stocker ou à partager, on utilise la compression la plus forte.
Bash

# Compression en format .xz (très efficace)
# -v : voir la progression / -k : garde l'original
xz -vk agrocam_shrinked.img

Résultat final : Tu obtiens un fichier agrocam_shrinked.img.xz d'environ 1 à 2 Go, prêt à être flashé sur n'importe quelle carte SD (même une de 8 Go !) avec Raspberry Pi Imager.
Résumé des outils utilisés

    Win32DiskImager : Pour la copie brute sous Windows.

    e2fsck / tune2fs : Pour la réparation et la compatibilité descendante.

    PiShrink : Pour supprimer l'espace vide de l'image.

    XZ : Pour la compression finale.

Tout semble opérationnel pour ta production en série ! Est-ce que tu souhaites que je t'aide à automatiser la configuration du Wi-Fi pour que tes futurs clones se connectent tout seuls au premier démarrage ?

