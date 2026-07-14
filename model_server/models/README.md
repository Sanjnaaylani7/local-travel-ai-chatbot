# Model Server Documentation

This directory contains the models used in the local travel AI chatbot's model server. The models are designed to handle various tasks related to travel inquiries, including visa information, ticketing, tours, and travel insurance.

## Model Overview

- **Base Model**: The model is based on a commercially usable open-weight instruct model that has been fine-tuned for travel-related queries.
- **Fine-Tuning**: The model has undergone parameter-efficient fine-tuning using techniques such as LoRA or QLoRA to adapt it to the specific needs of the travel industry.
- **Languages Supported**: The model supports queries in English, Urdu, and Roman Urdu.

## Model Components

1. **Inference Engine**: The model is served using a local inference engine optimized for the selected hardware, allowing for efficient response generation.
2. **Embeddings**: The model utilizes a locally hosted multilingual sentence embedding model to understand and process user queries effectively.
3. **Retrieval-Augmented Generation (RAG)**: The model employs a RAG architecture, which combines the language model with a local vector database to retrieve relevant information in real-time.

## Usage

To use the models, ensure that the model server is running and accessible. The models can be queried through the backend API, which handles incoming requests and returns generated responses based on user input.

## Maintenance

Regular updates to the model and its underlying knowledge base are essential to ensure accuracy and relevance. The knowledge base should be maintained separately, allowing for easy updates without the need for retraining the model.

## License

Ensure compliance with the licensing terms of the base model and any additional components used in this project.