import sqlite3
import random
from io import StringIO
import streamlit as st
import pandas as pd

# ==================== DATABASE INITIALIZATION & AUTO-SEEDING ====================
DB_FILE = "fertilizer_distribution.db"

def get_db_connection():
    conn = sqlite3.connect(DB_FILE, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("PRAGMA foreign_keys = ON;")
    
    # Hierarchy Tables with Quota Allocations
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS regions (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            total_quota INTEGER DEFAULT 10000
        )
    """)
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS zones (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            region_id TEXT NOT NULL,
            fertilizer_quota INTEGER DEFAULT 0,
            FOREIGN KEY (region_id) REFERENCES regions (id)
        )
    """)
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS woredas (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            zone_id TEXT NOT NULL,
            fertilizer_quota INTEGER DEFAULT 0,
            FOREIGN KEY (zone_id) REFERENCES zones (id)
        )
    """)
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS kebeles (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            woreda_id TEXT NOT NULL,
            da_name TEXT NOT NULL,
            assistant_name TEXT NOT NULL,
            fertilizer_quota INTEGER DEFAULT 0,
            FOREIGN KEY (woreda_id) REFERENCES woredas (id)
        )
    """)
    
    # Farmers Table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS farmers (
            id TEXT PRIMARY KEY,
            national_id TEXT UNIQUE NOT NULL,
            name TEXT NOT NULL,
            kebele_id TEXT NOT NULL,
            village TEXT NOT NULL,
            land_size REAL NOT NULL,
            phone TEXT NOT NULL,
            fee_verified INTEGER DEFAULT 0,
            status TEXT DEFAULT 'In Queue',
            group_id INTEGER,
            FOREIGN KEY (kebele_id) REFERENCES kebeles (id)
        )
    """)
    
    # Safe Idempotent Auto-Seeding
    cursor.execute("INSERT OR IGNORE INTO regions VALUES ('REG-001', 'Oromia Region', 10000)")
    cursor.execute("INSERT OR IGNORE INTO zones VALUES ('ZN-001', 'Jimma Zone', 'REG-001', 3000)")
    cursor.execute("INSERT OR IGNORE INTO zones VALUES ('ZN-002', 'West Shoa Zone', 'REG-001', 2000)")
    cursor.execute("INSERT OR IGNORE INTO woredas VALUES ('WRD-001', 'Manna Woreda', 'ZN-001', 1500)")
    cursor.execute("INSERT OR IGNORE INTO woredas VALUES ('WRD-002', 'Goma Woreda', 'ZN-001', 1000)")
    cursor.execute("INSERT OR IGNORE INTO kebeles VALUES ('KEB-001', 'Yebu Kebele', 'WRD-001', 'Alemayehu Tadesse', 'Getachew Bekele', 500)")
    
    seed_farmers = [
        ('FAR-001', 'ETH-10293847', 'Abebe Bikila', 'KEB-001', 'Gudeta', 2.5, '+251911000000', 1, 'Registered', 1),
        ('FAR-002', 'ETH-20394857', 'Kebede Tessema', 'KEB-001', 'Gudeta', 1.8, '+251911000001', 0, 'In Queue', None),
        ('FAR-003', 'ETH-30495867', 'Almaz Ayana', 'KEB-001', 'Boreta', 3.0, '+251911000002', 1, 'Registered', 1),
        ('FAR-004', 'ETH-40596877', 'Tirunesh Dibaba', 'KEB-001', 'Boreta', 1.2, '+251911000003', 0, 'In Queue', None),
        ('FAR-005', 'ETH-50697887', 'Haile Gebrselassie', 'KEB-001', 'Gudeta', 4.1, '+251911000004', 1, 'Registered', None),
    ]
    cursor.executemany("INSERT OR IGNORE INTO farmers VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", seed_farmers)
        
    conn.commit()
    conn.close()

init_db()

# ==================== PAGE CONFIG & STYLING ====================
st.set_page_config(
    page_title="Fertilizer Distribution Management System",
    page_icon="🌾",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
    <style>
    .main { background-color: #f8fafc; }
    .hero-banner {
        background: linear-gradient(135deg, #1e3a8a 0%, #0d9488 100%);
        padding: 24px 32px;
        border-radius: 16px;
        color: white;
        box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.1);
        margin-bottom: 25px;
    }
    .hero-banner h1 { color: #ffffff !important; font-weight: 700 !important; margin-bottom: 4px !important; }
    .hero-banner p { color: #e2e8f0 !important; font-size: 1.05rem; margin-bottom: 0px !important; }
    div[data-testid="stMetric"] {
        background-color: #ffffff;
        padding: 18px 24px;
        border-radius: 12px;
        border: 1px solid #e2e8f0;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05);
    }
    div[data-testid="stMetricLabel"] { font-weight: 600; color: #64748b; }
    div[data-testid="stMetricValue"] { color: #0f172a; font-weight: 700; }
    .stButton>button { border-radius: 8px !important; font-weight: 600 !important; }
    </style>
""", unsafe_allow_html=True)

