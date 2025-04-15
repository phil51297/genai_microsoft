# MedAssist - Assistant IA Médical 🏥

MedAssist is a hackathon project designed to assist healthcare professionals by providing a streamlined solution for managing medical records and answering medical queries using AI-powered tools. The application leverages Azure AI services for document indexing, vector search, and OpenAI for generating responses.

## Features

- **Document Upload**: Upload PDF or DOCX files containing medical information.
- **Text Extraction**: Extract text from uploaded documents.
- **Text Chunking**: Segment extracted text into manageable chunks for processing.
- **Azure AI Search Integration**: Index text chunks in Azure AI Search for efficient retrieval.
- **Medical Query Answering**: Use Azure OpenAI to generate answers to medical questions based on indexed documents.

## Installation

1. Clone the repository:
   ```bash
   git clone <repository-url>
   ```

2. Navigate to the project directory:
    ```bash
    cd medassist
    ```

3. Install dependencies:
    ```bash
    pip install -r requirements.txt
    ```
    
4. Set up environment variables:
    - Copy .env.example to .env:
    ```bash
    cp .env.example .env
    ```
    - Fill in the required API keys and endpoints in the .env file.

## Usage

1. Run the application: 
    ```bash
    streamlit run app.py
    ```

2. Open your browser and navigate to http://localhost:8501.

