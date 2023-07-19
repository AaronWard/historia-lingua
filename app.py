"""
This is the main flask application for Historia Lingua. The script contains endpoints
to handle the different kinds of requests that come from the dashboard.

TODO: Add webpage for manually OpenAI key input.

Written by: AaronWard
"""
import os
import requests
import openai
import atexit
import shutil
from flask import Flask, render_template, request, jsonify, session, redirect, url_for
from flask_session import Session
from geopy.geocoders import Nominatim
from dotenv import load_dotenv
from src.chains.history_chain import HistoryChain
from src.chains.followup_chain import FollowUpChain

app = Flask(__name__)

app.config['SESSION_TYPE'] = 'filesystem'
app.config['SECRET_KEY'] = 'you-should-change-this'  # Set a secret key for session

# Check if session directory exists and delete it if found
session_dir = app.config.get('SESSION_FILE_DIR')
if session_dir and os.path.exists(session_dir):
    try:
        shutil.rmtree(session_dir)
    except Exception as e:
        print(f"Error deleting session directory: {str(e)}")

Session(app)
geolocator = Nominatim(user_agent="map_app")
history_chain = None
followup_chain = None

def set_up_chains(model):
    global history_chain
    global followup_chain
    openai.api_key = session['api_key']

    history_chain = HistoryChain(openai_api_key=session['api_key'], model=model)
    followup_chain = FollowUpChain(openai_api_key=session['api_key'], model=model)

def get_location_detail(lat, lon, zoom):
    location = geolocator.reverse([lat, lon], exactly_one=True)    
    address = location.raw.get('address')

    # Display different location granularity
    # depending on the zoom level of the map.
    # IE: you can go down to street level if 
    # you soom in enough
    if zoom <= 2:
        return address.get('country', '')
    elif zoom <= 5:
        return ', '.join(filter(None, [address.get('state', ''),
                                       address.get('country', '')]))
    elif zoom <= 13:
        return ', '.join(filter(None, [address.get('city', ''), 
                                       address.get('state', ''), 
                                       address.get('country', '')]))
    else:
        return ', '.join(filter(None, [address.get('road', ''), 
                                       address.get('city', ''),
                                       address.get('state', ''), 
                                       address.get('country', '')]))

def get_available_models():
    try:
        response = requests.get(
            "https://api.openai.com/v1/models",
            headers={"Authorization": f"Bearer {session['api_key']}"}
        )
        if response.status_code == 200:
            models = response.json()['data']
            return [model['id'] for model in models]
        else:
            print("Error in getting available models: HTTP status code", response.status_code)
            return []
    except Exception as e:
        print("Error in getting available models:", str(e))
        return []



@app.route('/select_model', methods=['POST', 'GET'])
def select_model():
    if request.method == 'POST':

        session['model'] = request.form['model']
        set_up_chains(session['model'])
        return redirect('/')
    else:
        if 'api_key' in session:
            # Set the API key from session
            openai.api_key = session['api_key']
            # Use the key to list models
            session['models'] = [model.id for model in openai.Model.list().data]
            return render_template('select_model.html', models=session['models'])
        else:
            # Redirect to API key page if no key is found in session
            return redirect('/api_key')



@app.route('/api_key', methods=['GET', 'POST'])
def api_key():
    if request.method == 'POST':
        # Store API key in session
        session['api_key'] = request.form['api-key']
        # Redirect to select_model after setting API key
        # If the model isn't set, then it will use the set api 
        # key and request the list of available models 
        # with select_models.html
        return redirect('/select_model')
    else:
        return render_template('api_key.html')


@app.route('/')
def main():
    # checks to see if the model and the api key are set within the session
    # If not, it will redirect to the api_key page for the users input with api_key.html
    if 'api_key' not in session or 'model' not in session:
        return redirect('/api_key')
    else:
        # When both are set, then it will instantiate the global chain 
        # variables using the selected model name and given api key,
        # and load index.html
        return render_template('index.html')
    
@app.route('/logout')
def logout():
    # remove the API key from the session if it's there
    session.pop('api_key', None)
    return redirect(url_for('index'))


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
    data = request.get_json()
    if history_chain is None:
        # Initialize the chains if not already done
        set_up_chains(session['model'])

    response = history_chain.run({"location": data['location'], "time_period": data['year']})
    return jsonify({'response': response['response']})



@app.route('/handle_selected_text', methods=['POST'])
def handle_selected_text():
    data = request.get_json()
    if followup_chain is None:
        # Initialize the chains if not already done
        set_up_chains(session['model'])

    response = followup_chain.run({
        "location": data['location'],
        "time_period": data['year'],
        "previous_response": data['previous_response'],
        "selected_text": data['selected_text']
    })
    return jsonify({'response': response['response']})

if __name__ == "__main__":
    app.run(debug=True)