def get_app_url():
    try:
        host = st.context.headers.get("Host", "")
        if host:
            return f"https://{host}"
    except Exception:
        pass
    return "http://localhost:8501"

# ==================== SESSION STATE & URL PARSING ====================
if "user" not in st.session_state:
    st.session_state.user = None

query_params = st.query_params
if "role" in query_params and st.session_state.user is None:
    role = query_params["role"]
    if role == "regional_manager":
        st.session_state.user = {"role": "regional_manager", "name": "Regional Director", "region_id": query_params.get("region_id", "REG-001")}
    elif role == "zonal_manager":
        st.session_state.user = {"role": "zonal_manager", "name": "Zonal Representative", "zone_id": query_params.get("zone_id", "ZN-001")}
    elif role == "woreda_manager":
        st.session_state.user = {"role": "woreda_manager", "name": "Woreda Administrator", "woreda_id": query_params.get("woreda_id", "WRD-001")}
    elif role == "da_worker":
        st.session_state.user = {"role": "da_worker", "name": query_params.get("da_name", "Development Agent"), "kebele_id": query_params.get("kebele_id", "KEB-001")}

def logout():
    st.session_state.user = None
    st.query_params.clear()
    st.rerun()

# ==================== 1. REGIONAL MANAGER PORTAL ====================
def show_regional_manager():
    st.markdown("""
        <div class="hero-banner">
            <h1>🗺️ Regional Executive Portal</h1>
            <p>Allocate fertilizer quotas to Zones, register Zones, and oversee all regional data.</p>
        </div>
    """, unsafe_allow_html=True)

    conn = get_db_connection()
    region = conn.execute("SELECT * FROM regions WHERE id = ?", (st.session_state.user.get("region_id", "REG-001"),)).fetchone()
    zones = conn.execute("SELECT * FROM zones WHERE region_id = ?", (region["id"],)).fetchall()
    
    total_assigned_zones = sum([z["fertilizer_quota"] for z in zones]) if zones else 0
    remaining_reg_quota = region["total_quota"] - total_assigned_zones

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Region Total Stock", f"{region['total_quota']} Qtl")
    c2.metric("Allocated to Zones", f"{total_assigned_zones} Qtl")
    c3.metric("Unallocated Stock", f"{remaining_reg_quota} Qtl")
    c4.metric("Active Zones", len(zones))

    st.markdown("---")

    tab1, tab2, tab3 = st.tabs(["📦 Zone Quota Allocation", "➕ Register Zone & Link", "📊 Full Region Overview (All Data)"])

    with tab1:
        st.subheader("Assign / Update Fertilizer Quota for Zones")
        if zones:
            with st.form("allocate_zone_quota"):
                sel_zone = st.selectbox("Select Zone", [dict(z) for z in zones], format_func=lambda x: f"{x['name']} (Current Quota: {x['fertilizer_quota']} Qtl)")
                new_quota = st.number_input("Set Fertilizer Quota (Quintals)", min_value=0, max_value=region["total_quota"], value=sel_zone["fertilizer_quota"], step=50)
                
                if st.form_submit_button("Update Zone Quota", use_container_width=True):
                    conn.execute("UPDATE zones SET fertilizer_quota = ? WHERE id = ?", (new_quota, sel_zone["id"]))
                    conn.commit()
                    st.success(f"Updated quota for {sel_zone['name']} to {new_quota} Quintals!")
                    st.rerun()
        else:
            st.info("No zones registered yet.")

    with tab2:
        left_col, right_col = st.columns([1.5, 1])
        with left_col:
            st.subheader("➕ Register New Zone")
            with st.form("add_zone_form"):
                z_name = st.text_input("Zone Name", placeholder="e.g., Jimma Zone")
                initial_quota = st.number_input("Initial Quota (Quintals)", min_value=0, value=500, step=50)
                if st.form_submit_button("Register Zone", use_container_width=True) and z_name:
                    new_id = f"ZN-00{len(zones) + 1}"
                    conn.execute("INSERT INTO zones VALUES (?, ?, ?, ?)", (new_id, z_name, region["id"], initial_quota))
                    conn.commit()
                    st.success(f"Zone '{z_name}' registered successfully!")
                    st.rerun()

        with right_col:
            st.subheader("🔗 Send Link to Zonal Manager")
            if zones:
                selected_zone = st.selectbox("Select Zone for Link", [dict(z) for z in zones], format_func=lambda x: x["name"])
                generated_link = f"{get_app_url()}/?role=zonal_manager&zone_id={selected_zone['id']}"
                st.code(generated_link, language="text")
                st.info("Share this access link with the assigned Zonal Manager.")

    with tab3:
        st.subheader("🌐 Complete Regional Data Breakdown")
        
        st.write("#### 🏛️ Zonal Allocations")
        st.dataframe(pd.DataFrame([dict(z) for z in zones]), use_container_width=True, hide_index=True)
        
        st.write("#### 📍 All Woredas in Region")
        all_woredas = conn.execute("SELECT w.id, w.name AS woreda_name, z.name AS zone_name, w.fertilizer_quota FROM woredas w JOIN zones z ON w.zone_id = z.id").fetchall()
        st.dataframe(pd.DataFrame([dict(w) for w in all_woredas]), use_container_width=True, hide_index=True)

        st.write("#### 🏡 All Kebeles & Field Teams")
        all_kebeles = conn.execute("SELECT k.id, k.name AS kebele_name, w.name AS woreda_name, k.da_name, k.fertilizer_quota FROM kebeles k JOIN woredas w ON k.woreda_id = w.id").fetchall()
        st.dataframe(pd.DataFrame([dict(k) for k in all_kebeles]), use_container_width=True, hide_index=True)

        st.write("#### 👨‍🌾 All Registered Farmers")
        all_farmers = conn.execute("SELECT f.id, f.national_id, f.name, k.name as kebele, f.village, f.land_size, f.fee_verified, f.status FROM farmers f JOIN kebeles k ON f.kebele_id = k.id").fetchall()
        st.dataframe(pd.DataFrame([dict(f) for f in all_farmers]), use_container_width=True, hide_index=True)

    conn.close()
    st.sidebar.markdown("### User Session")
    st.sidebar.info(f"Logged in as: **{st.session_state.user['name']}**")
    st.sidebar.button("🚪 Sign Out", on_click=logout, use_container_width=True)

