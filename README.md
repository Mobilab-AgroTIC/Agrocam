# AgriCam
La caméra connectée pour suivre l'évolution de vos cultures !

Démarrer la script au boot :
Dans le script, ajouter au début 
```
#! bin/sh
```

Donner tous les droits au script :
```
chmod 777 Viticam_raspberry.sh
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


