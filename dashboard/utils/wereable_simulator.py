import random
import time

class WereableSimulator:
    def __init__(self, individual_id, lat, lng, stress=False, illness = False, normal = True):
        self.stress = stress
        self.illness = illness
        self.normal = normal
        self.individual_id = individual_id
        self.lat = float(lat)
        self.lng = float(lng)
        self.data = {
            'heart_rate': 70,
            'ibi': 1000 / 70,
            'eda': 5,
            'skin_temp': 33,
            'activity_level': 0
        }

    def _update_data(self):
        previous_data = self.data.copy()
        
        # Gradual heart rate change
        self.data['heart_rate'] = round(
            previous_data['heart_rate'] + random.uniform(-1, 1), 2
        )
        # Recalculate IBI
        self.data['ibi'] = round(1000 / self.data['heart_rate'], 2)
        
        # EDA changes more slowly
        self.data['eda'] = round(
            0.9 * previous_data['eda'] + 0.1 * (previous_data['eda'] + random.uniform(-0.2, 0.2)), 2
        )
        
        # Skin temperature changes very slowly
        self.data['skin_temp'] = round(
            0.99 * previous_data['skin_temp'] + 0.01 * (previous_data['skin_temp'] + random.uniform(-0.05, 0.05)), 2
        )
        
        # Activity level updates with small variability
        self.data['activity_level'] = round(
            max(0, min(1, previous_data['activity_level'] + random.uniform(-0.01, 0.01))), 2
        )

        # Apply bounds for realism
        self.data['eda'] = max(1, min(10, self.data['eda']))
        self.data['heart_rate'] = max(50, min(150, self.data['heart_rate']))
        self.data['skin_temp'] = max(30, min(40, self.data['skin_temp']))


        

    def _simulate_stress_increase(self, stress_level=3):
        """
        Simulates the physiological effects of stress.
        - Increases heart rate, EDA, and skin temperature.
        - Adjusts activity level slightly to reflect agitation.
        """
        # Gradual increase in heart rate
        stress_impact = random.uniform(5, 15) * stress_level
        self.data['heart_rate'] = round(
            min(150, self.data['heart_rate'] + stress_impact), 2
        )
        # Ensure heart_rate is above 101
        self.data['heart_rate'] = max(self.data['heart_rate'], 101)

        self.data['ibi'] = round(1000 / self.data['heart_rate'], 2)
        
        # Significant increase in EDA during stress
        self.data['eda'] = round(min(15, self.data['eda'] + random.uniform(3, 6)), 2)
        # Ensure EDA is above 10.5
        self.data['eda'] = max(self.data['eda'], 10.5)
        
        # Slight increase in skin temperature due to stress
        self.data['skin_temp'] = round(
            min(37.5, self.data['skin_temp'] + random.uniform(0.1, 0.3)), 2
        )
        
        # Small increase in activity level
        self.data['activity_level'] = round(
            min(1, self.data['activity_level'] + random.uniform(0.02, 0.1)), 2
        )


    def _simulate_illness(self):
        """
        Simulates the physiological effects of illness.
        - Elevates skin temperature to mimic fever.
        - Modifies heart rate and EDA to reflect sickness.
        - Reduces activity level to mimic fatigue.
        """
        # Elevated skin temperature to fever range
        self.data['skin_temp'] = round(random.uniform(37.5, 40.0), 2)
        
        # Increased heart rate due to fever/stress
        fever_impact = random.uniform(5, 10)
        self.data['heart_rate'] = round(
            min(150, self.data['heart_rate'] + fever_impact), 2
        )
        self.data['ibi'] = round(1000 / self.data['heart_rate'], 2)
        
        # Slight increase in EDA due to illness-related stress
        self.data['eda'] = round(min(12, self.data['eda'] + random.uniform(1, 3)), 2)
        
        # Reduced activity level due to fatigue
        self.data['activity_level'] = round(
            max(0, self.data['activity_level'] - random.uniform(0.1, 0.3)), 2
        )


    def set_stress(self, stress):
        self.stress = stress
        self.normal = not stress

    def set_illness(self, illness):
        self.illness = illness
        self.normal = not illness

    def generate_data(self):
        if self.stress:
            self._simulate_stress_increase(stress_level=3)
            self.stress = False

        if self.illness:
            self._simulate_illness()
            self.illness = False

        # Update data to reflect normal variability
        self._update_data()
        
        # Add location and ID information
        self.data["id"] = self.individual_id
        self.data["lat"] = self.lat
        self.data["lng"] = self.lng
        self.data["timestamp"] = time.time()

        return self.data