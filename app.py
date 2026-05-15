from flask import Flask, jsonify
from flask_cors import CORS
import requests
import os

app = Flask(__name__)
CORS(app)

FOOTBALL_DATA_KEY = os.environ.get('FOOTBALL_DATA_KEY', '')
FOOTBALL_DATA_URL = 'https://api.football-data.org/v4'
OPENF1 = 'https://api.openf1.org/v1'

GRUPOS_2026 = {
  "A": ["México","Jamaica","Honduras","Ecuador"],
  "B": ["Estados Unidos","Panamá","Bosnia y Herzegovina","Ghana"],
  "C": ["Canadá","Trinidad y Tobago","Países Bajos","Noruega"],
  "D": ["Brasil","Japón","Suiza","Camerún"],
  "E": ["Argentina","Ecuador","Hungría","Marruecos"],
  "F": ["España","Senegal","Serbia","Nueva Zelanda"],
  "G": ["Alemania","Australia","Arabia Saudita","Costa Rica"],
  "H": ["Portugal","Eslovenia","Ucrania","Sudáfrica"],
  "I": ["Francia","Bélgica","R. Checa","Haití"],
  "J": ["Inglaterra","Túnez","Eslovaquia","Kenia"],
  "K": ["Colombia","Rumania","Côte d'Ivoire","Togo"],
  "L": ["Uruguay","Cuba","Qatar","China"],
}

@app.route('/')
def health():
    return jsonify({'status':'ok','service':'asado-sports-api',
        'endpoints':['/mundial/grupos','/mundial/fixtures','/f1/pilotos','/f1/calendario','/f1/ultima']})

# ── MUNDIAL ───────────────────────────────────────────

@app.route('/mundial/grupos')
def mundial_grupos():
    if FOOTBALL_DATA_KEY:
        try:
            r = requests.get(f'{FOOTBALL_DATA_URL}/competitions/WC/standings',
                headers={'X-Auth-Token': FOOTBALL_DATA_KEY}, timeout=8)
            if r.status_code == 200 and r.json().get('standings'):
                return jsonify({'ok':True,'source':'live','data':r.json()['standings']})
        except: pass
    grupos_fmt = [{'grupo':f'Grupo {k}','letra':k,
        'equipos':[{'nombre':e,'pts':0,'pj':0,'pg':0,'pe':0,'pp':0,'gf':0,'gc':0} for e in v]}
        for k,v in GRUPOS_2026.items()]
    return jsonify({'ok':True,'source':'static','data':grupos_fmt})

@app.route('/mundial/fixtures')
def mundial_fixtures():
    if FOOTBALL_DATA_KEY:
        try:
            r = requests.get(f'{FOOTBALL_DATA_URL}/competitions/WC/matches',
                headers={'X-Auth-Token': FOOTBALL_DATA_KEY}, timeout=8)
            if r.status_code == 200:
                return jsonify({'ok':True,'source':'live','data':r.json().get('matches',[])})
        except: pass
    return jsonify({'ok':False,'error':'El torneo aún no comenzó','data':[]})

# ── F1 via OpenF1 (gratis, sin key, 2025 real) ────────

@app.route('/f1/pilotos')
def f1_pilotos():
    try:
        # Obtener drivers de la temporada 2025
        r = requests.get(f'{OPENF1}/drivers?session_key=latest', timeout=10)
        drivers = r.json()
        # Deduplicar por driver_number
        seen = {}
        for d in drivers:
            n = d.get('driver_number')
            if n and n not in seen:
                seen[n] = {
                    'numero':    n,
                    'nombre':    d.get('full_name',''),
                    'codigo':    d.get('name_acronym',''),
                    'escuderia': d.get('team_name',''),
                    'color':     d.get('team_colour',''),
                    'pais':      d.get('country_code',''),
                }
        result = sorted(seen.values(), key=lambda x: x['numero'])
        return jsonify({'ok':True,'source':'openf1','data':result})
    except Exception as e:
        return jsonify({'ok':False,'error':str(e)})

@app.route('/f1/calendario')
def f1_calendario():
    try:
        r = requests.get(f'{OPENF1}/meetings?year=2025', timeout=10)
        meetings = r.json()
        result = []
        for m in meetings:
            result.append({
                'ronda':    m.get('meeting_key'),
                'nombre':   m.get('meeting_name',''),
                'circuito': m.get('circuit_short_name',''),
                'pais':     m.get('country_name',''),
                'ciudad':   m.get('location',''),
                'fecha':    m.get('date_start','')[:10] if m.get('date_start') else '',
            })
        return jsonify({'ok':True,'source':'openf1','data':result})
    except Exception as e:
        return jsonify({'ok':False,'error':str(e)})

@app.route('/f1/ultima')
def f1_ultima():
    try:
        # Última sesión de carrera
        r = requests.get(f'{OPENF1}/sessions?session_type=Race&year=2025', timeout=10)
        sessions = r.json()
        if not sessions:
            return jsonify({'ok':False,'error':'Sin carreras aún'})
        ultima = sessions[-1]
        session_key = ultima['session_key']

        # Posiciones finales
        rpos = requests.get(f'{OPENF1}/position?session_key={session_key}', timeout=10)
        positions = rpos.json()

        # Última posición de cada piloto
        pos_map = {}
        for p in positions:
            n = p['driver_number']
            pos_map[n] = p['position']

        # Drivers de esa sesión
        rdrivers = requests.get(f'{OPENF1}/drivers?session_key={session_key}', timeout=10)
        drivers = {d['driver_number']: d for d in rdrivers.json()}

        result = []
        for num, pos in sorted(pos_map.items(), key=lambda x: x[1])[:10]:
            d = drivers.get(num, {})
            result.append({
                'pos':       pos,
                'nombre':    d.get('full_name',''),
                'codigo':    d.get('name_acronym',''),
                'escuderia': d.get('team_name',''),
            })

        return jsonify({'ok':True,'source':'openf1',
            'carrera':{
                'nombre':  ultima.get('session_name',''),
                'circuito':ultima.get('circuit_short_name',''),
                'pais':    ultima.get('country_name',''),
                'fecha':   ultima.get('date_start','')[:10],
            },
            'data': result})
    except Exception as e:
        return jsonify({'ok':False,'error':str(e)})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
