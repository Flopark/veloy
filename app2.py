# -*- coding: utf-8 -*-
"""
Created on Thu Dec 25 00:04:15 2025

@author: march
"""
import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime, timedelta, time

# --- CONFIGURATION DE LA PAGE ---
st.set_page_config(page_title="Veloy - Gadz", page_icon="🚲")

# --- CONFIGURATION BASE DE DONNÉES ---
conn = sqlite3.connect('velos_ecole.db', check_same_thread=False)
c = conn.cursor()

def create_tables():
    c.execute('CREATE TABLE IF NOT EXISTS users(username TEXT PRIMARY KEY, password TEXT)')
    c.execute('''CREATE TABLE IF NOT EXISTS reservations(
                    id INTEGER PRIMARY KEY, 
                    bike_id TEXT, 
                    username TEXT, 
                    start_dt TEXT, 
                    end_dt TEXT)''')
    conn.commit()

create_tables()

# --- FONCTIONS LOGIQUES ---

def check_overlap(bike_id, new_start, new_end):
    # On récupère les réservations futures pour ce vélo
    c.execute('SELECT start_dt, end_dt FROM reservations WHERE bike_id=?', (bike_id,))
    existing_resas = c.fetchall()
    
    for start_str, end_str in existing_resas:
        existing_start = datetime.fromisoformat(start_str)
        existing_end = datetime.fromisoformat(end_str)
        
        # Logique de chevauchement
        if new_start < existing_end and new_end > existing_start:
            return True
    return False

def make_reservation(bike_id, username, start_dt, end_dt):
    if check_overlap(bike_id, start_dt, end_dt):
        return False
    else:
        c.execute('INSERT INTO reservations(bike_id, username, start_dt, end_dt) VALUES (?,?,?,?)', 
                  (bike_id, username, start_dt.isoformat(), end_dt.isoformat()))
        conn.commit()
        return True

def cancel_reservation(reservation_id):
    c.execute("DELETE FROM reservations WHERE id=?", (reservation_id,))
    conn.commit()

def add_user(username, password):
    try:
        c.execute('INSERT INTO users(username, password) VALUES (?,?)', (username, password))
        conn.commit()
        return True
    except:
        return False

def login_user(username, password):
    c.execute('SELECT * FROM users WHERE username =? AND password =?', (username, password))
    return c.fetchone()

# --- INTERFACE ---

# Sidebar : Authentification
if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False

with st.sidebar:
    st.markdown("### Espace Membre")
    if not st.session_state['logged_in']:
        choice = st.radio("Option", ["Connexion", "Inscription"])
        user = st.text_input("Identifiant (bucque Li prom's)")
        password = st.text_input("Mot de passe", type='password')
        
        if choice == "Inscription":
            if st.button("Créer compte"):
                if add_user(user, password):
                    st.success("Compte créé ! Connectez-vous.")
                else:
                    st.error("Identifiant pris.")
        else:
            if st.button("Se connecter"):
                if login_user(user, password):
                    st.session_state['logged_in'] = True
                    st.session_state['user'] = user
                    st.rerun()
                else:
                    st.error("Erreur d'identifiants.")
    else:
        st.write(f"Bonjour, **{st.session_state['user']}** 👋")
        if st.button("Se déconnecter"):
            st.session_state['logged_in'] = False
            st.rerun()

# --- CONTENU PRINCIPAL ---
st.title("🚲 Veloy - Gadz")
st.markdown("Faites chauffez vos giboles pour préparer SKZ.")

