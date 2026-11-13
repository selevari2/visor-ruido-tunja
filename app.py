import os
from flask import Flask, render_template, request, jsonify
import psycopg2
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
app.config['TEMPLATES_AUTO_RELOAD'] = True

DB_CONFIG = {
    "host": os.environ.get("DB_HOST"),
    "database": os.environ.get("DB_NAME", "postgres"),
    "user": os.environ.get("DB_USER"),
    "password": os.environ.get("DB_PASS"),
    "port": os.environ.get("DB_PORT", "6543"),
    "sslmode": "require"
}

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/ejecutar_sql', methods=['POST'])
def ejecutar_sql():
    datos_req = request.get_json(silent=True) or {}
    consulta_usuario = datos_req.get('sql', '').strip()
    
    if not consulta_usuario.lower().startswith('select'):
        return jsonify({"error": "Solo se permiten consultas SELECT."}), 400

    consulta_limpia = consulta_usuario.rstrip(';')

    sql_geojson = f"""
    SELECT json_build_object(
        'type', 'FeatureCollection',
        'features', COALESCE(json_agg(ST_AsGeoJSON(t.*)::json), '[]'::json)
    )
    FROM ({consulta_limpia}) AS t;
    """

    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()
        cur.execute(sql_geojson)
        fila = cur.fetchone()
        resultado = fila[0] if fila else {"type": "FeatureCollection", "features": []}
        cur.close()
        conn.close()
        return jsonify(resultado)
    except Exception as e:
        return jsonify({"error": str(e)}), 400

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
