import streamlit as st
import re
import PyPDF2
import docx
import json
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

# Fonction d'anonymisation RGPD renforcée
def anonymize_cv(text):
    """
    Anonymise les données personnelles sensibles du CV selon le RGPD
    """
    anonymized = text
    
    # Masquer les noms et prénoms courants (patterns basiques)
    # Recherche de "Prénom NOM" en début de ligne ou après certains mots-clés
    anonymized = re.sub(
        r'\b(M\.|Mme|Mlle|Monsieur|Madame|Mademoiselle)\s+([A-Z][a-zàâäéèêëïîôùûüç]+(\s+[A-Z][a-zàâäéèêëïîôùûüç]+)?)\s+([A-Z][A-ZÀÂÄÉÈÊËÏÎÔÙÛÜÇ\-]+)\b',
        r'\1 [PRÉNOM_MASQUÉ] [NOM_MASQUÉ]',
        anonymized
    )
    
    # Masquer les noms en majuscules suivis de prénoms
    anonymized = re.sub(
        r'\b([A-Z][A-ZÀÂÄÉÈÊËÏÎÔÙÛÜÇ\-]{2,})\s+([A-Z][a-zàâäéèêëïîôùûüç]+)\b',
        '[NOM_MASQUÉ] [PRÉNOM_MASQUÉ]',
        anonymized
    )
    
    # Masquer format "Prénom Nom" en début de document ou ligne
    anonymized = re.sub(
        r'^([A-Z][a-zàâäéèêëïîôùûüç]+)\s+([A-Z][a-zàâäéèêëïîôùûüç]+)',
        '[PRÉNOM_MASQUÉ] [NOM_MASQUÉ]',
        anonymized,
        flags=re.MULTILINE
    )
    
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
    
    # Masquer les adresses complètes (pattern amélioré)
    anonymized = re.sub(
        r'\d{1,5}\s+(bis|ter)?\s*(rue|avenue|boulevard|allée|impasse|place|chemin|route|cours|quai)\s+[\w\s\'\-]+,?\s*\d{5}?\s*[\w\s\-]*',
        '[ADRESSE_MASQUÉE]',
        anonymized,
        flags=re.IGNORECASE
    )
    
    # Masquer les adresses sans numéro
    anonymized = re.sub(
        r'\b(rue|avenue|boulevard|allée|impasse|place|chemin|route|cours|quai)\s+[\w\s\'\-]{3,40}\s*,?\s*\d{5}',
        '[ADRESSE_MASQUÉE]',
        anonymized,
        flags=re.IGNORECASE
    )
    
    # Masquer les codes postaux français
    anonymized = re.sub(r'\b\d{5}\b', '[CODE_POSTAL_MASQUÉ]', anonymized)
    
    # Masquer les villes après code postal
    anonymized = re.sub(
        r'\[CODE_POSTAL_MASQUÉ\]\s+[A-ZÀÂÄÉÈÊËÏÎÔÙÛÜÇ][a-zàâäéèêëïîôùûüç\s\-]+',
        '[CODE_POSTAL_MASQUÉ] [VILLE_MASQUÉE]',
        anonymized
    )
    
    # Masquer les dates de naissance
    anonymized = re.sub(
        r'\b(né|née|naissance|birth)\s*(le|date)?\s*:?\s*\d{1,2}[\/\-\.]\d{1,2}[\/\-\.]\d{2,4}\b', 
        '[DATE_NAISSANCE_MASQUÉE]', 
        anonymized, 
        flags=re.IGNORECASE
    )
    
    # Masquer les dates au format JJ/MM/AAAA
    anonymized = re.sub(
        r'\b\d{1,2}[\/\-\.]\d{1,2}[\/\-\.](19|20)\d{2}\b', 
        '[DATE_MASQUÉE]', 
        anonymized
    )
    
    # Masquer l'âge
    anonymized = re.sub(r'\b\d{2}\s*ans\b', '[ÂGE_MASQUÉ]', anonymized, flags=re.IGNORECASE)
    
    # Masquer les numéros de sécurité sociale
    anonymized = re.sub(
        r'\b[1-2]\s?\d{2}\s?\d{2}\s?\d{2}\s?\d{3}\s?\d{3}\s?\d{2}\b', 
        '[NUMÉRO_SÉCU_MASQUÉ]', 
        anonymized
    )
    
    # Masquer permis de conduire
    anonymized = re.sub(
        r'\b(permis)\s*(de conduire)?\s*:?\s*[A-Z0-9]{10,}\b',
        '[PERMIS_MASQUÉ]',
        anonymized,
        flags=re.IGNORECASE
    )
    
    return anonymized