# ==================== 2. ZONAL MANAGER PORTAL ====================
def show_zonal_manager():
    st.markdown("""
        <div class="hero-banner">
            <h1>🏛️ Zonal Operations Portal</h1>
            <p>Allocate assigned Zonal stock to Woredas and oversee all Zonal level field data.</p>
        </div>
    """, unsafe_allow_html=True)

    conn = get_db_connection()
    zone_id = st.session_state.user.get("zone_id", "ZN-001")
    zone = conn.execute("SELECT * FROM zones WHERE id = ?", (zone_id,)).fetchone()
    woredas = conn.execute("SELECT * FROM woredas WHERE zone_id = ?", (zone_id,)).fetchall()

    total_assigned_woredas = sum([w["fertilizer_quota"] for w in woredas]) if woredas else 0
    remaining_zone_quota = zone["fertilizer_quota"] - total_assigned_woredas

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Zone Name", zone["name"])
    c2.metric("Assigned Zone Stock", f"{zone['fertilizer_quota']} Qtl")
    c3.metric("Allocated to Woredas", f"{total_assigned_woredas} Qtl")
    c4.metric("Unallocated Stock", f"{remaining_zone_quota} Qtl")

    st.markdown("---")

    tab1, tab2, tab3 = st.tabs(["📦 Woreda Quota Allocation", "➕ Register Woreda & Link", "📊 Zonal Data Overview"])

    with tab1:
        st.subheader("Assign / Update Fertilizer Quota for Woredas")
        if woredas:
            with st.form("allocate_woreda_quota"):
                sel_woreda = st.selectbox("Select Woreda", [dict(w) for w in woredas], format_func=lambda x: f"{x['name']} (Current Quota: {x['fertilizer_quota']} Qtl)")
                new_quota = st.number_input("Set Fertilizer Quota (Quintals)", min_value=0, max_value=zone["fertilizer_quota"], value=sel_woreda["fertilizer_quota"], step=20)
                
                if st.form_submit_button("Update Woreda Quota", use_container_width=True):
                    conn.execute("UPDATE woredas SET fertilizer_quota = ? WHERE id = ?", (new_quota, sel_woreda["id"]))
                    conn.commit()
                    st.success(f"Updated quota for {sel_woreda['name']} to {new_quota} Quintals!")
                    st.rerun()
        else:
            st.info("No woredas registered under this Zone.")

    with tab2:
        left_col, right_col = st.columns([1.5, 1])
        with left_col:
            st.subheader("➕ Register New Woreda")
            with st.form("add_woreda_form"):
                w_name = st.text_input("Woreda Name", placeholder="e.g., Manna Woreda")
                initial_quota = st.number_input("Initial Quota (Quintals)", min_value=0, value=200, step=20)
                if st.form_submit_button("Register Woreda", use_container_width=True) and w_name:
                    new_id = f"WRD-00{len(woredas) + 1}"
                    conn.execute("INSERT INTO woredas VALUES (?, ?, ?, ?)", (new_id, w_name, zone_id, initial_quota))
                    conn.commit()
                    st.success(f"Woreda '{w_name}' registered successfully!")
                    st.rerun()

        with right_col:
            st.subheader("🔗 Send Link to Woreda Manager")
            if woredas:
                selected_woreda = st.selectbox("Select Woreda", [dict(w) for w in woredas], format_func=lambda x: x["name"])
                generated_link = f"{get_app_url()}/?role=woreda_manager&woreda_id={selected_woreda['id']}"
                st.code(generated_link, language="text")
                st.info("Share this link with the assigned Woreda Manager.")

    with tab3:
        st.subheader("📊 Data Scoped to " + zone["name"])
        st.write("#### 📍 Woredas Allocation")
        st.dataframe(pd.DataFrame([dict(w) for w in woredas]), use_container_width=True, hide_index=True)

        st.write("#### 🏡 Kebeles in Zone")
        zone_kebeles = conn.execute("SELECT k.id, k.name as kebele_name, w.name as woreda_name, k.da_name, k.fertilizer_quota FROM kebeles k JOIN woredas w ON k.woreda_id = w.id WHERE w.zone_id = ?", (zone_id,)).fetchall()
        st.dataframe(pd.DataFrame([dict(k) for k in zone_kebeles]), use_container_width=True, hide_index=True)

        st.write("#### 👨‍🌾 Farmers in Zone")
        zone_farmers = conn.execute("SELECT f.id, f.national_id, f.name, k.name as kebele_name, f.land_size, f.fee_verified, f.status FROM farmers f JOIN kebeles k ON f.kebele_id = k.id JOIN woredas w ON k.woreda_id = w.id WHERE w.zone_id = ?", (zone_id,)).fetchall()
        st.dataframe(pd.DataFrame([dict(f) for f in zone_farmers]), use_container_width=True, hide_index=True)

    conn.close()
    st.sidebar.markdown("### User Session")
    st.sidebar.info(f"Logged in as: **{st.session_state.user['name']}**")
    st.sidebar.button("🚪 Sign Out", on_click=logout, use_container_width=True)

