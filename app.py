import os
from flask import Flask, render_template, request, jsonify
from geopy.geocoders import Nominatim
from dotenv import load_dotenv
import argparse
from src.history_chain import HistoryChain
from src.followup_chain import FollowUpChain
from src.utils.env_utils import get_openai_key

app = Flask(__name__)
geolocator = Nominatim(user_agent="map_app")

parser = argparse.ArgumentParser()
parser.add_argument("--env_path", help="The path to the .env file containing the OpenAI key")
args = parser.parse_args()
load_dotenv(dotenv_path=args.env_path)
openai_api_key = get_openai_key(args.env_path)

history_chain = HistoryChain(openai_api_key=openai_api_key)
followup_chain = FollowUpChain(openai_api_key=openai_api_key)

def get_location_detail(lat, lon, zoom):
    location = geolocator.reverse([lat, lon], exactly_one=True)
    address = location.raw['address']

    if zoom <=2:
        return address.get('country', '')
    elif zoom <= 5:
        return ', '.join(filter(None, [address.get('state', ''), address.get('country', '')]))
    elif zoom <= 10:
        return ', '.join(filter(None, [address.get('city', ''), address.get('state', ''), address.get('country', '')]))
    else:
        return ', '.join(filter(None, [address.get('road', ''), address.get('city', ''), address.get('state', ''), address.get('country', '')]))

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
    response = history_chain.run({"location": data['location'], "time_period": data['year']})
    
    return jsonify({'response': response['response']})

@app.route('/handle_selected_text', methods=['POST'])
def handle_selected_text():
    data = request.get_json()

    response = followup_chain.run({"location": data['location'], "time_period": data['year'],
                                   "previous_response": data['previous_response'], "selected_text": data['selected_text']})
    
    return jsonify({'response': response['response']})


@app.route('/')
def index():
    return render_template('index.html')

if __name__ == "__main__":
    app.run(debug=True)
