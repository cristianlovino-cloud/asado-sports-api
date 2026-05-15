from flask import Flask, jsonify
from flask_cors import CORS
import requests
import os

app = Flask(__name__)
CORS(app)

API_KEY = os.environ.get('API_FOOTBALL_KEY', '')
BASE_URL = 'https://v3.football.api-sports.io'
BASE_F1  = 'https://v1.formula-1.api-sports.io'

HEADERS_FOOTBALL = {
    'x-apisports-key': API_KEY
}
HEADERS_F1 = {
    'x-apisports-key': API_KEY
}

# ── Mundial 2026 ──────────────────────────────────────
# ID del torneo Mundial: league=1, season=2026
MUNDIAL_LEAGUE = 1
MUNDIAL_SEASON = 2026

@app.route('/mundial/grupos')
def mundial_grupos():
    """Posiciones por grupo del Mundial 2026"""
    try:
        r = requests.get(
            f'{BASE_URL}/standings',
            headers=HEADERS_FOOTBALL,
            params={'league': MUNDIAL_LEAGUE, 'season': MUNDIAL_SEASON},
            timeout=10
        )
        data = r.json()
        if data.get('errors') or not data.get('response'):
            return jsonify({'ok': False, 'error': 'Sin datos disponibles aún', 'raw': data}), 200
        return jsonify({'ok': True, 'data': data['response']})
    except Exception as e:
        return jsonify({'ok': False, 'error': str(e)}), 500

@app.route('/mundial/partidos')
def mundial_partidos():
    """Partidos del Mundial 2026 (todos)"""
    try:
        r = requests.get(
            f'{BASE_URL}/fixtures',
            headers=HEADERS_FOOTBALL,
            params={'league': MUNDIAL_LEAGUE, 'season': MUNDIAL_SEASON},
            timeout=10
        )
        data = r.json()
        if data.get('errors') or not data.get('response'):
            return jsonify({'ok': False, 'error': 'Sin datos disponibles aún', 'raw': data}), 200
        return jsonify({'ok': True, 'data': data['response']})
    except Exception as e:
        return jsonify({'ok': False, 'error': str(e)}), 500

@app.route('/mundial/proximos')
def mundial_proximos():
    """Próximos partidos del Mundial (next 10)"""
    try:
        r = requests.get(
            f'{BASE_URL}/fixtures',
            headers=HEADERS_FOOTBALL,
            params={'league': MUNDIAL_LEAGUE, 'season': MUNDIAL_SEASON, 'next': 10},
            timeout=10
        )
        data = r.json()
        if not data.get('response'):
            return jsonify({'ok': False, 'error': 'Sin datos', 'raw': data}), 200
        return jsonify({'ok': True, 'data': data['response']})
    except Exception as e:
        return jsonify({'ok': False, 'error': str(e)}), 500

# ── F1 ────────────────────────────────────────────────
F1_SEASON = 2025

@app.route('/f1/calendario')
def f1_calendario():
    """Calendario de carreras F1 2025"""
    try:
        r = requests.get(
            f'{BASE_F1}/races',
            headers=HEADERS_F1,
            params={'season': F1_SEASON},
            timeout=10
        )
        data = r.json()
        if not data.get('response'):
            return jsonify({'ok': False, 'error': 'Sin datos F1', 'raw': data}), 200
        return jsonify({'ok': True, 'data': data['response']})
    except Exception as e:
        return jsonify({'ok': False, 'error': str(e)}), 500

@app.route('/f1/pilotos')
def f1_pilotos():
    """Standings de pilotos F1 2025"""
    try:
        r = requests.get(
            f'{BASE_F1}/rankings/drivers',
            headers=HEADERS_F1,
            params={'season': F1_SEASON},
            timeout=10
        )
        data = r.json()
        if not data.get('response'):
            return jsonify({'ok': False, 'error': 'Sin datos F1', 'raw': data}), 200
        return jsonify({'ok': True, 'data': data['response']})
    except Exception as e:
        return jsonify({'ok': False, 'error': str(e)}), 500

@app.route('/f1/constructores')
def f1_constructores():
    """Standings de constructores F1 2025"""
    try:
        r = requests.get(
            f'{BASE_F1}/rankings/teams',
            headers=HEADERS_F1,
            params={'season': F1_SEASON},
            timeout=10
        )
        data = r.json()
        if not data.get('response'):
            return jsonify({'ok': False, 'error': 'Sin datos F1', 'raw': data}), 200
        return jsonify({'ok': True, 'data': data['response']})
    except Exception as e:
        return jsonify({'ok': False, 'error': str(e)}), 500

@app.route('/f1/ultima')
def f1_ultima():
    """Última carrera disputada"""
    try:
        r = requests.get(
            f'{BASE_F1}/races',
            headers=HEADERS_F1,
            params={'season': F1_SEASON, 'type': 'Race'},
            timeout=10
        )
        data = r.json()
        if not data.get('response'):
            return jsonify({'ok': False, 'error': 'Sin datos', 'raw': data}), 200
        # Filtrar las que ya tienen resultado (status finished)
        terminadas = [r for r in data['response'] if r.get('status') == 'Completed']
        ultima = terminadas[-1] if terminadas else None
        return jsonify({'ok': True, 'data': ultima})
    except Exception as e:
        return jsonify({'ok': False, 'error': str(e)}), 500

# ── Health check ──────────────────────────────────────
@app.route('/')
def health():
    return jsonify({
        'status': 'ok',
        'service': 'asado-sports-api',
        'endpoints': [
            '/mundial/grupos',
            '/mundial/partidos',
            '/mundial/proximos',
            '/f1/calendario',
            '/f1/pilotos',
            '/f1/constructores',
            '/f1/ultima',
        ]
    })

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