# ==================== 3. WOREDA MANAGER PORTAL ====================
def show_woreda_manager():
    st.markdown("""
        <div class="hero-banner">
            <h1>📍 Woreda Administration Portal</h1>
            <p>Allocate assigned Woreda quota to local Kebeles, set up DA field teams, and oversee Woreda data.</p>
        </div>
    """, unsafe_allow_html=True)

    conn = get_db_connection()
    woreda_id = st.session_state.user.get("woreda_id", "WRD-001")
    woreda = conn.execute("SELECT * FROM woredas WHERE id = ?", (woreda_id,)).fetchone()
    kebeles = conn.execute("SELECT * FROM kebeles WHERE woreda_id = ?", (woreda_id,)).fetchall()

    total_assigned_kebeles = sum([k["fertilizer_quota"] for k in kebeles]) if kebeles else 0
    remaining_woreda_quota = woreda["fertilizer_quota"] - total_assigned_kebeles

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Woreda Name", woreda["name"])
    c2.metric("Assigned Woreda Stock", f"{woreda['fertilizer_quota']} Qtl")
    c3.metric("Allocated to Kebeles", f"{total_assigned_kebeles} Qtl")
    c4.metric("Unallocated Stock", f"{remaining_woreda_quota} Qtl")

    st.markdown("---")

    tab1, tab2, tab3 = st.tabs(["📦 Kebele Quota Allocation", "➕ Register Kebele & Assign DA", "📊 Woreda Data Overview"])

    with tab1:
        st.subheader("Assign / Update Fertilizer Quota for Kebeles")
        if kebeles:
            with st.form("allocate_kebele_quota"):
                sel_kebele = st.selectbox("Select Kebele", [dict(k) for k in kebeles], format_func=lambda x: f"{x['name']} (DA: {x['da_name']} | Quota: {x['fertilizer_quota']} Qtl)")
                new_quota = st.number_input("Set Fertilizer Quota (Quintals)", min_value=0, max_value=woreda["fertilizer_quota"], value=sel_kebele["fertilizer_quota"], step=10)
                
                if st.form_submit_button("Update Kebele Quota", use_container_width=True):
                    conn.execute("UPDATE kebeles SET fertilizer_quota = ? WHERE id = ?", (new_quota, sel_kebele["id"]))
                    conn.commit()
                    st.success(f"Updated quota for {sel_kebele['name']} to {new_quota} Quintals!")
                    st.rerun()
        else:
            st.info("No kebeles registered under this Woreda.")

    with tab2:
        left_col, right_col = st.columns([1.5, 1])
        with left_col:
            st.subheader("➕ Register Kebele & Assign Field Team")
            with st.form("add_kebele_form"):
                k_name = st.text_input("Kebele Name", placeholder="e.g., Yebu Kebele")
                da_name = st.text_input("DA Name", placeholder="e.g., Alemayehu Tadesse")
                assistant_name = st.text_input("Assistant Name", placeholder="e.g., Getachew Bekele")
                f_quota = st.number_input("Assign Initial Quota (Quintals)", min_value=0, value=100, step=10)

                if st.form_submit_button("Register Kebele", use_container_width=True) and k_name and da_name:
                    new_id = f"KEB-00{len(kebeles) + 1}"
                    conn.execute("INSERT INTO kebeles VALUES (?, ?, ?, ?, ?, ?)", (new_id, k_name, woreda_id, da_name, assistant_name, f_quota))
                    conn.commit()
                    st.success(f"Kebele '{k_name}' registered successfully!")
                    st.rerun()

        with right_col:
            st.subheader("🔗 Send Link to DA Worker")
            if kebeles:
                selected_kebele = st.selectbox("Select Kebele", [dict(k) for k in kebeles], format_func=lambda x: f"{x['name']} (DA: {x['da_name']})")
                generated_link = f"{get_app_url()}/?role=da_worker&kebele_id={selected_kebele['id']}&da_name={selected_kebele['da_name']}"
                st.code(generated_link, language="text")
                st.info("Send this link to the assigned Development Agent (DA).")

    with tab3:
        st.subheader("📊 Data Scoped to " + woreda["name"])
        st.write("#### 🏡 Kebeles Overview")
        st.dataframe(pd.DataFrame([dict(k) for k in kebeles]), use_container_width=True, hide_index=True)

        st.write("#### 👨‍🌾 Farmers in Woreda")
        woreda_farmers = conn.execute("SELECT f.id, f.national_id, f.name, k.name as kebele_name, f.village, f.land_size, f.fee_verified, f.status FROM farmers f JOIN kebeles k ON f.kebele_id = k.id WHERE k.woreda_id = ?", (woreda_id,)).fetchall()
        st.dataframe(pd.DataFrame([dict(f) for f in woreda_farmers]), use_container_width=True, hide_index=True)

    conn.close()
    st.sidebar.markdown("### User Session")
    st.sidebar.info(f"Logged in as: **{st.session_state.user['name']}**")
    st.sidebar.button("🚪 Sign Out", on_click=logout, use_container_width=True)

