# app.py - NO FIREBASE VERSION
import streamlit as st
import pandas as pd
from datetime import datetime

st.set_page_config(page_title="🌾 Fertilizer App", page_icon="🌾", layout="wide")

# DEMO DATA (no database needed)
ZONES = [
    {"name": "Jimma Zone", "woredas": 17, "farmers": 5400, "assigned": 50000, "distributed": 32000},
    {"name": "West Wellega", "woredas": 22, "farmers": 7200, "assigned": 75000, "distributed": 48000},
]

WOREDAS = [
    {"name": "Jimma Woreda", "kebeles": 8, "farmers": 1240, "assigned": 5000, "distributed": 3200},
    {"name": "Seka Woreda", "kebeles": 6, "farmers": 980, "assigned": 4000, "distributed": 2800},
]

KEBELES = [
    {"name": "Kebele 01", "villages": 3, "farmers": 156, "assigned": 600, "distributed": 450},
    {"name": "Kebele 02", "villages": 4, "farmers": 198, "assigned": 800, "distributed": 620},
    {"name": "Kebele 03", "villages": 3, "farmers": 234, "assigned": 800, "distributed": 520},
]

FARMERS = [
    {"name": "Abebe Kebede", "nid": "NID-1985-4455667", "land": 8.0, "entitled": 16, "taken": 6},
    {"name": "Fatuma Mohamed", "nid": "NID-1990-7788990", "land": 5.5, "entitled": 11, "taken": 0},
    {"name": "Dawit Tesfaye", "nid": "NID-1982-3344556", "land": 12.0, "entitled": 24, "taken": 10},
]

# SESSION
if "user" not in st.session_state:
    st.session_state.user = None

# LOGIN
def login():
    st.title("🌾 Fertilizer Distribution System")
    st.caption("Government of Ethiopia")
    
    c1, c2, c3 = st.columns([1,2,1])
    with c2:
        role = st.selectbox("Role", ["regional", "zonal", "woreda", "da"],
                           format_func=lambda x: {"regional":"🗺️ Regional", "zonal":"🏛️ Zonal", "woreda":"📍 Woreda", "da":"👤 DA"}[x])
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        
        if st.button("🔐 Sign In", use_container_width=True):
            if password == "admin123":
                names = {"regional":"Ato Girma", "zonal":"Ato Kebede", "woreda":"Ato Tadesse", "da":"Dawit"}
                st.session_state.user = {"role": role, "name": names[role]}
                st.rerun()
            else:
                st.error("Password: admin123")

# DASHBOARDS
def regional():
    st.sidebar.title(f"🗺️ {st.session_state.user['name']}")
    menu = st.sidebar.radio("Menu", ["Dashboard", "Assign Zone", "Reports"])
    if st.sidebar.button("Logout"): st.session_state.user = None; st.rerun()
    
    if menu == "Dashboard":
        st.header("📊 Regional Dashboard")
        c = st.columns(4)
        c[0].metric("Zones", len(ZONES))
        c[1].metric("Woredas", sum(z['woredas'] for z in ZONES))
        c[2].metric("Farmers", sum(z['farmers'] for z in ZONES))
        c[3].metric("Fertilizer", f"{sum(z['assigned'] for z in ZONES):,}")
        st.dataframe(pd.DataFrame(ZONES), hide_index=True, use_container_width=True)
    
    elif menu == "Assign Zone":
        st.header("📦 Assign Zone")
        z = st.selectbox("Zone", [z['name'] for z in ZONES])
        amt = st.number_input("Bags", value=10000, step=100)
        if st.button("Assign"): st.success(f"✅ {amt:,} bags to {z}")

def zonal():
    st.sidebar.title(f"🏛️ {st.session_state.user['name']}")
    menu = st.sidebar.radio("Menu", ["Dashboard", "Assign Woreda"])
    if st.sidebar.button("Logout"): st.session_state.user = None; st.rerun()
    
    st.header("📊 Zonal Dashboard")
    c = st.columns(3)
    c[0].metric("Woredas", len(WOREDAS))
    c[1].metric("Farmers", sum(w['farmers'] for w in WOREDAS))
    c[2].metric("Stock", sum(w['assigned'] for w in WOREDAS))
    st.dataframe(pd.DataFrame(WOREDAS), hide_index=True, use_container_width=True)

def woreda():
    st.sidebar.title(f"📍 {st.session_state.user['name']}")
    menu = st.sidebar.radio("Menu", ["Dashboard", "Register Worker", "Assign Kebele"])
    if st.sidebar.button("Logout"): st.session_state.user = None; st.rerun()
    
    st.header("📊 Woreda Dashboard")
    c = st.columns(3)
    c[0].metric("Kebeles", len(KEBELES))
    c[1].metric("Farmers", sum(k['farmers'] for k in KEBELES))
    c[2].metric("Stock", sum(k['assigned'] for k in KEBELES))
    
    if menu == "Register Worker":
        with st.form("reg"):
            st.text_input("Name")
            st.text_input("Username")
            st.selectbox("Kebele", [k['name'] for k in KEBELES])
            if st.form_submit_button("Register"): st.success("✅ Worker registered!")

def da():
    st.sidebar.title(f"👤 {st.session_state.user['name']}")
    menu = st.sidebar.radio("Menu", ["Dashboard", "Register Farmer", "Distribute"])
    if st.sidebar.button("Logout"): st.session_state.user = None; st.rerun()
    
    st.header("📊 DA Dashboard")
    c = st.columns(3)
    c[0].metric("Farmers", len(FARMERS))
    c[1].metric("Entitled", sum(f['entitled'] for f in FARMERS))
    c[2].metric("Distributed", sum(f['taken'] for f in FARMERS))
    
    if menu == "Register Farmer":
        with st.form("reg"):
            st.text_input("National ID")
            name = st.text_input("Full Name")
            land = st.number_input("Land (ha)", value=5.0)
            entitled = int(land * 2)
            st.success(f"🧪 Auto: {entitled} bags")
            if st.form_submit_button("Register"): st.success(f"✅ {name} registered!")

# MAIN
if st.session_state.user is None:
    login()
else:
    r = st.session_state.user['role']
    if r == "regional": regional()
    elif r == "zonal": zonal()
    elif r == "woreda": woreda()
    elif r == "da": da()
