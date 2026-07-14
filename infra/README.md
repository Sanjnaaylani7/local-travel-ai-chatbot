# Infrastructure Setup for Local Travel AI Chatbot

This README provides an overview of the infrastructure components used in the Local Travel AI Chatbot project. It includes details about the deployment setup, configuration, and monitoring.

## Overview

The infrastructure for the Local Travel AI Chatbot is designed to support the backend services, model serving, data processing, and web widget functionalities. The architecture leverages Docker for containerization, ensuring easy deployment and scalability.

## Components

1. **Docker Compose**: The `docker-compose.yml` file defines the services required for the application, including the backend, model server, vector database, and any other necessary components.

2. **Nginx**: The Nginx configuration file (`nginx.conf`) is set up to act as a reverse proxy, handling incoming requests and routing them to the appropriate services. It also manages SSL termination and load balancing.

3. **Prometheus**: The `prometheus.yml` file contains the configuration for monitoring the application. Prometheus collects metrics from the various services, allowing for performance monitoring and alerting.

## Deployment

To deploy the application, follow these steps:

1. **Clone the Repository**: Clone the Local Travel AI Chatbot repository to your local machine.

2. **Set Up Environment Variables**: Create a `.env` file based on the `.env.example` provided in the root directory. Ensure all necessary environment variables are set.

3. **Build and Start Services**: Navigate to the `infra` directory and run the following command to build and start all services:
   ```
   docker-compose up --build
   ```

4. **Access the Application**: Once the services are running, you can access the chatbot through the web widget integrated into the existing website.

## Monitoring

Prometheus will scrape metrics from the services as configured in `prometheus.yml`. Ensure that Prometheus is running and configured to access the endpoints exposed by the services.

## Conclusion

This infrastructure setup provides a robust foundation for the Local Travel AI Chatbot, ensuring that all components work seamlessly together. For further details on individual components, refer to their respective documentation files located in the project structure.