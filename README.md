# PollenSense: A Data-Driven System for Personalized Allergy Recommendations

##  Abstract

This repository contains the source code and documentation for the 'PollenSense project, part of the course of Big Data Technologes at the University of Trento. The primary goal of the project is to provide real-time health recommendations to individuals affected by pollen allergies. By leveraging data from diverse sources such as meteorological APIs, wearable health devices, and user-reported symptoms and conditions, this system offers personalized advice to minimize allergen exposure and improve quality of life.

## Technologies

-   **Data Ingestion and Streaming:**
    -   Apache Kafka: Real-time data streaming from environmental sensors and APIs.
    -   RESTful APIs: Integration with external weather and pollen services.
-   **Data Storage and Management:**
    -   Apache Cassandra: Distributed NoSQL database for managing large-scale, structured, and semi-structured data with high availability.
    -   Redis: In-memory data store used for caching and fast access to frequently queried information.
-   **Data Processing and Analytics:**
    -   Apache Spark: Distributed data processing for high-velocity data streams.
-   **Synthetica data generation:**
    -   CTGAN (Conditional Tabular Generative Adversarial Network): Generates synthetic tabular data.
-   **Deployment:**
    -   Docker: Containerization and orchestration of the system's microservices.
-   **User Interface and Notifications:**
    -   Flask & Bootstrap: Web-based user dashboards.

## Architecture

![Architecture file](architecture.png)


##  How to run

The core application is containerized and managed using Docker for easy setup and deployment. Please Follow these steps to run the application:

