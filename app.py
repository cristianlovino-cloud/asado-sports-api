from flask import Flask, jsonify
from flask_cors import CORS
import requests, os

app = Flask(__name__)
CORS(app)

FOOTBALL_DATA_KEY = os.environ.get('FOOTBALL_DATA_KEY', '')
FOOTBALL_DATA_URL = 'https://api.football-data.org/v4'
JOLPICA = 'https://api.jolpi.ca/ergast/f1'

GRUPOS_2026 = {
  "A": ["Mexico","Jamaica","Honduras","Ecuador"],
  "B": ["Estados Unidos","Panama","Bosnia y Herzegovina","Ghana"],
  "C": ["Canada","Trinidad y Tobago","Paises Bajos","Noruega"],
  "D": ["Brasil","Japon","Suiza","Camerun"],
  "E": ["Argentina","Marruecos","Hungria","Arabia Saudita"],
  "F": ["Espana","Senegal","Serbia","Nueva Zelanda"],
  "G": ["Alemania","Colombia","Costa de Marfil","Eslovaquia"],
  "H": ["Portugal","Eslovenia","Ucrania","Sudafrica"],
  "I": ["Francia","Belgica","Rep. Checa","Haiti"],
  "J": ["Inglaterra","Tunez","Costa Rica","Kenia"],
  "K": ["Uruguay","Rumania","Egipto","Togo"],
  "L": ["Iran","Cuba","Qatar","China"],
}

BANDERAS = {
  "Mexico":"MX","Jamaica":"JM","Honduras":"HN","Ecuador":"EC",
  "Estados Unidos":"US","Panama":"PA","Bosnia y Herzegovina":"BA","Ghana":"GH",
  "Canada":"CA","Trinidad y Tobago":"TT","Paises Bajos":"NL","Noruega":"NO",
  "Brasil":"BR","Japon":"JP","Suiza":"CH","Camerun":"CM",
  "Argentina":"AR","Marruecos":"MA","Hungria":"HU","Arabia Saudita":"SA",
  "Espana":"ES","Senegal":"SN","Serbia":"RS","Nueva Zelanda":"NZ",
  "Alemania":"DE","Colombia":"CO","Costa de Marfil":"CI","Eslovaquia":"SK",
  "Portugal":"PT","Eslovenia":"SI","Ucrania":"UA","Sudafrica":"ZA",
  "Francia":"FR","Belgica":"BE","Rep. Checa":"CZ","Haiti":"HT",
  "Inglaterra":"GB","Tunez":"TN","Costa Rica":"CR","Kenia":"KE",
  "Uruguay":"UY","Rumania":"RO","Egipto":"EG","Togo":"TG",
  "Iran":"IR","Cuba":"CU","Qatar":"QA","China":"CN",
}

@app.route('/')
def health():
    return jsonify({'status':'ok','service':'asado-sports-api'})

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
        'equipos':[{'nombre':e,'flag':BANDERAS.get(e,''),'pts':0,'pj':0,'pg':0,'pe':0,'pp':0,'gf':0,'gc':0} for e in v]}
        for k,v in GRUPOS_2026.items()]
    return jsonify({'ok':True,'source':'static','data':grupos_fmt})

@app.route('/f1/pilotos')
def f1_pilotos():
    try:
        r = requests.get(f'{JOLPICA}/2025/driverStandings.json', timeout=10)
        sl = r.json()['MRData']['StandingsTable']['StandingsLists']
        if not sl: return jsonify({'ok':False,'error':'Sin datos aun'})
        return jsonify({'ok':True,'source':'jolpica','data':[{
            'pos':int(p['position']),
            'nombre':p['Driver']['givenName']+' '+p['Driver']['familyName'],
            'codigo':p['Driver'].get('code',''),
            'escuderia':p['Constructors'][0]['name'] if p['Constructors'] else '',
            'pts':float(p['points']),
            'victorias':int(p['wins'])
        } for p in sl[0]['DriverStandings']]})
    except Exception as e:
        return jsonify({'ok':False,'error':str(e)})

@app.route('/f1/constructores')
def f1_constructores():
    try:
        r = requests.get(f'{JOLPICA}/2025/constructorStandings.json', timeout=10)
        sl = r.json()['MRData']['StandingsTable']['StandingsLists']
        if not sl: return jsonify({'ok':False,'error':'Sin datos aun'})
        return jsonify({'ok':True,'source':'jolpica','data':[{
            'pos':int(e['position']),
            'nombre':e['Constructor']['name'],
            'pts':float(e['points']),
            'victorias':int(e['wins'])
        } for e in sl[0]['ConstructorStandings']]})
    except Exception as e:
        return jsonify({'ok':False,'error':str(e)})

@app.route('/f1/calendario')
def f1_calendario():
    try:
        r = requests.get(f'{JOLPICA}/2025.json', timeout=10)
        carreras = r.json()['MRData']['RaceTable']['Races']
        return jsonify({'ok':True,'source':'jolpica','data':[{
            'ronda':int(c['round']),
            'nombre':c['raceName'],
            'circuito':c['Circuit']['circuitName'],
            'pais':c['Circuit']['Location']['country'],
            'ciudad':c['Circuit']['Location']['locality'],
            'fecha':c['date']
        } for c in carreras]})
    except Exception as e:
        return jsonify({'ok':False,'error':str(e)})

@app.route('/f1/ultima')
def f1_ultima():
    try:
        r = requests.get(f'{JOLPICA}/2025/last/results.json', timeout=10)
        races = r.json()['MRData']['RaceTable']['Races']
        if not races: return jsonify({'ok':False,'error':'Sin resultados aun'})
        c = races[0]
        return jsonify({'ok':True,'source':'jolpica',
            'carrera':{'nombre':c['raceName'],'circuito':c['Circuit']['circuitName'],
                'fecha':c['date'],'pais':c['Circuit']['Location']['country']},
            'data':[{'pos':res['position'],
                'nombre':res['Driver']['givenName']+' '+res['Driver']['familyName'],
                'codigo':res['Driver'].get('code',''),
                'escuderia':res['Constructor']['name'],
                'pts':res.get('points','0'),
                'tiempo':res.get('Time',{}).get('time',res.get('status',''))
            } for res in c.get('Results',[])[:10]]})
    except Exception as e:
        return jsonify({'ok':False,'error':str(e)})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
