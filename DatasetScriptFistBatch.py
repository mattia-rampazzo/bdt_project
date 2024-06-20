# Install CTGAN
#!pip install ctgan

# Import necessary libraries
import pandas as pd
from ctgan import CTGAN

# Load the dataset
dataset_path = "//content/drive/MyDrive/data/SyntheticV5_Updated(1).csv"
data = pd.read_csv(dataset_path)

# Display the first few rows and summary statistics of the original data
print("Original Data Head:")
print(data.head())
print("\nOriginal Data Statistics:")
print(data.describe())

#CTGAN needs to standardize the values in the columns
features = ['gender','age','Height_cm','Weight_kg','bmi','hypertension','heart_disease','ever_married','work_type','Residence_type','stroke','Current Smoker','EX-Smoker','Obesity','Cad','Hay Fever','Asthma','Birch Pollen','Ragweed Pollen','Grass Pollen','Oak Pollen','Cedar Pollen','Maple Pollen','Pine Pollen','Nettle Pollen']

# Train the CTGAN model
ctgan = CTGAN(verbose=True)
ctgan.fit(data, features, epochs=1000)

# Generate synthetic data
synthetic_data = ctgan.sample(1000)

# Display the first few rows of the synthetic data
print("\nSynthetic Data Head:")
print(synthetic_data.head())

# Compare the original and synthetic data statistics
original_stats = data.describe()
synthetic_stats = synthetic_data.describe()

print("\nOriginal Data Statistics:")
print(original_stats)

print("\nSynthetic Data Statistics:")
print(synthetic_stats)

#Save the data choose the correct folder desitnation

synthetic_file_path = '/content/DatasetSynthetic.csv'
synthetic_data.to_csv(synthetic_file_path, index=False)