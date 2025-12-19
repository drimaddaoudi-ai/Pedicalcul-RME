import streamlit as st
import pandas as pd
from fpdf import FPDF
import datetime

# --- CONFIGURATION DE LA PAGE ---
st.set_page_config(page_title="Pédicalcul CHU Fès", layout="wide", page_icon="👶")

# ==========================================
# 🔐 SÉCURITÉ : AUTHENTIFICATION PAR EMAIL
# ==========================================

# 1. LISTE DES UTILISATEURS AUTORISÉS
# Format : "email": "mot_de_passe"
# CONSEIL : Mettez des mots de passe un peu complexes
UTILISATEURS = {
    "imad.daoudi@usmba.ac.ma": "admin01",
    "doughmi.djoudline@gmail.com": "prof",
    "interne2@usmba.ac.ma": "1234",
    "infirmier@chu-fes.ma": "1234"
}

# Initialisation de l'état (mémoire)
if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False
if 'user_email' not in st.session_state:
    st.session_state.user_email = ""

def verifier_login():
    email_input = st.session_state.email_input.lower().strip() # Nettoyage (minuscule/espace)
    password_input = st.session_state.password_input
    
    if email_input in UTILISATEURS:
        if UTILISATEURS[email_input] == password_input:
            st.session_state.authenticated = True
            st.session_state.user_email = email_input
        else:
            st.error("⛔ Mot de passe incorrect")
    else:
        st.error("⛔ Cet email n'est pas autorisé")

# Si non connecté, afficher le formulaire de login
if not st.session_state.authenticated:
    col_lock1, col_lock2 = st.columns([1, 2])
    with col_lock1:
        try: st.image("logo.png", width=100)
        except: pass
    with col_lock2:
        st.markdown("## 🔒 Connexion Sécurisée")
        st.markdown("Service Réanimation Mère-Enfant - CHU Fès")
        
        st.text_input("Email :", key="email_input")
        st.text_input("Mot de passe :", type="password", key="password_input")
        
        st.button("Se connecter", on_click=verifier_login)
        
        st.info("Contactez-nous pour obtenir votre accès.")
    
    st.stop() # 🛑 Arrête l'application ici si pas connecté

# Petit message de bienvenue dans la barre latérale une fois connecté
st.sidebar.success(f"Connecté en tant que : {st.session_state.user_email}")
if st.sidebar.button("Se déconnecter"):
    st.session_state.authenticated = False
    st.rerun()

# ==========================================
# 🏥 DÉBUT DE L'APPLICATION (Le reste de votre code suit ici...)
# ==========================================

# --- FONCTION DE GÉNÉRATION PDF ---
class PDF(FPDF):
    def header(self):
        # Paramètres : nom du fichier, x, y, largeur (en mm)
        try:
            self.image('logo.png', 10, 8, 20) 
        except:
            pass # Si pas d'image, ne plante pas
        self.set_font('Arial', 'B', 14)
        self.cell(0, 10, 'CHU Hassan II - Réanimation Mère-Enfant', 0, 1, 'C')
        self.set_font('Arial', 'I', 10)
        self.cell(0, 10, 'Fiche de Calcul Automatisée', 0, 1, 'C')
        self.ln(5)

    def footer(self):
        self.set_y(-15)
        self.set_font('Arial', 'I', 8)
        self.cell(0, 10, f'Page {self.page_no()}', 0, 0, 'C')

def create_pdf(patient_info, data_sections):
    pdf = PDF()
    pdf.add_page()
    
    # Info Patient
    pdf.set_font("Arial", size=11)
    pdf.cell(0, 8, f"Patient: {patient_info['nom']} | IP: {patient_info['ip']} | Admission: {patient_info['date_adm']}", ln=True)
    pdf.cell(0, 8, f"Age: {patient_info['age_str']} | Poids: {patient_info['poids']} kg | Généré le: {datetime.datetime.now().strftime('%d/%m/%Y %H:%M')}", ln=True)
    pdf.line(10, 30, 200, 30)
    pdf.ln(5)
    
    # Sections
    for title, df in data_sections.items():
        if df is not None and not df.empty:
            # Titre Section
            pdf.set_font("Arial", 'B', 10)
            pdf.set_fill_color(240, 240, 240)
            pdf.cell(0, 7, title, ln=True, fill=True)
            
            # Tableau
            pdf.set_font("Arial", size=8)
            cols = df.columns.tolist()
            page_width = 190
            
            # --- CORRECTION ICI : Ajustement intelligent largeur colonnes ---
            if len(cols) == 4:
                # Cas ACR / Urgences : On donne plus de place à la col 2 (Présentation)
                # Col 1: 22%, Col 2: 38% (Large), Col 3: 20%, Col 4: 20%
                col_widths = [page_width * 0.22, page_width * 0.38, page_width * 0.20, page_width * 0.20]
            
            elif len(cols) == 3:
                # Cas Sédation / Divers
                col_widths = [page_width * 0.30, page_width * 0.30, page_width * 0.40]
            
            elif len(cols) == 2:
                # Cas Physio / Bio / Intubation
                col_widths = [page_width * 0.40, page_width * 0.60]
            
            elif len(cols) > 0:
                # Fallback générique
                col_widths = [page_width * 0.35] + [page_width * 0.65 / (len(cols)-1)] * (len(cols)-1)
            else:
                col_widths = [page_width]
            # -------------------------------------------------------------

            # En-têtes
            pdf.set_font("Arial", 'B', 8)
            for i, col in enumerate(cols):
                pdf.cell(col_widths[i], 6, str(col), border=1, align='C')
            pdf.ln()
            
            # Données
            pdf.set_font("Arial", size=8)
            for index, row in df.iterrows():
                # On calcule la hauteur nécessaire pour la ligne (multicell support)
                # Pour simplifier ici, on garde cell mais on tronque si trop long ou on réduit la police
                # L'ajustement des colonnes ci-dessus devrait suffire pour éviter le débordement
                for i, col in enumerate(cols):
                    # Nettoyage
                    val = str(row[col]).replace('**', '').replace('⚠️', '!').replace('⛔', 'STOP').replace('⚡', '').replace('💧', '')
                    pdf.cell(col_widths[i], 6, val, border=1, align='L' if i==0 else 'C')
                pdf.ln()
            pdf.ln(3)
            
    return pdf.output(dest='S').encode('latin-1', 'replace')