# ==================== 4. DA WORKER PORTAL ====================
def show_da_worker():
    st.markdown("""
        <div class="hero-banner">
            <h1>🌾 Field Operations & DA Portal</h1>
            <p>Verify fees, register farmers, manage queues, and construct verified distribution groups.</p>
        </div>
    """, unsafe_allow_html=True)

    conn = get_db_connection()
    kebele_id = st.session_state.user.get("kebele_id", "KEB-001")
    kebele_info = conn.execute("SELECT * FROM kebeles WHERE id = ?", (kebele_id,)).fetchone()

    if kebele_info:
        c1, c2, c3 = st.columns(3)
        c1.metric("Kebele Name", kebele_info["name"])
        c2.metric("Assigned Assistant", kebele_info["assistant_name"])
        c3.metric("Fertilizer Quota Stock", f"{kebele_info['fertilizer_quota']} Quintals")

    st.sidebar.markdown("### DA Navigation")
    menu = st.sidebar.radio("Select Module", [
        "💳 Fee Verification Dashboard",
        "📝 Register Farmer", 
        "⏳ Verified Farmer Queue", 
        "✅ Registered Farmers Directory", 
        "🎲 Distribution Grouping & CSV"
    ])

    if menu == "💳 Fee Verification Dashboard":
        st.subheader("💳 DA Fee Verification Dashboard")
        st.write("Search, verify, or revoke farmer service fee verification statuses.")

        search_id = st.text_input("🔍 Search Farmer by National ID or Name", placeholder="e.g., ETH-10293847 or Abebe")

        if search_id:
            results = conn.execute("SELECT * FROM farmers WHERE kebele_id = ? AND (national_id LIKE ? OR name LIKE ?)", (kebele_id, f"%{search_id}%", f"%{search_id}%")).fetchall()
        else:
            results = conn.execute("SELECT * FROM farmers WHERE kebele_id = ?", (kebele_id,)).fetchall()

        if results:
            st.dataframe(pd.DataFrame([dict(r) for r in results]), use_container_width=True, hide_index=True)

            st.markdown("---")
            st.write("### Toggle Fee Status")
            col_sel, col_act = st.columns([2, 1])
            with col_sel:
                selected_farmer_id = st.selectbox(
                    "Select Farmer", 
                    [r["id"] for r in results], 
                    format_func=lambda x: f"{x} - {next(r['name'] for r in results if r['id'] == x)} (ID: {next(r['national_id'] for r in results if r['id'] == x)})"
                )
            
            f_current = next(r for r in results if r["id"] == selected_farmer_id)
            
            with col_act:
                st.write(" ")
                st.write(" ")
                if f_current["fee_verified"] == 0:
                    if st.button("✅ Verify Fee Payment", type="primary", use_container_width=True):
                        conn.execute("UPDATE farmers SET fee_verified = 1 WHERE id = ?", (selected_farmer_id,))
                        conn.commit()
                        st.success(f"Verified fee for {f_current['name']}")
                        st.rerun()
                else:
                    if st.button("🚫 Revoke Fee Verification", use_container_width=True):
                        conn.execute("UPDATE farmers SET fee_verified = 0 WHERE id = ?", (selected_farmer_id,))
                        conn.commit()
                        st.warning(f"Revoked fee verification for {f_current['name']}")
                        st.rerun()

    elif menu == "📝 Register Farmer":
        st.subheader("📝 Register New Farmer")
        with st.form("add_farmer_form"):
            col1, col2 = st.columns(2)
            with col1:
                f_name = st.text_input("Farmer Full Name", placeholder="e.g., Chala Beyene")
                f_nat_id = st.text_input("National ID (Unique)", placeholder="e.g., ETH-99887766")
                f_phone = st.text_input("Phone Number", placeholder="+2519...")
            with col2:
                f_village = st.text_input("Village / Got Name", placeholder="e.g., Gudeta")
                f_land = st.number_input("Farmland Area (Hectares)", min_value=0.1, value=1.0, step=0.1)
                f_fee = st.checkbox("Mark Fee as Paid & Verified immediately", value=False)

            submit = st.form_submit_button("Submit Farmer Record", use_container_width=True)
            if submit:
                if not f_name or not f_nat_id:
                    st.error("Full Name and National ID are required.")
                else:
                    try:
                        f_id = f"FAR-00{conn.execute('SELECT COUNT(*) FROM farmers').fetchone()[0] + 1}"
                        fee_val = 1 if f_fee else 0
                        conn.execute("""
                            INSERT INTO farmers (id, national_id, name, kebele_id, village, land_size, phone, fee_verified, status)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'In Queue')
                        """, (f_id, f_nat_id, f_name, kebele_id, f_village, f_land, f_phone, fee_val))
                        conn.commit()
                        st.success(f"Farmer '{f_name}' registered successfully with National ID `{f_nat_id}`!")
                        st.rerun()
                    except sqlite3.IntegrityError:
                        st.error(f"❌ Error: A farmer with National ID `{f_nat_id}` already exists in the database.")

    elif menu == "⏳ Verified Farmer Queue":
        st.subheader("⏳ Pending Queue (Access Restricted to Fee-Verified Farmers)")
        st.caption("🔒 Access Enforcement: Only farmers with verified fee payments appear in this queue.")

        queue_farmers = conn.execute("SELECT * FROM farmers WHERE kebele_id = ? AND fee_verified = 1 AND status = 'In Queue'", (kebele_id,)).fetchall()

        if not queue_farmers:
            st.warning("No fee-verified farmers are currently waiting in the queue.")
        else:
            st.dataframe(pd.DataFrame([dict(f) for f in queue_farmers]), use_container_width=True, hide_index=True)

            st.markdown("---")
            st.write("### Approve Farmer for Distribution")
            selected_farmer_id = st.selectbox(
                "Select Verified Farmer to Approve", 
                [f["id"] for f in queue_farmers], 
                format_func=lambda x: next(f["name"] for f in queue_farmers if f["id"] == x)
            )
            if st.button("Approve & Mark as Fully Registered", type="primary"):
                conn.execute("UPDATE farmers SET status = 'Registered' WHERE id = ?", (selected_farmer_id,))
                conn.commit()
                st.success("Farmer approved successfully for distribution!")
                st.rerun()

    elif menu == "✅ Registered Farmers Directory":
        st.subheader("✅ Fully Registered Farmers Directory")
        registered_farmers = conn.execute("SELECT * FROM farmers WHERE kebele_id = ? AND status = 'Registered'", (kebele_id,)).fetchall()
        if registered_farmers:
            st.dataframe(pd.DataFrame([dict(f) for f in registered_farmers]), use_container_width=True, hide_index=True)
        else:
            st.warning("No fully registered farmers found.")

    elif menu == "🎲 Distribution Grouping & CSV":
        st.subheader("🎲 Fertilizer Distribution Grouping Engine")
        st.caption("🔒 Access Restriction: Only fee-verified registered farmers can be assigned to distribution groups.")

        verified_registered = conn.execute("SELECT * FROM farmers WHERE kebele_id = ? AND status = 'Registered' AND fee_verified = 1", (kebele_id,)).fetchall()

        if not verified_registered:
            st.warning("No fee-verified registered farmers available for grouping.")
        else:
            col1, col2 = st.columns([1, 2])
            with col1:
                group_size = st.number_input("Target Group Size", min_value=1, max_value=10, value=2)
                if st.button("Generate & Assign Groups", type="primary", use_container_width=True):
                    farmer_list = [dict(f) for f in verified_registered]
                    random.shuffle(farmer_list)
                    
                    group_num = 1
                    for i in range(0, len(farmer_list), group_size):
                        batch = farmer_list[i:i + group_size]
                        for f in batch:
                            conn.execute("UPDATE farmers SET group_id = ? WHERE id = ?", (group_num, f["id"]))
                        group_num += 1
                    conn.commit()
                    st.success("Groups successfully generated and saved!")
                    st.rerun()

            with col2:
                grouped_data = conn.execute("SELECT DISTINCT group_id FROM farmers WHERE kebele_id = ? AND group_id IS NOT NULL ORDER BY group_id", (kebele_id,)).fetchall()
                if grouped_data:
                    st.write("### Active Distribution Batches")
                    for g_row in grouped_data:
                        g_id = g_row["group_id"]
                        members = conn.execute("SELECT * FROM farmers WHERE kebele_id = ? AND group_id = ?", (kebele_id, g_id)).fetchall()
                        df_members = pd.DataFrame([dict(m) for m in members])
                        
                        with st.expander(f"📦 Group Batch #{g_id} ({len(members)} Members)", expanded=True):
                            st.dataframe(df_members[["id", "national_id", "name", "phone", "village", "land_size"]], hide_index=True)
                            
                            csv_buffer = StringIO()
                            df_members.to_csv(csv_buffer, index=False, encoding='utf-8')
                            st.download_button(
                                label=f"📥 Download Group #{g_id} CSV",
                                data=csv_buffer.getvalue(),
                                file_name=f"fertilizer_group_{g_id}.csv",
                                mime="text/csv",
                                key=f"dl_g_{g_id}"
                            )

    conn.close()
    st.sidebar.markdown("---")
    st.sidebar.info(f"Logged in as: **{st.session_state.user['name']}**")
    st.sidebar.button("🚪 Sign Out", on_click=logout, use_container_width=True)

