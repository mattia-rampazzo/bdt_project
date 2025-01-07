import folium.elements
import folium
import json
import os

from services.redis_client import RedisClient


# Classify pollen concentration in 4 levels
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

# Get the colors
def get_pollen_risk_color(pollen_risk):
    risk_colors = {
        "Low": "#00FF00",        # Green
        "Moderate": "#FFFF00",   # Yellow
        "High": "#FFA500",       # Orange
        "Very High": "#FF0000"   # Red
    }
    return risk_colors.get(pollen_risk, "#808080")  # Default to gray for unknown risks


# Function to add a legend to the map
def add_legend(map_object):
    legend_html = '''
     <div style="
     position: fixed; 
     bottom: 20px; right: 20px; width: 100px; height: 100px; 
     background-color: white; z-index:9999; font-size:11px;
     border:2px solid grey; padding: 10px;">
     <b>Pollen Levels</b><br>
     <span style="background-color: #00FF00; opacity: 0.8; width: 10px; height: 10px; display: inline-block; border-radius: 50%;"></span> Low<br>
     <span style="background-color: #FFFF00; opacity: 0.8; width: 10px; height: 10px; display: inline-block; border-radius: 50%;"></span> Moderate<br>
     <span style="background-color: #FFA500; opacity: 0.8; width: 10px; height: 10px; display: inline-block; border-radius: 50%;"></span> High<br>
     <span style="background-color: #FF0000; opacity: 0.8; width: 10px; height: 10px; display: inline-block; border-radius: 50%;"></span> Very High<br>
     </div>
     '''
    map_object.get_root().html.add_child(folium.Element(legend_html))

# Not working
def add_js(m):
    # Define the JavaScript code to be injected
    javascript = """
        <script>
            function onMapClick(e) {
                var lat = e.latlng.lat;
                var lon = e.latlng.lng;

                console.log("Clicked coordinates:", lat, lon);  // Debugging
                
                // Send the coordinates to the parent window
                window.parent.postMessage({ lat: lat, lon: lon }, '*');
            }
            map.on('click', onMapClick);
        </script>
    """

    # Add the JavaScript code to the map
    m.get_root().html.add_child(folium.Element(javascript))



# Generate Map 
def generate_pollen_risk_map():
 
    # Load the GeoJSON data of Trentino-AltoAdige
    geojson_path = os.path.join("data", "Trentino-AltoAdige_municipalities.geojson")
    with open(geojson_path) as f:
        geojson_data = json.load(f)


    r = RedisClient()
    # Get all keys matching the pattern 'municipality:*'
    municipality_keys = r.keys('municipality:*')

    # A dict containing a dict for each municipality
    # The inner dict contains the relative level of concentration for each pollen
    municipalities_pollen_risk_dict = {}
    
    for key in municipality_keys:        
        municipality_data = r.hgetall(key)
        municipality_id =  int(key.split(':')[1])
        
        # print(municipality_id)
        # print(municipality_data)
        alder_pollen = float(municipality_data.get('alder_pollen', 0.0))
        birch_pollen = float(municipality_data.get('birch_pollen', 0.0))
        mugwort_pollen = float(municipality_data.get('mugwort_pollen', 0.0))
        olive_pollen = float(municipality_data.get('olive_pollen', 0.0))
        ragweed_pollen = float(municipality_data.get('ragweed_pollen', 0.0))
        grass_pollen = float(municipality_data.get('grass_pollen', 0.0))

        # Classify pollen concentration
        pollen_risk = {}
        pollen_risk["Alder"] = classify_pollen_concentration("Alder", alder_pollen)
        pollen_risk["Birch"] = classify_pollen_concentration("Birch", birch_pollen)
        pollen_risk["Mugwort"] = classify_pollen_concentration("Mugwort", mugwort_pollen)
        pollen_risk["Olive"] = classify_pollen_concentration("Olive", olive_pollen)
        pollen_risk["Ragweed"] = classify_pollen_concentration("Ragweed", ragweed_pollen)
        pollen_risk["Grass"] = classify_pollen_concentration("Grass", grass_pollen)

        # Assign the pollen ris
        municipalities_pollen_risk_dict[municipality_id] = pollen_risk


    # https://python-visualization.github.io/folium/latest/advanced_guide/colormaps.html#Self-defined
    def my_color_function(feature, key):

        # Those municipalities with no data
        if feature["properties"]["com_istat_code_num"] not in municipalities_pollen_risk_dict.keys():
            return"#000000"

        # pollen risk for a specific type (e.g key=Alder)
        pollen_risk = municipalities_pollen_risk_dict[feature["properties"]["com_istat_code_num"]][key]


        return get_pollen_risk_color(pollen_risk)

    
    # almost average coordinates of Trentino Alto Adige
    m = folium.Map(location=[46.4, 11.4], tiles="cartodb positron", zoom_start=8)


    for pollen in ['Alder','Birch', 'Mugwort', 'Olive', 'Ragweed', 'Grass']:

        fg = folium.FeatureGroup(name=pollen, show=False, control=True)  

        # Show by default
        if pollen == 'Grass':
            fg = folium.FeatureGroup(name=pollen, show=True)

        folium.GeoJson(
            geojson_data,
            style_function=lambda feature, key=pollen: {
                "fillColor": my_color_function(feature, key),
                "fillOpacity": 0.4,
                "opacity": 0.1,
            },
            highlight_function=lambda feature: {
                "fillOpacity": 1,
                "opacity": 0.8,
            },
            
        ).add_to(fg)

        # Add the FeatureGroup to the map
        fg.add_to(m)


    # Layer control to the map to toggle between pollen types
    folium.LayerControl(collapsed=False).add_to(m)
    # Add legend
    add_legend(m)

    # Save map
    print("Saving map")
    map_path = os.path.join("static", "pollen_risk_map.html")
    m.save(map_path)

    return m.get_root()._repr_html_()
    # return m._repr_html_()

if __name__=="__main__":
    generate_pollen_risk_map()