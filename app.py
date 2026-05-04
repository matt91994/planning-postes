from flask import Flask, request, jsonify, send_file, make_response, session, redirect
from flask_cors import CORS
import openpyxl
import json
import io
import os
import psycopg2
import psycopg2.extras

app = Flask(__name__)
CORS(app)
app.secret_key = os.environ.get('SECRET_KEY', 'planning-secret-2026')

ADMIN_PASSWORD = os.environ.get('ADMIN_PASSWORD', 'planning2026')
DATABASE_URL = os.environ.get('DATABASE_URL', 'postgresql://planning_db_xumh_user:VlIqUA6kVy2TR71IUvVvd1AjpMm1KcCf@dpg-d7sivcegkk3c73d9ah20-a/planning_db_xumh')

def get_db():
    conn = psycopg2.connect(DATABASE_URL)
    return conn

def init_db():
    conn = get_db()
    cur = conn.cursor()
    cur.execute('''CREATE TABLE IF NOT EXISTS config (key TEXT PRIMARY KEY, value TEXT NOT NULL)''')
    cur.execute("SELECT value FROM config WHERE key='postes'")
    if not cur.fetchone():
        postes_defaut = [
            {"id":1,"nom":"Déchargement","cellule":"F23","priorite":1},
            {"id":2,"nom":"Frigo","cellule":"F28","priorite":1},
            {"id":3,"nom":"Coupe droite","cellule":"I32","priorite":1},
            {"id":4,"nom":"Coupe gauche","cellule":"I20","priorite":1},
            {"id":5,"nom":"Lève droite 1","cellule":"M32","priorite":1},
            {"id":6,"nom":"Lève droite 2","cellule":"Q32","priorite":1},
            {"id":7,"nom":"Lève gauche 1","cellule":"M19","priorite":1},
            {"id":8,"nom":"Lève gauche 2","cellule":"P19","priorite":1},
            {"id":9,"nom":"Longe droite","cellule":"U32","priorite":1},
            {"id":10,"nom":"Longe gauche","cellule":"U19","priorite":1},
            {"id":11,"nom":"Bout du tapis","cellule":"W28","priorite":1},
            {"id":12,"nom":"Bout du tapis poitrine","cellule":"S10","priorite":1},
            {"id":13,"nom":"Poitrine","cellule":"P15","priorite":1},
            {"id":14,"nom":"BK doc1","cellule":"M17","priorite":1},
            {"id":15,"nom":"BK doc2","cellule":"M15","priorite":1},
            {"id":16,"nom":"BK commande","cellule":"M13","priorite":1},
            {"id":17,"nom":"Jambon","cellule":"K10","priorite":1},
            {"id":18,"nom":"Jambon aide","cellule":"H15","priorite":1},
            {"id":19,"nom":"Palette doc1","cellule":"U17","priorite":2},
            {"id":20,"nom":"Palette doc2","cellule":"U15","priorite":2},
            {"id":21,"nom":"Doc1","cellule":"X8","priorite":2},
            {"id":22,"nom":"Doc2","cellule":"X1","priorite":2},
            {"id":23,"nom":"Doc3","cellule":"AD8","priorite":2},
            {"id":24,"nom":"Doc4","cellule":"AD1","priorite":3},
            {"id":25,"nom":"Doc5","cellule":"AA1","priorite":3},
            {"id":26,"nom":"Doc6","cellule":"AA8","priorite":3},
        ]
        cur.execute("INSERT INTO config VALUES (%s,%s)", ('postes', json.dumps(postes_defaut)))
        cur.execute("INSERT INTO config VALUES (%s,%s)", ('employes', '[]'))
        cur.execute("INSERT INTO config VALUES (%s,%s)", ('nextEmpId', '1'))
        cur.execute("INSERT INTO config VALUES (%s,%s)", ('nextPostId', '27'))
    conn.commit()
    cur.close()
    conn.close()

init_db()

def is_logged_in():
    return session.get('logged_in') == True

