#!/bin/bash

# Charger les utilitaires Witty Pi
source /home/pi/wittypi/utilities.sh

# Synchroniser lheure réseau avec le système
net_to_system

# Synchroniser lheure du système avec lhorloge RTC
system_to_rtc
