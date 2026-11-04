import os
import subprocess
import sys
"""
Version SIMPLE - Montage USB avec permissions maximales
"""

def find_usb_device():
    """
    Détecte les périphériques USB amovibles (disks) en utilisant lsblk.
    Retourne le chemin du premier disque USB trouvé (ex: /dev/sda) ou None.
    """
    try:
        result = subprocess.run(
            ["lsblk", "-ndo", "NAME,RM,TYPE"],
            capture_output=True,
            text=True,
            timeout=5
        )
        
        for line in result.stdout.strip().split('\n'):
            if not line:
                continue
            parts = line.split()
            if len(parts) >= 3:
                device_name, removable, dev_type = parts[0], parts[1], parts[2]
                if removable == "1" and dev_type == "disk":
                    print(f"[INFO] Clé USB détectée : /dev/{device_name}")
                    return f"/dev/{device_name}"
        
        print("[INFO] Aucune clé USB détectée.")
        return None
    except Exception as e:
        print(f"[ERROR] Erreur lors de la détection USB : {e}", file=sys.stderr)
        return None


def get_usb_partition():
    """
    Récupère la première partition du disque USB détecté.
    Retourne: "/dev/sda1" ou None
    """
    usb_device = find_usb_device()
    if not usb_device:
        return None
    
    try:
        result = subprocess.run(
            ["lsblk", "-nlo", "NAME,RM,TYPE"],
            capture_output=True,
            text=True,
            timeout=5
        )
        
        usb_base = usb_device.split('/')[-1]
        
        for line in result.stdout.strip().split('\n'):
            if not line:
                continue
            parts = line.split()
            if len(parts) >= 3:
                device_name, removable, dev_type = parts[0], parts[1], parts[2]
                if device_name.startswith(usb_base) and removable == "1" and dev_type == "part":
                    partition = f"/dev/{device_name}"
                    print(f"[INFO] Partition USB trouvée : {partition}")
                    return partition
        
        partition = f"{usb_device}1"
        print(f"[INFO] Partition par convention : {partition}")
        return partition
    except Exception as e:
        print(f"[ERROR] Erreur lors de la récupération de la partition : {e}", file=sys.stderr)
        return None


def is_usb_mounted(mount_point="/mnt/usb"):
    """
    Vérifie si la clé USB est déjà montée sur le point de montage spécifié.
    Retourne: True si montée, False sinon
    """
    try:
        result = subprocess.run(
            ["grep", mount_point, "/proc/mounts"],
            capture_output=True,
            timeout=5
        )
        return result.returncode == 0
    except Exception as e:
        print(f"[WARNING] Erreur lors de la vérification du montage : {e}", file=sys.stderr)
        return False


def setup_storage_path(usb_mount_point="/mnt/usb", local_fallback="/home/pi/Agrocam"):
    """
    Détecte si une clé USB est disponible et configure le chemin de stockage des photos.
    
    VERSION SIMPLE :
    - Crée /mnt/usb s'il n'existe pas (avec sudo)
    - Monte la partition USB si présente
    - Crée le dossier /mnt/usb/Agrocam avec permissions 777
    - Fallback vers /home/pi/Agrocam si USB indisponible
    
    Retourne: Le chemin du dossier de stockage
    """
    print("[INFO] Configuration du stockage...")
    
    # Chercher une clé USB
    usb_partition = get_usb_partition()
    
    if usb_partition:
        print(f"[INFO] USB trouvée : {usb_partition}")
        
        # Vérifier si déjà montée
        if not is_usb_mounted(usb_mount_point):
            # Créer le point de montage s'il n'existe pas
            if not os.path.exists(usb_mount_point):
                try:
                    print(f"[INFO] Création de {usb_mount_point}...")
                    subprocess.run(
                        ["sudo", "mkdir", "-p", usb_mount_point],
                        capture_output=True,
                        text=True,
                        timeout=5,
                        check=True
                    )
                except Exception as e:
                    print(f"[ERROR] Impossible de créer {usb_mount_point} : {e}", file=sys.stderr)
                    usb_partition = None
            
            # Monter la clé USB
            if usb_partition:
                try:
                    print(f"[INFO] Montage de {usb_partition} sur {usb_mount_point}...")
                    subprocess.run(
                        ["sudo", "mount", "-o", "umask=0000,dmask=0000,fmask=0000", usb_partition, usb_mount_point],
                        capture_output=True,
                        text=True,
                        timeout=10,
                        check=True
                    )
                    # Permissions totales pour tous les utilisateurs sur le point de montage
                    subprocess.run(
                        ["sudo", "chmod", "777", usb_mount_point],
                        capture_output=True,
                        text=True,
                        timeout=5,
                        check=True
                    )

                    print(f"[INFO] ✅ Clé USB montée avec permissions 777")
                except subprocess.CalledProcessError as e:
                    if "already mounted" not in str(e):
                        print(f"[ERROR] Impossible de monter : {e}", file=sys.stderr)
                        usb_partition = None
        else:
            print(f"[INFO] ✅ Clé USB déjà montée")
            # Permissions totales pour tous les utilisateurs sur le point de montage
            subprocess.run(
                ["sudo", "chmod", "777", usb_mount_point],
                capture_output=True,
                text=True,
                timeout=5,
                check=True
            )


    
    # Déterminer le chemin de stockage
    if usb_partition:
        storage_path = f"{usb_mount_point}/Agrocam"
        print(f"[INFO] Mode USB activé")
    else:
        storage_path = local_fallback
        print(f"[INFO] Mode stockage local")
    
    # Créer le dossier de stockage avec permissions 777
    try:
        #os.makedirs(storage_path, exist_ok=True)
        subprocess.run(
            ["sudo", "mkdir", "-p", storage_path],
            capture_output=True,
            text=True,
            timeout=5,
            check=True
        )
        subprocess.run(
            ["sudo", "chmod", "777", storage_path],
            capture_output=True,
            text=True,
            timeout=5,
            check=True
        )
        print(f"[INFO] ✅ Dossier de stockage créé : {storage_path}")
        print(f"[INFO] ✅ Permissions 777 appliquées")
    except Exception as e:
        print(f"[ERROR] Erreur lors de la création : {e}", file=sys.stderr)
        # Fallback
        storage_path = local_fallback
        subprocess.run(
            ["sudo", "mkdir", "-p", storage_path],
            capture_output=True,
            text=True,
            timeout=5,
            check=True
        )
        subprocess.run(
            ["sudo", "chmod", "777", storage_path],
            capture_output=True,
            text=True,
            timeout=5,
            check=True
        )
        print(f"[INFO] Fallback vers : {storage_path}")
    
    return storage_path