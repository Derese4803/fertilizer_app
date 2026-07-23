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
    
    # Hierarchy Tables
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
    
    # Fee Items Table (Managed by Woreda)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS fee_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            woreda_id TEXT NOT NULL,
            fee_name TEXT NOT NULL,
            amount REAL NOT NULL,
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
    
    # Safe Auto-Seeding
    cursor.execute("INSERT OR IGNORE INTO regions VALUES ('REG-001', 'Oromia Region', 10000)")
    cursor.execute("INSERT OR IGNORE INTO zones VALUES ('ZN-001', 'Jimma Zone', 'REG-001', 3000)")
    cursor.execute("INSERT OR IGNORE INTO zones VALUES ('ZN-002', 'West Shoa Zone', 'REG-001', 2000)")
    cursor.execute("INSERT OR IGNORE INTO woredas VALUES ('WRD-001', 'Manna Woreda', 'ZN-001', 1500)")
    cursor.execute("INSERT OR IGNORE INTO kebeles VALUES ('KEB-001', 'Yebu Kebele', 'WRD-001', 'Alemayehu Tadesse', 'Getachew Bekele', 500)")
    
    # Seed default fee structure
    cursor.execute("INSERT OR IGNORE INTO fee_items (id, woreda_id, fee_name, amount) VALUES (1, 'WRD-001', 'Registration & Logistics Fee', 150.0)")
    cursor.execute("INSERT OR IGNORE INTO fee_items (id, woreda_id, fee_name, amount) VALUES (2, 'WRD-001', 'Local Extension Service Fee', 50.0)")

    seed_farmers = [
        ('FAR-001', 'ETH-10293847', 'Abebe Bikila', 'KEB-001', 'Gudeta', 2.5, '+251911000000', 1, 'In Queue', None),
        ('FAR-002', 'ETH-20394857', 'Kebede Tessema', 'KEB-001', 'Gudeta', 1.8, '+251911000001', 0, 'In Queue', None),
        ('FAR-003', 'ETH-30495867', 'Almaz Ayana', 'KEB-001', 'Boreta', 3.0, '+251911000002', 1, 'In Queue', None),
        ('FAR-004', 'ETH-40596877', 'Tirunesh Dibaba', 'KEB-001', 'Boreta', 1.2, '+251911000003', 1, 'In Queue', None),
        ('FAR-005', 'ETH-50697887', 'Haile Gebrselassie', 'KEB-001', 'Gudeta', 4.1, '+251911000004', 0, 'In Queue', None),
    ]
    cursor.executemany("INSERT OR IGNORE INTO farmers VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", seed_farmers)
        
    conn.commit()
    conn.close()

init_db()

