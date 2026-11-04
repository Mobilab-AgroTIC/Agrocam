#!/usr/bin/env python3
from flask import Flask, Response, request, render_template_string
import json
import os
import re
import requests
import subprocess
import tempfile
import threading
from wittypi import set_startup_time, calculate_next_startup_time, setup_wittypi
from servo import move_servo, ServoManager
CREDENTIALS_FILE = "/home/pi/credentials.json"

# Angles de l'obturateur, identiques à ceux utilisés par agrocam.py
SHUTTER_OPEN_ANGLE = 0
SHUTTER_CLOSED_ANGLE = 90

PREVIEW_WIDTH = 640
PREVIEW_FRAMERATE = 10

USB_INTERFACE = "usb0"
# API de la clé 4G : funcNo 1001 renvoie l'opérateur, le réseau, l'état et le signal (0 à 5)
DONGLE_API_URL = "http://192.168.100.1/ajax"
DONGLE_STATUS_FUNC = 1001

app = Flask(__name__)

# La caméra n'accepte qu'un seul processus à la fois : un nouveau flux remplace le précédent
preview_lock = threading.Lock()
preview_process = None


HTML_FORM = """
<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>Configuration Agrocam</title>
    <!-- Tout le style reste dans la page : le hotspot n'a pas forcément accès à Internet -->
    <style>
        :root {
            color-scheme: light dark;
            --bg: #f3f6f4;
            --surface: #ffffff;
            --text: #1b2420;
            --muted: #5c6863;
            --border: #d5ddd8;
            --accent: #1f7a4d;
            --accent-hover: #18643f;
            --on-accent: #ffffff;
            --ok: #1a7a48;
            --warn: #9a5700;
            --err: #c02626;
            --shadow: 0 1px 3px rgba(20, 40, 30, 0.1);
        }
        @media (prefers-color-scheme: dark) {
            :root {
                --bg: #121715;
                --surface: #1c2320;
                --text: #e8eeeb;
                --muted: #a0ada7;
                --border: #36423c;
                --accent: #2f9e68;
                --accent-hover: #3bb378;
                --on-accent: #06140d;
                --ok: #5fd39a;
                --warn: #e8b05a;
                --err: #ff8a80;
                --shadow: none;
            }
        }
        * { box-sizing: border-box; }
        body {
            max-width: 720px;
            margin: 0 auto;
            padding: 16px 12px calc(24px + env(safe-area-inset-bottom));
            background: var(--bg);
            color: var(--text);
            font: 16px/1.5 system-ui, -apple-system, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
            -webkit-text-size-adjust: 100%;
        }
        h1 { font-size: 1.5rem; line-height: 1.25; margin: 4px 4px 0; }
        h2 { font-size: 1.1rem; margin: 0 0 8px; }
        h3 { font-size: 1rem; margin: 20px 0 0; padding-top: 16px; border-top: 1px solid var(--border); }
        label { display: block; font-size: 0.9rem; font-weight: 600; margin: 14px 0 6px; }
        input:not([type="submit"]), select {
            display: block;
            width: 100%;
            min-height: 46px;
            padding: 10px 12px;
            border: 1px solid var(--border);
            border-radius: 10px;
            background: var(--surface);
            color: var(--text);
            font: inherit;  /* 16px minimum : évite le zoom automatique sur iPhone */
        }
        input:focus-visible, select:focus-visible, .btn:focus-visible {
            outline: 2px solid var(--accent);
            outline-offset: 2px;
        }
        .section {
            margin-top: 12px;
            padding: 16px;
            background: var(--surface);
            border: 1px solid var(--border);
            border-radius: 14px;
            box-shadow: var(--shadow);
        }
        .field-row { display: grid; grid-template-columns: 1fr; column-gap: 12px; }
        .hint { font-size: 0.85rem; color: var(--muted); margin: 8px 0; }
        .status { font-size: 0.9rem; color: var(--muted); margin: 8px 0 0; overflow-wrap: anywhere; }
        .status:empty { display: none; }
        .status ul { padding-left: 20px; }
        #clock-status { margin: 2px 4px 0; }
        #camera-preview { width: 100%; margin-top: 12px; border-radius: 10px; }
        .btn {
            display: block;
            width: 100%;
            min-height: 48px;
            padding: 10px 18px;
            border: 1px solid transparent;
            border-radius: 10px;
            font: inherit;
            font-weight: 600;
            cursor: pointer;
            -webkit-appearance: none;
            appearance: none;
        }
        .btn:disabled { opacity: 0.6; cursor: wait; }
        .btn-primary { background: var(--accent); color: var(--on-accent); }
        .btn-primary:hover { background: var(--accent-hover); }
        .btn-secondary { background: transparent; color: var(--accent); border-color: var(--accent); margin-top: 16px; }
        .btn-secondary:hover { background: var(--bg); }
        .btn-danger { background: transparent; color: var(--err); border-color: var(--err); margin-top: 16px; }
        .btn-danger:hover { background: var(--bg); }
        .section > .btn-secondary:first-of-type { margin-top: 4px; }
        /* Le bouton d'enregistrement reste visible pendant le défilement du formulaire */
        .save-bar {
            position: sticky;
            bottom: 0;
            margin: 12px -12px 0;
            padding: 12px 12px calc(12px + env(safe-area-inset-bottom));
            background: var(--bg);
            border-top: 1px solid var(--border);
        }
        .ok, .err { margin: 12px 0 0; padding: 12px 14px; border-radius: 10px; color: #ffffff; font-weight: 600; }
        .ok { background: #1a7a48; }
        .err { background: #c02626; }
        @media (min-width: 560px) {
            body { padding-top: 28px; padding-left: 20px; padding-right: 20px; }
            .section { padding: 20px; }
            .field-row { grid-template-columns: 1fr 1fr; }
            .btn-secondary, .btn-danger { width: auto; }
            .save-bar { margin-left: -20px; margin-right: -20px; padding-left: 20px; padding-right: 20px; }
        }
    </style>
</head>

<script>
// ── Sync heure ────────────────────────────────────────────────────────────────
// Dès le chargement de la page, on envoie l'heure du navigateur au Pi.
// Cela règle l'horloge système puis synchronise la RTC WittyPi,
// sans aucune action de l'utilisateur.
document.addEventListener("DOMContentLoaded", function () {
    const now = new Date();
    const pad = n => String(n).padStart(2, "0");
    const iso = now.getFullYear() + "-" +
                pad(now.getMonth() + 1) + "-" +
                pad(now.getDate()) + "T" +
                pad(now.getHours()) + ":" +
                pad(now.getMinutes()) + ":" +
                pad(now.getSeconds());

    fetch("/sync_time", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ iso: iso })
    })
    .then(r => r.json())
    .then(data => {
        const el = document.getElementById("clock-status");
        if (data.status === "ok") {
            el.textContent = "✅ Heure synchronisée : " + iso;
            el.style.color = "var(--ok)";
        } else {
            el.textContent = "⚠️ Synchronisation de l'heure échouée";
            el.style.color = "var(--warn)";
        }
    })
    .catch(() => {
        document.getElementById("clock-status").textContent = "⚠️ Synchronisation de l'heure échouée";
    });
});

// ── Affichage conditionnel des champs ─────────────────────────────────────────
function updateUploadFields() {
    const type = document.getElementById("upload_type").value;
    document.getElementById("agrocam_fields").style.display =
        type === "agrocam" ? "block" : "none";
    document.getElementById("immich_fields").style.display =
        type === "immich" ? "block" : "none";
}

function updateFilterFields() {
    const doubleCaptureSelect = document.getElementById("photo_double_capture").value;
    document.getElementById("filter_fields").style.display =
        doubleCaptureSelect === "true" ? "block" : "none";
}

function updateFormatFields() {
    const formatSelect = document.getElementById("photo_format").value;
    document.getElementById("format_fields").style.display =
        formatSelect === "jpg" ? "block" : "none";
}

document.addEventListener("DOMContentLoaded", updateUploadFields);
document.addEventListener("DOMContentLoaded", updateFilterFields);
document.addEventListener("DOMContentLoaded", updateFormatFields);

// ── État de la clé 4G ─────────────────────────────────────────────────────────
function updateDongleStatus() {
    const el = document.getElementById("dongle-status");
    fetch("/dongle_status")
        .then(r => r.json())
        .then(data => {
            if (!data.detected) {
                el.textContent = "⚪ Clé 4G non détectée en USB";
                el.style.color = "var(--muted)";
            } else if (!data.readable) {
                el.textContent = "⚠️ Clé 4G détectée, état illisible";
                el.style.color = "var(--warn)";
            } else if (data.connected) {
                el.textContent = "✅ 4G connectée : " + data.operator + ", " + data.network + ", signal " + data.signal + "/5";
                el.style.color = "var(--ok)";
            } else {
                el.textContent = "❌ Clé 4G détectée, réseau 4G non connecté (signal " + data.signal + "/5)";
                el.style.color = "var(--err)";
            }
        })
        .catch(() => {
            el.textContent = "❌ Erreur de connexion";
            el.style.color = "var(--err)";
        });
}

document.addEventListener("DOMContentLoaded", function () {
    updateDongleStatus();
    setInterval(updateDongleStatus, 10000);
});

// ── Test d'envoi d'une photo ──────────────────────────────────────────────────
function showTestUploadResult(title, color, messages) {
    const el = document.getElementById("test-upload-status");
    el.textContent = title;
    el.style.color = color;
    if (messages && messages.length > 0) {
        const list = document.createElement("ul");
        list.style.margin = "4px 0";
        messages.forEach(message => {
            const item = document.createElement("li");
            item.textContent = message;
            list.appendChild(item);
        });
        el.appendChild(list);
    }
}

function testUpload() {
    const btn = document.getElementById("test-upload-button");
    const fieldValue = name => document.querySelector('[name="' + name + '"]').value;

    // L'aperçu occupe la caméra : on l'arrête proprement avant la photo
    if (document.getElementById("camera-preview").hasAttribute("src")) {
        togglePreview();
    }

    btn.disabled = true;
    showTestUploadResult("Prise de la photo et envoi en cours...", "var(--muted)");
    fetch("/test_upload", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
            url: fieldValue("immich_url"),
            api_key: fieldValue("immich_api_key"),
            album_id: fieldValue("immich_album_id"),
            timeout: fieldValue("sending_timeout")
        })
    })
    .then(r => r.json())
    .then(data => {
        if (data.status === "ok") {
            showTestUploadResult("✅ Photo envoyée et ajoutée à l'album", "var(--ok)");
        } else if (data.status === "partial") {
            showTestUploadResult("⚠️ Photo envoyée, mais avec des erreurs :", "var(--warn)", data.messages);
        } else {
            showTestUploadResult("❌ Envoi impossible :", "var(--err)", data.messages);
        }
    })
    .catch(() => {
        showTestUploadResult("❌ Erreur de connexion avec l'Agrocam", "var(--err)");
    })
    .finally(() => {
        btn.disabled = false;
    });
}

// ── Aperçu caméra ─────────────────────────────────────────────────────────────
function togglePreview() {
    const img = document.getElementById("camera-preview");
    const btn = document.getElementById("camera-button");
    const el = document.getElementById("camera-status");

    function hidePreview() {
        img.onload = null;
        img.onerror = null;
        img.removeAttribute("src");
        img.style.display = "none";
        btn.textContent = "Démarrer l'aperçu";
    }

    if (img.hasAttribute("src")) {
        hidePreview();
        el.textContent = "";
        fetch("/camera_stop", { method: "POST" })
            .then(r => r.json())
            .then(data => {
                if (data.status !== "ok") {
                    el.textContent = "❌ Erreur : " + data.message;
                    el.style.color = "var(--err)";
                }
            })
            .catch(() => {
                el.textContent = "❌ Erreur de connexion";
                el.style.color = "var(--err)";
            });
        return;
    }

    el.textContent = "Démarrage de la caméra...";
    el.style.color = "var(--muted)";
    btn.textContent = "Arrêter l'aperçu";
    img.onload = () => {
        el.textContent = "✅ Aperçu en direct, obturateur ouvert";
        el.style.color = "var(--ok)";
    };
    img.onerror = () => {
        hidePreview();
        el.textContent = "❌ Impossible d'afficher le flux de la caméra";
        el.style.color = "var(--err)";
    };
    img.src = "/camera_stream?t=" + Date.now();
    img.style.display = "block";
}

</script>

<body>

<h1>Configuration Agrocam</h1>
<p id="clock-status" class="status">Synchronisation de l'heure...</p>

{% if message %}
<p class="ok">{{ message }}</p>
{% endif %}
{% if error %}
<p class="err">{{ error }}</p>
{% endif %}

<div class="section">
    <h2>Connexion 4G</h2>
    <p id="dongle-status" class="status">Lecture de l'état de la clé 4G...</p>
</div>

<div class="section">
    <h2>Aperçu caméra</h2>
    <button type="button" id="camera-button" class="btn btn-secondary" onclick="togglePreview()">Démarrer l'aperçu</button>
    <p id="camera-status" class="status"></p>
    <img id="camera-preview" alt="Aperçu de la caméra" style="display:none;">
</div>


<form method="POST">
    <div class="section">
        <h2>Général</h2>
        <label>Heures de déclenchement [HH:MM:SS,HH:MM:SS]</label>
        <input name="trigger_times" value="{{ trigger_times }}">

        <label>Voltage minimum (en Volts) pour l'envoi des photos en attente</label>
        <input type="number" step="0.1" name="min_voltage_pending_photo" value="{{ c.general.min_voltage_pending_photo }}">

        <label>Voltage minimum (en Volts) pour le démarrage de l'Agrocam</label>
        <input type="number" step="0.1" name="threshold_voltage" value="{{ c.witty.threshold_voltage/10 }}">

        <label>Timeout pour l'envoi d'une photo</label>
        <input type="number" step="1" name="sending_timeout" value="{{ c.general.sending_timeout }}" min="1" max="60">
    </div>

    <div class="section">
        <h2>Destination des photos</h2>

        <label>Plateforme</label>
        <select name="upload_type" id="upload_type" onchange="updateUploadFields()">
            <option value="agrocam" {% if c.upload.type == "agrocam" %}selected{% endif %}>Agrocam</option>
            <option value="immich" {% if c.upload.type == "immich" %}selected{% endif %}>Immich</option>
        </select>

        <!-- Agrocam -->
        <div id="agrocam_fields">
            <label>URL Agrocam</label>
            <input name="agrocam_url" value="{{ c.upload.agrocam.url }}">

            <label>Nom Agrocam (8 caractères)</label>
            <input name="agrocam_name" value="{{ c.upload.agrocam.name }}">
        </div>

        <!-- Immich -->
        <div id="immich_fields">
            <label>URL Immich</label>
            <input name="immich_url" value="{{ c.upload.immich.url }}">

            <label>API Key Immich</label>
            <input name="immich_api_key" value="{{ c.upload.immich.api_key }}">

            <label>Album ID</label>
            <input name="immich_album_id" value="{{ c.upload.immich.album_id }}">

            <button type="button" id="test-upload-button" class="btn btn-secondary" onclick="testUpload()">Tester l'envoi d'une photo</button>
            <p class="hint">Envoie une vraie photo vers l'album avec les champs ci-dessus, même non enregistrés. Les réglages de la section Photo doivent être enregistrés pour être pris en compte.</p>
            <div id="test-upload-status" class="status"></div>
        </div>
    </div>

    <div class="section">
        <h2>WiFi</h2>
        <label>SSID</label>
        <input name="wifi_ssid" value="{{ c.wifi.ssid }}">

        <label>Mot de passe</label>
        <input name="wifi_password" value="{{ c.wifi.password }}">

        <label>Timeout WiFi (secondes)</label>
        <input type="number" name="wifi_timeout" value="{{ c.wifi.timeout }}">
    </div>

    <div class="section">
        <h2>Photo</h2>
        <label>Format</label>
        <p class="hint">Le format JPEG est recommandé pour réduire la taille des fichiers, mais le PNG peut être utilisé si vous souhaitez une qualité maximale sans compression.</p>
        <select name="photo_format" id="photo_format" onchange="updateFormatFields()">
            <option value="jpg" {% if c.photo.format == "jpg" %}selected{% endif %}>JPEG (compressé)</option>
            <option value="png" {% if c.photo.format == "png" %}selected{% endif %}>PNG (non compressé)</option>
        </select>
        <div id="format_fields">
            <label>Qualité (10 à 100%)</label>
            <input type="number" name="photo_quality" value="{{ c.photo.quality }}" min="10" max="100">
        </div>

        <div class="field-row">
            <div>
                <label>Latitude (optionnel)</label>
                <input type="text" name="photo_latitude" value="{{ c.photo.location.latitude }}">
            </div>
            <div>
                <label>Longitude (optionnel)</label>
                <input type="text" name="photo_longitude" value="{{ c.photo.location.longitude }}">
            </div>
        </div>

        <div class="field-row">
            <div>
                <label>Largeur (max 4608)</label>
                <input type="number" name="photo_width" value="{{ c.photo.size.width }}" min="1" max="4608">
            </div>
            <div>
                <label>Hauteur (max 2592)</label>
                <input type="number" name="photo_height" value="{{ c.photo.size.height }}" min="1" max="2592">
            </div>
        </div>

        <label>Timeout Photo (ms)</label>
        <input type="number" name="photo_timeout" value="{{ c.photo.timeout }}" min="0">
    </div>

    <div class="section">
        <h2>Filtre</h2>
        <label>Activation double capture</label>
        <select name="photo_double_capture" id="photo_double_capture" onchange="updateFilterFields()">
            <option value="false" {% if not c.photo.double_capture %}selected{% endif %}>Non</option>
            <option value="true" {% if c.photo.double_capture %}selected{% endif %}>Oui</option>
        </select>

        <div id="filter_fields">
            <h3>Filtre 1</h3>
            <div class="field-row">
                <div>
                    <label>Tag filtre 1</label>
                    <input name="filter1_tag" value="{{ c.photo.filters[0].tag if c.photo.filters|length > 0 else 'nofilter' }}">
                </div>
                <div>
                    <label>Angle filtre 1</label>
                    <input type="number" name="filter1_angle" value="{{ c.photo.filters[0].angle if c.photo.filters|length > 0 else 0 }}" min="0" max="180">
                </div>
            </div>

            <h3>Filtre 2</h3>
            <div class="field-row">
                <div>
                    <label>Tag filtre 2</label>
                    <input name="filter2_tag" value="{{ c.photo.filters[1].tag if c.photo.filters|length > 1 else 'filter' }}">
                </div>
                <div>
                    <label>Angle filtre 2</label>
                    <input type="number" name="filter2_angle" value="{{ c.photo.filters[1].angle if c.photo.filters|length > 1 else 90 }}" min="0" max="180">
                </div>
            </div>
        </div>
    </div>

    <div class="save-bar">
        <input type="submit" class="btn btn-primary" value="Enregistrer les modifications">
    </div>
</form>

<form method="POST" action="/shutdown" onsubmit="return confirm('Éteindre le système ?');">
    <input type="submit" class="btn btn-danger" value="Shutdown">
</form>


</body>
</html>
"""