# ==========================================
# INTERFACE UTILISATEUR (STREAMLIT)
# ==========================================

# Affichage du Logo sur le site (optionnel)
col_logo, col_titre = st.columns([1, 5])
with col_logo:
    try:
        st.image("logo.png", width=100)
    except:
        pass
with col_titre:
    st.title("👶 Pédicalcul - Réa Mère Enfant - CHU Fès")

# 1. ZONE DE SAISIE
st.markdown("### 📝 Identification & Paramètres")

col_id1, col_id2, col_id3 = st.columns(3)
with col_id1:
    nom_patient = st.text_input("Nom & Prénom", placeholder="ex: ALAMI Mohammed")
with col_id2:
    ip_patient = st.text_input("IP / Dossier", placeholder="ex: 2025/12345")
with col_id3:
    date_admission = st.date_input("Date d'admission", datetime.date.today())

# --- NOUVELLE LOGIQUE D'ÂGE EXCLUSIVE ---
st.markdown("---")
col_age_type, col_age_val, col_poids = st.columns([1, 1, 2])

with col_age_type:
    # Choix exclusif de l'unité
    type_age = st.radio("Unité d'âge :", ["Mois (< 2 ans)", "Années (≥ 2 ans)"])

with col_age_val:
    if type_age == "Mois (< 2 ans)":
        # Saisie en MOIS uniquement (0 à 23 mois)
        valeur_age = st.number_input("Âge (en mois)", min_value=0, max_value=23, value=6)
        
        # Conversion interne
        total_months = valeur_age
        age_years_float = total_months / 12.0
        age_display = f"{valeur_age} mois"
        
        # Variables pour compatibilité avec le reste du code
        age_years = 0
        age_months = valeur_age

    else:
        # Saisie en ANNÉES uniquement (2 à 16 ans)
        valeur_age = st.number_input("Âge (en années)", min_value=2, max_value=16, value=5)
        
        # Conversion interne
        total_months = valeur_age * 12
        age_years_float = float(valeur_age)
        age_display = f"{valeur_age} ans"
        
        # Variables pour compatibilité
        age_years = valeur_age
        age_months = 0

# Calcul Poids APLS (Basé sur l'âge total unifié)
if total_months < 12:
    poids_estime = (0.5 * total_months) + 4
elif 12 <= total_months <= 60:
    poids_estime = (2.0 * age_years_float) + 8
elif 60 < total_months <= 144:
    poids_estime = (3.0 * age_years_float) + 7
else:
    poids_estime = (3.0 * age_years_float) + 7

with col_poids:
    st.info(f"Poids théorique calculé : **{round(poids_estime, 1)} kg**")
    poids_retenu = st.number_input("Poids RETENU (kg)", value=float(round(poids_estime, 1)), step=0.5)

# --- AJOUT DU DISCLAIMER ---
st.warning("""
⚠️ **AVERTISSEMENT** :
* Cette application est destinée **exclusivement** à un usage interne au service de **Réanimation Mère-Enfant** au CHU HASSAN II de Fès (Maroc).
* Elle constitue une aide au calcul et ne remplace en aucun moment le **jugement clinique**.
""")

# Dictionnaire pour stocker les DataFrames pour le PDF
pdf_data_store = {}

