#!/usr/bin/env python3
from flask import Flask, request, render_template_string
import json
import os
import re
import subprocess
from wittypi import set_startup_time, calculate_next_startup_time, setup_wittypi
from servo import hello_world_servo, ServoManager
CREDENTIALS_FILE = "/home/pi/credentials.json"

app = Flask(__name__)


HTML_FORM = """
<!DOCTYPE html>
<html>
<head>
    <title>Configuration Agrocam</title>
    <style>
        body { font-family: sans-serif; max-width: 700px; margin: auto; padding: 20px; }
        label { font-weight: bold; display: block; margin-top: 10px; }
        input, select { width: 100%; padding: 8px; margin-bottom: 10px; box-sizing: border-box; }
        .section { border-top: 1px solid #ccc; margin-top: 20px; padding-top: 10px; }
        .ok { color: white; background: green; padding: 10px; }
        .err { color: white; background: red; padding: 10px; }
        .btn-save { background: #007bff; color: white; font-weight: bold; cursor: pointer; border: none; padding: 10px; margin-top: 20px; }
        #clock-status { font-size: 0.85em; color: gray; margin: 4px 0 0 0; }
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
            el.style.color = "green";
        } else {
            el.textContent = "⚠️ Synchronisation de l'heure échouée";
            el.style.color = "orange";
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

function testServo() {
    const el = document.getElementById("servo-status");
    el.textContent = "Activation en cours...";
    el.style.color = "gray";
    fetch("/test_servo", { method: "POST" })
        .then(r => r.json())
        .then(data => {
            el.textContent = data.status === "ok" ? "✅ Servo activé" : "❌ Erreur : " + data.message;
            el.style.color = data.status === "ok" ? "green" : "red";
        })
        .catch(() => {
            el.textContent = "❌ Erreur de connexion";
            el.style.color = "red";
        });
}

</script>

<body>

<h1>Configuration Agrocam</h1>
<p id="clock-status">Synchronisation de l'heure...</p>

{% if message %}
<p class="ok">{{ message }}</p>
{% endif %}
{% if error %}
<p class="err">{{ error }}</p>
{% endif %}

<hr>

<button type="button" onclick="testServo()" style="background:#8b7ad6;color:black;font-weight:bold;padding:10px;border:none;cursor:pointer;">Test Servo</button>
<p id="servo-status" style="font-size:0.85em;color:gray;margin:4px 0;"></p>


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
        <p>Le format JPEG est recommandé pour réduire la taille des fichiers, mais le PNG peut être utilisé si vous souhaitez une qualité maximale sans compression.</p>
        <select name="photo_format" id="photo_format" onchange="updateFormatFields()">
            <option value="jpg" {% if c.photo.format == "jpg" %}selected{% endif %}>JPEG (compressé)</option>
            <option value="png" {% if c.photo.format == "png" %}selected{% endif %}>PNG (non compressé)</option>
        </select>
        <div id="format_fields">
            <label>Qualité (10 à 100%)</label>
            <input type="number" name="photo_quality" value="{{ c.photo.quality }}" min="10" max="100">
        </div>

        <label>Latitude (optionnel)</label>
        <input type="text" name="photo_latitude" value="{{ c.photo.location.latitude }}">
        <label>Longitude (optionnel)</label>
        <input type="text" name="photo_longitude" value="{{ c.photo.location.longitude }}">

        <label>Largeur (max 4608)</label>
        <input type="number" name="photo_width" value="{{ c.photo.size.width }}" min="1" max="4608">

        <label>Hauteur (max 2592)</label>
        <input type="number" name="photo_height" value="{{ c.photo.size.height }}" min="1" max="2592">

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
            <label>Tag filtre 1</label>
            <input name="filter1_tag" value="{{ c.photo.filters[0].tag if c.photo.filters|length > 0 else 'nofilter' }}">
            <label>Angle filtre 1</label>
            <input type="number" name="filter1_angle" value="{{ c.photo.filters[0].angle if c.photo.filters|length > 0 else 0 }}" min="0" max="180">

            <h3>Filtre 2</h3>
            <label>Tag filtre 2</label>
            <input name="filter2_tag" value="{{ c.photo.filters[1].tag if c.photo.filters|length > 1 else 'filter' }}">
            <label>Angle filtre 2</label>
            <input type="number" name="filter2_angle" value="{{ c.photo.filters[1].angle if c.photo.filters|length > 1 else 90 }}" min="0" max="180">
        </div>
    </div>

    <input type="submit" class="btn-save" value="Enregistrer les modifications">
</form>

<form method="POST" action="/shutdown" onsubmit="return confirm('Éteindre le système ?');">
    <input type="submit" value="Shutdown" style="background:#c00;color:white;font-weight:bold;width:auto;">
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

@app.route("/test_servo", methods=["POST"])
def servo():
    try:
        creds = load_credentials()
        with ServoManager(creds["servo"]["gpio_shutter"], creds["servo"]["gpio_filter"]) as servo:
            hello_world_servo(servo.shutter)
            hello_world_servo(servo.filter)
        return {"status": "ok"}
    except Exception as e:
        return {"status": "error", "message": str(e)}, 500


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False, use_reloader=False)