# ---------- Utils ----------

def load_credentials():
    with open(CREDENTIALS_FILE, "r") as f:
        return json.load(f)

def save_credentials(data):
    with open(CREDENTIALS_FILE, "w") as f:
        json.dump(data, f, indent=4)

def valid_time(t):
    return re.match(r"^\d{2}:\d{2}:\d{2}$", t) is not None

def move_shutter(angle):
    creds = load_credentials()
    with ServoManager(creds["servo"]["gpio_shutter"], creds["servo"]["gpio_filter"]) as servo:
        move_servo(servo.shutter, angle)

def terminate_process(process):
    process.terminate()
    try:
        process.wait(timeout=3)
    except subprocess.TimeoutExpired:
        process.kill()
        process.wait()

def start_preview():
    """Ouvre l'obturateur et lance la capture MJPEG, en remplaçant le flux en cours s'il existe."""
    global preview_process
    with preview_lock:
        if preview_process is not None:
            terminate_process(preview_process)
            preview_process = None

        # Même cadrage que les photos : la hauteur suit le ratio configuré (valeur paire)
        size = load_credentials()["photo"]["size"]
        height = round(PREVIEW_WIDTH * size["height"] / size["width"] / 2) * 2

        move_shutter(SHUTTER_OPEN_ANGLE)
        preview_process = subprocess.Popen(
            ["rpicam-vid", "-t", "0", "--nopreview", "--codec", "mjpeg", "--flush",
             "--width", str(PREVIEW_WIDTH), "--height", str(height),
             "--framerate", str(PREVIEW_FRAMERATE), "--verbose", "0", "-o", "-"],
            stdout=subprocess.PIPE
        )
        return preview_process

