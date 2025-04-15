import os
import time
import requests
from dotenv import load_dotenv

load_dotenv()

# Variables Azure Search
service_name = os.getenv("AZURE_SEARCH_SERVICE_NAME")
admin_key = os.getenv("AZURE_SEARCH_ADMIN_KEY")
search_endpoint = f"https://{service_name}.search.windows.net/"

# Variables Azure OpenAI Embeddings
embedding_endpoint = os.getenv("AZURE_OPENAI_EMBEDDING_ENDPOINT")
embedding_key = os.getenv("AZURE_OPENAI_EMBEDDING_API_KEY")
embedding_api_version = os.getenv("AZURE_OPENAI_EMBEDDING_API_VERSION")
embedding_deployment_name = os.getenv("AZURE_OPENAI_EMBEDDING_DEPLOYMENT_NAME")

# Variables Azure OpenAIGPT
openai_endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
openai_key = os.getenv("AZURE_OPENAI_API_KEY")
openai_api_version = os.getenv("AZURE_OPENAI_API_VERSION")
openai_deployment_name = os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME")

def create_search_index(index_name, status_callback=None):
    """Crée un index dans Azure AI Search."""
    if status_callback:
        status_callback("Création de l'index de recherche...")
    
    headers = {
        'Content-Type': 'application/json',
        'api-key': admin_key
    }
    
    # list of existing indexes
    list_indexes_url = f"{search_endpoint}indexes?api-version=2023-07-01-Preview"
    response = requests.get(list_indexes_url, headers=headers)
    
    if response.status_code == 200:
        indexes = response.json().get('value', [])
        index_names = [index['name'] for index in indexes]
        
        if index_name in index_names:
            if status_callback:
                status_callback(f"✅ Utilisation de l'index existant '{index_name}'")
            return index_name
    
    # create index
    create_index_url = f"{search_endpoint}indexes/{index_name}?api-version=2023-07-01-Preview"
    
    # definition of index with vectorial search
    index_definition = {
        "name": index_name,
        "fields": [
            {
                "name": "id",
                "type": "Edm.String",
                "key": True,
                "searchable": False
            },
            {
                "name": "content",
                "type": "Edm.String",
                "searchable": True,
                "analyzer": "standard.lucene"
            },
            {
                "name": "embedding",
                "type": "Collection(Edm.Single)",
                "dimensions": 1536,
                "vectorSearchConfiguration": "my-vector-config"
            }
        ],
        "vectorSearch": {
            "algorithmConfigurations": [
                {
                    "name": "my-vector-config",
                    "kind": "hnsw",
                    "hnswParameters": {
                        "m": 4,
                        "efConstruction": 400,
                        "efSearch": 500,
                        "metric": "cosine"
                    }
                }
            ]
        }
    }
    
    response = requests.put(
        create_index_url,
        headers=headers,
        json=index_definition
    )
    
    if response.status_code in [201, 204]:
        time.sleep(1)
        if status_callback:
            status_callback(f"✅ Index '{index_name}' créé avec succès")
        return index_name
    else:
        error_msg = f"Erreur lors de la création de l'index: {response.status_code} - {response.text}"
        if status_callback:
            status_callback(f"❌ {error_msg}")
        raise Exception(error_msg)

def generate_embeddings(text, error_callback=None):
    """Génère des embeddings pour un texte en utilisant Azure OpenAI."""
    headers = {
        "Content-Type": "application/json",
        "api-key": embedding_key
    }
    
    payload = {
        "input": text,
        "dimensions": 1536
    }
    
    embedding_url = f"{embedding_endpoint}openai/deployments/{embedding_deployment_name}/embeddings?api-version={embedding_api_version}"
    
    try:
        response = requests.post(
            embedding_url,
            headers=headers,
            json=payload
        )
        
        if response.status_code == 200:
            response_data = response.json()
            return response_data["data"][0]["embedding"]
        else:
            error_msg = f"Erreur lors de la génération des embeddings: {response.status_code} - {response.text}"
            if error_callback:
                error_callback(error_msg)
            return None
    except Exception as e:
        if error_callback:
            error_callback(f"Exception lors de la génération des embeddings: {str(e)}")
        return None