# --- BOUTON PDF (Visible seulement si poids validé) ---
if poids_retenu > 0:
    st.markdown("---")
    
    # Texte âge propre pour le PDF
    if age_years == 0:
        age_display = f"{age_months} mois"
    elif age_months == 0:
        age_display = f"{age_years} ans"
    else:
        age_display = f"{age_years} ans et {age_months} mois"

    p_info = {
        "nom": nom_patient, "ip": ip_patient, 
        "date_adm": date_admission.strftime("%d/%m/%Y"),
        "age": age_display, "age_str": age_display, "poids": poids_retenu
    }
    
    pdf_button_placeholder = st.empty()

    # ==========================================
    # LOGIQUE MÉDICALE
    # ==========================================

    st.subheader(f"Paramètres pour patient de {poids_retenu} kg")

    # --- SECTION 1 : INTUBATION ---
    st.subheader("1. 🌬️ Intubation & Voies Aériennes")
    
    # Logique basée sur total_months / age_years_float
    if age_years_float < 2: lame = "Taille 1"
    elif 2 <= age_years_float <= 5: lame = "Taille 2"
    elif 5 < age_years_float <= 12: lame = "Taille 2 ou 3"
    else: lame = "Taille 3 ou 4"

    if total_months < 12: sonde_id = 3.5
    else: sonde_id = (age_years_float / 4.0) + 3.5
    
    # Arrondi sonde à 0.5 le plus proche si besoin, ou garder float
    # Généralement on garde une décimale ex: 4.1 -> 4.0, 4.4 -> 4.5. 
    # Pour simplifier ici on affiche la valeur calculée arrondie à 1 décimale
    sonde_id = round(sonde_id * 2) / 2 # Arrondi au 0.5 le plus proche si on veut être puriste, sinon round 1
    
    fixation = round(sonde_id * 3, 1)
    
    if poids_retenu < 6: guedel = "00 (Bleu)"
    elif poids_retenu < 10: guedel = "0 (Noir)"
    elif poids_retenu < 15: guedel = "1 (Blanc)"
    elif poids_retenu < 25: guedel = "2 (Vert)"
    elif poids_retenu < 50: guedel = "3 (Orange)"
    else: guedel = "4 (Rouge)"
    
    aspir_sz = sonde_id * 2
    if aspir_sz <= 6: aspir = "6 Fr (Vert clair)"
    elif aspir_sz <= 8: aspir = "8 Fr (Bleu)"
    elif aspir_sz <= 10: aspir = "10 Fr (Noir)"
    elif aspir_sz <= 12: aspir = "12 Fr (Blanc)"
    else: aspir = "14 Fr (Vert foncé)"

    df_intub = pd.DataFrame({
        "Paramètre": ["Sonde (Ballonnet)", "Fixation (lèvres)", "Lame", "Guedel", "Sonde Aspiration", "Pression Ballonnet"],
        "Valeur": [f"Taille {sonde_id}", f"{fixation} cm", lame, guedel, aspir, "20-30 cmH2O"]
    })
    st.table(df_intub.set_index("Paramètre"))
    pdf_data_store["1. Intubation"] = df_intub

    # --- SECTION 2 : PHYSIO ---
    st.subheader("2. 📊 Paramètres Physiologiques")

    # A. Détermination des constantes normales selon l'âge TOTAL (Mois)
    if total_months < 12:
        # Nourrisson < 1 an
        fc_range = "100 - 150 bpm"
        fr_range_val = (30, 60)
        pas_range = "70 - 90 mmHg"
        pad_range = "40 - 55 mmHg"
        pam_range = "50 - 65 mmHg"
        vol_sang_ratio = 80 
        
    elif 12 <= total_months < 36:
        # Bambin (1 à 3 ans)
        fc_range = "90 - 140 bpm"
        fr_range_val = (24, 40)
        pas_range = "80 - 100 mmHg"
        pad_range = "50 - 65 mmHg"
        pam_range = "60 - 75 mmHg"
        vol_sang_ratio = 80
        
    elif 36 <= total_months < 72:
        # Préscolaire (3 à 6 ans)
        fc_range = "80 - 130 bpm"
        fr_range_val = (22, 34)
        pas_range = "80 - 110 mmHg"
        pad_range = "55 - 70 mmHg"
        pam_range = "65 - 80 mmHg"
        vol_sang_ratio = 75 
        
    elif 72 <= total_months < 144:
        # Scolaire (6 à 12 ans)
        fc_range = "70 - 120 bpm"
        fr_range_val = (18, 30)
        pas_range = "90 - 120 mmHg"
        pad_range = "60 - 75 mmHg"
        pam_range = "70 - 90 mmHg"
        vol_sang_ratio = 75
        
    else:
        # Adolescent (> 12 ans)
        fc_range = "60 - 100 bpm"
        fr_range_val = (12, 16)
        pas_range = "100 - 130 mmHg"
        pad_range = "65 - 80 mmHg"
        pam_range = "80 - 100 mmHg"
        vol_sang_ratio = 75

    # B. Calculs Volumétriques
    vt_min = round(poids_retenu * 4, 1)
    vt_max = round(poids_retenu * 8, 1)
    ebv = round(poids_retenu * vol_sang_ratio, 0)
    
    vm_min_l = round((vt_min * fr_range_val[0]) / 1000, 1) 
    vm_max_l = round((vt_max * fr_range_val[1]) / 1000, 1) 

   # ... (Code existant du calcul VM_min/max) ...

    # --- MISE A JOUR : Ajout Gazométrie dans le tableau Physiologie ---
    data_physio = {
        "Paramètre": [
            "Fréquence Cardiaque (FC)",
            "Pression Artérielle (PAS / PAD)",
            "Pression Moyenne (PAM)",
            "Fréquence Respiratoire (FR)",
            "Volume Courant (Vt 4-8 ml/kg)",
            "Ventilation Minute (Vm)",
            f"Masse Sanguine ({vol_sang_ratio} ml/kg)",
            "Gazométrie : pH (Art / Vein)",
            "Gazométrie : PCO2 (Art / Vein)",
            "Gazométrie : PO2 (Art / Vein)",
            "Gazométrie : HCO3- (Bicar)",
            "Gazométrie : Lactates"
        ],
        "Valeur Normale / Cible": [
            fc_range,
            f"{pas_range} / {pad_range}",
            pam_range,
            f"{fr_range_val[0]} - {fr_range_val[1]} cpm",
            f"{vt_min} - {vt_max} ml",
            f"{vm_min_l} - {vm_max_l} L/min",
            f"~ {int(ebv)} ml",
            "7.35-7.45  /  7.32-7.43",
            "35-45 mmHg  /  38-50 mmHg",
            "80-100 mmHg /  30-50 mmHg",
            "22 - 26 mmol/L",
            "< 2.0 mmol/L"
        ]
    }
    
    df_physio = pd.DataFrame(data_physio)
    st.table(df_physio.set_index('Paramètre'))
    pdf_data_store["2. Physiologie & Gazo"] = df_physio

    # --- SECTION 3 : ACR ---
    st.subheader("3. 💔 Arrêt Cardio-Respiratoire")

    adre_dose = min(poids_retenu * 0.01, 1.0)
    adre_vol = adre_dose / 0.1
    amio_dose = min(poids_retenu * 5, 300.0)
    amio_vol = amio_dose / 50.0
    lido_dose = min(poids_retenu * 1.5, 100.0)
    lido_vol = lido_dose / 20.0
    choc_min = round(poids_retenu * 2, 0)
    choc_max = round(poids_retenu * 4, 0)

    data_acr = {
        "Médicament / Geste": [
            "Adrénaline (IV/IO)",
            "Amiodarone (Bolus)",
            "Lidocaïne (Bolus)",
            "Défibrillation (Choc)"
        ],
        "Présentation & Dilution": [
            "Amp 1mg/1ml. DILUER dans 10ml (-> 0.1 mg/ml)",
            "Amp 150mg/3ml (Pur = 50 mg/ml)",
            "Flacon 2% (20 mg/ml)",
            "-"
        ],
        "Posologie/kg": [
            "0.01 mg/kg",
            "5 mg/kg",
            "1.5 mg/kg",
            "2 - 4 J/kg"
        ],
        "Dose à administrer": [
            f"{round(adre_dose, 3)} mg  =  {round(adre_vol, 2)} ml",
            f"{int(amio_dose)} mg  =  {round(amio_vol, 1)} ml",
            f"{int(lido_dose)} mg  =  {round(lido_vol, 1)} ml",
            f"{int(choc_min)} - {int(choc_max)} Joules"
        ]
    }
    df_acr = pd.DataFrame(data_acr)
    st.table(df_acr.set_index('Médicament / Geste'))
    # CORRECTION PDF: Ajout au dictionnaire
    pdf_data_store["3. ACR"] = df_acr

    # --- SECTION 4 : DROGUES D'URGENCE ---
    st.subheader("4. ⚡ Drogues d'Urgence")

    atro_brut = poids_retenu * 0.02
    if atro_brut < 0.1: atro_dose = 0.1 
    elif atro_brut > 0.5 and age_years_float < 12: atro_dose = 0.5 
    elif atro_brut > 1.0: atro_dose = 1.0 
    else: atro_dose = atro_brut
    
    atro_vol = atro_dose / 0.5 
    ephed_dose = min(poids_retenu * 0.2, 10.0)
    ephed_vol = ephed_dose / 3.0
    ca_vol = min(poids_retenu * 0.5, 20.0)
    mg_min = round(poids_retenu * 25, 0)
    mg_max = min(round(poids_retenu * 50, 0), 2000.0)
    mg_vol_min = round(mg_min / 150, 1)
    mg_vol_max = round(mg_max / 150, 1)
    cv_min = round(poids_retenu * 0.5, 0)
    cv_max = round(poids_retenu * 2, 0)

    data_urg = {
        "Médicament / Geste": [
            "Atropine",
            "Ephédrine",
            "Gluconate de Calcium 10%",
            "Sulfate de Magnésium 15%",
            "Cardioversion Sync."
        ],
        "Présentation & Dilution": [
            "Amp 0.5 mg/ml (Pur)",
            "Amp 30mg. DILUER dans 10ml (-> 3 mg/ml)",
            "Amp 10% (0.5 ml/kg)",
            "Amp 15% (150 mg/ml)",
            "-"
        ],
        "Posologie/kg": [
            "0.02 mg/kg (Min 0.1mg)",
            "0.2 mg/kg",
            "0.5 ml/kg",
            "25 - 50 mg/kg",
            "0.5 - 2 J/kg"
        ],
        "Dose à administrer": [
            f"{round(atro_dose, 2)} mg  =  {round(atro_vol, 2)} ml",
            f"{round(ephed_dose, 1)} mg  =  {round(ephed_vol, 1)} ml",
            f"{round(ca_vol, 1)} ml (direct)",
            f"{int(mg_min)}-{int(mg_max)} mg = {mg_vol_min}-{mg_vol_max} ml",
            f"{int(cv_min)} - {int(cv_max)} Joules"
        ]
    }
    df_urg = pd.DataFrame(data_urg)
    st.table(df_urg.set_index('Médicament / Geste'))
    # CORRECTION PDF: Ajout au dictionnaire
    pdf_data_store["4. Urgences"] = df_urg

    # --- SECTION 5 : ISR ---
    st.subheader("5. 💉 Induction Séquence Rapide")
    
    propofol_min = round(poids_retenu * 2, 0)
    propofol_max = round(poids_retenu * 3, 0)
    etomidate_dose = round(poids_retenu * 0.3, 1)
    keta_min = round(poids_retenu * 1, 0)
    keta_max = round(poids_retenu * 3, 0)
    fenta_min = round(poids_retenu * 2, 0)
    fenta_max = round(poids_retenu * 3, 0)
    rocu_min = round(poids_retenu * 0.6, 1)
    rocu_max = round(poids_retenu * 1.2, 1)

    data_isr = {
        "Médicament": [
            "Propofol",
            "Etomidate",
            "Kétamine",
            "Fentanyl",
            "Rocuronium (Esmeron)"
        ],
        "Concentration (Réf)": [
            "10 mg/ml (1%)",
            "2 mg/ml",
            "50 mg/ml",
            "50 mcg/ml",
            "10 mg/ml"
        ],
        "Posologie/kg": [
            "2 - 3 mg/kg",
            "0.3 mg/kg",
            "1 - 3 mg/kg",
            "2 - 3 mcg/kg",
            "0.6 - 1.2 mg/kg"
        ],
        "Dose à administrer": [
            f"{int(propofol_min)} - {int(propofol_max)} mg",
            f"{etomidate_dose} mg",
            f"{int(keta_min)} - {int(keta_max)} mg",
            f"{int(fenta_min)} - {int(fenta_max)} mcg (gamma)",
            f"{rocu_min} - {rocu_max} mg"
        ]
    }
    
    df_isr = pd.DataFrame(data_isr)
    st.table(df_isr.set_index('Médicament'))
    # CORRECTION PDF: Ajout au dictionnaire
    pdf_data_store["5. ISR"] = df_isr

