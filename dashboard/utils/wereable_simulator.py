import random
import time

class WereableSimulator:
    def __init__(self, stress=False, illness = False, normal = True, individual_id="c6155cd0-d865-4265-af3a-dfb1102c1067", lat=46.215179, lng=11.119681):
        self.stress = stress
        self.illness = True
        self.normal = normal
        self.individual_id = individual_id
        self.lat = lat
        self.lng = lng
        self.data = {
            'heart_rate': 70,
            'ibi': 1000 / 70,
            'eda': 5,
            'skin_temp': 33,
            'activity_level': 0
        }

    def _update_data(self):
        # Update heart_rate with some variability
        previous_data = self.data.copy()

        # Update heart_rate with a small random variation
        self.data['heart_rate'] = round(previous_data['heart_rate'] + random.uniform(-5, 5), 2)

        # Update ibi based on the new heart_rate
        self.data['ibi'] = round(1000 / self.data['heart_rate'], 2)

        # Update eda with a small random variation
        self.data['eda'] = round(previous_data['eda'] + random.uniform(-1, 1), 2)
        
        # Update skin_temp with a small random variation
        self.data['skin_temp'] = round(previous_data['skin_temp'] + random.uniform(-0.5, 0.5), 2)

        # Update activity_level with a small random variation
        self.data['activity_level'] = round(previous_data['activity_level'] + random.uniform(-0.05, 0.05), 2)

        if self.normal:
            # ensure normal values
            self.data['eda'] = max(1, min(10, self.data['eda']))
            self.data['heart_rate'] = max(60, min(100, self.data['heart_rate']))
            self.data['skin_temp'] = max(30, min(37, self.data['skin_temp']))
            self.data['activity_level'] = max(0, min(1, self.data['activity_level']))

        

    def _simulate_stress_increase(self, stress_level):

        # Increase heart rate with stress
        self.data['heart_rate'] += stress_level * random.uniform(5, 15)
        self.data['ibi'] = 1000 / self.data['heart_rate']

        # Increase EDA with stress
        self.data['eda'] = 12

        # Increase skin temperature slightly with stress
        self.data['skin_temp'] += stress_level * random.uniform(0.1, 0.3)

        # Increase activity level slightly
        self.data['activity_level'] += stress_level * random.uniform(0.05, 0.1)

    def _simulate_illness(self):

        # Increase heart rate with stress
        self.data['skin_temp'] =  random.uniform(37.5, 40)


    def set_stress(self, stress):
        self.stress = stress
        self.normal = not stress

    def set_illness(self, illness):
        self.illness = illness
        self.normal = not illness

    def generate_data(self):

        if self.stress:
            self._simulate_stress_increase(stress_level=1)
            self.stress = False

        if self.illness:
            self._simulate_illness()
            self.illness = False
        self._update_data()
        
        # Add location and ID information
        self.data["id"] = self.individual_id
        self.data["lat"] = self.lat
        self.data["lng"] = self.lng
        self.data["timestamp"] = time.time()

        return self.data