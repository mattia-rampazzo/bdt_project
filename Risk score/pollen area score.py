from flask import Flask, jsonify, request
from flask_sqlalchemy import SQLAlchemy

risk_weights = {
    'pollen_level': 0.4,
    'severity_of_allergy': 0.3,
    'air_quality': 0.2,
    'physical_activity': 0.1,
    'combination_effect': 0.5  # Additional weight for combination effects
}

# Example thresholds for different risk levels (these should be adjusted based on expert opinion)
pollen_thresholds = {'low': 30, 'medium': 60, 'high': 100}
air_quality_thresholds = {'good': 50, 'moderate': 100, 'unhealthy': 150}

def get_pollen_level(location, pollen_type):
    # Fetch pollen level for the location and pollen type
    pass

def get_air_quality(location):
    # Fetch air quality index for the location
    pass

def get_physical_activity(user_id):
    # Fetch physical activity status for the user
    pass

def calculate_risk_score(pollen_level, severity_of_allergy, air_quality, physical_activity):
    normalized_pollen_level = pollen_level / pollen_thresholds['high']
    normalized_air_quality = air_quality / air_quality_thresholds['unhealthy']
    severity_weight = {'mild': 0.3, 'moderate': 0.6, 'severe': 1.0}[severity_of_allergy]
    normalized_physical_activity = physical_activity  # 1 if active, 0 if inactive

    risk_score = (
        risk_weights['pollen_level'] * normalized_pollen_level +
        risk_weights['severity_of_allergy'] * severity_weight +
        risk_weights['air_quality'] * normalized_air_quality +
        risk_weights['physical_activity'] * normalized_physical_activity
    )

    # Add combination effect if necessary
    if pollen_level > pollen_thresholds['medium'] and physical_activity:
        risk_score += risk_weights['combination_effect']

    return risk_score

# Example of combining factors to get the risk score
pollen_level = get_pollen_level('Trento')
air_quality = get_air_quality('Trento')
physical_activity = get_physical_activity('user_123')
severity_of_allergy = 'severe'  # This would be user input

risk_score = calculate_risk_score(pollen_level, severity_of_allergy, air_quality, physical_activity)

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///risk_data.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

class UserRiskData(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.String(100), nullable=False)
    location = db.Column(db.String(100), nullable=False)
    risk_score = db.Column(db.Float, nullable=False)

@app.route('/calculate-risk', methods=['POST'])
def calculate_risk():
    data = request.json
    pollen_level = get_pollen_level(data['location'], data['pollen_type'])
    air_quality = get_air_quality(data['location'])
    physical_activity = data['physical_activity']
    severity_of_allergy = data['severity_of_allergy']

    risk_score = calculate_risk_score(pollen_level, severity_of_allergy, air_quality, physical_activity)
    
    new_risk = UserRiskData(
        user_id=data['user_id'], 
        location=data['location'], 
        risk_score=risk_score
    )
    db.session.add(new_risk)
    db.session.commit()
    return jsonify({'user_id': data['user_id'], 'risk_score': risk_score})

if __name__ == '__main__':
    db.create_all()
    app.run(debug=True)
