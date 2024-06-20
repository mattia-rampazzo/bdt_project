from flask import Flask, jsonify, request
from flask_sqlalchemy import SQLAlchemy

risk_weights = {
    'age': 0.2,
    'lifestyle': 0.2,
    'BMI': 0.2,
    'family_history': 0.1,
    'air_quality': 0.1,
    'heart_rate_peak': 0.2,
    'combination_effect': 0.5  # Additional weight for combination effects
}

# Example thresholds for different risk levels (these should be adjusted based on expert opinion)
bmi_thresholds = {'normal': 24.9, 'overweight': 29.9, 'obese': 30}
air_quality_thresholds = {'good': 50, 'moderate': 100, 'unhealthy': 150}
heart_rate_thresholds = {'normal': 100, 'elevated': 140, 'peak': 180}

def get_age(user_id):
    # Fetch the age of the user
    pass

def get_lifestyle(user_id):
    # Fetch lifestyle data (e.g., smoking, alcohol, diet, activity level)
    pass

def get_bmi(user_id):
    # Fetch the BMI of the user
    pass

def get_family_history(user_id):
    # Fetch family history of heart disease
    pass

def get_air_quality(location):
    # Fetch air quality index for the location
    pass

def get_heart_rate(user_id):
    # Fetch current heart rate from wearable device
    pass

def calculate_heart_risk_score(age, lifestyle, bmi, family_history, air_quality, heart_rate_peak):
    normalized_age = age / 100  # Normalizing age assuming a maximum of 100 years
    normalized_bmi = bmi / bmi_thresholds['obese']
    normalized_air_quality = air_quality / air_quality_thresholds['unhealthy']
    normalized_heart_rate = heart_rate_peak / heart_rate_thresholds['peak']
    normalized_family_history = 1 if family_history else 0

    risk_score = (
        risk_weights['age'] * normalized_age +
        risk_weights['lifestyle'] * lifestyle +
        risk_weights['BMI'] * normalized_bmi +
        risk_weights['family_history'] * normalized_family_history +
        risk_weights['air_quality'] * normalized_air_quality +
        risk_weights['heart_rate_peak'] * normalized_heart_rate
    )

    # Add combination effect if necessary
    if heart_rate_peak > heart_rate_thresholds['elevated'] and bmi > bmi_thresholds['overweight']:
        risk_score += risk_weights['combination_effect']

    return risk_score

# Example of combining factors to get the risk score
age = get_age('user_123')
lifestyle = get_lifestyle('user_123')
bmi = get_bmi('user_123')
family_history = get_family_history('user_123')
air_quality = get_air_quality('Trento')
heart_rate_peak = get_heart_rate('user_123')

risk_score = calculate_heart_risk_score(age, lifestyle, bmi, family_history, air_quality, heart_rate_peak)

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///heart_risk_data.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

class UserHeartRiskData(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.String(100), nullable=False)
    location = db.Column(db.String(100), nullable=False)
    risk_score = db.Column(db.Float, nullable=False)

@app.route('/calculate-heart-risk', methods=['POST'])
def calculate_heart_risk():
    data = request.json
    age = get_age(data['user_id'])
    lifestyle = get_lifestyle(data['user_id'])
    bmi = get_bmi(data['user_id'])
    family_history = get_family_history(data['user_id'])
    air_quality = get_air_quality(data['location'])
    heart_rate_peak = get_heart_rate(data['user_id'])

    risk_score = calculate_heart_risk_score(age, lifestyle, bmi, family_history, air_quality, heart_rate_peak)
    
    new_risk = UserHeartRiskData(
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