def index_chunks(chunks, index_name, status_callback=None):
    """Indexe les chunks de texte dans Azure AI Search."""
    if status_callback:
        status_callback("Indexation des chunks (cette étape peut prendre un moment)...")
    
    headers = {
        "Content-Type": "application/json",
        "api-key": admin_key
    }
    
    index_url = f"{search_endpoint}indexes/{index_name}/docs/index?api-version=2023-07-01-Preview"
    
    # prepare documents for indexing
    documents = []
    for i, chunk in enumerate(chunks):
        if status_callback and i % 5 == 0:  # Mettre à jour le statut tous les 5 chunks
            status_callback(f"Génération d'embedding pour le chunk {i+1}/{len(chunks)}...")
        
        embedding = generate_embeddings(chunk, status_callback)
        
        if embedding:
            document = {
                "id": str(i),
                "content": chunk,
                "embedding": embedding
            }
            documents.append(document)
    
    # index documents
    if documents:
        payload = {"value": documents}
        
        response = requests.post(
            index_url,
            headers=headers,
            json=payload
        )
        
        if response.status_code in [200, 201, 204]:
            if status_callback:
                status_callback(f"✅ {len(documents)} chunks indexés avec succès")
            return len(documents), response.json()
        else:
            error_msg = f"Erreur lors de l'indexation: {response.status_code} - {response.text}"
            if status_callback:
                status_callback(f"❌ {error_msg}")
            raise Exception(error_msg)
    else:
        if status_callback:
            status_callback("❌ Aucun chunk n'a pu être indexé")
        return 0, None

def search_documents(query, index_name, top_k=3, error_callback=None):
    """Recherche les documents pertinents dans Azure AI Search."""
    headers = {
        "Content-Type": "application/json",
        "api-key": admin_key
    }
    
    search_url = f"{search_endpoint}indexes/{index_name}/docs/search?api-version=2023-07-01-Preview"
    
    # generate embedding of the request
    query_embedding = generate_embeddings(query, error_callback)
    
    if not query_embedding:
        if error_callback:
            error_callback("Impossible de générer l'embedding pour la requête")
        return []
    
    # format for vectorial search with Azure AI Search
    search_payload = {
        "select": "content",
        "top": top_k,
        "vectors": [
            {
                "value": query_embedding,
                "fields": "embedding",
                "k": top_k
            }
        ]
    }
    
    try:
        response = requests.post(
            search_url,
            headers=headers,
            json=search_payload
        )
        
        if response.status_code == 200:
            results = response.json().get("value", [])
            return [result["content"] for result in results]
        else:
            if error_callback:
                error_callback(f"Erreur lors de la recherche: {response.status_code} - {response.text}")
            return []
    except Exception as e:
        if error_callback:
            error_callback(f"Exception lors de la recherche: {str(e)}")
        return []

def generate_answer(query, contexts, error_callback=None):
    """Génère une réponse basée sur les contextes fournis en utilisant Azure OpenAI."""
    headers = {
        "Content-Type": "application/json",
        "api-key": openai_key
    }
    
    context_text = "\n\n".join(contexts)
    
    chat_url = f"{openai_endpoint}openai/deployments/{openai_deployment_name}/chat/completions?api-version={openai_api_version}"
    
    payload = {
        "messages": [
            {
                "role": "system",
                "content": "Vous êtes un assistant médical expert qui aide les médecins à trouver des informations précises. Utilisez uniquement le contexte fourni pour répondre à la question. Si l'information n'est pas présente dans le contexte, indiquez-le clairement. N'inventez pas d'information."
            },
            {
                "role": "user",
                "content": f"Contexte :\n{context_text}\n\nQuestion : {query}\n\nRéponse :"
            }
        ],
        "temperature": 0.7,
        "max_tokens": 800
    }
    
    try:
        response = requests.post(
            chat_url,
            headers=headers,
            json=payload
        )
        
        if response.status_code == 200:
            return response.json()["choices"][0]["message"]["content"]
        else:
            error_msg = f"Erreur lors de la génération de la réponse: {response.status_code} - {response.text}"
            if error_callback:
                error_callback(error_msg)
            return "Désolé, je n'ai pas pu générer une réponse. Veuillez réessayer."
    except Exception as e:
        if error_callback:
            error_callback(f"Exception lors de la génération de la réponse: {str(e)}")
        return "Une erreur s'est produite lors de la génération de la réponse."

def process_document(uploaded_file, status_callback=None):
    """Traite un document complet: extraction, chunking, indexation."""
    from models import process_uploaded_file
    
    try:
        # extraction and chunking
        _, chunks = process_uploaded_file(uploaded_file, status_callback)
        
        # create index
        index_name = f"medassist-index-{int(time.time())}"
        create_search_index(index_name, status_callback)
        
        # indexation
        indexed_count, _ = index_chunks(chunks, index_name, status_callback)
        
        if indexed_count > 0:
            if status_callback:
                status_callback(f"✅ Document traité avec succès!")
            return index_name
        else:
            if status_callback:
                status_callback("❌ Échec du traitement: aucun chunk indexé")
            return None
    except Exception as e:
        if status_callback:
            status_callback(f"❌ Erreur lors du traitement: {str(e)}")
        return None