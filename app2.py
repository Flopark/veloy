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
def cancel_reservation(reservation_id):
    c.execute("DELETE FROM reservations WHERE id=?", (reservation_id,))
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
st.title("🚲 VeloShare - Arts et Métiers")
st.markdown("Réservez un vélo gratuitement pour vos déplacements.")

if st.session_state['logged_in']:
    
    # ---------------------------------------------------------
    # 1. FORMULAIRE DE RÉSERVATION
    # ---------------------------------------------------------
    st.subheader("📅 Nouvelle Réservation")
    
    bikes = ["VTT Rockrider", "Vélo de ville Peugeot", "Vélo Électrique", "Tandem"]
    
    col1, col2 = st.columns(2)
    with col1:
        bike_choice = st.selectbox("Choisir un vélo", bikes)
        date_choice = st.date_input("Date de l'emprunt", min_value=datetime.today())
    
    with col2:
        start_time = st.time_input("Heure de début", value=time(9, 0))
        duration = st.number_input("Durée (heures)", min_value=0.5, max_value=24.0, step=0.5, value=1.0)

    # Calcul des horaires
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
                st.rerun() # On recharge pour mettre à jour les tableaux
            else:
                st.error("⚠️ Ce vélo est déjà pris sur ce créneau.")

    # ---------------------------------------------------------
    # 2. MES RÉSERVATIONS (AVEC ANNULATION)
    # ---------------------------------------------------------
    st.markdown("### 🎫 Mes réservations actives")
    
    # On cherche les réservations de l'utilisateur connecté
    my_res = c.execute("""
        SELECT id, bike_id, start_dt, end_dt 
        FROM reservations 
        WHERE username=? 
        ORDER BY start_dt
    """, (st.session_state['user'],)).fetchall()

    if my_res:
        # On affiche les réservations sous forme de cartes
        for res in my_res:
            res_id = res[0]
            bike_name = res[1]
            s_dt = datetime.fromisoformat(res[2])
            e_dt = datetime.fromisoformat(res[3])

            # Affichage conditionnel (Futur vs Passé)
            if e_dt > datetime.now():
                with st.expander(f"{bike_name} | {s_dt.strftime('%d/%m')} de {s_dt.strftime('%H:%M')} à {e_dt.strftime('%H:%M')}", expanded=True):
                    c1, c2 = st.columns([4, 1])
                    with c1:
                        st.caption("Cliquez sur Annuler pour libérer le vélo.")
                    with c2:
                        # Bouton rouge pour annuler
                        if st.button("Annuler 🗑️", key=f"cancel_{res_id}", type="primary"):
                            cancel_reservation(res_id)
                            st.toast("Réservation annulée !", icon="🗑️")
                            st.rerun()
    else:
        st.info("Vous n'avez aucune réservation à venir.")

    st.divider()
    
    # ---------------------------------------------------------
    # 3. PLANNING GÉNÉRAL (POUR VOIR LA DISPONIBILITÉ)
    # ---------------------------------------------------------
    st.subheader("🗓️ Planning global des réservations")
    
    res_data = c.execute("SELECT bike_id, start_dt, end_dt, username FROM reservations ORDER BY start_dt DESC").fetchall()
    
    if res_data:
        clean_data = []
        for r in res_data:
            s = datetime.fromisoformat(r[1])
            e = datetime.fromisoformat(r[2])
            # On n'affiche que les réservations futures ou en cours pour alléger le tableau
            if e > datetime.now() - timedelta(hours=24):
                clean_data.append({
                    "Vélo": r[0],
                    "Début": s.strftime('%d/%m %H:%M'),
                    "Fin": e.strftime('%d/%m %H:%M'),
                    "Réservé par": r[3]
                })
        
        if clean_data:
            st.dataframe(pd.DataFrame(clean_data), use_container_width=True)
        else:
            st.write("Le planning est vide pour les prochains jours.")
    else:
        st.write("Aucune réservation enregistrée.")

else:
    st.warning("🔒 Veuillez vous identifier dans le menu de gauche pour accéder à la réservation.")
# --- PIED DE PAGE (FOOTER) ---
st.markdown("---")
col_f1, col_f2 = st.columns([1, 4])

with col_f1:
    # Logo Arts et Métiers (URL publique Wikimedia)
    st.image("asset/Amtradszaloeil-modified.png", width=80)

with col_f2:
    st.markdown("""
    **Veloy - Gadz** Une initiative lars tradz pour évacuer les bières de vos coin².  
    *Développé avec ❤️ par Seratr1 ??Li225 et K'sséne 148Li224*
    """)










