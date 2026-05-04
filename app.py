from flask import Flask, request, jsonify, send_file, send_from_directory
from flask_cors import CORS
import openpyxl
import json
import io
import os

app = Flask(__name__, static_folder='.')
CORS(app)

@app.route('/')
def index():
    return send_from_directory('.', 'index.html')


@app.route('/export', methods=['POST'])
def export():
    try:
        # Récupérer le planning JSON
        planning_json = request.form.get('planning')
        planning = json.loads(planning_json)  # [{poste, cellule, employe}, ...]

        # Récupérer le fichier Excel s'il est fourni
        excel_file = request.files.get('excel')

        if excel_file:
            wb = openpyxl.load_workbook(excel_file)
        else:
            wb = openpyxl.Workbook()
            wb.active.title = "Planning"

        ws = wb.active

        # Écrire les noms dans les cellules
        for item in planning:
            cellule = item.get('cellule')
            employe = item.get('employe')
            if cellule and employe:
                ws[cellule] = employe

        # Sauvegarder en mémoire
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
