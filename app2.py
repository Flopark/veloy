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
st.set_page_config(page_title="Veloy Gadz", page_icon="🚲")

# --- CONFIGURATION BASE DE DONNÉES ---
conn = sqlite3.connect('velos_ecole.db', check_same_thread=False)
c = conn.cursor()

def create_tables():
    # On ajoute start_dt et end_dt (datetime stockés en texte ISO)
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
    """
    Vérifie si le créneau demandé chevauche une réservation existante.
    Logique: Un chevauchement existe si (StartA < EndB) et (EndA > StartB)
    """
    # On récupère toutes les résas futures pour ce vélo
    c.execute('SELECT start_dt, end_dt FROM reservations WHERE bike_id=?', (bike_id,))
    existing_resas = c.fetchall()
    
    for start_str, end_str in existing_resas:
        existing_start = datetime.fromisoformat(start_str)
        existing_end = datetime.fromisoformat(end_str)
        
        # Vérification mathématique du chevauchement
        if new_start < existing_end and new_end > existing_start:
            return True # Il y a conflit
    return False

def make_reservation(bike_id, username, start_dt, end_dt):
    if check_overlap(bike_id, start_dt, end_dt):
        return False
    else:
        c.execute('INSERT INTO reservations(bike_id, username, start_dt, end_dt) VALUES (?,?,?,?)', 
                  (bike_id, username, start_dt.isoformat(), end_dt.isoformat()))
        conn.commit()
        return True

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
        user = st.text_input("Identifiant")
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
st.markdown("Réservez un vélo gratuitement pour vos déplacements.")

if st.session_state['logged_in']:
    
    st.subheader("📅 Nouvelle Réservation")
    
    # Liste des vélos
    bikes = ["Vélo 1", "Vélo 2", "Vélo 3", "Vélo 4"]
    
    col1, col2 = st.columns(2)
    with col1:
        bike_choice = st.selectbox("Choisir un vélo", bikes)
        date_choice = st.date_input("Date de l'emprunt", min_value=datetime.today())
    
    with col2:
        start_time = st.time_input("Heure de début", value=time(9, 0))
        # Durée en heures (step 0.5 = 30 minutes)
        duration = st.number_input("Durée (heures)", min_value=0.5, max_value=24.0, step=0.5, value=1.0)

    # Calcul des datetime complets
    start_dt = datetime.combine(date_choice, start_time)
    end_dt = start_dt + timedelta(hours=duration)

    st.info(f"Créneau demandé : **{start_dt.strftime('%H:%M')}** à **{end_dt.strftime('%H:%M')}** ({date_choice})")

    if st.button("Valider la réservation"):
        if end_dt <= start_dt:
            st.error("L'heure de fin doit être après l'heure de début !")
        else:
            success = make_reservation(bike_choice, st.session_state['user'], start_dt, end_dt)
            if success:
                st.success(f"✅ Réservé ! Vous avez le {bike_choice}.")
            else:
                st.error("⚠️ Ce vélo est déjà pris sur une partie de ce créneau. Vérifiez le planning ci-dessous.")

    st.divider()
    
    # Affichage du planning visuel
    st.subheader("🗓️ Planning des réservations en cours")
    
    # Récupération des données pour affichage
    res_data = c.execute("SELECT bike_id, start_dt, end_dt, username FROM reservations ORDER BY start_dt DESC").fetchall()
    
    if res_data:
        # Transformation en DataFrame pour un affichage propre
        clean_data = []
        for r in res_data:
            s = datetime.fromisoformat(r[1])
            e = datetime.fromisoformat(r[2])
            clean_data.append({
                "Vélo": r[0],
                "Début": s.strftime('%d/%m %H:%M'),
                "Fin": e.strftime('%d/%m %H:%M'),
                "Utilisateur": r[3]
            })
        st.dataframe(pd.DataFrame(clean_data), use_container_width=True)
    else:
        st.write("Aucune réservation pour le moment.")

else:
    st.warning("Veuillez vous identifier dans le menu de gauche pour accéder aux vélos.")

# --- PIED DE PAGE (FOOTER) ---
st.markdown("---")
col_f1, col_f2 = st.columns([1, 4])

with col_f1:
    # Logo Arts et Métiers (URL publique Wikimedia)
    st.image("https://drive.google.com/file/d/1CmbtFBjpVbxw7u4KNI4qccM_esby74eV/view?usp=sharing", width=80)

with col_f2:
    st.markdown("""
    **Veloy - Gadz** Une initiative lars tradz pour évacuer les bières de vos coin².  
    *Développé avec ❤️ par Seratr1 ??Li225 et K'sséne 148Li224*
    """)







