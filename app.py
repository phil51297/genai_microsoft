import streamlit as st
import os
import tempfile
import PyPDF2
import docx
import time
import re

st.set_page_config(
    page_title="MedAssist - Assistant IA médical",
    page_icon="🏥",
    layout="wide"
)

def extract_text_from_pdf(pdf_file):
    pdf_reader = PyPDF2.PdfReader(pdf_file)
    text = ""
    for page_num in range(len(pdf_reader.pages)):
        page = pdf_reader.pages[page_num]
        text += page.extract_text() + "\n\n"
    return text

def extract_text_from_docx(docx_file):
    doc = docx.Document(docx_file)
    text = ""
    for paragraph in doc.paragraphs:
        text += paragraph.text + "\n"
    return text

def chunk_text(text, chunk_size=1000, overlap=200):
    chunks = []
    
    text = re.sub(r'\s+', ' ', text).strip()
    
    if len(text) <= chunk_size:
        return [text]
    
    start = 0
    end = chunk_size
    
    while start < len(text):
        if end < len(text):
            next_space = text.find(' ', end)
            if next_space != -1:
                end = next_space
            else:
                end = len(text)
        else:
            end = len(text)
        
        chunk = text[start:end]
        chunks.append(chunk)
        
        start += (chunk_size - overlap)
        end = start + chunk_size
    
    return chunks

# initialize session state if necessary
if 'document_text' not in st.session_state:
    st.session_state.document_text = None
if 'chunks' not in st.session_state:
    st.session_state.chunks = None
if 'processing_stage' not in st.session_state:
    st.session_state.processing_stage = 'upload'  # Étapes: 'upload', 'extracted', 'chunked'

# interface
st.title("MedAssist - Assistant IA médical")

# sidebar
with st.sidebar:
    st.title("🏥 MedAssist")
    st.write("Assistant IA médical pour l'aide au diagnostic")
    st.write("---")
    st.write("Développé pour le Hackathon OpenCertif")
    
    # Affichage de l'étape actuelle
    if st.session_state.processing_stage == 'upload':
        st.info("Étape 1: Upload du document")
    elif st.session_state.processing_stage == 'extracted':
        st.info("Étape 2: Extraction du texte")
    elif st.session_state.processing_stage == 'chunked':
        st.info("Étape 3: Segmentation en chunks")

if st.session_state.processing_stage == 'upload':
    st.subheader("Téléversez votre document pour commencer")

    uploaded_file = st.file_uploader("Choisissez un fichier PDF ou DOCX", type=["pdf", "docx"])
    
    if uploaded_file is not None:
        file_details = {
            "Nom du fichier": uploaded_file.name,
            "Type de fichier": uploaded_file.type,
            "Taille": f"{uploaded_file.size / 1024:.2f} KB"
        }
        st.write("### Détails du fichier")
        for key, value in file_details.items():
            st.write(f"**{key}:** {value}")
        
        if st.button("Extraire le texte"):
            with st.spinner("Extraction du texte en cours..."):
                with tempfile.NamedTemporaryFile(delete=False, suffix=f".{uploaded_file.name.split('.')[-1]}") as tmp_file:
                    tmp_file.write(uploaded_file.getvalue())
                    tmp_file_path = tmp_file.name
                
                if uploaded_file.type == "application/pdf":
                    text = extract_text_from_pdf(tmp_file_path)
                elif uploaded_file.type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
                    text = extract_text_from_docx(tmp_file_path)
                else:
                    text = "Type de fichier non pris en charge"
                
                os.unlink(tmp_file_path)
                
                time.sleep(0.5)
            
            st.session_state.document_text = text
            st.session_state.processing_stage = 'extracted'
            st.experimental_rerun()

# display extracted text
elif st.session_state.processing_stage == 'extracted':
    st.subheader("Texte extrait du document")
    
    st.success(f"Extraction terminée! {len(st.session_state.document_text)} caractères extraits.")
    
    with st.expander("Aperçu du texte extrait", expanded=True):
        st.text_area("Texte extrait", st.session_state.document_text[:5000] + 
                    ("..." if len(st.session_state.document_text) > 5000 else ""), 
                    height=300)
    
    # chunking
    if st.button("Segmenter le texte en chunks"):
        with st.spinner("Segmentation en cours..."):
            chunks = chunk_text(st.session_state.document_text)
            
            time.sleep(0.5)
        
        st.session_state.chunks = chunks
        st.session_state.processing_stage = 'chunked'
        st.experimental_rerun()
    
    if st.button("Téléverser un autre document"):
        st.session_state.document_text = None
        st.session_state.processing_stage = 'upload'
        st.experimental_rerun()

# display chunks
elif st.session_state.processing_stage == 'chunked':
    st.subheader("Segmentation du texte en chunks")
    
    chunks = st.session_state.chunks
    st.success(f"Segmentation terminée! {len(chunks)} chunks créés.")
    
    for i, chunk in enumerate(chunks[:5]):  # Limiter l'affichage aux 5 premiers chunks
        with st.expander(f"Chunk {i+1}/{len(chunks)}"):
            st.text_area(f"Contenu du chunk {i+1}", chunk, height=150)
    
    if len(chunks) > 5:
        st.info(f"{len(chunks) - 5} autres chunks non affichés.")
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Revenir à l'extraction"):
            st.session_state.chunks = None
            st.session_state.processing_stage = 'extracted'
            st.experimental_rerun()
    with col2:
        if st.button("Téléverser un nouveau document"):
            st.session_state.document_text = None
            st.session_state.chunks = None
            st.session_state.processing_stage = 'upload'
            st.experimental_rerun()
    