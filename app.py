from flask import Flask, jsonify, request
from flask_cors import CORS
import requests, os

app = Flask(__name__)
CORS(app)

FOOTBALL_DATA_KEY = os.environ.get('FOOTBALL_DATA_KEY', '')
FOOTBALL_DATA_URL = 'https://api.football-data.org/v4'
JOLPICA = 'https://api.jolpi.ca/ergast/f1'

# SportMonks token — setear como env var SPORTMONKS_TOKEN en producción
SPORTMONKS_TOKEN = os.environ.get('SPORTMONKS_TOKEN', 'sfvnNhihy5FY4JWTM1B7JOXA3jlatU1Jv6NtWfn0xS7VTkiA28HKUQNsNNbu')
SPORTMONKS_BASE = 'https://api.sportmonks.com/v3/football'

# Grupos oficiales FIFA Mundial 2026 — fuente: 365score (mayo 2026)
GRUPOS_2026 = {
  "A": ["Mexico","Corea del Sur","Sudafrica","Republica Checa"],
  "B": ["Canada","Suiza","Qatar","Bosnia Herzegovina"],
  "C": ["Brasil","Marruecos","Escocia","Haiti"],
  "D": ["Estados Unidos","Australia","Paraguay","Turquia"],
  "E": ["Alemania","Ecuador","Costa de Marfil","Curazao"],
  "F": ["Paises Bajos","Peru","Tunez","Suecia"],
  "G": ["Belgica","Iran","Egipto","Nueva Zelanda"],
  "H": ["Cabo Verde","Arabia Saudita","Espana","Uruguay"],
  "I": ["Francia","Senegal","Noruega","Irak"],
  "J": ["Argelia","Argentina","Austria","Jordania"],
  "K": ["Portugal","Colombia","Eslovenia","RD Congo"],
  "L": ["Inglaterra","Croacia","Panama","Ghana"],
}

BANDERAS = {
  "Mexico":"MX","Corea del Sur":"KR","Sudafrica":"ZA","Republica Checa":"CZ",
  "Canada":"CA","Suiza":"CH","Qatar":"QA","Bosnia Herzegovina":"BA",
  "Brasil":"BR","Marruecos":"MA","Escocia":"GB-SCT","Haiti":"HT",
  "Estados Unidos":"US","Australia":"AU","Paraguay":"PY","Turquia":"TR",
  "Alemania":"DE","Ecuador":"EC","Costa de Marfil":"CI","Curazao":"CW",
  "Paises Bajos":"NL","Honduras":"HN","Tunez":"TN","Suecia":"SE",
  "Belgica":"BE","Iran":"IR","Egipto":"EG","Nueva Zelanda":"NZ",
  "Cabo Verde":"CV","Arabia Saudita":"SA","Espana":"ES","Uruguay":"UY",
  "Francia":"FR","Senegal":"SN","Noruega":"NO","Irak":"IQ",
  "Argelia":"DZ","Argentina":"AR","Austria":"AT","Jordania":"JO",
  "Portugal":"PT","Colombia":"CO","Eslovenia":"SI","RD Congo":"CD",
  "Peru":"PE",
  "Inglaterra":"GB","Croacia":"HR","Panama":"PA","Ghana":"GH",
}

# ─── HEALTH ────────────────────────────────────────────────────────────────────

@app.route('/')
def health():
    return jsonify({'status':'ok','service':'asado-sports-api'})

# ─── MUNDIAL ───────────────────────────────────────────────────────────────────

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

# ─── SPORTMONKS PROXY ──────────────────────────────────────────────────────────
# Resuelve el problema de CORS: el browser no puede llamar SportMonks directo,
# pero sí puede llamar este backend que actúa como proxy transparente.

def sm_get(path, params=None):
    """Helper: GET a SportMonks endpoint con el token del backend."""
    url = f'{SPORTMONKS_BASE}/{path.lstrip("/")}'
    p = params or {}
    p['api_token'] = SPORTMONKS_TOKEN
    r = requests.get(url, params=p, timeout=10)
    return r.json(), r.status_code

@app.route('/sm/ping')
def sm_ping():
    """Verifica token y muestra recursos disponibles en el plan."""
    data, status = sm_get('/../../core/my/resources'.replace('../../', '').replace('football/', ''),
                          {})
    # endpoint correcto para recursos
    r = requests.get('https://api.sportmonks.com/v3/core/my/resources',
                     params={'api_token': SPORTMONKS_TOKEN}, timeout=10)
    return jsonify({'ok': r.status_code == 200, 'status': r.status_code, 'data': r.json()}), r.status_code

@app.route('/sm/leagues')
def sm_leagues():
    """Lista ligas disponibles en el plan (busca FIFA World Cup)."""
    data, status = sm_get('leagues', {'page': 1, 'per_page': 50})
    return jsonify(data), status

@app.route('/sm/seasons')
def sm_seasons():
    """Busca seasons del Mundial 2026."""
    data, status = sm_get('seasons', {'filters': 'seasonName:2026 FIFA World Cup'})
    return jsonify(data), status

@app.route('/sm/standings/<int:season_id>')
def sm_standings(season_id):
    """Standings/tabla de posiciones por season_id."""
    data, status = sm_get(f'standings/seasons/{season_id}')
    return jsonify(data), status

@app.route('/sm/groups/<int:season_id>')
def sm_groups(season_id):
    """Grupos de una season (si el plan lo permite)."""
    data, status = sm_get(f'groups/seasons/{season_id}')
    return jsonify(data), status

@app.route('/sm/stages/<int:season_id>')
def sm_stages(season_id):
    """Stages/fases de una season."""
    data, status = sm_get(f'stages/seasons/{season_id}', {'include': 'rounds'})
    return jsonify(data), status

@app.route('/sm/fixtures/upcoming')
def sm_fixtures_upcoming():
    """Próximos partidos — filtrable por league_id query param."""
    league_id = request.args.get('league_id', '')
    params = {'include': 'participants'}
    if league_id:
        params['filters'] = f'leagueId:{league_id}'
    data, status = sm_get('fixtures/upcoming', params)
    return jsonify(data), status

@app.route('/sm/proxy')
def sm_proxy():
    """Proxy genérico: ?path=leagues&param1=val1 — para explorar desde el frontend."""
    path = request.args.get('path', '')
    if not path:
        return jsonify({'ok': False, 'error': 'Falta ?path='}), 400
    extra_params = {k: v for k, v in request.args.items() if k != 'path'}
    data, status = sm_get(path, extra_params)
    return jsonify(data), status

# ─── F1 ────────────────────────────────────────────────────────────────────────

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