# ==================== PAGE CONFIG & STYLING ====================
st.set_page_config(
    page_title="Cascade Fertilizer Allocation Engine",
    page_icon="🌾",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
    <style>
    .main { background-color: #f8fafc; }
    .hero-banner {
        background: linear-gradient(135deg, #0f172a 0%, #0d9488 100%);
        padding: 24px 32px;
        border-radius: 16px;
        color: white;
        box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.1);
        margin-bottom: 25px;
    }
    .hero-banner h1 { color: #ffffff !important; font-weight: 700 !important; margin-bottom: 4px !important; }
    .hero-banner p { color: #cbd5e1 !important; font-size: 1.05rem; margin-bottom: 0px !important; }
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

# ==================== SESSION STATE ====================
if "user" not in st.session_state:
    st.session_state.user = None

def logout():
    st.session_state.user = None
    st.query_params.clear()
    st.rerun()

# ==================== 1. REGIONAL MANAGER PORTAL ====================
def show_regional_manager():
    st.markdown("""
        <div class="hero-banner">
            <h1>🗺️ Regional Executive Portal</h1>
            <p>Set Zonal Quotas, register new Zones, and inspect regional data across all tiers.</p>
        </div>
    """, unsafe_allow_html=True)

    conn = get_db_connection()
    region = conn.execute("SELECT * FROM regions WHERE id = 'REG-001'").fetchone()
    zones = conn.execute("SELECT * FROM zones WHERE region_id = 'REG-001'").fetchall()
    
    total_assigned_zones = sum([z["fertilizer_quota"] for z in zones]) if zones else 0
    remaining_reg_quota = region["total_quota"] - total_assigned_zones

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Region Total Stock", f"{region['total_quota']} Qtl")
    c2.metric("Allocated to Zones", f"{total_assigned_zones} Qtl")
    c3.metric("Unallocated Stock", f"{remaining_reg_quota} Qtl")
    c4.metric("Active Zones", len(zones))

    st.markdown("---")

    tab1, tab2, tab3 = st.tabs(["📦 Assign Zonal Quota", "➕ Register Zone", "📊 Regional Aggregated View"])

    with tab1:
        st.subheader("Assign or Update Zonal Fertilizer Quotas")
        if zones:
            with st.form("allocate_zone_quota"):
                sel_zone = st.selectbox("Select Zone", [dict(z) for z in zones], format_func=lambda x: f"{x['name']} (Current Quota: {x['fertilizer_quota']} Qtl)")
                new_quota = st.number_input("Set Fertilizer Quota (Quintals)", min_value=0, max_value=region["total_quota"], value=sel_zone["fertilizer_quota"], step=50)
                
                if st.form_submit_button("Save Zone Quota Allocation", use_container_width=True):
                    conn.execute("UPDATE zones SET fertilizer_quota = ? WHERE id = ?", (new_quota, sel_zone["id"]))
                    conn.commit()
                    st.success(f"Successfully updated quota for {sel_zone['name']} to {new_quota} Quintals.")
                    st.rerun()

    with tab2:
        st.subheader("➕ Register New Zone")
        with st.form("add_zone_form"):
            z_name = st.text_input("Zone Name", placeholder="e.g., East Hararghe Zone")
            initial_quota = st.number_input("Initial Allocated Quota (Quintals)", min_value=0, value=500, step=50)
            if st.form_submit_button("Register Zone", use_container_width=True) and z_name:
                new_id = f"ZN-00{len(zones) + 1}"
                conn.execute("INSERT INTO zones VALUES (?, ?, 'REG-001', ?)", (new_id, z_name, initial_quota))
                conn.commit()
                st.success(f"Zone '{z_name}' created successfully!")
                st.rerun()

    with tab3:
        st.subheader("📊 Complete Regional Tier Breakdown")
        
        st.write("#### 🏛️ Zonal Quotas")
        st.dataframe(pd.DataFrame([dict(z) for z in zones]), use_container_width=True, hide_index=True)
        
        st.write("#### 📍 All Woredas")
        all_woredas = conn.execute("SELECT w.id, w.name AS woreda_name, z.name AS zone_name, w.fertilizer_quota FROM woredas w JOIN zones z ON w.zone_id = z.id").fetchall()
        st.dataframe(pd.DataFrame([dict(w) for w in all_woredas]), use_container_width=True, hide_index=True)

        st.write("#### 🏡 All Kebeles & Field Officers")
        all_kebeles = conn.execute("SELECT k.id, k.name AS kebele_name, w.name AS woreda_name, k.da_name, k.assistant_name, k.fertilizer_quota FROM kebeles k JOIN woredas w ON k.woreda_id = w.id").fetchall()
        st.dataframe(pd.DataFrame([dict(k) for k in all_kebeles]), use_container_width=True, hide_index=True)

    conn.close()
    st.sidebar.markdown("---")
    st.sidebar.button("🚪 Sign Out", on_click=logout, use_container_width=True)

# ==================== 2. ZONAL MANAGER PORTAL ====================
def show_zonal_manager():
    st.markdown("""
        <div class="hero-banner">
            <h1>🏛️ Zonal Operations Portal</h1>
            <p>Distribute Zonal stock into Woreda Quotas, register new Woredas, and monitor local coverage.</p>
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
    c2.metric("Total Zone Quota", f"{zone['fertilizer_quota']} Qtl")
    c3.metric("Allocated to Woredas", f"{total_assigned_woredas} Qtl")
    c4.metric("Unallocated Stock", f"{remaining_zone_quota} Qtl")

    st.markdown("---")

    tab1, tab2, tab3 = st.tabs(["📦 Assign Woreda Quota", "➕ Register Woreda", "📊 Zonal Data Overview"])

    with tab1:
        st.subheader("Assign or Update Woreda Fertilizer Quotas")
        if woredas:
            with st.form("allocate_woreda_quota"):
                sel_woreda = st.selectbox("Select Woreda", [dict(w) for w in woredas], format_func=lambda x: f"{x['name']} (Current Quota: {x['fertilizer_quota']} Qtl)")
                new_quota = st.number_input("Set Fertilizer Quota (Quintals)", min_value=0, max_value=zone["fertilizer_quota"], value=sel_woreda["fertilizer_quota"], step=20)
                
                if st.form_submit_button("Save Woreda Quota Allocation", use_container_width=True):
                    conn.execute("UPDATE woredas SET fertilizer_quota = ? WHERE id = ?", (new_quota, sel_woreda["id"]))
                    conn.commit()
                    st.success(f"Updated quota for {sel_woreda['name']} to {new_quota} Quintals.")
                    st.rerun()

    with tab2:
        st.subheader("➕ Register New Woreda")
        with st.form("add_woreda_form"):
            w_name = st.text_input("Woreda Name", placeholder="e.g., Limmu Seka Woreda")
            initial_quota = st.number_input("Initial Quota (Quintals)", min_value=0, value=200, step=20)
            if st.form_submit_button("Register Woreda", use_container_width=True) and w_name:
                new_id = f"WRD-00{len(woredas) + 1}"
                conn.execute("INSERT INTO woredas VALUES (?, ?, ?, ?)", (new_id, w_name, zone_id, initial_quota))
                conn.commit()
                st.success(f"Woreda '{w_name}' registered successfully.")
                st.rerun()

    with tab3:
        st.subheader("📊 Jurisdiction View for " + zone["name"])
        st.write("#### 📍 Woredas")
        st.dataframe(pd.DataFrame([dict(w) for w in woredas]), use_container_width=True, hide_index=True)

        st.write("#### 🏡 Kebeles in Jurisdiction")
        zone_kebeles = conn.execute("SELECT k.id, k.name as kebele_name, w.name as woreda_name, k.da_name, k.assistant_name, k.fertilizer_quota FROM kebeles k JOIN woredas w ON k.woreda_id = w.id WHERE w.zone_id = ?", (zone_id,)).fetchall()
        st.dataframe(pd.DataFrame([dict(k) for k in zone_kebeles]), use_container_width=True, hide_index=True)

    conn.close()
    st.sidebar.markdown("---")
    st.sidebar.button("🚪 Sign Out", on_click=logout, use_container_width=True)

# ==================== 3. WOREDA MANAGER PORTAL ====================
def show_woreda_manager():
    st.markdown("""
        <div class="hero-banner">
            <h1>📍 Woreda Administration Portal</h1>
            <p>Distribute Woreda Quotas to Kebeles, assign DAs & Assistants, and configure local Fee Lists.</p>
        </div>
    """, unsafe_allow_html=True)

    conn = get_db_connection()
    woreda_id = st.session_state.user.get("woreda_id", "WRD-001")
    woreda = conn.execute("SELECT * FROM woredas WHERE id = ?", (woreda_id,)).fetchone()
    kebeles = conn.execute("SELECT * FROM kebeles WHERE woreda_id = ?", (woreda_id,)).fetchall()
    fee_items = conn.execute("SELECT * FROM fee_items WHERE woreda_id = ?", (woreda_id,)).fetchall()

    total_assigned_kebeles = sum([k["fertilizer_quota"] for k in kebeles]) if kebeles else 0
    remaining_woreda_quota = woreda["fertilizer_quota"] - total_assigned_kebeles

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Woreda Name", woreda["name"])
    c2.metric("Total Woreda Quota", f"{woreda['fertilizer_quota']} Qtl")
    c3.metric("Allocated to Kebeles", f"{total_assigned_kebeles} Qtl")
    c4.metric("Unallocated Stock", f"{remaining_woreda_quota} Qtl")

    st.markdown("---")

    tab1, tab2, tab3, tab4 = st.tabs(["📦 Assign Kebele Quota", "➕ Register Kebele & Assign DA/Assistant", "💳 Manage Mandatory Fee List", "📊 Woreda Data Directory"])

    with tab1:
        st.subheader("Assign or Update Kebele Quotas")
        if kebeles:
            with st.form("allocate_kebele_quota"):
                sel_kebele = st.selectbox("Select Kebele", [dict(k) for k in kebeles], format_func=lambda x: f"{x['name']} (DA: {x['da_name']} | Quota: {x['fertilizer_quota']} Qtl)")
                new_quota = st.number_input("Set Fertilizer Quota (Quintals)", min_value=0, max_value=woreda["fertilizer_quota"], value=sel_kebele["fertilizer_quota"], step=10)
                
                if st.form_submit_button("Save Kebele Quota Allocation", use_container_width=True):
                    conn.execute("UPDATE kebeles SET fertilizer_quota = ? WHERE id = ?", (new_quota, sel_kebele["id"]))
                    conn.commit()
                    st.success(f"Updated quota for {sel_kebele['name']} to {new_quota} Quintals.")
                    st.rerun()

    with tab2:
        st.subheader("➕ Register Kebele with Field Officers")
        with st.form("add_kebele_form"):
            col1, col2 = st.columns(2)
            with col1:
                k_name = st.text_input("Kebele Name", placeholder="e.g., Yebu Kebele")
                da_name = st.text_input("Assigned Development Agent (DA) Name", placeholder="e.g., Alemayehu Tadesse")
            with col2:
                assistant_name = st.text_input("Assigned Assistant Name", placeholder="e.g., Getachew Bekele")
                f_quota = st.number_input("Initial Allocated Quota (Quintals)", min_value=0, value=100, step=10)

            if st.form_submit_button("Register Kebele & Assign Staff", use_container_width=True):
                if k_name and da_name and assistant_name:
                    new_id = f"KEB-00{len(kebeles) + 1}"
                    conn.execute("INSERT INTO kebeles VALUES (?, ?, ?, ?, ?, ?)", (new_id, k_name, woreda_id, da_name, assistant_name, f_quota))
                    conn.commit()
                    st.success(f"Kebele '{k_name}' registered with DA '{da_name}' and Assistant '{assistant_name}'.")
                    st.rerun()
                else:
                    st.error("Please fill in all Kebele and Staff fields.")

    with tab3:
        st.subheader("💳 Configure Required Woreda Fee List")
        st.caption("DAs must verify full payment of these items before a farmer is queued or grouped.")
        
        with st.form("add_fee_item_form"):
            c_f1, c_f2 = st.columns([2, 1])
            with c_f1:
                fee_name_in = st.text_input("Fee Description / Item Name", placeholder="e.g., Administrative Processing Fee")
            with c_f2:
                fee_amount_in = st.number_input("Fee Amount (ETB)", min_value=0.0, value=100.0, step=10.0)
            
            if st.form_submit_button("Add Mandatory Fee Item", use_container_width=True) and fee_name_in:
                conn.execute("INSERT INTO fee_items (woreda_id, fee_name, amount) VALUES (?, ?, ?)", (woreda_id, fee_name_in, fee_amount_in))
                conn.commit()
                st.success(f"Added '{fee_name_in}' ({fee_amount_in} ETB) to mandatory fees.")
                st.rerun()

        st.write("#### Current Fee List for " + woreda["name"])
        if fee_items:
            df_fees = pd.DataFrame([dict(f) for f in fee_items])
            st.dataframe(df_fees[["id", "fee_name", "amount"]], use_container_width=True, hide_index=True)
            total_required = sum([f["amount"] for f in fee_items])
            st.info(f"💰 **Total Required Fee per Farmer:** {total_required:,.2f} ETB")
        else:
            st.warning("No fee items currently configured.")

    with tab4:
        st.subheader("📊 Data Scoped to " + woreda["name"])
        st.write("#### 🏡 Active Kebeles")
        st.dataframe(pd.DataFrame([dict(k) for k in kebeles]), use_container_width=True, hide_index=True)

        st.write("#### 👨‍🌾 Registered Farmers in Woreda")
        woreda_farmers = conn.execute("SELECT f.id, f.national_id, f.name, k.name as kebele_name, f.village, f.land_size, f.fee_verified, f.status FROM farmers f JOIN kebeles k ON f.kebele_id = k.id WHERE k.woreda_id = ?", (woreda_id,)).fetchall()
        st.dataframe(pd.DataFrame([dict(f) for f in woreda_farmers]), use_container_width=True, hide_index=True)

    conn.close()
    st.sidebar.markdown("---")
    st.sidebar.button("🚪 Sign Out", on_click=logout, use_container_width=True)

# ==================== 4. DA WORKER PORTAL ====================
def show_da_worker():
    st.markdown("""
        <div class="hero-banner">
            <h1>🌾 Field Operations & DA Portal</h1>
            <p>Verify mandatory fee payments, manage verified farmer queues, and build distribution groups.</p>
        </div>
    """, unsafe_allow_html=True)

    conn = get_db_connection()
    kebele_id = st.session_state.user.get("kebele_id", "KEB-001")
    kebele_info = conn.execute("SELECT k.*, w.id as woreda_id FROM kebeles k JOIN woredas w ON k.woreda_id = w.id WHERE k.id = ?", (kebele_id,)).fetchone()
    
    fee_items = conn.execute("SELECT * FROM fee_items WHERE woreda_id = ?", (kebele_info["woreda_id"],)).fetchall()
    total_fee_amount = sum([f["amount"] for f in fee_items]) if fee_items else 0.0

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Kebele", kebele_info["name"])
    c2.metric("Assigned DA", kebele_info["da_name"])
    c3.metric("Assistant", kebele_info["assistant_name"])
    c4.metric("Kebele Quota Stock", f"{kebele_info['fertilizer_quota']} Qtl")

    st.markdown("---")

    tab1, tab2, tab3, tab4 = st.tabs(["📝 Register Farmer", "💳 Fee Verification", "⏳ Verified Queue (Fee Paid All)", "🎲 Auto-Group & Distribution CSV"])

    # --- TAB 1: REGISTER FARMER ---
    with tab1:
        st.subheader("📝 Register New Local Farmer")
        with st.form("add_farmer_form"):
            col1, col2 = st.columns(2)
            with col1:
                f_name = st.text_input("Farmer Full Name", placeholder="e.g., Taye Bogale")
                f_nat_id = st.text_input("National ID (Unique)", placeholder="e.g., ETH-88776655")
                f_phone = st.text_input("Phone Number", placeholder="+2519...")
            with col2:
                f_village = st.text_input("Village / Got Name", placeholder="e.g., Gudeta")
                f_land = st.number_input("Farmland Area (Hectares)", min_value=0.1, value=1.5, step=0.1)

            submit = st.form_submit_button("Submit Farmer Record", use_container_width=True)
            if submit:
                if not f_name or not f_nat_id:
                    st.error("Full Name and National ID are required.")
                else:
                    try:
                        f_id = f"FAR-00{conn.execute('SELECT COUNT(*) FROM farmers').fetchone()[0] + 1}"
                        conn.execute("""
                            INSERT INTO farmers (id, national_id, name, kebele_id, village, land_size, phone, fee_verified, status)
                            VALUES (?, ?, ?, ?, ?, ?, ?, 0, 'In Queue')
                        """, (f_id, f_nat_id, f_name, kebele_id, f_village, f_land, f_phone))
                        conn.commit()
                        st.success(f"Farmer '{f_name}' registered successfully! (Fee verification pending)")
                        st.rerun()
                    except sqlite3.IntegrityError:
                        st.error(f"❌ Error: A farmer with National ID `{f_nat_id}` already exists.")

    # --- TAB 2: FEE VERIFICATION ---
    with tab2:
        st.subheader("💳 Fee Verification Dashboard")
        st.write(f"Mandatory Woreda Fee Schedule Total: **{total_fee_amount:,.2f} ETB**")
        
        if fee_items:
            st.dataframe(pd.DataFrame([dict(f) for f in fee_items])[["fee_name", "amount"]], use_container_width=True, hide_index=True)

        st.markdown("---")
        search_term = st.text_input("🔍 Search Farmer by Name or ID", placeholder="Search...")
        
        if search_term:
            farmers_list = conn.execute("SELECT * FROM farmers WHERE kebele_id = ? AND (national_id LIKE ? OR name LIKE ?)", (kebele_id, f"%{search_term}%", f"%{search_term}%")).fetchall()
        else:
            farmers_list = conn.execute("SELECT * FROM farmers WHERE kebele_id = ?", (kebele_id,)).fetchall()

        if farmers_list:
            df_display = pd.DataFrame([dict(f) for f in farmers_list])
            st.dataframe(df_display[["id", "national_id", "name", "village", "land_size", "fee_verified", "status"]], use_container_width=True, hide_index=True)

            st.write("### Update Fee Payment Status")
            col_sel, col_act = st.columns([2, 1])
            with col_sel:
                selected_farmer_id = st.selectbox(
                    "Select Farmer Record", 
                    [f["id"] for f in farmers_list], 
                    format_func=lambda x: f"{x} - {next(f['name'] for f in farmers_list if f['id'] == x)}"
                )
            
            f_current = next(f for f in farmers_list if f["id"] == selected_farmer_id)
            
            with col_act:
                st.write(" ")
                st.write(" ")
                if f_current["fee_verified"] == 0:
                    if st.button("✅ Mark ALL Fees Paid", type="primary", use_container_width=True):
                        conn.execute("UPDATE farmers SET fee_verified = 1 WHERE id = ?", (selected_farmer_id,))
                        conn.commit()
                        st.success(f"Verified all fees for {f_current['name']}")
                        st.rerun()
                else:
                    if st.button("🚫 Revoke Fee Status", use_container_width=True):
                        conn.execute("UPDATE farmers SET fee_verified = 0 WHERE id = ?", (selected_farmer_id,))
                        conn.commit()
                        st.warning(f"Revoked fee verification for {f_current['name']}")
                        st.rerun()

    # --- TAB 3: VERIFIED QUEUE ---
    with tab3:
        st.subheader("⏳ Verified Queue (Access Strict: Fee Paid All)")
        st.caption("🔒 Access Restriction: Only farmers who have paid ALL required fees are listed in this queue.")

        verified_queue = conn.execute("SELECT * FROM farmers WHERE kebele_id = ? AND fee_verified = 1", (kebele_id,)).fetchall()

        if not verified_queue:
            st.info("No fee-verified farmers currently in the queue.")
        else:
            df_vq = pd.DataFrame([dict(f) for f in verified_queue])
            st.dataframe(df_vq[["id", "national_id", "name", "phone", "village", "land_size", "status", "group_id"]], use_container_width=True, hide_index=True)

    # --- TAB 4: AUTO-GROUP & CSV ---
    with tab4:
        st.subheader("🎲 Auto-Group Generation & Distribution Manifest")
        st.caption("🔒 Fee Enforced: Groups are built strictly using fee-verified farmers.")

        eligible_farmers = conn.execute("SELECT * FROM farmers WHERE kebele_id = ? AND fee_verified = 1", (kebele_id,)).fetchall()

        if not eligible_farmers:
            st.warning("No fee-verified farmers are available to form distribution groups.")
        else:
            c_g1, c_g2 = st.columns([1, 2])
            with c_g1:
                group_size = st.number_input("Desired Group Size (Farmers / Group)", min_value=1, max_value=10, value=2)
                if st.button("Generate & Assign Groups", type="primary", use_container_width=True):
                    f_list = [dict(f) for f in eligible_farmers]
                    random.shuffle(f_list)
                    
                    g_num = 1
                    for i in range(0, len(f_list), group_size):
                        batch = f_list[i:i + group_size]
                        for f in batch:
                            conn.execute("UPDATE farmers SET group_id = ?, status = 'Grouped' WHERE id = ?", (g_num, f["id"]))
                        g_num += 1
                    conn.commit()
                    st.success("Groups successfully generated!")
                    st.rerun()

            with c_g2:
                grouped_ids = conn.execute("SELECT DISTINCT group_id FROM farmers WHERE kebele_id = ? AND group_id IS NOT NULL ORDER BY group_id", (kebele_id,)).fetchall()
                if grouped_ids:
                    st.write("### Active Fertilizer Distribution Batches")
                    for g_row in grouped_ids:
                        g_id = g_row["group_id"]
                        members = conn.execute("SELECT * FROM farmers WHERE kebele_id = ? AND group_id = ?", (kebele_id, g_id)).fetchall()
                        df_members = pd.DataFrame([dict(m) for m in members])
                        
                        with st.expander(f"📦 Group Batch #{g_id} ({len(members)} Members)", expanded=True):
                            st.dataframe(df_members[["id", "national_id", "name", "phone", "village", "land_size"]], use_container_width=True, hide_index=True)
                            
                            csv_buffer = StringIO()
                            df_members.to_csv(csv_buffer, index=False, encoding='utf-8')
                            st.download_button(
                                label=f"📥 Download Group #{g_id} Manifest (CSV)",
                                data=csv_buffer.getvalue(),
                                file_name=f"kebele_distribution_group_{g_id}.csv",
                                mime="text/csv",
                                key=f"dl_g_{g_id}"
                            )

    conn.close()
    st.sidebar.markdown("---")
    st.sidebar.button("🚪 Sign Out", on_click=logout, use_container_width=True)

# ==================== MAIN ROUTER ====================
def main():
    if st.session_state.user is None:
        st.markdown("""
            <div class="hero-banner" style="text-align: center;">
                <h1>🌾 Cascade Fertilizer Allocation & Distribution Engine</h1>
                <p>Select your operational administrative role to access your portal</p>
            </div>
        """, unsafe_allow_html=True)

        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            st.write("### 🔐 Select Administrative Portal")
            
            selected_role = st.selectbox(
                "Portal Role:",
                ["regional_manager", "zonal_manager", "woreda_manager", "da_worker"],
                format_func=lambda x: {
                    "regional_manager": "🗺️ Regional Executive Portal",
                    "zonal_manager": "🏛️ Zonal Operations Portal",
                    "woreda_manager": "📍 Woreda Administration Portal",
                    "da_worker": "🌾 Field Operations & DA Portal"
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
                    "name": role_names[selected_role],
                    "region_id": "REG-001",
                    "zone_id": "ZN-001",
                    "woreda_id": "WRD-001",
                    "kebele_id": "KEB-001"
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