# ==================== MAIN ROUTER ====================
def main():
    if st.session_state.user is None:
        st.markdown("""
            <div class="hero-banner" style="text-align: center;">
                <h1>🌾 Fertilizer Distribution Management System</h1>
                <p>Multi-Tier Regional, Zonal, Woreda & Field Operations System</p>
            </div>
        """, unsafe_allow_html=True)

        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            st.write("### 🔐 Select Administrative Portal")
            
            selected_role = st.selectbox(
                "Select Role Portal:",
                ["regional_manager", "zonal_manager", "woreda_manager", "da_worker"],
                format_func=lambda x: {
                    "regional_manager": "🗺️ Regional Executive Portal",
                    "zonal_manager": "🏛️ Zonal Operations Portal",
                    "woreda_manager": "📍 Woreda Administration Portal",
                    "da_worker": "🌾 DA Field Operations Portal"
                }[x]
            )
            
            if st.button("Enter Selected Portal", use_container_width=True, type="primary"):
                role_names = {
                    "regional_manager": "Regional Executive Director",
                    "zonal_manager": "Zonal Operations Representative",
                    "woreda_manager": "Woreda Administrator",
                    "da_worker": "Alemayehu Tadesse (DA Officer)"
                }
                st.session_state.user = {
                    "role": selected_role,
                    "name": role_names[selected_role]
                }
                st.rerun()
    else:
        role = st.session_state.user["role"]
        if role == "regional_manager":
            show_regional_manager()
        elif role == "zonal_manager":
            show_zonal_manager()
        elif role == "woreda_manager":
            show_woreda_manager()
        elif role == "da_worker":
            show_da_worker()

if __name__ == "__main__":
    main()
