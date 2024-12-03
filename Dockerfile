### Dockerfile for the Simulation
FROM ubuntu:22.04

# Update package list
RUN apt-get update -y 

# Install Python 3.11 and pip
RUN apt-get -y install python3.11 python3-pip

# Install Java (JDK)
RUN apt-get install -y openjdk-11-jdk
# Install curl
RUN apt-get update && apt-get install -y curl

# Set the working directory inside the container
# WORKDIR /bdt/dashboard

# Set the PYTHONPATH to the root of your project (the top-level directory)
ENV PYTHONPATH="/bdt:${PYTHONPATH}"

# Initializing docker's bashrc
RUN echo "export JAVA_PATH=/usr/lib/jvm/java-11-openjdk-amd64" >> ~/.bashrc
RUN echo "export PATH=$PATH:$JAVA_HOME/bin" >> ~/.bashrc

# Copy and install requirements
COPY ./requirements.txt ./bdt/requirements.txt
RUN  pip install -r ./bdt/requirements.txt

# Copy the package folder
COPY . /bdt/