if st.session_state['logged_in']:
    
    # 1. FORMULAIRE DE RÉSERVATION
    st.subheader("📅 Nouvelle Réservation")
    
    bikes = ["Vélo 1", "Vélo 2", "Vélo 3", "Vélo 4"]
    
    col1, col2 = st.columns(2)
    with col1:
        bike_choice = st.selectbox("Choisir un vélo", bikes)
        # On met la date par défaut à aujourd'hui
        date_choice = st.date_input("Date de l'emprunt", value=datetime.today())
    
    with col2:
        start_time = st.time_input("Heure de début", value=time(9, 0))
        duration = st.number_input("Durée (heures)", min_value=0.5, max_value=24.0, step=0.5, value=1.0)

    # Calcul des dates
    start_dt = datetime.combine(date_choice, start_time)
    end_dt = start_dt + timedelta(hours=duration)

    st.info(f"Créneau demandé : **{start_dt.strftime('%H:%M')}** à **{end_dt.strftime('%H:%M')}** ({date_choice.strftime('%d/%m')})")

    if st.button("Valider la réservation"):
        if end_dt <= start_dt:
            st.error("L'heure de fin doit être après l'heure de début !")
        else:
            success = make_reservation(bike_choice, st.session_state['user'], start_dt, end_dt)
            if success:
                st.success(f"✅ Réservé ! Vous avez le {bike_choice}.")
                st.rerun()
            else:
                st.error("⚠️ Ce vélo est déjà pris sur ce créneau (tu sais pas lire !?).")

    st.divider()

    # 2. MES RÉSERVATIONS (CORRIGÉ : AFFICHE TOUT)
    st.markdown("### 🎫 Mes réservations")
    LOCK_CODES = {
        "Vélo 1": "0225",
        "Vélo 2": "0225",
        "Vélo 3": "0225",
        "Vélo 4": "0225"
    }
    
    my_res = c.execute("""
        SELECT id, bike_id, start_dt, end_dt 
        FROM reservations 
        WHERE username=? 
        ORDER BY start_dt DESC
    """, (st.session_state['user'],)).fetchall()

    if my_res:
        for res in my_res:
            res_id = res[0]
            bike_name = res[1]
            s_dt = datetime.fromisoformat(res[2])
            e_dt = datetime.fromisoformat(res[3])
            
            # Récupération du code (ou "????" si le vélo n'est pas dans la liste)
            code = LOCK_CODES.get(bike_name, "????")

            # On affiche une carte pour chaque réservation
            with st.container():
                col_text, col_act = st.columns([4, 1])
                with col_text:
                    # LE FORMAT QUE VOUS AVEZ DEMANDÉ 👇
                    st.info(f"🚲 **{bike_name}** | 🔒 Code du cadenas : **{code}** | 📅 Le {s_dt.strftime('%d/%m/%Y')} de {s_dt.strftime('%H:%M')} à {e_dt.strftime('%H:%M')}")
                with col_act:
                    if st.button("Annuler", key=f"del_{res_id}", type="primary"):
                        cancel_reservation(res_id)
                        st.success("Réservation annulée !")
                        st.rerun()
    else:
        st.info("Bah alors ça RIDE pas 🤙")

    # 3. PLANNING GÉNÉRAL
    st.subheader("🗓️ Planning global des réservations")
    
    res_data = c.execute("SELECT bike_id, start_dt, end_dt, username FROM reservations ORDER BY start_dt DESC").fetchall()
    
    if res_data:
        clean_data = []
        for r in res_data:
            s = datetime.fromisoformat(r[1])
            e = datetime.fromisoformat(r[2])
            clean_data.append({
                "Vélo": r[0],
                "Début": s.strftime('%d/%m %H:%M'),
                "Fin": e.strftime('%d/%m %H:%M'),
                "Réservé par": r[3]
            })
        st.dataframe(pd.DataFrame(clean_data), use_container_width=True)
    else:
        st.write("Le planning est vide.")

else:
    st.warning("🔒 OH FADA IDENTIFIE TOI D'ABORD.")

# --- PIED DE PAGE ---
st.markdown("<br><br><br>", unsafe_allow_html=True)
st.markdown("---")
col_f1, col_f2 = st.columns([1.5, 4]) 

with col_f1:
    # Logo Arts et Métiers (URL publique Wikimedia)
    st.image("asset/Amtradszaloeil-modified.png", width=80)

with col_f2:
    st.markdown("""
    **Veloy - Gadz** Une initiative lars tradz pour évacuer les bières de vos coin².  
    *Développé avec ❤️ par Seratr1 71Li225 et K'sséne 148Li224*
    """)

















