import PyPDF2
import docx
import re
import os
import tempfile

def extract_text_from_pdf(pdf_file):
    """Extrait le texte d'un fichier PDF."""
    pdf_reader = PyPDF2.PdfReader(pdf_file)
    text = ""
    for page_num in range(len(pdf_reader.pages)):
        page = pdf_reader.pages[page_num]
        text += page.extract_text() + "\n\n"
    return text

def extract_text_from_docx(docx_file):
    """Extrait le texte d'un fichier DOCX."""
    doc = docx.Document(docx_file)
    text = ""
    for paragraph in doc.paragraphs:
        text += paragraph.text + "\n"
    return text

def chunk_text(text, chunk_size=1000, overlap=200):
    """Segmente le texte en chunks avec chevauchement."""
    # clean text
    text = re.sub(r'\s+', ' ', text)
    
    if len(text) <= chunk_size:
        return [text]
    
    chunks = []
    start = 0
    end = chunk_size
    
    while start < len(text):
        if end < len(text):
            sentence_end = text.rfind('. ', start, min(end + 100, len(text)))
            if sentence_end != -1 and sentence_end > start + int(chunk_size / 2):
                end = sentence_end + 2
            else:
                next_space = text.rfind(' ', start + int(chunk_size / 2), min(end + 20, len(text)))
                if next_space != -1:
                    end = next_space + 1
                else:
                    end = min(end, len(text))
        else:
            end = len(text)
        
        chunk = text[start:end].strip()
        chunks.append(chunk)
        
        start += (chunk_size - overlap)
        end = start + chunk_size
    
    return chunks

def extract_text(file_path, file_type):
    """Extrait le texte d'un fichier selon son type."""
    if file_type == "application/pdf":
        return extract_text_from_pdf(file_path)
    elif file_type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
        return extract_text_from_docx(file_path)
    else:
        raise ValueError(f"Type de fichier non pris en charge: {file_type}")

def process_uploaded_file(uploaded_file, status_callback=None):
    """Traite un fichier téléversé pour en extraire le texte."""
    if status_callback:
        status_callback("Extraction du texte...")
    
    with tempfile.NamedTemporaryFile(delete=False, suffix=f".{uploaded_file.name.split('.')[-1]}") as tmp_file:
        tmp_file.write(uploaded_file.getvalue())
        tmp_file_path = tmp_file.name
    
    try:
        text = extract_text(tmp_file_path, uploaded_file.type)
        if status_callback:
            status_callback(f"✅ Texte extrait ({len(text)} caractères)")
        
        if status_callback:
            status_callback("Segmentation du texte...")
        chunks = chunk_text(text)
        if status_callback:
            status_callback(f"✅ Texte segmenté en {len(chunks)} chunks")
        
        return text, chunks
    finally:
        os.unlink(tmp_file_path)