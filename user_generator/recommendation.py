import numpy as np
import pandas as pd

# Load the user data from the CSV file
df = pd.read_csv('/content/SmallDatasetV1.csv')

# Select a specific user (for example, the first user in the DataFrame)
user_data = df.iloc[0]  # Adjust the index to select different users

# Example functions for calculating individual indexes
# Sources:
# - Pollen impact: Bousquet et al., "ARIA (Allergic Rhinitis and its Impact on Asthma) guidelines."
# - Air quality impact: US EPA, WHO guidelines on AQI, PM2.5, PM10, Ozone, etc.
# - Asthma and respiratory conditions: Global Initiative for Asthma (GINA) reports.

# Calculate Pollen Exposure Index (PEI) and individual pollen scores
def calculate_pei(environmental_data):
    pollen_weights = {
        "alder_pollen": 1.0,  # Source: ARIA guidelines
        "birch_pollen": 1.5,  # Source: ARIA guidelines
        "grass_pollen": 1.2,  # Source: ARIA guidelines
        "mugwort_pollen": 1.3,  # Source: ARIA guidelines
        "olive_pollen": 1.0,  # Source: ARIA guidelines
        "ragweed_pollen": 1.4  # Source: ARIA guidelines
    }

    # Calculate individual pollen scores
    pollen_scores = {}
    for pollen_type, weight in pollen_weights.items():
        pollen_scores[pollen_type] = environmental_data[pollen_type] * weight

    # Total pollen exposure index
    total_pollen_score = sum(pollen_scores.values())

    return total_pollen_score, pollen_scores

# Calculate Air Quality Impact Index (AQII)
def calculate_aqii(environmental_data):
    # AQI is from 0 to 500
    aqi_score = environmental_data["european_aqi"]

    # Thresholds based on WHO/EPA guidelines (typical max concentrations)
    pm10_max = 50  # WHO guidelines
    pm2_5_max = 25  # WHO guidelines
    no2_max = 40  # WHO guidelines
    so2_max = 20  # WHO guidelines
    co_max = 10  # WHO guidelines
    ozone_max = 120  # WHO guidelines

    # Calculate impact scores directly from concentration levels
    pm10_score = (environmental_data["pm10"] / pm10_max) * 50
    pm2_5_score = (environmental_data["pm2_5"] / pm2_5_max) * 50
    no2_score = (environmental_data["nitrogen_dioxide"] / no2_max) * 40
    so2_score = (environmental_data["sulphur_dioxide"] / so2_max) * 20
    co_score = (environmental_data["carbon_monoxide"] / co_max) * 10
    ozone_score = (environmental_data["ozone"] / ozone_max) * 120

    # Aggregate air quality score without normalization
    aqii = aqi_score + pm10_score + pm2_5_score + no2_score + so2_score + co_score + ozone_score

    return aqii

# Define the missing function calculate_air_quality_impact
def calculate_air_quality_impact(environmental_data, weights):
    aqi_score = (environmental_data["european_aqi"] / 100) * weights["aqi"]
    pm10_score = (environmental_data["pm10"] / 100) * weights["pm10"]
    pm2_5_score = (environmental_data["pm2_5"] / 100) * weights["pm2_5"]
    ozone_score = (environmental_data["ozone"] / 100) * weights["ozone"]

    return aqi_score + pm10_score + pm2_5_score + ozone_score

# Calculate Ozone-Pollen Interaction Index (OPII)
def calculate_opii(environmental_data):
    # Ozone impact on pollen allergenicity
    total_pollen_score, _ = calculate_pei(environmental_data)
    ozone_concentration = environmental_data["ozone"]  # No normalization yet

    # Interaction: Ozone makes pollen more allergenic
    opii = total_pollen_score * (ozone_concentration / 120)  # Based on WHO guidelines

    return opii

# Calculate Particulate Matter Health Index (PMHI)
def calculate_pmhi(environmental_data):
    pm10_score = environmental_data["pm10"]  # No normalization yet
    pm2_5_score = environmental_data["pm2_5"]  # No normalization yet

    # Aggregate using literature weights, PM2.5 is more dangerous
    pmhi = (pm10_score * 0.4) + (pm2_5_score * 0.6)  # Based on WHO guidelines

    return pmhi