def stop_preview(owner=None):
    """
    Arrête le flux et referme l'obturateur. Si owner est fourni, ne fait rien
    lorsqu'un flux plus récent a pris le relais de ce processus.
    """
    global preview_process
    with preview_lock:
        if preview_process is None or (owner is not None and preview_process is not owner):
            return
        terminate_process(preview_process)
        preview_process = None
        move_shutter(SHUTTER_CLOSED_ANGLE)

def generate_frames(process):
    """
    Découpe la sortie de rpicam-vid en images JPEG pour un flux multipart.
    Le finally libère la caméra dès que le navigateur ferme le flux (page quittée
    ou rechargée) : call_on_close n'est pas fiable, Werkzeug peut lever une
    exception sur une connexion coupée avant d'appeler close().
    """
    buffer = b""
    try:
        while True:
            chunk = process.stdout.read1(65536)
            if not chunk:
                return
            buffer += chunk
            end = buffer.find(b"\xff\xd9")
            while end != -1:
                frame, buffer = buffer[:end + 2], buffer[end + 2:]
                yield b"--frame\r\nContent-Type: image/jpeg\r\n\r\n" + frame + b"\r\n"
                end = buffer.find(b"\xff\xd9")
    finally:
        stop_preview(process)

def read_dongle_status():
    if not os.path.exists(f"/sys/class/net/{USB_INTERFACE}"):
        return {"detected": False}

    try:
        response = requests.post(DONGLE_API_URL, json={"funcNo": DONGLE_STATUS_FUNC}, timeout=3)
        data = response.json()
        if str(data.get("flag")) != "1":
            raise ValueError(data.get("error_info"))
        result = data["results"][0]
    except (requests.RequestException, ValueError, KeyError, IndexError, TypeError, AttributeError) as e:
        print(f"[4G] État illisible : {e}", file=__import__('sys').stderr)
        return {"detected": True, "readable": False}

    return {
        "detected": True,
        "readable": True,
        "connected": str(result.get("netstatus", "")).lower() == "connected",
        "operator": result.get("oper", "opérateur inconnu"),
        "network": result.get("netmode", "réseau inconnu"),
        "signal": result.get("rssi", 0)
    }