# Fonction pour créer un export structuré JSON
def create_structured_export(anonymized_text):
    """
    Crée un export JSON structuré pour analyse par une autre application
    """
    # Extraction des sections principales
    sections = {
        "text_complet": anonymized_text,
        "metadata": {
            "anonymise": True,
            "conformite_rgpd": True,
            "date_traitement": st.session_state.get('processing_date', 'N/A')
        },
        "sections_detectees": {}
    }
    
    # Détecter les sections courantes d'un CV
    section_patterns = {
        "experience": r'(EXPÉRIENCE|EXPERIENCE|PARCOURS PROFESSIONNEL)',
        "formation": r'(FORMATION|DIPLÔMES|EDUCATION)',
        "competences": r'(COMPÉTENCES|COMPETENCES|SKILLS)',
        "langues": r'(LANGUES|LANGUAGES)',
        "certifications": r'(CERTIFICATIONS|CERTIFICATS)',
        "projets": r'(PROJETS|PROJECTS)',
        "loisirs": r'(LOISIRS|CENTRES D\'INTÉRÊT|HOBBIES)'
    }
    
    for section_name, pattern in section_patterns.items():
        if re.search(pattern, anonymized_text, re.IGNORECASE):
            sections["sections_detectees"][section_name] = True
    
    return sections

# Interface Streamlit
st.title("🔒 Anonymiseur de CV - Conforme RGPD")
st.markdown("---")

# Informations RGPD
with st.expander("ℹ️ Données anonymisées", expanded=True):
    st.info("""
    **Cette application masque automatiquement :**
    - ✅ Noms et prénoms
    - ✅ Adresses email
    - ✅ Numéros de téléphone
    - ✅ Adresses postales complètes
    - ✅ Codes postaux et villes
    - ✅ Dates de naissance
    - ✅ Âges
    - ✅ Numéros de sécurité sociale
    - ✅ Permis de conduire
    
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
            # Stocker la date de traitement
            import datetime
            st.session_state['processing_date'] = datetime.datetime.now().isoformat()
        
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
        st.subheader("💾 Téléchargement")
        
        col_dl1, col_dl2, col_dl3 = st.columns(3)
        
        with col_dl1:
            # Export texte
            st.download_button(
                label="📄 Texte (.txt)",
                data=anonymized_cv,
                file_name=f"{output_filename}.txt",
                mime="text/plain",
                use_container_width=True,
                help="Format texte simple"
            )
        
        with col_dl2:
            # Export JSON structuré
            structured_data = create_structured_export(anonymized_cv)
            json_data = json.dumps(structured_data, ensure_ascii=False, indent=2)
            
            st.download_button(
                label="📊 JSON structuré",
                data=json_data,
                file_name=f"{output_filename}.json",
                mime="application/json",
                use_container_width=True,
                help="Format JSON pour analyse automatique"
            )
        
        with col_dl3:
            # Export CSV (lignes du CV)
            csv_data = anonymized_cv.replace('\n', '|||')
            
            st.download_button(
                label="📋 CSV",
                data=csv_data,
                file_name=f"{output_filename}.csv",
                mime="text/csv",
                use_container_width=True,
                help="Format CSV (une ligne)"
            )
        
        # Statistiques d'anonymisation
        st.markdown("---")
        st.subheader("📊 Statistiques d'anonymisation")
        
        col_stat1, col_stat2, col_stat3, col_stat4 = st.columns(4)
        
        noms_masked = anonymized_cv.count('[NOM_MASQUÉ]') + anonymized_cv.count('[PRÉNOM_MASQUÉ]')
        emails_masked = anonymized_cv.count('[EMAIL_MASQUÉ]')
        phones_masked = anonymized_cv.count('[TÉLÉPHONE_MASQUÉ]')
        addresses_masked = anonymized_cv.count('[ADRESSE_MASQUÉE]')
        
        with col_stat1:
            st.metric("Noms/Prénoms", noms_masked)
        with col_stat2:
            st.metric("Emails", emails_masked)
        with col_stat3:
            st.metric("Téléphones", phones_masked)
        with col_stat4:
            st.metric("Adresses", addresses_masked)
        
        # Aperçu du JSON
        with st.expander("👁️ Aperçu du format JSON structuré"):
            st.json(structured_data)
            st.caption("Ce format est optimisé pour être lu par une application d'analyse automatique")
    else:
        st.info("👈 Uploadez un CV pour commencer l'anonymisation")

# Footer
st.markdown("---")
st.caption("🔐 Conforme RGPD - Aucune donnée conservée après votre session")
