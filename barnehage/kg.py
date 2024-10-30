from flask import Flask
from flask import url_for
from flask import render_template
from flask import request
from flask import redirect
from flask import session
from kgmodel import (Foresatt, Barn, Soknad, Barnehage)
from kgcontroller import (form_to_object_soknad, insert_soknad, commit_all, select_alle_barnehager)

app = Flask(__name__)
app.secret_key = 'BAD_SECRET_KEY'  # nødvendig for session
def hent_ledige_plasser(barnehage_navn):
    # Hent alle barnehager og deres ledige plasser
    barnehager = select_alle_barnehager()
    for barnehage in barnehager:
        if barnehage.barnehage_navn == barnehage_navn:  # Endret til riktig attributtnavn
            return barnehage.barnehage_ledige_plasser  # Bruker riktig attributtnavn for ledige plasser
    return 0  # Returner 0 hvis barnehagen ikke finnes eller har ingen ledige plasser


@app.route('/')
def index():
    return render_template('index.html')

@app.route('/barnehager')
def barnehager():
    information = select_alle_barnehager()
    return render_template('barnehager.html', data=information)

@app.route('/behandle', methods=['GET', 'POST'])
def behandle():
    if request.method == 'POST':
        sd = request.form
        print(sd)
        log = insert_soknad(form_to_object_soknad(sd))
        print(log)
        session['information'] = sd

        # Hent valgt barnehage og sjekk ledige plasser
        valgt_barnehage = sd.get("barnehage")
        antall_ledige_plasser = hent_ledige_plasser(valgt_barnehage)
        har_fortrinnsrett = bool(sd.get("fortrinnsrett", False))  # Sjekk om søkeren har fortrinnsrett

        # Sett resultat basert på ledige plasser og fortrinnsrett
        if antall_ledige_plasser > 0 or har_fortrinnsrett:
            session['resultat'] = "TILBUD"
        else:
            session['resultat'] = "AVSLAG"

        return redirect(url_for('svar'))
    else:
        return render_template('soknad.html')

@app.route('/svar')
def svar():
    information = session['information']
    resultat = session.get('resultat', 'Ingen respons tilgjengelig')
    data = {
        "resultat": resultat,
        "søknadsdata": information
    }
    return render_template('svar.html', data=data)

@app.route('/commit')
def commit():
    commit_all()
    return render_template('commit.html')

