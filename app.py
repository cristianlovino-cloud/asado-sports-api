from flask import Flask, jsonify
from flask_cors import CORS
import requests
import os

app = Flask(__name__)
CORS(app)

FOOTBALL_DATA_KEY = os.environ.get('FOOTBALL_DATA_KEY', '')
FOOTBALL_DATA_URL = 'https://api.football-data.org/v4'

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
    return jsonify({
        'status': 'ok',
        'service': 'asado-sports-api',
        'endpoints': ['/mundial/grupos','/mundial/fixtures','/f1/pilotos','/f1/constructores','/f1/calendario','/f1/ultima']
    })

@app.route('/mundial/grupos')
def mundial_grupos():
    if FOOTBALL_DATA_KEY:
        try:
            r = requests.get(f'{FOOTBALL_DATA_URL}/competitions/WC/standings',
                headers={'X-Auth-Token': FOOTBALL_DATA_KEY}, timeout=8)
            if r.status_code == 200 and r.json().get('standings'):
                return jsonify({'ok': True, 'source': 'live', 'data': r.json()['standings']})
        except: pass
    grupos_fmt = [{'grupo': f'Grupo {k}', 'letra': k,
        'equipos': [{'nombre': e,'pts':0,'pj':0,'pg':0,'pe':0,'pp':0,'gf':0,'gc':0} for e in v]}
        for k,v in GRUPOS_2026.items()]
    return jsonify({'ok': True, 'source': 'static', 'data': grupos_fmt})

@app.route('/mundial/fixtures')
def mundial_fixtures():
    if FOOTBALL_DATA_KEY:
        try:
            r = requests.get(f'{FOOTBALL_DATA_URL}/competitions/WC/matches',
                headers={'X-Auth-Token': FOOTBALL_DATA_KEY}, timeout=8)
            if r.status_code == 200:
                return jsonify({'ok': True, 'source': 'live', 'data': r.json().get('matches',[])})
        except: pass
    return jsonify({'ok': False, 'error': 'El torneo aún no comenzó', 'data': []})

@app.route('/f1/pilotos')
def f1_pilotos():
    try:
        r = requests.get('https://ergast.com/api/f1/2025/driverStandings.json', timeout=8)
        sl = r.json()['MRData']['StandingsTable']['StandingsLists']
        if not sl: return jsonify({'ok':False,'error':'Sin datos aún'})
        return jsonify({'ok':True,'source':'ergast','data':[{
            'pos':int(p['position']),'nombre':f"{p['Driver']['givenName']} {p['Driver']['familyName']}",
            'codigo':p['Driver'].get('code',''),'escuderia':p['Constructors'][0]['name'] if p['Constructors'] else '',
            'pts':float(p['points']),'victorias':int(p['wins'])} for p in sl[0]['DriverStandings']]})
    except Exception as e: return jsonify({'ok':False,'error':str(e)})

@app.route('/f1/constructores')
def f1_constructores():
    try:
        r = requests.get('https://ergast.com/api/f1/2025/constructorStandings.json', timeout=8)
        sl = r.json()['MRData']['StandingsTable']['StandingsLists']
        if not sl: return jsonify({'ok':False,'error':'Sin datos aún'})
        return jsonify({'ok':True,'source':'ergast','data':[{
            'pos':int(e['position']),'nombre':e['Constructor']['name'],
            'pts':float(e['points']),'victorias':int(e['wins'])} for e in sl[0]['ConstructorStandings']]})
    except Exception as e: return jsonify({'ok':False,'error':str(e)})

@app.route('/f1/calendario')
def f1_calendario():
    try:
        r = requests.get('https://ergast.com/api/f1/2025.json', timeout=8)
        carreras = r.json()['MRData']['RaceTable']['Races']
        return jsonify({'ok':True,'source':'ergast','data':[{
            'ronda':int(c['round']),'nombre':c['raceName'],
            'circuito':c['Circuit']['circuitName'],
            'pais':c['Circuit']['Location']['country'],
            'ciudad':c['Circuit']['Location']['locality'],
            'fecha':c['date'],'hora':c.get('time','')} for c in carreras]})
    except Exception as e: return jsonify({'ok':False,'error':str(e)})

@app.route('/f1/ultima')
def f1_ultima():
    try:
        r = requests.get('https://ergast.com/api/f1/2025/last/results.json', timeout=8)
        races = r.json()['MRData']['RaceTable']['Races']
        if not races: return jsonify({'ok':False,'error':'Sin resultados aún'})
        c = races[0]
        return jsonify({'ok':True,'source':'ergast',
            'carrera':{'nombre':c['raceName'],'circuito':c['Circuit']['circuitName'],
                       'fecha':c['date'],'pais':c['Circuit']['Location']['country']},
            'data':[{'pos':res['position'],
                'nombre':f"{res['Driver']['givenName']} {res['Driver']['familyName']}",
                'codigo':res['Driver'].get('code',''),'escuderia':res['Constructor']['name'],
                'pts':res.get('points','0'),
                'tiempo':res.get('Time',{}).get('time',res.get('status',''))}
                for res in c.get('Results',[])[:10]]})
    except Exception as e: return jsonify({'ok':False,'error':str(e)})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