# --- SECTION 6 : SEDATION ---
    st.subheader("6. 💤 Sédation Continue")
    st.markdown("**A. Midazolam + Fentanyl**")
    
    # Initialisation variables pour PDF
    titre_pdf_sedation = "6a. Sédation Midaz/Fenta"
    
    if poids_retenu < 20:
        # LOGIQUE < 20 KG
        mida_qty = round(poids_retenu * 2, 1)
        fenta_qty = round(poids_retenu * 25, 1)
        
        # Affichage Ecran
        st.info(f"""
        **PROTOCOLE < 20 KG (Dilution Spécifique)**
        * **Midazolam :** 2 x Poids = **{mida_qty} mg**
        * **Fentanyl :** 25 x Poids = **{fenta_qty} mcg**
        * *Compléter SAP 50 ml avec SSI/G5*
        """)
        st.error("⛔ Ne jamais dépasser 10 ml/h")
        
        # Titre PDF avec la dilution calculée
        titre_pdf_sedation = f"6. Sédation (Dilution: Midaz {mida_qty}mg + Fenta {fenta_qty}mcg / 50ml)"
        
        # Tableau 1 à 10 ml/h
        vitesses = list(range(1, 11)) 
        data_sedation = []
        for v in vitesses:
            dose_mida = round(v * 0.04, 2)
            dose_fenta = round(v * 0.5, 1)
            alert = "⚠️" if (dose_mida > 0.4 or dose_fenta > 5) else ""
            data_sedation.append([f"{v} ml/h {alert}", f"{dose_mida} mg/kg/h", f"{dose_fenta} mcg/kg/h"])
            
        df_sed = pd.DataFrame(data_sedation, columns=["Vitesse", "Dose Midaz", "Dose Fenta"])
    
    else:
        # LOGIQUE >= 20 KG
        st.info("**PROTOCOLE ≥ 20 KG (Dilution Standard)**\n* Midazolam 50mg + Fentanyl 500mcg QSP 50ml")
        
        vitesse_max_safe = round(poids_retenu * 0.4, 1)
        st.error(f"⛔ Max **{vitesse_max_safe} ml/h** (correspond à 0.4 mg/kg/h)")
        
        # Titre PDF avec la dilution standard
        titre_pdf_sedation = "6. Sédation (Dilution Std: Midaz 50mg + Fenta 500mcg / 50ml)"
        
        # Cibles incluant 0.4
        cibles_mida = [0.05, 0.1, 0.15, 0.2, 0.25, 0.3, 0.35, 0.4]
        data_sedation_grand = []
        for c in cibles_mida:
            c_fenta = c * 10
            vit = round(c * poids_retenu, 1)
            data_sedation_grand.append([f"{c} mg/kg/h", f"{c_fenta} mcg/kg/h", f"**{vit} ml/h**"])
            
        df_sed = pd.DataFrame(data_sedation_grand, columns=["Cible Midaz", "Cible Fenta", "Vitesse à régler"])

    st.table(df_sed.set_index(df_sed.columns[0]))
    
    # Enregistrement pour le PDF avec le titre contenant la dilution
    pdf_data_store[titre_pdf_sedation] = df_sed

    st.markdown("**B. Propofol (Pur 10 mg/ml)**")
    st.warning("⚠️ Changer seringue + prolongateur / 12h. Max 4 mg/kg/h (PRIS)")
    df_prop = pd.DataFrame([["Propofol", "1-4 mg/kg/h", f"**{int(poids_retenu)} - {int(poids_retenu*4)} mg/h** (soit {round(poids_retenu/10,1)} - {round(poids_retenu*4/10,1)} ml/h)"]], columns=["Drogue", "Poso", "Débit"])
    st.table(df_prop.set_index("Drogue"))
    pdf_data_store["6b. Propofol"] = df_prop

    # --- SECTION 7 : VASOACTIFS ---
    st.subheader("7. 💓 Vasoactifs (Noradré/Adré/Dobu)")
    if poids_retenu < 30: nora_p = "8mg/50ml (1 amp)"; nora_c = 160
    else: nora_p = "16mg/50ml (2 amp)"; nora_c = 320
    
    nora_min = (0.01 * poids_retenu * 60) / nora_c
    nora_max = (3.0 * poids_retenu * 60) / nora_c
    adre_min = (0.01 * poids_retenu * 60) / 200 
    adre_max = (1.0 * poids_retenu * 60) / 200
    dobu_min = (2.5 * poids_retenu * 60) / 5000 
    dobu_max = (20.0 * poids_retenu * 60) / 5000

    df_vaso = pd.DataFrame([
        ["Noradrénaline", nora_p, "0.01-3 mcg/kg/min", f"{round(nora_min,2)} - {round(nora_max,1)} ml/h"],
        ["Adrénaline", "10mg/50ml", "0.01-1 mcg/kg/min", f"{round(adre_min,2)} - {round(adre_max,1)} ml/h"],
        ["Dobutamine", "250mg/50ml", "2.5-20 mcg/kg/min", f"{round(dobu_min,2)} - {round(dobu_max,1)} ml/h"]
    ], columns=["Drogue", "Prép (50ml)", "Poso", "Vitesse"])
    st.table(df_vaso.set_index("Drogue"))
    pdf_data_store["7. Vasoactifs"] = df_vaso

    # --- SECTION 8 : REMPLISSAGE ---
    st.subheader("8. 💧 Remplissage Vasculaire")
    st.info("**Cristalloïdes Isotoniques :** NaCl 0.9% ou Ringer Lactate")
    st.warning("⚠️ **Précautions :** Vérifier signes de surcharge.")
    bolus_10 = int(poids_retenu * 10)
    bolus_20 = int(poids_retenu * 20)
    df_remp = pd.DataFrame({
        "Objectif": ["10 ml/kg", "20 ml/kg"],
        "Volume": [f"**{bolus_10} ml**", f"**{bolus_20} ml**"],
        "Durée": ["15 min", "15 min"]
    })
    st.table(df_remp.set_index("Objectif"))
    pdf_data_store["8. Remplissage"] = df_remp

    # --- SECTION 9 : RATION DE BASE ---
    st.subheader("9. 🍼 Ration de Base (Holliday-Segar)")
    if poids_retenu <= 10: base_rate = 4 * poids_retenu
    elif poids_retenu <= 20: base_rate = 40 + (2 * (poids_retenu - 10))
    else: base_rate = 60 + (1 * (poids_retenu - 20))
    
    base_daily = base_rate * 24
    is_capped = False
    if base_daily > 2500:
        base_daily = 2500
        base_rate = round(2500/24, 1)
        is_capped = True
        
    restr_rate = round(base_rate * 2/3, 1)
    restr_daily = round(base_daily * 2/3, 0)
    
    st.success("**Composition :** G5% + 4.5g NaCl + 1g KCl")
    if is_capped: st.warning("⚠️ Plafonné à 2500 ml/j")
    
    df_base = pd.DataFrame({
        "Situation": ["Standard (4-2-1)", "Restriction 2/3 (SIADH, Post-op, polytrauma, choc septique, SDRA)"],
        "Débit SAP": [f"**{base_rate} ml/h**", f"**{restr_rate} ml/h**"],
        "Volume/24h": [f"{int(base_daily)} ml", f"{int(restr_daily)} ml"]
    })
    st.table(df_base.set_index("Situation"))
    pdf_data_store["9. Ration de Base"] = df_base

    # --- SECTION 10 : REHYDRATATION ---
    st.subheader("10. 🚑 Réhydratation (Déficit 48h)")
    st.info("Soluté : NaCl 0.9% ou RL. (Corrige le déficit uniquement)")
    data_rehydro = []
    for p in [5, 10, 15]:
        vol = poids_retenu * p * 10
        v_tier = vol / 3.0
        data_rehydro.append([f"{p}%", f"**{int(vol)} ml**", f"{round(v_tier/8,1)} ml/h", f"{round(v_tier/16,1)} ml/h", f"{round(v_tier/24,1)} ml/h"])
    
    df_rehydro = pd.DataFrame(data_rehydro, columns=["%", "Total 48h", "Débit H0-H8", "Débit H8-H24", "Débit H24-H48"])
    st.table(df_rehydro.set_index("%"))
    pdf_data_store["10. Réhydratation"] = df_rehydro

    # --- SECTION 11 : POTASSIUM ---
    st.subheader("11. ⚠️ Charge Potassique (VVC !)")
    if poids_retenu < 20:
        kcl_prep = "18.5ml KCl + 31.5ml SSI"
        kcl_max = round(poids_retenu, 1)
    else:
        kcl_prep = "37ml KCl + 13ml SSI"
        kcl_max = round(poids_retenu * 0.5, 1)
        
    df_kcl = pd.DataFrame([["Charge K+", kcl_prep, f"Max **{kcl_max} ml/h**"]], columns=["Type", "Seringue 50ml", "Vitesse Max"])
    st.error(f"⛔ VVC UNIQUEMENT. Vitesse Max : {kcl_max} ml/h")
    st.table(df_kcl.set_index("Type"))
    pdf_data_store["11. Potassium"] = df_kcl

    # --- SECTION 12 : ANALGÉSIE ---
    st.subheader("12. 💊 Analgésie")
    # Morphine Bolus: Plafond 3mg
    raw_m_min = poids_retenu * 0.05
    raw_m_max = poids_retenu * 0.1
    morph_bolus_min = round(min(raw_m_min, 3.0), 2)
    morph_bolus_max = round(min(raw_m_max, 3.0), 2)
    
    df_analg = pd.DataFrame([
        ["Paracétamol", "15 mg/kg", f"**{int(poids_retenu*15)} mg** / 6h ou 8h"],
        ["Morphine (Bolus)", "0.05-0.1 mg/kg", f"**{morph_bolus_min} - {morph_bolus_max} mg** / 10-15 min"],
        ["Morphine (SAP)", "10-40 mcg/kg/h", f"**{round(poids_retenu*0.01, 2)} - {round(poids_retenu*0.04, 2)} mg/h**"]
    ], columns=["Drogue", "Réf", "Dose Calculée / Fréquence"])
    st.table(df_analg.set_index("Drogue"))
    st.error("⛔ Morphine Bolus : Ne jamais dépasser 3 mg.")
    pdf_data_store["12. Analgésie"] = df_analg