def validate_immich_fields(url, api_key, album_id, timeout):
    """Retourne tous les problèmes des champs du formulaire, pour les afficher en une fois."""
    errors = []
    if not url:
        errors.append("Champ manquant : URL Immich")
    elif not url.startswith(("http://", "https://")):
        errors.append("URL Immich invalide : elle doit commencer par http:// ou https://")
    if not api_key:
        errors.append("Champ manquant : API Key Immich")
    if not album_id:
        errors.append("Champ manquant : Album ID")
    if not timeout.isdigit() or int(timeout) < 1:
        errors.append("Timeout pour l'envoi d'une photo invalide : il doit être un entier positif")
    return errors

# ---------- Routes ----------

@app.route("/sync_time", methods=["POST"])
def sync_time():
    """
    Reçoit l'heure du navigateur (ISO local) et règle l'horloge système
    puis synchronise la RTC WittyPi. Appelé automatiquement au chargement
    de la page — aucune action utilisateur requise.
    """
    data = request.get_json()
    iso_time = data.get("iso") if data else None
    if not iso_time:
        return {"status": "error", "message": "Pas d'heure fournie"}, 400

    try:
        subprocess.run(["sudo", "date", "-s", iso_time],
                       check=True, capture_output=True, timeout=5)
        subprocess.run(
            ["sudo", "bash", "-c",
             "source /home/pi/wittypi/utilities.sh && system_to_rtc"],
            capture_output=True, timeout=5
        )
        print(f"[SYNC] Heure réglée : {iso_time}")
        return {"status": "ok", "time": iso_time}
    except subprocess.CalledProcessError as e:
        print(f"[SYNC] Erreur : {e}", file=__import__('sys').stderr)
        return {"status": "error", "message": str(e)}, 500