# Calculate Composite Environmental Risk Index (CERI)
def calculate_ceri(environmental_data):
    # Calculate individual indexes without normalization
    total_pollen_score, _ = calculate_pei(environmental_data)
    aqii = calculate_aqii(environmental_data)
    opii = calculate_opii(environmental_data)
    pmhi = calculate_pmhi(environmental_data)

    # Aggregate the total score before normalization
    total_score = total_pollen_score + aqii + opii + pmhi

    # Normalize the total score to a 0-1 scale (assuming max score is a high estimate like 2000)
    normalized_ceri = total_score / 2000.0
    normalized_ceri = min(max(normalized_ceri, 0), 1)  # Ensuring it's within 0-1

    return normalized_ceri

# Function to calculate the overall risk score for a specific user
def calculate_risk_score(environmental_data, user_data, weights):
    total_pollen_score, pollen_scores = calculate_pei(environmental_data)

    # Adjust for user allergies based on the new column names
    base_pollen_score = 0
    for pollen_type, score in pollen_scores.items():
        allergy_column = f"{pollen_type.split('_')[0].capitalize()}_Pollen_Allergy"  # Assuming column names like "Alder_Pollen_Allergy"
        if user_data[allergy_column] == 1:
            base_pollen_score += score * weights["pollen"] * 1.5  # Increase score due to allergy (literature-backed)
        else:
            base_pollen_score += score * weights["pollen"]

    # Calculate the environmental impact score
    environmental_impact_score = calculate_air_quality_impact(environmental_data, weights)

    # Adjust the final score for user-specific conditions
    final_score = base_pollen_score + environmental_impact_score

    if user_data["Asthma_Allergy"] == 1:
        final_score *= 1.3  # WHO and ARIA guidelines
    if user_data["HayFever"] == 1:
        final_score *= 1.1  # WHO and ARIA guidelines
    if user_data["Eczema"] == 1:
        final_score *= 1.05  # ARIA guidelines
    if user_data["Cad"] == 1:
        final_score *= 1.2  # CAD exacerbation due to poor air quality (American Heart Association)

    # Normalize the final score to 0-1
    final_score = min(final_score / 15.0, 1.0)

    return final_score, pollen_scores

def generate_recommendation(score, user_data, environmental_data, pollen_scores):
    recommendations = []

    # General recommendation based on the score
    if score < 0.3:
        recommendations.append("General: You might experience mild symptoms.")
    elif score < 0.7:
        recommendations.append("General: You might experience moderate symptoms. Be cautious.")
    else:
        recommendations.append("General: You might experience severe symptoms. Avoid exposure if possible.")

    # Specific recommendations based on allergies and conditions
    for pollen_type, pollen_score in pollen_scores.items():
        allergy_column = f"{pollen_type.split('_')[0].capitalize()}_Pollen_Allergy"
        if user_data[allergy_column] == 1:
            if pollen_score < 0.5:
                recommendations.append(f"{pollen_type.replace('_', ' ').title()}: Low pollen levels detected. You might experience mild symptoms.")
            elif pollen_score < 0.8:
                recommendations.append(f"{pollen_type.replace('_', ' ').title()}: Moderate pollen levels detected. You might experience moderate symptoms. Consider taking antihistamines.")
            else:
                recommendations.append(f"{pollen_type.replace('_', ' ').title()}: High pollen levels detected. Consider staying indoors and take necessary precautions.")

    if user_data["Asthma_Allergy"] == 1:
        asthma_risk = np.mean([pollen_scores[pt] for pt in pollen_scores if user_data[f"{pt.split('_')[0].capitalize()}_Pollen_Allergy"] == 1])
        if asthma_risk < 0.5:
            recommendations.append("Asthma: Low risk detected. Keep your inhaler handy, but you might not experience severe symptoms.")
        elif asthma_risk < 0.8:
            recommendations.append("Asthma: Moderate risk detected. Use your inhaler as needed and avoid strenuous activities.")
        else:
            recommendations.append("Asthma: High risk detected. Limit outdoor activities, have your inhaler accessible, and consider staying indoors.")

    if user_data["HayFever"] == 1:
        hay_fever_risk = np.mean([pollen_scores[pt] for pt in pollen_scores if user_data[f"{pt.split('_')[0].capitalize()}_Pollen_Allergy"] == 1])
        if hay_fever_risk < 0.5:
            recommendations.append("Hay Fever: Low risk detected. Symptoms might be mild.")
        elif hay_fever_risk < 0.8:
            recommendations.append("Hay Fever: Moderate risk detected. Take antihistamines and limit outdoor exposure.")
        else:
            recommendations.append("Hay Fever: High risk detected. Stay indoors if possible and take antihistamines.")

    if user_data["Eczema"] == 1:
        eczema_risk = np.mean([pollen_scores[pt] for pt in pollen_scores if user_data[f"{pt.split('_')[0].capitalize()}_Pollen_Allergy"] == 1])
        if eczema_risk < 0.5:
            recommendations.append("Eczema: Low risk of skin irritation. Keep your skin moisturized and avoid known irritants.")
        elif eczema_risk < 0.8:
            recommendations.append("Eczema: Moderate risk of skin irritation. Moisturize frequently and avoid exposure to high pollen areas.")
        else:
            recommendations.append("Eczema: High risk of severe skin irritation. Stay indoors, moisturize often, and avoid known irritants.")

    if user_data["Cad"] == 1:
        recommendations.append("Cardiac Health: High risk of exacerbation due to poor air quality. Avoid outdoor exertion, monitor your heart condition, and consult your doctor if necessary.")

    return recommendations


