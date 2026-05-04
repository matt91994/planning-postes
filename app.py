from flask import Flask, request, jsonify, send_file, send_from_directory
from flask_cors import CORS
import openpyxl
import json
import io
import os
import sqlite3
app = Flask(__name__, static_folder='static')
CORS(app)

DB_PATH = os.environ.get('DB_PATH', 'planning.db')

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    conn.execute('''
        CREATE TABLE IF NOT EXISTS config (
            key TEXT PRIMARY KEY,
            value TEXT NOT NULL
        )
    ''')
    # Données par défaut si vide
    cur = conn.execute("SELECT value FROM config WHERE key='postes'")
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
        conn.execute("INSERT INTO config (key, value) VALUES ('postes', ?)", [json.dumps(postes_defaut)])
        conn.execute("INSERT INTO config (key, value) VALUES ('employes', ?)", [json.dumps([])])
        conn.execute("INSERT INTO config (key, value) VALUES ('nextEmpId', '1')")
        conn.execute("INSERT INTO config (key, value) VALUES ('nextPostId', '27')")
    conn.commit()
    conn.close()

init_db()

# ===== ROUTES CONFIG =====
@app.route('/')
def index():
   return send_from_directory('static', 'index.html')

@app.route('/config', methods=['GET'])
def get_config():
    conn = get_db()
    rows = conn.execute("SELECT key, value FROM config").fetchall()
    conn.close()
    data = {}
    for row in rows:
        try:
            data[row['key']] = json.loads(row['value'])
        except:
            data[row['key']] = row['value']
    return jsonify(data)

@app.route('/config', methods=['POST'])
def save_config():
    try:
        data = request.get_json()
        conn = get_db()
        for key, value in data.items():
            conn.execute(
                "INSERT INTO config (key, value) VALUES (?, ?) ON CONFLICT(key) DO UPDATE SET value=excluded.value",
                [key, json.dumps(value) if not isinstance(value, str) else value]
            )
        conn.commit()
        conn.close()
        return jsonify({'ok': True})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ===== EXPORT EXCEL =====
@app.route('/export', methods=['POST'])
def export():
    try:
        planning_json = request.form.get('planning')
        planning = json.loads(planning_json)
        excel_file = request.files.get('excel')

        if excel_file:
            wb = openpyxl.load_workbook(excel_file)
        else:
            wb = openpyxl.Workbook()
            wb.active.title = "Planning"

        ws = wb.active

        for item in planning:
            cellule = item.get('cellule')
            employe = item.get('employe')
            if cellule and employe:
                ws[cellule] = employe

        output = io.BytesIO()
        wb.save(output)
        output.seek(0)

        filename = excel_file.filename if excel_file else "planning.xlsx"
        return send_file(
            output,
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            as_attachment=True,
            download_name=filename
        )
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