@app.route("/", methods=["GET", "POST"])
def index():
    error = None
    message = None
    creds = load_credentials()

    # Compatibilité ancienne config
    creds.setdefault("photo", {})
    creds["photo"].setdefault("double_capture", False)
    creds["photo"].setdefault("filters", [
        {"tag": "nofilter", "angle": 0},
        {"tag": "filter", "angle": 90}
    ])

    # Compatibilité avec l'ancien schéma angle unique
    if "filter_angle_open" in creds["photo"] and "filter_angle_active" in creds["photo"] and not creds["photo"].get("filters"):
        creds["photo"]["filters"] = [
            {"tag": "nofilter", "angle": int(creds["photo"].get("filter_angle_open", 0))},
            {"tag": "filter", "angle": int(creds["photo"].get("filter_angle_active", 90))}
        ]

    if request.method == "POST":
        # ---------- Validation ----------
        wifi_timeout = request.form["wifi_timeout"].strip()
        if not wifi_timeout.isdigit():
            error = "Le timeout WiFi doit être un entier."

        trigger_raw = request.form["trigger_times"].strip().strip("[]")
        triggers = []
        if trigger_raw:
            for part in trigger_raw.split(","):
                part = part.strip()
                if not valid_time(part):
                    error = "Trigger times invalide (format HH:MM:SS)."
                triggers.append(part)

        try:
            width = int(request.form["photo_width"])
            height = int(request.form["photo_height"])
            if not (1 <= width <= 4608):
                error = "Largeur invalide (1-4608)."
            if not (1 <= height <= 2592):
                error = "Hauteur invalide (1-2592)."
        except ValueError:
            error = "Largeur et hauteur doivent être des entiers."

        # ---------- Sauvegarde si OK ----------
        if error is None:
            upload_type = request.form["upload_type"]
            creds["upload"]["type"] = upload_type

            if upload_type == "agrocam":
                name = request.form["agrocam_name"].strip()
                if len(name) != 8:
                    error = "Le nom Agrocam doit contenir exactement 8 caractères."
                creds["upload"]["agrocam"]["url"] = request.form["agrocam_url"].strip()
                creds["upload"]["agrocam"]["name"] = name

            elif upload_type == "immich":
                creds["upload"]["immich"]["url"] = request.form["immich_url"].strip()
                creds["upload"]["immich"]["api_key"] = request.form["immich_api_key"].strip()
                creds["upload"]["immich"]["album_id"] = request.form["immich_album_id"].strip()

            lat_str = request.form.get("photo_latitude", "").strip()
            lon_str = request.form.get("photo_longitude", "").strip()

            creds["general"]["trigger_times"] = triggers
            creds["general"]["min_voltage_pending_photo"] = float(request.form["min_voltage_pending_photo"])
            creds["general"]["sending_timeout"] = int(request.form["sending_timeout"])

            creds["witty"]["threshold_voltage"] = int(float(request.form["threshold_voltage"]) * 10)

            creds["wifi"]["ssid"] = request.form["wifi_ssid"].strip()
            creds["wifi"]["password"] = request.form["wifi_password"].strip()
            creds["wifi"]["timeout"] = int(wifi_timeout)

            creds["photo"]["format"] = request.form["photo_format"]
            creds["photo"]["size"]["width"] = width
            creds["photo"]["size"]["height"] = height
            creds["photo"]["timeout"] = int(request.form["photo_timeout"])
            creds["photo"]["quality"] = int(request.form["photo_quality"])
            creds["photo"]["location"]["latitude"] = float(lat_str) if lat_str else 0.0
            creds["photo"]["location"]["longitude"] = float(lon_str) if lon_str else 0.0
            creds["photo"]["double_capture"] = request.form.get("photo_double_capture", "false") == "true"

            filter1_tag = request.form.get("filter1_tag", "nofilter").strip() or "nofilter"
            filter2_tag = request.form.get("filter2_tag", "filter").strip() or "filter"
            filter1_angle = int(request.form.get("filter1_angle", "0"))
            filter2_angle = int(request.form.get("filter2_angle", "90"))

            creds["photo"]["filters"] = [
                {"tag": filter1_tag, "angle": filter1_angle},
                {"tag": filter2_tag, "angle": filter2_angle}
            ]

            save_credentials(creds)
            day, hour, minute, second = calculate_next_startup_time(creds["general"]["trigger_times"])
            set_startup_time(day, hour, minute, second)
            setup_wittypi()
            message = "Modifications enregistrées ✔"

    trigger_times = "[" + ",".join(creds["general"]["trigger_times"]) + "]"

    return render_template_string(
        HTML_FORM,
        c=creds,
        trigger_times=trigger_times,
        message=message,
        error=error
    )


