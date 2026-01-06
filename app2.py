# -*- coding: utf-8 -*-
"""
Created on Thu Dec 25 00:04:15 2025

@author: march
"""
import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime, timedelta

# --- CONFIGURATION DE LA BASE DE DONNÉES ---
conn = sqlite3.connect('velos_ecole.db', check_same_thread=False)
c = conn.cursor()

def create_tables():
    c.execute('CREATE TABLE IF NOT EXISTS users(username TEXT PRIMARY KEY, password TEXT)')
    c.execute('CREATE TABLE IF NOT EXISTS reservations(id INTEGER PRIMARY KEY, bike_id TEXT, username TEXT, date DATE, slot TEXT)')
    # Simulation de vélos (on peut aussi les mettre en BDD)
    conn.commit()

create_tables()

# --- FONCTIONS UTILITAIRES ---
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

def make_reservation(bike_id, username, date, slot):
    # Vérifier si déjà réservé
    c.execute('SELECT * FROM reservations WHERE bike_id=? AND date=? AND slot=?', (bike_id, date, slot))
    if c.fetchone():
        return False
    else:
        c.execute('INSERT INTO reservations(bike_id, username, date, slot) VALUES (?,?,?,?)', (bike_id, username, date, slot))
        conn.commit()
        return True

# --- INTERFACE STREAMLIT ---
st.title("🚲 VeloShare - Réservation École")

if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False

# Sidebar pour la connexion
with st.sidebar:
    if not st.session_state['logged_in']:
        menu = ["Connexion", "Inscription"]
        choice = st.selectbox("Menu", menu)
        
        user = st.text_input("Identifiant")
        password = st.text_input("Mot de passe", type='password')
        
        if choice == "Inscription":
            if st.button("Créer mon compte"):
                if add_user(user, password):
                    st.success("Compte créé ! Connectez-vous.")
                else:
                    st.error("Cet identifiant existe déjà.")
        else:
            if st.button("Se connecter"):
                if login_user(user, password):
                    st.session_state['logged_in'] = True
                    st.session_state['user'] = user
                    st.rerun()
                else:
                    st.error("Identifiant ou mot de passe incorrect.")
    else:
        st.write(f"Bienvenue, **{st.session_state['user']}** !")
        if st.button("Se déconnecter"):
            st.session_state['logged_in'] = False
            st.rerun()

# --- CONTENU PRINCIPAL ---
if st.session_state['logged_in']:
    st.header("Réserver un vélo")
    
    # Paramètres de réservation
    bikes = ["Vélo Rouge", "Vélo Bleu", "VTT Flash", "Vélo Électrique"]
    slots = ["08:00 - 10:00", "10:00 - 12:00", "12:00 - 14:00", "14:00 - 16:00", "16:00 - 18:00"]
    
    col1, col2, col3 = st.columns(3)
    with col1:
        bike_choice = st.selectbox("Choisir un vélo", bikes)
    with col2:
        date_choice = st.date_input("Date", min_value=datetime.today())
    with col3:
        slot_choice = st.selectbox("Créneau horaire", slots)
        
    if st.button("Confirmer la réservation"):
        if make_reservation(bike_choice, st.session_state['user'], str(date_choice), slot_choice):
            st.success(f"Réservation confirmée pour le {bike_choice} !")
        else:
            st.error("❌ Désolé, ce vélo est déjà réservé pour ce créneau.")

    st.divider()
    st.subheader("Planning des réservations")
    df = pd.read_sql_query("SELECT bike_id, date, slot, username FROM reservations", conn)
    st.table(df)

else:
    st.info("Veuillez vous connecter sur le panneau de gauche pour voir les disponibilités et réserver.")



