
import streamlit as st
import re
import PyPDF2
import docx
from io import BytesIO

# Configuration de la page
st.set_page_config(
    page_title="Anonymiseur de CV - RGPD",
    page_icon="🔒",
    layout="wide"
)

# Fonction pour extraire le texte d'un PDF
def extract_text_from_pdf(pdf_file):
    pdf_reader = PyPDF2.PdfReader(BytesIO(pdf_file.read()))
    text = ""
    for page in pdf_reader.pages:
        text += page.extract_text()
    return text

# Fonction pour extraire le texte d'un DOCX
def extract_text_from_docx(docx_file):
    doc = docx.Document(BytesIO(docx_file.read()))
    text = ""
    for paragraph in doc.paragraphs:
        text += paragraph.text + "\n"
    return text

# Fonction d'anonymisation RGPD
def anonymize_cv(text):
    """
    Anonymise les données personnelles sensibles du CV selon le RGPD
    """
    anonymized = text
    
    # Masquer les emails
    anonymized = re.sub(
        r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', 
        '[EMAIL_MASQUÉ]', 
        anonymized
    )
    
    # Masquer les numéros de téléphone français et internationaux
    anonymized = re.sub(
        r'(\+33|0033|0)[1-9](\s?\d{2}){4}', 
        '[TÉLÉPHONE_MASQUÉ]', 
        anonymized
    )
    anonymized = re.sub(
        r'\b\d{2}[\s\.\-]?\d{2}[\s\.\-]?\d{2}[\s\.\-]?\d{2}[\s\.\-]?\d{2}\b', 
        '[TÉLÉPHONE_MASQUÉ]', 
        anonymized
    )
    
    # Masquer les adresses postales
    anonymized = re.sub(
        r'\d{1,5}\s+\w+\s+(rue|avenue|boulevard|allée|impasse|place|chemin|route)\s+[\w\s]+,?\s*\d{5}', 
        '[ADRESSE_MASQUÉE]', 
        anonymized, 
        flags=re.IGNORECASE
    )
    
    # Masquer les codes postaux français
    anonymized = re.sub(r'\b\d{5}\b', '[CODE_POSTAL_MASQUÉ]', anonymized)
    
    # Masquer les dates de naissance
    anonymized = re.sub(
        r'\b(né|née|naissance)\s*(le)?\s*:?\s*\d{1,2}[\/\-\.]\d{1,2}[\/\-\.]\d{2,4}\b', 
        '[DATE_NAISSANCE_MASQUÉE]', 
        anonymized, 
        flags=re.IGNORECASE
    )
    
    # Masquer les dates au format JJ/MM/AAAA ou DD-MM-YYYY dans un contexte de naissance
    anonymized = re.sub(
        r'\b\d{1,2}[\/\-\.]\d{1,2}[\/\-\.](19|20)\d{2}\b', 
        '[DATE_MASQUÉE]', 
        anonymized
    )
    
    # Masquer l'âge
    anonymized = re.sub(r'\b\d{2}\s*ans\b', '[ÂGE_MASQUÉ]', anonymized, flags=re.IGNORECASE)
    
    # Masquer les numéros de sécurité sociale (format français)
    anonymized = re.sub(
        r'\b[1-2]\s?\d{2}\s?\d{2}\s?\d{2}\s?\d{3}\s?\d{3}\s?\d{2}\b', 
        '[NUMÉRO_SÉCU_MASQUÉ]', 
        anonymized
    )
    
    return anonymized

# Interface Streamlit
st.title("🔒 Anonymiseur de CV - Conforme RGPD")
st.markdown("---")

# Informations RGPD
with st.expander("ℹ️ Données anonymisées", expanded=True):
    st.info("""
    **Cette application masque automatiquement :**
    - ✅ Adresses email
    - ✅ Numéros de téléphone
    - ✅ Adresses postales
    - ✅ Codes postaux
    - ✅ Dates de naissance
    - ✅ Âges
    - ✅ Numéros de sécurité sociale
    
    **Sécurité :**
    - 🔒 Aucun CV n'est stocké
    - 🔒 Traitement en mémoire uniquement
    - 🔒 Aucune conservation après la session
    """)

# Colonnes pour l'interface
col1, col2 = st.columns([1, 1])

with col1:
    st.header("📤 CV Original")
    
    # Upload de fichier
    uploaded_file = st.file_uploader(
        "Choisissez un fichier CV",
        type=['pdf', 'docx', 'txt'],
        help="Formats acceptés : PDF, DOCX, TXT"
    )
    
    cv_text = None
    
    if uploaded_file:
        try:
            with st.spinner("📖 Lecture du fichier..."):
                if uploaded_file.type == "application/pdf":
                    cv_text = extract_text_from_pdf(uploaded_file)
                elif uploaded_file.type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
                    cv_text = extract_text_from_docx(uploaded_file)
                elif uploaded_file.type == "text/plain":
                    cv_text = uploaded_file.read().decode('utf-8')
                
                if cv_text:
                    st.success("✅ Fichier lu avec succès")
                    
                    # Afficher le texte original
                    st.text_area(
                        "Contenu original",
                        cv_text,
                        height=400,
                        disabled=True
                    )
        except Exception as e:
            st.error(f"Erreur lors de la lecture du fichier : {str(e)}")

with col2:
    st.header("🔐 CV Anonymisé")
    
    if cv_text:
        # Anonymisation
        with st.spinner("🔒 Anonymisation en cours..."):
            anonymized_cv = anonymize_cv(cv_text)
        
        st.success("✅ Anonymisation terminée")
        
        # Champ pour personnaliser le nom du fichier
        output_filename = st.text_input(
            "📝 Nom du fichier de sortie",
            value="cv_anonymise",
            help="Entrez le nom souhaité (sans extension)",
            max_chars=50
        )
        
        # Afficher le texte anonymisé
        st.text_area(
            "Contenu anonymisé (conforme RGPD)",
            anonymized_cv,
            height=400,
            disabled=True
        )
        
        # Boutons de téléchargement
        col_download1, col_download2 = st.columns(2)
        
        with col_download1:
            st.download_button(
                label="📥 Télécharger (.txt)",
                data=anonymized_cv,
                file_name=f"{output_filename}.txt",
                mime="text/plain",
                use_container_width=True
            )
        
        with col_download2:
            # Copier dans le presse-papiers
            if st.button("📋 Copier le texte", use_container_width=True):
                st.code(anonymized_cv, language=None)
                st.info("Sélectionnez et copiez le texte ci-dessus")
        
        # Statistiques d'anonymisation
        st.markdown("---")
        st.subheader("📊 Statistiques")
        
        col_stat1, col_stat2, col_stat3 = st.columns(3)
        
        emails_masked = anonymized_cv.count('[EMAIL_MASQUÉ]')
        phones_masked = anonymized_cv.count('[TÉLÉPHONE_MASQUÉ]')
        addresses_masked = anonymized_cv.count('[ADRESSE_MASQUÉE]')
        
        with col_stat1:
            st.metric("Emails masqués", emails_masked)
        with col_stat2:
            st.metric("Téléphones masqués", phones_masked)
        with col_stat3:
            st.metric("Adresses masquées", addresses_masked)
    else:
        st.info("👈 Uploadez un CV pour commencer l'anonymisation")

# Footer
st.markdown("---")
st.caption("🔐 Conforme RGPD - Aucune donnée conservée après votre session")