# --- SECTION 13 : DIVERS ---
    st.subheader("13. 🏥 Divers & Thérapeutiques")
    data_divers = []

    # 1. Oméprazole
    calc_ome = round(poids_retenu * 1.0, 2)
    data_divers.append(["Oméprazole", "1.0 mg/kg", f"**{calc_ome} mg** / 24h"])

    # 2. Métoclopramide (Contre-indiqué < 1 an)
    meto_d = "⛔ < 1 an" if age_years < 1 else f"**{round(poids_retenu*0.15,2)} mg** / 8h"
    data_divers.append(["Métoclopramide", "0.15 mg/kg", meto_d])

    # 3. Ondansétron
    calc_onda = round(poids_retenu * 0.15, 2)
    data_divers.append(["Ondansétron", "0.15 mg/kg", f"**{calc_onda} mg** / 8h (Max 8mg)"])

    # 4. Méthylprédni
    calc_methyl = round(poids_retenu * 1.0, 2)
    data_divers.append(["Méthylprédni", "1.0 mg/kg", f"**{calc_methyl} mg** / 6h"])

    # 5. Hydrocortisone
    calc_hydro = round(poids_retenu * 1.0, 2)
    data_divers.append(["Hydrocortisone", "1 mg/kg/dose", f"**{calc_hydro} mg** / 6h"])

    # 6. Dexaméthasone
    calc_dexa = round(poids_retenu * 0.2, 2)
    data_divers.append(["Dexaméthasone", "0.2 mg/kg", f"**{calc_dexa} mg** / jour"])

    # 7. Furosémide
    calc_furo = round(poids_retenu * 1.0, 2)
    data_divers.append(["Furosémide", "1.0 mg/kg", f"**{calc_furo} mg** / 6-12h"])

    # 8. Mannitol 10%
    manni_min, manni_max = int(poids_retenu*5), int(poids_retenu*10)
    data_divers.append(["Mannitol 10%", "0.5-1 g/kg", f"**{manni_min}-{manni_max} ml** (Bolus)"])

    # 9. SSH 3%
    ssh_min = int(poids_retenu * 2)
    ssh_max = int(poids_retenu * 5)
    data_divers.append(["SSH 3%", "2-5 ml/kg", f"**{ssh_min} - {ssh_max} ml** (Bolus 15-20 min)"])

    # 10. Bicar 1.4%
    calc_bicar = int(poids_retenu * 6.0) # En ml directement
    data_divers.append(["Bicar 1.4%", "6.0 ml/kg", f"**{calc_bicar} ml** (Bolus lent, à répéter si nécessaire)"])

    # 11. Acide Tranex
    calc_tranex = round(poids_retenu * 20.0, 2)
    data_divers.append(["Acide Tranex", "20.0 mg/kg", f"**{calc_tranex} mg** (Bolus 15 min)"])

    # 12. Nicardipine (Bolus)
    loxen_min, loxen_max = round(poids_retenu*0.02,2), round(poids_retenu*0.03,2)
    data_divers.append(["Nicardipine (Bolus)", "20-30 mcg/kg", f"**{loxen_min}-{loxen_max} mg**"])

    # 13. Nicardipine (SAP)
    loxen_sap_min = round((poids_retenu * 0.5 * 60) / 1000, 2)
    loxen_sap_max = round((poids_retenu * 3.0 * 60) / 1000, 2)
    data_divers.append(["Nicardipine (SAP)", "0.5-3 mcg/kg/min", f"**{loxen_sap_min} - {loxen_sap_max} mg/h** (Continu)"])

    # --- AFFICHAGE ---
    df_divers = pd.DataFrame(data_divers, columns=["Médicament", "Poso Réf", "Dose Calculée"])
    st.table(df_divers.set_index("Médicament"))
    pdf_data_store["13. Divers"] = df_divers
