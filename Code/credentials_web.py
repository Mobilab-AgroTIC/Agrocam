from flask import Flask, request, render_template_string
import os
from datetime import time
import ast

CREDENTIALS_FILE = "credentials.py"

app = Flask(__name__)

HTML_FORM = """
<!DOCTYPE html>
<html>
<head>
    <title>Édition credentials.py</title>
</head>
<body>
    <h1>Édition credentials.py</h1>
    <form method="POST">
    {% for var, value in variables.items() %}
        <label>{{ var }}:</label><br>
        <input type="text" name="{{ var }}" value="{{ value }}"><br><br>
    {% endfor %}
        <input type="submit" value="Enregistrer">
    </form>
</body>
</html>
"""

def read_credentials():
    """Lit le fichier credentials.py et renvoie un dict {var: valeur}"""
    variables = {}
    if os.path.exists(CREDENTIALS_FILE):
        with open(CREDENTIALS_FILE) as f:
            content = f.read()
        try:
            # On exécute le fichier dans un dictionnaire temporaire pour récupérer les variables
            temp = {}
            exec(content, {}, temp)
            # On filtre les objets valides (exclut builtins)
            for k, v in temp.items():
                if not k.startswith("__"):
                    # Convertit time en string lisible, listes et autres via repr()
                    if isinstance(v, time):
                        variables[k] = v.strftime("%H:%M:%S")
                    else:
                        variables[k] = repr(v)
        except Exception as e:
            print(f"Erreur lecture credentials.py: {e}")
    return variables

def write_credentials(data):
    """Écrit le fichier credentials.py avec les données fournies"""
    lines = []
    for k, v in data.items():
        # Tente d'évaluer la valeur pour garder les types
        try:
            val = ast.literal_eval(v)
        except Exception:
            # sinon on laisse en string
            val = v
            val = f'"{val}"'
        # Si c’est une heure sous format HH:MM:SS
        if isinstance(val, str) and ":" in val:
            try:
                h, m, s = map(int, val.split(":"))
                val = f"time({h},{m},{s})"
            except:
                pass
        lines.append(f"{k} = {val}")
    with open(CREDENTIALS_FILE, "w") as f:
        f.write("\n".join(lines))
        f.write("\n")

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        data = {k: request.form[k] for k in request.form}
        write_credentials(data)
        return "<h2>Modifications enregistrées ! Redémarrez le script principal pour appliquer.</h2>"
    
    variables = read_credentials()
    return render_template_string(HTML_FORM, variables=variables)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
