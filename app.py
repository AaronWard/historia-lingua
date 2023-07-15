import os
import requests
import argparse
from flask import Flask, render_template, request, jsonify, session, redirect, url_for
from flask_session import Session
from geopy.geocoders import Nominatim
from dotenv import load_dotenv
from src.history_chain import HistoryChain
from src.followup_chain import FollowUpChain
from src.utils.env_utils import get_openai_key

app = Flask(__name__)
app.config['SESSION_TYPE'] = 'filesystem'
Session(app)
geolocator = Nominatim(user_agent="map_app")

parser = argparse.ArgumentParser()
parser.add_argument("--env_path", help="The path to the .env file containing the OpenAI key")
args = parser.parse_args()
load_dotenv(dotenv_path=args.env_path)
app.secret_key = get_openai_key(args.env_path)

if app.config['SECRET_KEY']:
    print("Secret key set correctly.")
else:
    print("Failed to set secret key.")

def set_up_chains(model):
    history_chain = HistoryChain(openai_api_key=app.secret_key, model=model)
    followup_chain = FollowUpChain(openai_api_key=app.secret_key, model=model)
    return history_chain, followup_chain

def get_location_detail(lat, lon, zoom):
    location = geolocator.reverse([lat, lon], exactly_one=True)
    address = location.raw['address']

    if zoom <=2:
        return address.get('country', '')
    elif zoom <= 5:
        return ', '.join(filter(None, [address.get('state', ''), address.get('country', '')]))
    elif zoom <= 13:
        return ', '.join(filter(None, [address.get('city', ''), address.get('state', ''), address.get('country', '')]))
    else:
        return ', '.join(filter(None, [address.get('road', ''), address.get('city', ''), address.get('state', ''), address.get('country', '')]))

def get_available_models():
    try:
        response = requests.get(
            "https://api.openai.com/v1/models",
            headers={"Authorization": f"Bearer {app.secret_key}"}
        )
        if response.status_code == 200:
            models = response.json()['data']
            return [model['id'] for model in models]
        else:
            return None
    except Exception as e:
        print("Error in getting available models:", str(e))
        return None

@app.route('/select_model', methods=['GET', 'POST'])
def select_model():
    available_models = get_available_models()
    if available_models:
        if request.method == 'POST':
            selected_model = request.form.get('model')
            if selected_model in available_models:
                session['model'] = selected_model
                return redirect(url_for('index'))
        return render_template('select_model.html', models=available_models)
    else:
        return "Error in getting models from OpenAI", 500
    
@app.route('/')
def index():
    if 'model' in session:
        return render_template('index.html')
    else:
        return redirect(url_for('select_model'))

@app.route('/get_location', methods=['POST'])
def get_location():
    data = request.get_json()
    lat = data['lat']
    lon = data['lon']
    zoom = data['zoom']

    location_detail = get_location_detail(lat, lon, zoom)
    
    return jsonify({'address': location_detail})

@app.route('/get_history', methods=['POST'])
def get_history():
    if 'model' not in session:
        return redirect(url_for('select_model'))

    history_chain, _ = set_up_chains(session['model'])
    data = request.get_json()
    response = history_chain.run({"location": data['location'], "time_period": data['year']})
    
    return jsonify({'response': response['response']})

@app.route('/handle_selected_text', methods=['POST'])
def handle_selected_text():
    if 'model' not in session:
        return redirect(url_for('select_model'))

    _, followup_chain = set_up_chains(session['model'])
    data = request.get_json()

    response = followup_chain.run({"location": data['location'], "time_period": data['year'],
                                   "previous_response": data['previous_response'], "selected_text": data['selected_text']})
    
    return jsonify({'response': response['response']})

if __name__ == "__main__":
    app.run(debug=True)
