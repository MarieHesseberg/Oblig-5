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

def sjekk_prioritert_barnehage(prioriteter, har_fortrinnsrett):
    """
    Checks availability in prioritized kindergartens and grants a spot if any kindergarten
    in the list has available spots or if priority rights are applicable.
    """
    for barnehage_navn in prioriteter:
        antall_ledige_plasser = hent_ledige_plasser(barnehage_navn)
        print(f"Checking {barnehage_navn}: {antall_ledige_plasser} spots available")

        # Grant offer if there are available spots or if the applicant has priority rights
        if antall_ledige_plasser > 0 or har_fortrinnsrett:
            print(f"Offer granted at: {barnehage_navn}")
            return "TILBUD", barnehage_navn

    # If no kindergarten offers are possible, return denial
    print("No spots available; application denied.")
    return "AVSLAG", None


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
        try:
            print("Processing POST request at /behandle")

            # Retrieve form data
            sd = request.form
            print("Form data received:", sd)
            session['information'] = sd

            # Collect priority selections from the form
            prioritet_1 = sd.get("barnehage_prioritet_1")
            prioritet_2 = sd.get("barnehage_prioritet_2")
            prioritet_3 = sd.get("barnehage_prioritet_3")
            print("Priorities received:", prioritet_1, prioritet_2, prioritet_3)
            prioriteter = [prioritet_1, prioritet_2, prioritet_3]

            # Check if the applicant has any priority rights
            har_fortrinnsrett = bool(sd.get("fortrinnsrett_barnevern") or
                                     sd.get("fortrinnsrett_sykdom_familie") or
                                     sd.get("fortrinnsrett_sykdom_barn") or
                                     sd.get("fortrinnsrett_annet"))
            print("Priority rights:", har_fortrinnsrett)

            # Check availability in prioritized kindergartens
            resultat, valgt_barnehage = sjekk_prioritert_barnehage(prioriteter, har_fortrinnsrett)
            print("Result:", resultat, "Chosen kindergarten:", valgt_barnehage)

            # Store the result and selected kindergarten in the session
            session['resultat'] = resultat
            session['valgt_barnehage'] = valgt_barnehage
            print("Session valgt_barnehage:", session['valgt_barnehage'])  # Debug statement

            # Save the application data
            insert_soknad(form_to_object_soknad(sd))
            print("Application saved successfully.")

            return redirect(url_for('svar'))
        except Exception as e:
            print("Error in processing application:", e)
            return "An error occurred while processing the application.", 500
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
