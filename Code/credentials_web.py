#!/usr/bin/env python3
from flask import Flask, request, render_template_string
import json
import os
import re
import subprocess

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
    </style>
</head>
<body>

<h1>Configuration Agrocam</h1>

{% if message %}
<p class="ok">{{ message }}</p>
{% endif %}
{% if error %}
<p class="err">{{ error }}</p>
{% endif %}

<hr> 

<form method="POST" action="/shutdown" onsubmit="return confirm('Éteindre le système ?');">
    <input type="submit" value="Shutdown" style="background:#c00;color:white;font-weight:bold;width:auto;">
</form>

<form method="POST">
    <div class="section">
        <h2>Général</h2>
        <label>URL API</label>
        <input name="url_api" value="{{ c.general.url_api }}">

        <label>Clé de l'Agrocam (8 caractères)</label>
        <input name="name" value="{{ c.general.name }}">

        <label>Heures de déclenchement [HH:MM:SS,HH:MM:SS]</label>
        <input name="trigger_times" value="{{ trigger_times }}">
        
        <label>Voltage minimum (en Volts)</label>
        <input type="number" step="0.1" name="min_voltage_pending_photo" value="{{ c.general.min_voltage_pending_photo }}">

        <label>Timeout pour l'envoi d'une photo</label>
        <input type="number" step="1" name="sending_timeout" value="{{ c.general.sending_timeout }}" min="1" max="60" >
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
        <label>Largeur (max 4608)</label>
        <input type="number" name="photo_width" value="{{ c.photo.size.width }}" min="1" max="4608">

        <label>Hauteur (max 2592)</label>
        <input type="number" name="photo_height" value="{{ c.photo.size.height }}" min="1" max="2592">

        <label>Extension</label>
        <select name="photo_extension">
            <option value=".png" {% if c.photo.extension == ".png" %}selected{% endif %}>.png</option>
            <option value=".jpg" {% if c.photo.extension == ".jpg" %}selected{% endif %}>.jpg</option>
        </select>

        <label>Qualité (10 à 100%)</label>
        <input type="number" name="photo_quality" value="{{ c.photo.quality }}" min="10" max="100">

        <label>Timeout Photo (ms)</label>
        <input type="number" name="photo_timeout" value="{{ c.photo.timeout }}" min="0">

    </div>

    <input type="submit" class="btn-save" value="Enregistrer les modifications">
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

# ---------- Route ----------

@app.route("/", methods=["GET", "POST"])
def index():
    error = None
    message = None
    creds = load_credentials()

    if request.method == "POST":
        # ---------- Validation ----------
        name = request.form["name"].strip()
        if len(name) != 8:
            error = "Le champ name doit contenir exactement 8 caractères."

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

        # Largeur / hauteur photo
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
            creds["general"]["url_api"] = request.form["url_api"].strip()
            creds["general"]["name"] = name
            creds["general"]["trigger_times"] = triggers
            creds["general"]["min_voltage_pending_photo"]=float(request.form["min_voltage_pending_photo"])
            creds["general"]["sending_timeout"]=int(request.form["sending_timeout"])

            creds["wifi"]["ssid"] = request.form["wifi_ssid"].strip()
            creds["wifi"]["password"] = request.form["wifi_password"].strip()
            creds["wifi"]["timeout"] = int(wifi_timeout)

            creds["photo"]["size"]["width"] = width
            creds["photo"]["size"]["height"] = height
            creds["photo"]["extension"] = request.form["photo_extension"]
            creds["photo"]["timeout"]=int(request.form["photo_timeout"])
            creds["photo"]["quality"]=int(request.form["photo_quality"])

            save_credentials(creds)
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

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False, use_reloader=False)