# Main function to process user and environmental data
def main(user_data, environmental_data):
    # Weightings for the environmental factors based on literature
    weights = {
        "pollen": 1.0,  # Pollen weight reflects its direct impact on allergic individuals
        "aqi": 1.5,     # Higher weight for AQI due to its compounded effects on respiratory conditions
        "pm10": 1.0,
        "pm2_5": 1.3,   # PM2.5 has a greater impact on respiratory health (WHO and EPA guidelines)
        "ozone": 1.2,   # Ozone is known to exacerbate asthma and allergic reactions
    }

    # Calculate each index
    pei, pollen_scores = calculate_pei(environmental_data)
    aqii = calculate_aqii(environmental_data)
    opii = calculate_opii(environmental_data)
    pmhi = calculate_pmhi(environmental_data)
    ceri = calculate_ceri(environmental_data)

    # Calculate the risk score for the user
    final_score, pollen_scores = calculate_risk_score(environmental_data, user_data, weights)

    # Generate personalized recommendations
    recommendations = generate_recommendation(final_score, user_data, environmental_data, pollen_scores)

    # Return all the scores and the recommendations
    return {
        "pei": pei,
        "aqii": aqii,
        "opii": opii,
        "pmhi": pmhi,
        "ceri": ceri,
        "final_score": final_score,
        "pollen_scores": pollen_scores,
        "recommendations": recommendations
    }

# Example usage with user data and environmental data
if __name__ == "__main__":
    # Example environmental data
    environmental_data = {
        "municipality_id": "22127",
        "name": "Nogaredo",
        "latitude": "45.91201029",
        "longitude": "11.02309066",
        "european_aqi": 42.0,
        "us_aqi": 44.39236068725586,
        "pm10": 16.700000762939453,
        "pm2_5": 9.399999618530273,
        "carbon_monoxide": 155.0,
        "nitrogen_dioxide": 1.2999999523162842,
        "sulphur_dioxide": 0.4000000059604645,
        "ozone": 103.0,
        "aerosol_optical_depth": 0.28999999165534973,
        "dust": 6.0,
        "uv_index": 5.849999904632568,
        "uv_index_clear_sky": 7.25,
        "ammonia": 2.5,
        "alder_pollen": 0.0,
        "birch_pollen": 0.0,
        "grass_pollen": 2.2,
        "mugwort_pollen": 4.9,
        "olive_pollen": 0.0,
        "ragweed_pollen": 2.1,
        "temperature_2m": 31.5
    }

    # Example user data (from a DataFrame, here we select the first row as an example)
    user_data = df.iloc[0]  # Adjust the index to select different users

    # Run the main function
    results = main(user_data, environmental_data)

# Output the results
results = main(user_data, environmental_data)

print("Scores:")
print(f"PEI: {results['pei']:.2f}")
print(f"AQII: {results['aqii']:.2f}")
print(f"OPII: {results['opii']:.2f}")
print(f"PMHI: {results['pmhi']:.2f}")
print(f"CERI: {results['ceri']:.2f}")
print(f"Final Risk Score: {results['final_score']:.2f}\n")

# Print individual pollen scores
print("Pollen Scores:")
for pollen_type, pollen_score in results['pollen_scores'].items():
    print(f"{pollen_type.replace('_', ' ').title()}: {pollen_score:.2f}")

print("\nRecommendations:")
for recommendation in results['recommendations']:
    print(f"- {recommendation}")