@app.route("/shutdown", methods=["POST"])
def shutdown():
    subprocess.Popen(["sudo", "shutdown", "-h", "now"])
    return "<h1>Arrêt du système en cours...</h1>"

@app.route("/test_upload", methods=["POST"])
def test_upload():
    """
    Prend une photo et l'envoie vers Immich avec les fonctions de agrocam.py.
    La photo passe par un dossier temporaire : elle n'est pas conservée et ne sera
    donc pas renvoyée comme photo en attente. Le réseau reste celui en place, car
    wait_for_network() couperait le hotspot en se connectant au Wi-Fi.
    """
    data = request.get_json(silent=True) or {}
    url = str(data.get("url", "")).strip()
    api_key = str(data.get("api_key", "")).strip()
    album_id = str(data.get("album_id", "")).strip()
    timeout = str(data.get("timeout", "")).strip()

    errors = validate_immich_fields(url, api_key, album_id, timeout)
    if errors:
        return {"status": "error", "messages": errors}, 400

    upload_errors = []
    try:
        # Import tardif : un problème dans agrocam.py ne doit pas rendre la page inaccessible
        import agrocam
        agrocam.credentials = load_credentials()

        stop_preview()
        with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as dir_path:
            with preview_lock:
                move_shutter(SHUTTER_OPEN_ANGLE)
                try:
                    filepath = agrocam.prendre_photo(
                        None,
                        extension=agrocam.credentials["photo"]["format"],
                        tag="test",
                        dir_path=dir_path
                    )
                finally:
                    move_shutter(SHUTTER_CLOSED_ANGLE)

            asset = agrocam.envoyer_http_immich(
                filepath, url, api_key, album_id,
                timeout=int(timeout), errors=upload_errors
            )
    except subprocess.CalledProcessError as e:
        # prendre_photo échoue au chmod quand rpicam-still n'a pas créé le fichier
        print(f"[TEST] Erreur : {e}", file=__import__('sys').stderr)
        return {"status": "error", "messages": ["La caméra n'a pas produit de photo : vérifiez son branchement"]}, 500
    except Exception as e:
        print(f"[TEST] Erreur : {e}", file=__import__('sys').stderr)
        return {"status": "error", "messages": [f"Test impossible : {e}"]}, 500

    if asset is None:
        return {"status": "error", "messages": upload_errors}, 502
    if upload_errors:
        return {"status": "partial", "messages": upload_errors}
    return {"status": "ok"}

@app.route("/dongle_status")
def dongle_status():
    return read_dongle_status()

@app.route("/camera_stream")
def camera_stream():
    try:
        process = start_preview()
    except Exception as e:
        print(f"[CAMERA] Erreur : {e}", file=__import__('sys').stderr)
        return {"status": "error", "message": str(e)}, 500

    response = Response(generate_frames(process), mimetype="multipart/x-mixed-replace; boundary=frame")
    response.headers["Cache-Control"] = "no-store"
    return response

@app.route("/camera_stop", methods=["POST"])
def camera_stop():
    try:
        stop_preview()
        return {"status": "ok"}
    except Exception as e:
        return {"status": "error", "message": str(e)}, 500


if __name__ == "__main__":
    # "::" écoute aussi en IPv4 sous Linux : agrocam.local peut ne résoudre qu'en IPv6
    host = "::" if os.path.exists("/proc/net/if_inet6") else "0.0.0.0"
    app.run(host=host, port=5000, debug=False, use_reloader=False)