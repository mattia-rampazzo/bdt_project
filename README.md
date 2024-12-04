# Project title

##  Abstract

This repository contains the source code and documentation for the 'project title' project, part of the course of Big Data Technologes at the University of Trento. The primary goal of the project is to provide real-time health recommendations to individuals affected by pollen allergies. By leveraging data from diverse sources such as meteorological APIs, wearable health devices, and user-reported symptoms and conditions, this system offers personalized advice to minimize allergen exposure and improve quality of life.

## Technologies

-   **Data Ingestion and Streaming:**
    
    -   Apache Kafka: Real-time data streaming from environmental sensors and APIs.
    -   RESTful APIs: Integration with external weather and pollen services.
-   **Data Storage and Management:**
    -   Apache Cassandra: Distributed NoSQL database for managing large-scale, structured, and semi-structured data with high availability.
    -  Redis: In-memory data store used for caching and fast access to frequently queried information.
-   **Data Processing and Analytics:**
    
    -   Apache Spark: Distributed data processing for high-velocity data streams.
    -   Python (Pandas, NumPy): Data cleaning, preprocessing, and exploratory analysis.
-   **Machine Learning:**
    
    -  Apache Spark MLlib: Scalable machine learning capabilities integrated with Spark for predictive modeling.
    -  CTGAN (Conditional Tabular Generative Adversarial Network): Generates synthetic tabular data to enhance training datasets and improve model performance.
-   **Deployment:**
    
    -   Docker: Containerization and orchestration of the system's microservices.
-   **User Interface and Notifications:**
    
    -   Flask & Bootstrap: Web-based user dashboards.

## Architecture

Architecture file


##  How to run

The entire application is containerized and managed using Docker for easy setup and deployment. Please Follow these steps to run the application:

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
    docker-compose build
    ```
    
4.  **Start the Application:**  
    Start the entire application stack (including all services like Kafka, Cassandra, Redis, Flask, and Spark) using Docker Compose:
    
    ```bash
    docker-compose up -d
    
    ```
    
5.  **Access the Dashboard:**  
    Once the application is running, you can access the dashboard by navigating with your preferred browser to:
    
    ```
    http://localhost:5000
    ```
    
6.  **Stop the Application:**  
    To stop the application run:
    
    ```bash
    docker-compose down
 
    ```

## Project Structure 

A summary of the project structure and the main files is reported below:

### air_quality   
 -   `air_quality_fetch.py`: Script to fetch pollen and weather data and write it to Kafka.
 
### dashboard   
 -   `app.py`: The main Flask application file that runs the dashboard and handles server-side logic.
    -   `utils`: A directory containing two Python utility files:
		-   One for generating the live map representation.
		- Another for simulating data from a wearable device.
  
    -   `templates`: Contains HTML templates for the dashboard.
    -   `data`: Contains GeoJSON data used for rendering geographic information on the map.

### data
 -   `Trentino-AltoAdige_municipalities.csv`: A CSV file containing updated information about municipalities in the Trentino-Alto Adige.

### services
 -   `cassandra_client.py`: Manages communications with the Cassandra database.
 -   `kafka_client.py`: Manages interaction with Kafka.
 -   `redis_client.py`: Manages communications with the Redis database.

### spark_streaming
 -   `air_quality_stream.py`: Ingests real-time air quality data streams and writes to both Cassandra (for long-term storage) and Redis (for fast access and caching).
 -   `recommendations_stream.py`:  Analyzes incoming data streams to generate real-time personalized health recommendations for users based on environmental and wearable data.

### users



## Authors

This project was developed by group 13, consisting of:

- Mattia Rampazzo - 
- Davide Giordani - 
- Tommaso Grotto -


#### TODO:
- user stream
- map updates how?
- wereable
- recommendations
- report
- forecast
- postgres?
- github
