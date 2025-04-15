import streamlit as st
import time
from dotenv import load_dotenv
from azure_search import process_document, search_documents, generate_answer

load_dotenv()

st.set_page_config(
    page_title="MedAssist - Assistant IA médical",
    page_icon="🏥",
    layout="wide"
)

def load_css():
    st.markdown("""
    <style>
    .main-header {margin-bottom: 10px;}
    .block-container {padding-top: 3rem; padding-bottom: 0;}
    .stButton button {padding: 0.25rem 0.5rem; height: auto;}
    div.row-widget.stButton {margin-bottom: 10px;}
    .return-button-container {margin-top: 10px; margin-bottom: 20px;}
    </style>
    """, unsafe_allow_html=True)

if 'messages' not in st.session_state:
    st.session_state.messages = []

if 'index_name' not in st.session_state:
    st.session_state.index_name = None

if 'file_processed' not in st.session_state:
    st.session_state.file_processed = False


def show_landing_page():
    st.title("MedAssist - Assistant IA médical")
    st.subheader("Posez des questions sur vos documents médicaux avec l'IA")
    
    col1, col2 = st.columns([3, 2])
    
    with col1:
        st.markdown("### Téléversez votre document")
        uploaded_file = st.file_uploader("Choisissez un fichier PDF ou DOCX", type=["pdf", "docx"])
        
        if uploaded_file:
            st.write(f"**Document sélectionné:** {uploaded_file.name} ({uploaded_file.size / 1024:.1f} KB)")
            if st.button("Analyser ce document", type="primary"):
                with st.status("Traitement du document...", expanded=True) as status:
                    def update_status(message):
                        status.write(message)
                    
                    index_name = process_document(uploaded_file, update_status)
                    
                    if index_name:
                        st.session_state.index_name = index_name
                        st.session_state.file_processed = True
                        st.session_state.messages = []
                        st.session_state.messages.append({
                            "role": "assistant", 
                            "content": f"J'ai analysé le document '{uploaded_file.name}'. Vous pouvez maintenant me poser des questions sur son contenu."
                        })
                        
                        status.update(label="Document traité avec succès!", state="complete")
                        time.sleep(1)
                        st.rerun()
                    else:
                        status.update(label="Échec du traitement du document", state="error")
    
    with col2:
        st.markdown("### Exemples de questions")
        examples = [
            "Quels sont les principaux symptômes décrits?",
            "Résume les points clés du document",
            "Quels sont les traitements recommandés?",
            "Quelles sont les contre-indications mentionnées?",
        ]
        
        for example in examples:
            if st.button(f"📝 {example}", key=example):
                st.session_state.example_question = example
                st.info("Veuillez d'abord téléverser et analyser un document")

def show_chat_interface():
    st.markdown('<div style="height: 50px;"></div>', unsafe_allow_html=True)
    
    if st.button("⬅️ Téléverser un nouveau document", type="secondary"):
        
        st.session_state.index_name = None
        st.session_state.file_processed = False
        st.session_state.messages = []
        st.rerun()
    
    st.title("MedAssist - Assistant IA médical")
    
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
    
    if prompt := st.chat_input("Posez votre question sur le document..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        
        with st.chat_message("user"):
            st.markdown(prompt)
        
        with st.chat_message("assistant"):
            message_placeholder = st.empty()
            message_placeholder.markdown("Recherche en cours...")
            
            def show_error(error_message):
                st.error(error_message)
            
            relevant_passages = search_documents(
                prompt, 
                st.session_state.index_name, 
                top_k=3, 
                error_callback=show_error
            )
            
            if relevant_passages:
                answer = generate_answer(
                    prompt, 
                    relevant_passages, 
                    error_callback=show_error
                )
                
                message_placeholder.markdown(answer)
                
                st.session_state.messages.append({"role": "assistant", "content": answer})
                
                with st.expander("Sources utilisées 📚", expanded=False):
                    for i, passage in enumerate(relevant_passages):
                        st.markdown(f"**Source {i+1}:**")
                        st.markdown(passage[:300] + "..." if len(passage) > 300 else passage)
            else:
                message = "Je n'ai pas trouvé d'information pertinente sur ce sujet dans le document. Pouvez-vous reformuler votre question ou demander autre chose ?"
                message_placeholder.markdown(message)
                st.session_state.messages.append({"role": "assistant", "content": message})

def main():
    load_css()
    
    if st.session_state.file_processed:
        show_chat_interface()
    else:
        show_landing_page()
    
    st.markdown('<div style="position:fixed; bottom:5px; right:10px; font-size:0.8rem; color:#666;">Développé pour le Hackathon OpenCertif</div>', unsafe_allow_html=True)
    
if __name__ == "__main__":
    main()