1.  **Install Docker:**  
    Ensure Docker is installed on your system. You can download and install Docker from [Docker's official website](https://www.docker.com/).
    
2.  **Clone the Repository:**  
    Clone this GitHub repository to your local machine:
    
    ```bash
    git clone https://github.com/mattia-rampazzo/bdt_project.git
    cd bdt_project
    ```
    
3.  **Build the Docker Images:**  
    Build the required Docker images using the provided `Dockerfile` and `docker-compose.yml`:
    
    ```bash
    docker compose build
    ```
    
4.  **Start the Application:**  
    Start the entire application stack (including all services like Kafka, Cassandra, Redis, Flask, and Spark) using Docker Compose:
    
    ```bash
    docker compose up -d
    
    ```
    
5.  **Access the Dashboard:**  
    Once the application is running, you can access the dashboard by navigating with your preferred browser to:
    
    ```
    http://localhost:5000
    ```
    
6.  **Stop the Application:**  
    To stop the application run:
    
    ```bash
    docker compose down
 
    ```

## Project Structure 

A summary of the project structure and the main files is reported below:

`setup.py`:  Script that initializes the system.

### air_quality   
 -   `air_quality_fetch.py`: Script to fetch pollen and weather data and write it to Kafka.
 
### dashboard   
 -   `app.py`: The main Flask application file that runs the dashboard and handles server-side logic.
    -   `utils`: A directory containing two Python utility files:
		-   One for generating the live map representation.
		-   Another for simulating data from a wearable device.
    -   `templates`: Contains HTML templates for the dashboard.
    -   `data`: Contains GeoJSON data used for rendering geographic information on the map.

### data
 -   `Trentino-AltoAdige_municipalities.csv`: A CSV file containing updated data as of 2024, including ISTAT codes, municipality names, latitude, and longitude information for the municipalities in the Trentino-Alto Adige region.
 -   `Users_synthetic_dataset.csv`: A CSV file containing anonymized synthetic data including personal informations, medical conditions and pollen allergies.

### services
 -   `cassandra_client.py`: Manages communications with the Cassandra database.
 -   `kafka_client.py`: Manages interaction with Kafka.
 -   `redis_client.py`: Manages communications with the Redis database.

### spark_streaming
 -   `air_quality_stream.py`: Ingests real-time air quality data streams and writes to both Cassandra (for long-term storage) and Redis (for fast access and caching).
 -   `users_stream.py`:  Ingests and stores to Cassandra data about new users of the system.
 -   `recommendations_stream.py`:  Analyzes incoming data streams to generate real-time personalized health recommendations for users based on environmental and wearable data.

### user_generator
 -   `BGTOriginalDatasetBuilder_2_0.ipynb`: A notebook showing the procedure followed to build the CTGAN model to create synthetic user data.
 -   `CAD.csv`:  A CSV file for Cardiovascular disease analysis.
 -   `asthma_disease_data.csv`:  A CSV file for asthm analysis.
 -   `user_generation.py`:  Script that send new user to the system.


## Results

![Dashboard file](runs/1_first_recommendations.png)


# Predictions Folder

The `Predictions` folder, though not yet integrated with the core functionalities and the interface, serves as a foundation for future enhancements to the project. It showcases a solid, although not yet perfect, prediction system designed to empower users with insights into pollen levels. Once integrated, this system will enable users to make informed decisions, take proactive measures to manage their allergies, and plan their daily activities with greater confidence and protection. Below is a brief explanation of the contents of this folder:

### Folder Contents

1. **`Merged_Valleys_and_Municipalities.csv`**  
   This file contains the coordinates of most municipalities in the region, along with the valleys they are associated with. The dataset was built by integrating data from a geojson file ([source here](https://github.com/openpolis/geojson-italy/blob/5dd489e676158175c75ae452ab9ec449bf5efb4b/geojson/limits_IT_municipalities.geojson)) and additional data gathered via ChatGPT and online sources. While it does not cover all municipalities and valleys, it is sufficient for creating a structured model that includes the region's major valleys for reliable data gathering and predictions.

2. **`Valley_Boundaries.csv`**  
   This file defines the boundaries of each selected valley by constructing perimeters based on the municipalities within them. The area enclosed within these perimeters represents the corresponding valley's boundary.

3. **`config.json`**  
   A configuration file allowing users to launch simulations. It includes details such as:
   - The latitude and longitude for the region's focal point.
   - Types of pollen being monitored (e.g., Birch, Grass, Olive).
   - The specific pollen type selected for prediction.

4. **`daily_data.csv`**  
   A dataset containing simulation results for testing purposes. It includes daily pollen levels as captured or simulated during the project.

5. **`model.ipynb`**  
   A Jupyter Notebook that generates predictive models for pollen levels in each valley using the data collected. The predictive models for pollen levels across various valleys show promising overall performance, with many models achieving high R² values and low error metrics (RMSE, MAE), particularly for Alder, Grass, and Birch pollen in key regions. These results highlight the models' ability to generalize effectively in diverse geographic contexts. However, certain challenges remain, such as occasional overfitting indicated by overly optimistic R² values near 1.0 and instances of high RMSE or negative R² in specific valleys, particularly for Mugwort pollen. These issues suggest room for improvement in data quality, preprocessing, and model calibration. Future developments will focus on addressing these criticalities through enhanced datasets and refined predictive techniques to ensure more robust and reliable outcomes.

   ### Model Performance by Valley and Pollen Type
| Valley           	  | Pollen Type   |   RMSE |   MAE |    R² |
|:------------------------|:--------------|-------:|------:|------:|
| Val Venosta             | Alder         |   0.25 |  0.05 |  0.99 |
| Val Venosta             | Birch         |   2.72 |  0.93 |  0.89 |
| Val Venosta             | Grass         |   3.69 |  1.12 |  0.93 |
| Val Venosta             | Mugwort       |   0    |  0    | -0.5  |
| Val Venosta             | Olive         |   0.07 |  0.01 |  0.9  |
| Val Venosta             | Ragweed       |   0.03 |  0    |  0.96 |
| Val di Non              | Alder         |   0.97 |  0.12 |  0.89 |
| Val di Non              | Birch         |   3.32 |  0.72 |  0.99 |
| Val di Non              | Grass         |   1.18 |  0.33 |  0.99 |
| Val di Non              | Mugwort       |   0    |  0    |  1    |
| Val di Non              | Olive         |   0.1  |  0.01 |  1    |
| Val di Non              | Ragweed       |   0.05 |  0.01 |  0.97 |
| Burgraviato             | Alder         |   0.22 |  0.06 |  0.93 |
| Burgraviato             | Birch         |   3.2  |  1.29 |  0.9  |
| Burgraviato             | Grass         |   2.3  |  0.94 |  0.98 |
| Burgraviato             | Mugwort       |   0    |  0    |  0.79 |
| Burgraviato             | Olive         |   0.08 |  0.02 |  0.95 |
| Burgraviato             | Ragweed       |   0.02 |  0    |  0.97 |
| Val Badia               | Alder         |   0.33 |  0.06 |  0.88 |
| Val Badia               | Birch         |   2.3  |  0.8  |  0.95 |
| Val Badia               | Grass         |   2.34 |  0.82 |  0.97 |
| Val Badia               | Mugwort       |   0    |  0    |  0.71 |
| Val Badia               | Olive         |   0.06 |  0.01 |  0.95 |
| Val Badia               | Ragweed       |   0.04 |  0.01 |  0.96 |
| Valle di Cembra         | Alder         |   2.83 |  0.62 |  0.82 |
| Valle di Cembra         | Birch         |  18.45 |  2.83 |  0.84 |
| Valle di Cembra         | Grass         |   2.3  |  0.97 |  0.94 |
| Valle di Cembra         | Mugwort       |   0    |  0    | -0.27 |
| Valle di Cembra         | Olive         |   0.19 |  0.04 |  0.91 |
| Valle di Cembra         | Ragweed       |   0.27 |  0.05 |  0.88 |
| Val Pusteria            | Alder         |   0.12 |  0.03 |  0.86 |
| Val Pusteria            | Birch         |   2.66 |  0.99 |  0.91 |
| Val Pusteria            | Grass         |   2.2  |  0.78 |  0.97 |
| Val Pusteria            | Mugwort       |   0    |  0    |  0.61 |
| Val Pusteria            | Olive         |   0.07 |  0.01 |  0.91 |
| Val Pusteria            | Ragweed       |   0.04 |  0.01 |  0.96 |
| Valli Giudicarie        | Alder         |   3.26 |  0.77 |  0.55 |
| Valli Giudicarie        | Birch         |   6.92 |  2.4  |  0.77 |
| Valli Giudicarie        | Grass         |   2.54 |  1.1  |  0.93 |
| Valli Giudicarie        | Mugwort       |   0    |  0    |  1    |
| Valli Giudicarie        | Olive         |   0.22 |  0.06 |  0.71 |
| Valli Giudicarie        | Ragweed       |   0.3  |  0.05 |  0.76 |
| Alta Valsugana          | Alder         |   2.2  |  0.73 |  0.81 |
| Alta Valsugana          | Birch         |   7.74 |  1.91 |  0.97 |
| Alta Valsugana          | Grass         |   2.7  |  1.07 |  0.92 |
| Alta Valsugana          | Mugwort       |   0    |  0    |  1    |
| Alta Valsugana          | Olive         |   0.32 |  0.08 |  0.84 |
| Alta Valsugana          | Ragweed       |   0.26 |  0.04 |  0.88 |
| Valle di Fiemme         | Alder         |   1.87 |  0.41 |  0.79 |
| Valle di Fiemme         | Birch         |   5.14 |  1.4  |  0.93 |
| Valle di Fiemme         | Grass         |   1.83 |  0.69 |  0.97 |
| Valle di Fiemme         | Mugwort       |   0    |  0    |  0.17 |
| Valle di Fiemme         | Olive         |   0.11 |  0.03 |  0.95 |
| Valle di Fiemme         | Ragweed       |   0.12 |  0.02 |  0.92 |
| Val di Fassa            | Alder         |   0.32 |  0.08 |  0.6  |
| Val di Fassa            | Birch         |   4.7  |  1.53 |  0.82 |
| Val di Fassa            | Grass         |   3.45 |  1.31 |  0.94 |
| Val di Fassa            | Mugwort       |   0    |  0    |  0.31 |
| Val di Fassa            | Olive         |   0.11 |  0.02 |  0.85 |
| Val di Fassa            | Ragweed       |   0.1  |  0.01 |  0.84 |
| Val Rendena             | Alder         |   2.24 |  0.79 |  0.19 |
| Val Rendena             | Birch         |  10.06 |  3.79 |  0.27 |
| Val Rendena             | Grass         |   4.21 |  1.8  |  0.77 |
| Val Rendena             | Mugwort       |   0    |  0    |  1    |
| Val Rendena             | Olive         |   0.37 |  0.08 |  0.4  |
| Val Rendena             | Ragweed       |   0.24 |  0.06 |  0.62 |
| Valsugana               | Alder         |   2.15 |  0.47 |  0.89 |
| Valsugana               | Birch         |  11.59 |  2.03 |  0.88 |
| Valsugana               | Grass         |   2.32 |  0.72 |  0.94 |
| Valsugana               | Mugwort       |   0    |  0    |  1    |
| Valsugana               | Olive         |   0.19 |  0.04 |  0.87 |
| Valsugana               | Ragweed       |   0.16 |  0.03 |  0.96 |
| Alto Garda e Ledro      | Alder         |   5.13 |  1.25 |  0.85 |
| Alto Garda e Ledro      | Birch         |  12.71 |  3.15 |  0.84 |
| Alto Garda e Ledro      | Grass         |   2.68 |  1.19 |  0.94 |
| Alto Garda e Ledro      | Mugwort       |   0    |  0    |  1    |
| Alto Garda e Ledro      | Olive         |   0.58 |  0.13 |  0.9  |
| Alto Garda e Ledro      | Ragweed       |   0.39 |  0.08 |  0.92 |
| Valle di Primiero       | Alder         |   2    |  0.35 |  0.74 |
| Valle di Primiero       | Birch         |  12.27 |  2.28 |  0.81 |
| Valle di Primiero       | Grass         |   2.64 |  0.81 |  0.91 |
| Valle di Primiero       | Mugwort       |   0    |  0    |  0    |
| Valle di Primiero       | Olive         |   0.14 |  0.03 |  0.85 |
| Valle di Primiero       | Ragweed       |   0.21 |  0.02 |  0.92 |
| Oltradige-Bassa Atesina | Alder         |   1.16 |  0.16 |  0.99 |
| Oltradige-Bassa Atesina | Birch         |   1.93 |  0.37 |  1    |
| Oltradige-Bassa Atesina | Grass         |   0.61 |  0.19 |  0.99 |
| Oltradige-Bassa Atesina | Mugwort       |   0    |  0    |  0.67 |
| Oltradige-Bassa Atesina | Olive         |   0.09 |  0.02 |  0.99 |
| Oltradige-Bassa Atesina | Ragweed       |   0.05 |  0.01 |  0.99 |
| Salto-Sciliar           | Alder         |   1.29 |  0.26 |  0.93 |
| Salto-Sciliar           | Birch         |   3.08 |  1.17 |  0.99 |
| Salto-Sciliar           | Grass         |   2.77 |  1.28 |  0.94 |
| Salto-Sciliar           | Mugwort       |   0    |  0    |  0.8  |
| Salto-Sciliar           | Olive         |   0.37 |  0.07 |  0.96 |
| Salto-Sciliar           | Ragweed       |   0.07 |  0.01 |  0.94 |
| Valle Isarco            | Alder         |   0.79 |  0.15 |  0.96 |
| Valle Isarco            | Birch         |   3.07 |  1.03 |  0.96 |
| Valle Isarco            | Grass         |   2.56 |  0.89 |  0.97 |
| Valle Isarco            | Mugwort       |   0    |  0    |  0.15 |
| Valle Isarco            | Olive         |   0.13 |  0.02 |  0.95 |
| Valle Isarco            | Ragweed       |   0.04 |  0.01 |  0.96 |
| Vallagarina             | Alder         |   7.6  |  1.94 |  0.81 |
| Vallagarina             | Birch         |   9.8  |  2.17 |  0.93 |
| Vallagarina             | Grass         |   2.81 |  1.2  |  1    |
| Vallagarina             | Mugwort       |   0    |  0    |  0.92 |
| Vallagarina             | Olive         |   0.49 |  0.12 |  0.89 |
| Vallagarina             | Ragweed       |   0.39 |  0.07 |  0.94 |
| Val d'Adige             | Alder         |   2.16 |  0.41 |  0.92 |
| Val d'Adige             | Birch         |   7.31 |  1.15 |  0.96 |
| Val d'Adige             | Grass         |   2.09 |  0.72 |  0.97 |
| Val d'Adige             | Mugwort       |   0    |  0    |  0.61 |
| Val d'Adige             | Olive         |   0.19 |  0.04 |  0.99 |
| Val d'Adige             | Ragweed       |   0.18 |  0.02 |  0.89 |
| Val di Sole             | Alder         |   1    |  0.22 |  0.85 |
| Val di Sole             | Birch         |   6.3  |  2.41 |  0.86 |
| Val di Sole             | Grass         |   2.94 |  1.16 |  0.93 |
| Val di Sole             | Mugwort       |   0    |  0    |  1    |
| Val di Sole             | Olive         |   0.14 |  0.03 |  0.93 |
| Val di Sole             | Ragweed       |   0.11 |  0.01 |  0.79 |


7. **`predictions.ipynb`**  
   Another Jupyter Notebook designed to enable users to visualize and analyze prediction results. Proper execution of this notebook provides insights into pollen levels across the region.


### How to Run

To generate predictions for today's and tomorrow's pollen levels in the Trentino-Alto Adige region, follow these steps:

1. **Configure Parameters**  
   Open the `config.json` file and insert your preferred settings:
   - Specify the **latitude** and **longitude** of the desired location.
   - Choose the pollen types to include and set the **selected_pollen** parameter to your preferred pollen type.

2. **Run the Prediction Notebook**  
   Open the `predictions.ipynb` file and follow the steps outlined in the notebook.

3. **Analyze Results**  
   The output will display predictions for the desired location pollen levels, allowing for visualization and interpretation of the data.

---


## Authors

This project was developed by group 13, consisting of:

- [Mattia Rampazzo](https://github.com/mattia-rampazzo)
- [Davide Giordani](https://github.com/DavideGiordani11)
- [Tommaso Grotto](https://github.com/TommasoGrotto2)
