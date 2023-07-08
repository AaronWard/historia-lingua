from flask import Flask, render_template, request
from geopy.geocoders import Nominatim

app = Flask(__name__)
geolocator = Nominatim(user_agent="geoapiExercises")

@app.route("/")
def index():
    return render_template('index.html')

@app.route("/location", methods=['POST'])
def location():
    data = request.get_json()
    lat = data['lat']
    lon = data['lon']

    location = geolocator.reverse([lat, lon])

    return location.address

if __name__ == "__main__":
    app.run(debug=True)