LOGIN_PAGE = '''<!DOCTYPE html>
<html lang="fr">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Planning — Connexion</title>
<link href="https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;600;700;800&display=swap" rel="stylesheet">
<style>
  * { box-sizing: border-box; margin: 0; padding: 0; }
  body { font-family: "DM Sans", sans-serif; background: #0d1117; min-height: 100vh; display: flex; align-items: center; justify-content: center; }
  .box { background: #161b22; border: 1px solid #30363d; border-radius: 16px; padding: 40px 36px; width: 100%; max-width: 380px; margin: 16px; }
  .logo-icon { font-size: 40px; text-align: center; margin-bottom: 10px; }
  h1 { color: #fff; font-size: 20px; font-weight: 800; text-align: center; }
  .subtitle { color: #7d8590; font-size: 13px; text-align: center; margin-top: 4px; margin-bottom: 28px; }
  label { display: block; font-size: 12px; font-weight: 700; color: #7d8590; text-transform: uppercase; letter-spacing: 1px; margin-bottom: 6px; }
  input[type=password] { width: 100%; padding: 11px 14px; border-radius: 8px; background: #21262d; border: 1px solid #30363d; color: #e6edf3; font-size: 15px; font-family: "DM Sans", sans-serif; outline: none; margin-bottom: 16px; }
  input[type=password]:focus { border-color: #388bfd; }
  button { width: 100%; padding: 12px; border-radius: 8px; border: none; background: linear-gradient(90deg, #388bfd, #a371f7); color: #fff; font-size: 15px; font-weight: 700; cursor: pointer; font-family: "DM Sans", sans-serif; }
  .error { background: #3a111133; border: 1px solid #f8514966; border-radius: 8px; padding: 10px 14px; color: #fca5a5; font-size: 13px; margin-bottom: 16px; text-align: center; }
</style>
</head>
<body>
<div class="box">
  <div class="logo-icon">📋</div>
  <h1>Planning des Postes</h1>
  <p class="subtitle">Accès réservé à l équipe</p>
  {error}
  <form method="POST" action="/login">
    <label>Mot de passe</label>
    <input type="password" name="password" placeholder="••••••••" autofocus>
    <button type="submit">Se connecter</button>
  </form>
</div>
</body>
</html>'''

@app.route('/')
def index():
    if not is_logged_in():
        return make_response(LOGIN_PAGE.replace('{error}', ''), 200)
    try:
        with open(os.path.join(os.path.dirname(__file__), 'static', 'index.html'), 'r', encoding='utf-8') as f:
            html = f.read()
        resp = make_response(html)
        resp.headers['Content-Type'] = 'text/html; charset=utf-8'
        return resp
    except FileNotFoundError:
        return "Fichier index.html introuvable", 404

@app.route('/login', methods=['POST'])
def login():
    password = request.form.get('password', '')
    if password == ADMIN_PASSWORD:
        session['logged_in'] = True
        return redirect('/')
    error = '<div class="error">❌ Mot de passe incorrect</div>'
    return make_response(LOGIN_PAGE.replace('{error}', error), 401)

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/')

@app.route('/config', methods=['GET'])
def get_config():
    if not is_logged_in():
        return jsonify({'error': 'Non autorisé'}), 401
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT key, value FROM config")
    rows = cur.fetchall()
    cur.close()
    conn.close()
    data = {}
    for key, value in rows:
        try:
            data[key] = json.loads(value)
        except:
            data[key] = value
    return jsonify(data)

@app.route('/config', methods=['POST'])
def save_config():
    if not is_logged_in():
        return jsonify({'error': 'Non autorisé'}), 401
    try:
        data = request.get_json()
        conn = get_db()
        cur = conn.cursor()
        for key, value in data.items():
            v = json.dumps(value) if not isinstance(value, str) else value
            cur.execute("INSERT INTO config VALUES (%s,%s) ON CONFLICT(key) DO UPDATE SET value=EXCLUDED.value", [key, v])
        conn.commit()
        cur.close()
        conn.close()
        return jsonify({'ok': True})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/export', methods=['POST'])
def export():
    if not is_logged_in():
        return jsonify({'error': 'Non autorisé'}), 401
    try:
        planning = json.loads(request.form.get('planning'))
        excel_file = request.files.get('excel')
        wb = openpyxl.load_workbook(excel_file) if excel_file else openpyxl.Workbook()
        if not excel_file:
            wb.active.title = "Planning"
        ws = wb.active
        for item in planning:
            if item.get('cellule') and item.get('employe'):
                ws[item['cellule']] = item['employe']
        output = io.BytesIO()
        wb.save(output)
        output.seek(0)
        filename = excel_file.filename if excel_file else "planning.xlsx"
        return send_file(output, mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet', as_attachment=True, download_name=filename)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
