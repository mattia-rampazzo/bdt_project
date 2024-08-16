import redis
import folium
import random
import json
import pandas as pd

def get_redis_connection():
    return redis.Redis(host='localhost', port=6379, db=0)

# Define the classify_pollen_concentration function
def classify_pollen_concentration(pollen_type, concentration):
    thresholds = {
        "Alder": [15, 90, 1500, float('inf')],
        "Birch": [15, 90, 1500, float('inf')],
        "Grass": [5, 20, 200, float('inf')],
        "Mugwort": [10, 50, 500, float('inf')],
        "Olive": [15, 90, 1500, float('inf')],
        "Ragweed": [10, 50, 500, float('inf')]
    }

    levels = ["Low", "Moderate", "High", "Very High"]

    if pollen_type in thresholds:
        index = 0
        while concentration > thresholds[pollen_type][index]:
            index += 1
        return levels[index]

    return "Unknown Pollen Type or Invalid Concentration"

# Define the get_pollen_risk_color function
def get_pollen_risk_color(pollen_risk):
    risk_colors = {
        "Low": "#00FF00",        # Green
        "Moderate": "#FFFF00",   # Yellow
        "High": "#FFA500",       # Orange
        "Very High": "#FF0000"   # Red
    }
    return risk_colors.get(pollen_risk, "#808080")  # Default to gray for unknown risks



def generate_pollen_risk_map():
 
    # Load the GeoJSON data
    geojson_path = 'Trentino-AltoAdige_municipalities.geojson'
    with open(geojson_path) as f:
        geojson_data = json.load(f)

    r = get_redis_connection()
    # Get all keys matching the pattern 'municipality:*'
    municipality_keys = r.keys('municipality:*')



    data = []
    pollen_risk_dict = {}

    # Here implement the user logic
    for key in municipality_keys:
        key_str = key.decode('utf-8')
        
        municipality_data = r.hgetall(key_str)
        municipality_data = {key.decode('utf-8'): value.decode('utf-8') for key, value in municipality_data.items()}

        # print(municipality_data)

        # Simulation for Grass
        pollen_type = "Grass"
        concentration = random.randint(0, 250) 

        # Classify pollen concentration
        pollen_risk = classify_pollen_concentration(pollen_type, concentration)

        # Get the color corresponding to the risk level
        color = get_pollen_risk_color(pollen_risk)

        record = {"municipality_id": municipality_data["municipality_id"], "pollen_risk": concentration}

        pollen_risk_dict[int(municipality_data["municipality_id"])] = pollen_risk


        data.append(record)

    # Convert into a DataFrame
    df = pd.DataFrame(data)


    # https://python-visualization.github.io/folium/latest/advanced_guide/colormaps.html#Self-defined
    def my_color_function(feature):

        # If I have no data
        if feature["properties"]["com_istat_code_num"] not in pollen_risk_dict.keys():
            return"#000000"
        
        pollen_risk = pollen_risk_dict[feature["properties"]["com_istat_code_num"]]

        return get_pollen_risk_color(pollen_risk)

    
    # almost average coordinates of Trentino Alto Adige
    m = folium.Map(location=[46.4, 11.4], tiles="cartodb positron", zoom_start=8)

    folium.GeoJson(
        geojson_data,
        style_function=lambda feature: {
            "fillColor": my_color_function(feature),
            "fill_opacity": 0.8,
            "opacity": 0.1,
        },
    ).add_to(m)
    
    m.save("static/pollen_risk_map.html")

    return
    # return m._repr_html_()

generate_pollen_risk_map()