# --- SECTION 14 : BIOLOGIE (NOUVEAU) ---
    st.subheader("14. 🩸 Constantes Biologiques (Valeurs Normales)")
    
    # A. Définition des normes selon l'âge (Sources: Harriet Lane / CALIPER)
    if total_months < 12: # Nourrisson
        bio_hb = "10.0 - 12.0 g/dL"
        bio_hte = "30 - 36 %"
        bio_gb = "6.0 - 17.5 G/L"
        bio_creat = "2 - 4 mg/L"
        bio_uree = "0.10 - 0.35 g/L"
        bio_phos = "40 - 70 mg/L" # Élevé (Croissance)
        bio_alb = "30 - 45 g/L"
        bio_got = "20 - 80 UI/L"
        
    elif total_months < 144: # Enfant (1 - 12 ans)
        bio_hb = "11.0 - 13.5 g/dL"
        bio_hte = "33 - 40 %"
        bio_gb = "5.5 - 15.5 G/L"
        bio_creat = "3 - 6 mg/L"
        bio_uree = "0.15 - 0.40 g/L"
        bio_phos = "35 - 55 mg/L"
        bio_alb = "35 - 50 g/L"
        bio_got = "20 - 60 UI/L"

    else: # Ado (> 12 ans)
        bio_hb = "12.0 - 15.5 g/dL"
        bio_hte = "36 - 46 %"
        bio_gb = "4.5 - 11.0 G/L"
        bio_creat = "5 - 9 mg/L" # Masse musculaire
        bio_uree = "0.15 - 0.45 g/L"
        bio_phos = "25 - 45 mg/L" # Adulte
        bio_alb = "35 - 50 g/L"
        bio_got = "15 - 40 UI/L"

    # B. Tableau des données (Sans la colonne Bilan)
    data_bio = [
        ["Hémoglobine (Hb)", bio_hb],
        ["Hématocrite (Hte)", bio_hte],
        ["Globules Blancs (GB)", bio_gb],
        ["Plaquettes", "150 - 450 G/L"],
        ["Sodium (Na+)", "135 - 145 mmol/L"],
        ["Potassium (K+)", "3.5 - 5.0 mmol/L"],
        ["Chlore (Cl-)", "98 - 107 mmol/L"],
        ["Réserve Alcaline (RA)", "22 - 26 mmol/L"],
        ["Calcium (Ca++)", "88 - 108 mg/L"],
        ["Phosphore", bio_phos],
        ["Magnésium", "0.017 - 0.022 g/L"],
        ["Albumine", bio_alb],
        ["Urée", bio_uree],
        ["Créatinine", bio_creat],
        ["GOT (ASAT)", bio_got],
        ["GPT (ALAT)", "10 - 45 UI/L"]
    ]

    df_bio = pd.DataFrame(data_bio, columns=["Paramètre", "Valeurs de Référence"])
    st.table(df_bio.set_index("Paramètre"))
    pdf_data_store["14. Biologie"] = df_bio
    
    
    # --- GÉNÉRATION DU BOUTON PDF (FIN) ---
    with pdf_button_placeholder:
        pdf_bytes = create_pdf(p_info, pdf_data_store)
        st.download_button(
            label="📥 Télécharger la Fiche PDF",
            data=pdf_bytes,
            file_name=f"Fiche_Rea_{nom_patient.replace(' ', '_')}.pdf",
            mime="application/pdf",
            type="primary" 
        )


















