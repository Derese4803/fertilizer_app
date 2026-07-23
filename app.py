import sqlite3
import pandas as pd
import streamlit as st
from io import StringIO

# ==================== DATABASE INITIALIZATION ====================
DB_FILE = "fertilizer_cascade_beauty_v4.db"

def get_db_connection():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("PRAGMA foreign_keys = ON;")

    # 1. Regions Table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS regions (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            total_quota INTEGER DEFAULT 0
        )
    """)

    # 2. Zones Table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS zones (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            region_id TEXT NOT NULL,
            fertilizer_quota INTEGER DEFAULT 0,
            FOREIGN KEY (region_id) REFERENCES regions (id)
        )
    """)

    # 3. Woredas Table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS woredas (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            zone_id TEXT NOT NULL,
            fertilizer_quota INTEGER DEFAULT 0,
            fertilizer_price_per_qtl REAL DEFAULT 4500.0,
            FOREIGN KEY (zone_id) REFERENCES zones (id)
        )
    """)

    # 4. Kebeles Table
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

    # 5. Dynamic Fee List per Woreda
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS fee_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            woreda_id TEXT NOT NULL,
            fee_name TEXT NOT NULL,
            amount REAL NOT NULL,
            FOREIGN KEY (woreda_id) REFERENCES woredas (id)
        )
    """)

    # 6. Farmers Table with Itemized Fee Verification & Quintals
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS farmers (
            id TEXT PRIMARY KEY,
            national_id TEXT UNIQUE NOT NULL,
            name TEXT NOT NULL,
            kebele_id TEXT NOT NULL,
            village TEXT NOT NULL,
            land_size REAL NOT NULL,
            phone TEXT NOT NULL,
            requested_quintals REAL DEFAULT 1.0,
            fertilizer_paid INTEGER DEFAULT 0,
            sport_fee_paid INTEGER DEFAULT 0,
            tax_paid INTEGER DEFAULT 0,
            other_fee_paid INTEGER DEFAULT 0,
            fee_verified INTEGER DEFAULT 0,
            status TEXT DEFAULT 'Pending Fees',
            group_id INTEGER,
            FOREIGN KEY (kebele_id) REFERENCES kebeles (id)
        )
    """)

    # Seed Baseline Sample Data safely
    cursor.execute("INSERT OR IGNORE INTO regions VALUES ('REG-001', 'Oromia Region', 50000)")
    cursor.execute("INSERT OR IGNORE INTO zones VALUES ('ZN-001', 'Jimma Zone', 'REG-001', 15000)")
    cursor.execute("INSERT OR IGNORE INTO woredas VALUES ('WRD-001', 'Manna Woreda', 'ZN-001', 5000, 4500.0)")
    cursor.execute("INSERT OR IGNORE INTO kebeles VALUES ('KEB-001', 'Yebu Kebele', 'WRD-001', 'Alemayehu Tadesse', 'Getachew Bekele', 1500)")

    # Standard Local Fees
    cursor.execute("INSERT OR IGNORE INTO fee_items (id, woreda_id, fee_name, amount) VALUES (1, 'WRD-001', 'ስፖርት ክፍያ (Sport Fee)', 150.0)")
    cursor.execute("INSERT OR IGNORE INTO fee_items (id, woreda_id, fee_name, amount) VALUES (2, 'WRD-001', 'የመሬት ግብር (Land Tax)', 350.0)")
    cursor.execute("INSERT OR IGNORE INTO fee_items (id, woreda_id, fee_name, amount) VALUES (3, 'WRD-001', 'የአገልግሎት ክፍያ (Service Fee)', 100.0)")

    seed_farmers = [
        ('FAR-001', 'ETH-10293847', 'Abebe Bikila', 'KEB-001', 'Gudeta', 2.5, '+251911000000', 2.0, 1, 1, 1, 1, 1, 'Grouped', 1),
        ('FAR-002', 'ETH-20394857', 'Kebede Tessema', 'KEB-001', 'Gudeta', 1.8, '+251911000001', 1.0, 1, 1, 1, 1, 1, 'Grouped', 1),
        ('FAR-003', 'ETH-30495867', 'Almaz Ayana', 'KEB-001', 'Boreta', 3.0, '+251911000002', 1.5, 1, 1, 1, 1, 1, 'In Queue', None),
        ('FAR-004', 'ETH-40596877', 'Tirunesh Dibaba', 'KEB-001', 'Boreta', 1.2, '+251911000003', 1.0, 1, 0, 1, 1, 0, 'Pending Fees', None),
        ('FAR-005', 'ETH-50697887', 'Haile Gebrselassie', 'KEB-001', 'Gudeta', 4.1, '+251911000004', 3.0, 0, 0, 0, 0, 0, 'Pending Fees', None),
    ]
    cursor.executemany("INSERT OR IGNORE INTO farmers VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", seed_farmers)

    conn.commit()
    conn.close()

# ==================== STREAMLIT CONFIG & UI STYLING ====================
st.set_page_config(
    page_title="Cascade Fertilizer Allocation Engine",
    page_icon="🌾",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Premium Modern Glassmorphism CSS
st.markdown("""
    <style>
    .main { background: #f1f5f9; }
    .hero-banner {
        background: linear-gradient(135deg, #059669 0%, #0d9488 50%, #0f172a 100%);
        padding: 30px;
        border-radius: 20px;
        color: white;
        box-shadow: 0 15px 30px -10px rgba(13, 148, 136, 0.3);
        margin-bottom: 25px;
    }
    .hero-banner h1 { color: #ffffff !important; font-size: 2.2rem !important; font-weight: 800 !important; margin-bottom: 8px !important; }
    .hero-banner p { color: #e2e8f0 !important; font-size: 1.1rem; margin-bottom: 0px !important; }
    div[data-testid="stMetric"] {
        background: #ffffff;
        padding: 20px;
        border-radius: 16px;
        border: 1px solid #e2e8f0;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.03);
    }
    div[data-testid="stMetricLabel"] { font-weight: 700; color: #475569; }
    div[data-testid="stMetricValue"] { color: #0f172a; font-weight: 800; }
    .stButton>button {
        border-radius: 10px !important;
        font-weight: 700 !important;
        background: linear-gradient(135deg, #059669 0%, #0d9488 100%) !important;
        color: white !important;
        border: none !important;
        padding: 10px 20px !important;
        box-shadow: 0 4px 10px rgba(5, 150, 105, 0.2) !important;
    }
    .stButton>button:hover {
        background: linear-gradient(135deg, #047857 0%, #0f766e 100%) !important;
        box-shadow: 0 6px 15px rgba(5, 150, 105, 0.3) !important;
    }
    .status-badge-yes {
        background-color: #dcfce7; color: #15803d; padding: 4px 12px; border-radius: 20px; font-weight: 700; font-size: 0.85rem;
    }
    .status-badge-no {
        background-color: #fee2e2; color: #b91c1c; padding: 4px 12px; border-radius: 20px; font-weight: 700; font-size: 0.85rem;
    }
    </style>
""", unsafe_allow_html=True)

init_db()

def get_shareable_link():
    try:
        host = st.context.headers.get("Host", "localhost:8501")
        return f"https://{host}"
    except Exception:
        return "http://localhost:8501"

# ==================== SIDEBAR ROLE ROUTER & LINK GENERATOR ====================
st.sidebar.markdown("## 🌾 Cascade Portal")
role = st.sidebar.selectbox(
    "Select Access Role:",
    ["Regional Manager", "Zonal Manager", "Woreda Manager", "DA Worker (Kebele Level)"]
)

st.sidebar.markdown("---")
st.sidebar.markdown("### 🔗 Shareable App Link")
st.sidebar.info(f"Access URL:\n`{get_shareable_link()}`")
st.sidebar.code(get_shareable_link(), language="text")

conn = get_db_connection()

# ==============================================================================
# 1. REGIONAL MANAGER ROLE
# ==============================================================================
if role == "Regional Manager":
    st.markdown("""
        <div class="hero-banner">
            <h1>🗺️ Regional Executive Operations</h1>
            <p>Set Zonal quotas, track regional distribution pipelines, and register new administrative Zones.</p>
        </div>
    """, unsafe_allow_html=True)

    region = conn.execute("SELECT * FROM regions WHERE id = 'REG-001'").fetchone()
    zones = conn.execute("SELECT * FROM zones WHERE region_id = 'REG-001'").fetchall()
    
    allocated = sum([z["fertilizer_quota"] for z in zones]) if zones else 0
    remaining = region["total_quota"] - allocated

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Regional Total Quota", f"{region['total_quota']:,} Qtl")
    c2.metric("Allocated to Zones", f"{allocated:,} Qtl")
    c3.metric("Unallocated Reserve", f"{remaining:,} Qtl")
    c4.metric("Active Zones", len(zones))

    st.markdown("---")
    tab1, tab2, tab3 = st.tabs(["📊 Aggregated Regional Hierarchy", "⚖️ Cascade Zonal Quotas", "➕ Register New Zone"])

    with tab1:
        st.subheader("Regional Cascade View")
        df_all = pd.read_sql_query("""
            SELECT 
                r.name AS Region, z.name AS Zone, z.fertilizer_quota AS Zone_Quota,
                w.name AS Woreda, w.fertilizer_quota AS Woreda_Quota,
                k.name AS Kebele, k.fertilizer_quota AS Kebele_Quota
            FROM regions r
            LEFT JOIN zones z ON z.region_id = r.id
            LEFT JOIN woredas w ON w.zone_id = z.id
            LEFT JOIN kebeles k ON k.woreda_id = w.id
        """, conn)
        st.dataframe(df_all, use_container_width=True)

    with tab2:
        st.subheader("Set & Adjust Zonal Quotas")
        if zones:
            with st.form("set_zonal_quota"):
                sel_z = st.selectbox("Select Zone", [dict(z) for z in zones], format_func=lambda x: f"{x['name']} (Current: {x['fertilizer_quota']} Qtl)")
                new_q = st.number_input("Assign Fertilizer Quota (Quintals)", min_value=0, max_value=region["total_quota"], value=sel_z["fertilizer_quota"], step=100)
                if st.form_submit_button("Update Zonal Allocation"):
                    conn.execute("UPDATE zones SET fertilizer_quota = ? WHERE id = ?", (new_q, sel_z["id"]))
                    conn.commit()
                    st.success(f"Quota for {sel_z['name']} updated to {new_q} Quintals!")
                    st.rerun()

    with tab3:
        st.subheader("➕ Register New Zone")
        with st.form("reg_zone_form"):
            z_name = st.text_input("Zone Name", placeholder="e.g., East Hararghe Zone")
            z_quota = st.number_input("Initial Quota (Quintals)", min_value=0, value=1000, step=100)
            if st.form_submit_button("Register Zone") and z_name:
                new_id = f"ZN-00{len(zones)+1}"
                conn.execute("INSERT INTO zones VALUES (?, ?, 'REG-001', ?)", (new_id, z_name, z_quota))
                conn.commit()
                st.success(f"Zone '{z_name}' created!")
                st.rerun()

# ==============================================================================
# 2. ZONAL MANAGER ROLE
# ==============================================================================
elif role == "Zonal Manager":
    st.markdown("""
        <div class="hero-banner">
            <h1>🏛️ Zonal Operations & Allocation Engine</h1>
            <p>Manage Woreda allocations, verify jurisdiction totals, and register new Woredas.</p>
        </div>
    """, unsafe_allow_html=True)

    zones = conn.execute("SELECT * FROM zones").fetchall()
    selected_z = st.sidebar.selectbox("Select Active Zone", [dict(z) for z in zones], format_func=lambda x: x["name"])
    
    woredas = conn.execute("SELECT * FROM woredas WHERE zone_id = ?", (selected_z["id"],)).fetchall()
    allocated = sum([w["fertilizer_quota"] for w in woredas]) if woredas else 0
    remaining = selected_z["fertilizer_quota"] - allocated

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Selected Zone", selected_z["name"])
    c2.metric("Total Zone Stock", f"{selected_z['fertilizer_quota']:,} Qtl")
    c3.metric("Allocated to Woredas", f"{allocated:,} Qtl")
    c4.metric("Unallocated Stock", f"{remaining:,} Qtl")

    st.markdown("---")
    tab1, tab2, tab3 = st.tabs(["⚖️ Allocate Woreda Quotas", "➕ Register Woreda", "📊 Woreda Overview"])

    with tab1:
        st.subheader("Set Woreda Quota Allocations")
        if woredas:
            with st.form("set_woreda_q_form"):
                sel_w = st.selectbox("Select Woreda", [dict(w) for w in woredas], format_func=lambda x: f"{x['name']} (Current: {x['fertilizer_quota']} Qtl)")
                new_w_q = st.number_input("Set Quota (Quintals)", min_value=0, max_value=selected_z["fertilizer_quota"], value=sel_w["fertilizer_quota"], step=50)
                
                if st.form_submit_button("Save Woreda Quota"):
                    conn.execute("UPDATE woredas SET fertilizer_quota = ? WHERE id = ?", (new_w_q, sel_w["id"]))
                    conn.commit()
                    st.success(f"Woreda '{sel_w['name']}' quota updated to {new_w_q} Qtl!")
                    st.rerun()

    with tab2:
        st.subheader("➕ Register New Woreda")
        with st.form("add_woreda_form"):
            w_name = st.text_input("Woreda Name", placeholder="e.g., Limmu Seka Woreda")
            w_quota = st.number_input("Initial Quota (Quintals)", min_value=0, value=500, step=50)
            w_price = st.number_input("Fertilizer Unit Price (ETB / Quintal)", min_value=1000.0, value=4500.0, step=100.0)
            if st.form_submit_button("Register Woreda") and w_name:
                new_w_id = f"WRD-00{len(woredas)+1}"
                conn.execute("INSERT INTO woredas VALUES (?, ?, ?, ?, ?)", (new_w_id, w_name, selected_z["id"], w_quota, w_price))
                conn.commit()
                st.success(f"Woreda '{w_name}' registered successfully!")
                st.rerun()

    with tab3:
        st.subheader("Woredas under " + selected_z["name"])
        st.dataframe(pd.DataFrame([dict(w) for w in woredas]), use_container_width=True)

# ==============================================================================
# 3. WOREDA MANAGER ROLE
# ==============================================================================
elif role == "Woreda Manager":
    st.markdown("""
        <div class="hero-banner">
            <h1>📍 Woreda Administration & Fee Manager</h1>
            <p>Set Kebele Quotas, configure local fee items (Sport Fee, Land Tax), and assign DAs & Assistants.</p>
        </div>
    """, unsafe_allow_html=True)

    woredas = conn.execute("SELECT * FROM woredas").fetchall()
    selected_w = st.sidebar.selectbox("Select Active Woreda", [dict(w) for w in woredas], format_func=lambda x: x["name"])

    kebeles = conn.execute("SELECT * FROM kebeles WHERE woreda_id = ?", (selected_w["id"],)).fetchall()
    fee_items = conn.execute("SELECT * FROM fee_items WHERE woreda_id = ?", (selected_w["id"],)).fetchall()

    allocated = sum([k["fertilizer_quota"] for k in kebeles]) if kebeles else 0
    remaining = selected_w["fertilizer_quota"] - allocated

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Woreda Name", selected_w["name"])
    c2.metric("Total Stock Quota", f"{selected_w['fertilizer_quota']:,} Qtl")
    c3.metric("Fertilizer Price / Qtl", f"{selected_w['fertilizer_price_per_qtl']:,.2f} ETB")
    c4.metric("Unallocated Stock", f"{remaining:,} Qtl")

    st.markdown("---")
    tab1, tab2, tab3, tab4 = st.tabs(["💳 Configure Fee Schedule", "⚖️ Cascade Kebele Quota", "➕ Register Kebele & Staff", "📊 Woreda Master View"])

    with tab1:
        st.subheader("💳 Configure Mandatory Woreda Fee Items")
        st.caption("These fees (e.g., Sport Fee, Land Tax, Registration Fee) will be enforced by DA Officers.")
        
        col_f1, col_f2 = st.columns([2, 1])
        with col_f1:
            with st.form("add_fee_item_form"):
                fee_name_in = st.text_input("Fee Description", placeholder="e.g., ስፖርት ክፍያ (Sport Fee)")
                fee_amount_in = st.number_input("Amount per Farmer (ETB)", min_value=0.0, value=150.0, step=10.0)
                if st.form_submit_button("Add Fee Item to Schedule") and fee_name_in:
                    conn.execute("INSERT INTO fee_items (woreda_id, fee_name, amount) VALUES (?, ?, ?)", (selected_w["id"], fee_name_in, fee_amount_in))
                    conn.commit()
                    st.success(f"Added '{fee_name_in}' ({fee_amount_in} ETB) to mandatory fees.")
                    st.rerun()

        with col_f2:
            st.write("#### Active Woreda Fee List")
            if fee_items:
                df_f = pd.DataFrame([dict(f) for f in fee_items])
                st.dataframe(df_f[["fee_name", "amount"]], use_container_width=True, hide_index=True)
                st.info(f"**Total Fixed Fees / Farmer:** {sum([f['amount'] for f in fee_items]):,.2f} ETB")

    with tab2:
        st.subheader("Assign Kebele Fertilizer Quotas")
        if kebeles:
            with st.form("set_kebele_q_form"):
                sel_k = st.selectbox("Select Kebele", [dict(k) for k in kebeles], format_func=lambda x: f"{x['name']} (DA: {x['da_name']} | Quota: {x['fertilizer_quota']} Qtl)")
                new_k_q = st.number_input("Set Quota (Quintals)", min_value=0, max_value=selected_w["fertilizer_quota"], value=sel_k["fertilizer_quota"], step=10)
                if st.form_submit_button("Save Kebele Quota"):
                    conn.execute("UPDATE kebeles SET fertilizer_quota = ? WHERE id = ?", (new_k_q, sel_k["id"]))
                    conn.commit()
                    st.success(f"Quota for {sel_k['name']} set to {new_k_q} Qtl!")
                    st.rerun()

    with tab3:
        st.subheader("➕ Register Kebele with Lead DA & Assistant")
        with st.form("add_kebele_staff_form"):
            col1, col2 = st.columns(2)
            with col1:
                k_name = st.text_input("Kebele Name", placeholder="e.g., Yebu Kebele")
                da_name = st.text_input("Assigned Development Agent (DA)", placeholder="e.g., Alemayehu Tadesse")
            with col2:
                assistant_name = st.text_input("Assigned Assistant DA", placeholder="e.g., Getachew Bekele")
                k_quota = st.number_input("Initial Allocated Quota (Quintals)", min_value=0, value=200, step=10)

            if st.form_submit_button("Register Kebele & Staff"):
                if k_name and da_name and assistant_name:
                    new_k_id = f"KEB-00{len(kebeles)+1}"
                    conn.execute("INSERT INTO kebeles VALUES (?, ?, ?, ?, ?, ?)", (new_k_id, k_name, selected_w["id"], da_name, assistant_name, k_quota))
                    conn.commit()
                    st.success(f"Kebele '{k_name}' registered with DA {da_name} and Assistant {assistant_name}.")
                    st.rerun()

    with tab4:
        st.subheader("Kebele Directory under " + selected_w["name"])
        st.dataframe(pd.DataFrame([dict(k) for k in kebeles]), use_container_width=True)

# ==============================================================================
# 4. DA WORKER ROLE (KEBELE LEVEL)
# ==============================================================================
elif role == "DA Worker (Kebele Level)":
    st.markdown("""
        <div class="hero-banner">
            <h1>🌾 Field Operations & DA Workstation</h1>
            <p>Register local farmers, verify multi-item fees (Sport, Tax, Fertilizer), and build dynamic group clusters.</p>
        </div>
    """, unsafe_allow_html=True)

    kebeles = conn.execute("SELECT k.*, w.fertilizer_price_per_qtl, w.id as woreda_id FROM kebeles k JOIN woredas w ON k.woreda_id = w.id").fetchall()
    selected_k = st.sidebar.selectbox("Select Active Kebele Workstation", [dict(k) for k in kebeles], format_func=lambda x: f"{x['name']} (DA: {x['da_name']})")

    # Fetch fee items
    fee_items = conn.execute("SELECT * FROM fee_items WHERE woreda_id = ?", (selected_k["woreda_id"],)).fetchall()
    fixed_fees_total = sum([f["amount"] for f in fee_items]) if fee_items else 0.0

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Kebele Name", selected_k["name"])
    c2.metric("Assigned DA", selected_k["da_name"])
    c3.metric("Assistant DA", selected_k["assistant_name"])
    c4.metric("Kebele Quota Stock", f"{selected_k['fertilizer_quota']:,} Qtl")

    st.markdown("---")
    tab1, tab2, tab3, tab4 = st.tabs(["📝 Register Farmer with Fee Status", "💳 Fee Calculation & Verification", "🎲 Auto-Group Generation", "📋 Kebele Distribution Manifest"])

    # --- TAB 1: REGISTER FARMER WITH FEE CHECKBOXES ---
    with tab1:
        st.subheader("📝 Register New Farmer & Record Initial Fee Verification")
        st.caption("Select paid items directly during registration.")

        with st.form("reg_farmer_da_form"):
            col1, col2 = st.columns(2)
            with col1:
                f_name = st.text_input("Farmer Full Name", placeholder="e.g., Taye Bogale")
                f_nat_id = st.text_input("National ID (Unique)", placeholder="e.g., ETH-99887766")
                f_phone = st.text_input("Phone Number", placeholder="+2519...")
                f_qtl = st.number_input("Requested Fertilizer (Quintals)", min_value=0.5, value=1.0, step=0.5)

            with col2:
                f_village = st.text_input("Village / Got Name", placeholder="e.g., Gudeta")
                f_land = st.number_input("Farmland Area (Hectares)", min_value=0.1, value=1.5, step=0.1)
                st.markdown("##### 💳 Fee Payment Verification Checkbox")
                f_paid_fert = st.checkbox("Fertilizer Payment Complete?", value=False)
                f_paid_sport = st.checkbox("ስፖርት ክፍያ (Sport Fee Paid)?", value=False)
                f_paid_tax = st.checkbox("የመሬት ግብር (Land Tax Paid)?", value=False)
                f_paid_other = st.checkbox("Other Administrative Fees Paid?", value=False)

            if st.form_submit_button("Submit Farmer Registration"):
                if f_name and f_nat_id:
                    # Fee verified only if all paid
                    all_verified = 1 if (f_paid_fert and f_paid_sport and f_paid_tax and f_paid_other) else 0
                    status_text = "In Queue" if all_verified else "Pending Fees"
                    
                    try:
                        new_f_id = f"FAR-00{conn.execute('SELECT COUNT(*) FROM farmers').fetchone()[0] + 1}"
                        conn.execute("""
                            INSERT INTO farmers (id, national_id, name, kebele_id, village, land_size, phone, requested_quintals, 
                                                 fertilizer_paid, sport_fee_paid, tax_paid, other_fee_paid, fee_verified, status)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """, (new_f_id, f_nat_id, f_name, selected_k["id"], f_village, f_land, f_phone, f_qtl,
                              1 if f_paid_fert else 0, 1 if f_paid_sport else 0, 1 if f_paid_tax else 0, 1 if f_paid_other else 0,
                              all_verified, status_text))
                        conn.commit()
                        st.success(f"Farmer '{f_name}' registered successfully! (Status: {status_text})")
                        st.rerun()
                    except sqlite3.IntegrityError:
                        st.error("❌ National ID already registered!")
                else:
                    st.error("Full Name and National ID are required.")

    # --- TAB 2: DETAILED FEE CALCULATOR & VERIFICATION DASHBOARD ---
    with tab2:
        st.subheader("💰 Individual Fee Calculation & Verification Dashboard")
        
        # Fee Breakdown Calculation Card
        st.markdown(f"""
            > **🧮 Fee Reference Rates for {selected_k['name']}:**
            > * **Fertilizer Price:** `{selected_k['fertilizer_price_per_qtl']:,.2f} ETB` per Quintal
            > * **Woreda Mandatory Fixed Fees:** `{fixed_fees_total:,.2f} ETB` (Includes Sport Fee, Tax, Service Charge)
        """)

        farmers_list = conn.execute("SELECT * FROM farmers WHERE kebele_id = ?", (selected_k["id"],)).fetchall()

        if farmers_list:
            df_f_display = pd.DataFrame([dict(f) for f in farmers_list])
            
            # Add calculated fee column
            df_f_display["Total_Due_ETB"] = (df_f_display["requested_quintals"] * selected_k["fertilizer_price_per_qtl"]) + fixed_fees_total
            df_f_display["All_Fees_Verified"] = df_f_display["fee_verified"].apply(lambda x: "✅ YES (In Queue)" if x == 1 else "❌ NO (Pending)")
            
            st.dataframe(
                df_f_display[["id", "national_id", "name", "village", "requested_quintals", "Total_Due_ETB", "fertilizer_paid", "sport_fee_paid", "tax_paid", "other_fee_paid", "All_Fees_Verified"]],
                use_container_width=True, hide_index=True
            )

            st.markdown("---")
            st.write("### Update Specific Farmer Payment Checklists")

            col_sel, col_chk = st.columns([1, 2])
            with col_sel:
                selected_fid = st.selectbox(
                    "Select Farmer Record to Update",
                    [f["id"] for f in farmers_list],
                    format_func=lambda x: f"{x} - {next(f['name'] for f in farmers_list if f['id'] == x)}"
                )
                f_curr = next(f for f in farmers_list if f["id"] == selected_fid)
                total_farmer_due = (f_curr["requested_quintals"] * selected_k["fertilizer_price_per_qtl"]) + fixed_fees_total
                
                st.info(f"**Selected:** {f_curr['name']}\n\n**Quintals Requested:** {f_curr['requested_quintals']} Qtl\n\n**Total Payment Required:** {total_farmer_due:,.2f} ETB")

            with col_chk:
                with st.form("update_fee_checklist_form"):
                    st.write("#### Check Received Payment Items:")
                    chk_fert = st.checkbox("Fertilizer Payment Received", value=bool(f_curr["fertilizer_paid"]))
                    chk_sport = st.checkbox("ስፖርት ክፍያ (Sport Fee) Received", value=bool(f_curr["sport_fee_paid"]))
                    chk_tax = st.checkbox("የመሬት ግብር (Land Tax) Received", value=bool(f_curr["tax_paid"]))
                    chk_other = st.checkbox("Other Administrative Fees Received", value=bool(f_curr["other_fee_paid"]))

                    if st.form_submit_button("Save & Update Payment Verification Status"):
                        all_paid = 1 if (chk_fert and chk_sport and chk_tax and chk_other) else 0
                        status_update = "In Queue" if all_paid else "Pending Fees"
                        
                        conn.execute("""
                            UPDATE farmers SET fertilizer_paid = ?, sport_fee_paid = ?, tax_paid = ?, other_fee_paid = ?, 
                                               fee_verified = ?, status = ? WHERE id = ?
                        """, (1 if chk_fert else 0, 1 if chk_sport else 0, 1 if chk_tax else 0, 1 if chk_other else 0,
                              all_paid, status_update, selected_fid))
                        conn.commit()
                        st.success(f"Payment records updated for {f_curr['name']}. Status: {status_update}")
                        st.rerun()

    # --- TAB 3: CUSTOMIZABLE AUTO-GROUPING (5, 7, 10 MEMBERS) ---
    with tab3:
        st.subheader("🎲 Custom-Sized Group Generation Engine")
        st.caption("🔒 Strict Enforcement: Only farmers who have paid ALL fees (Fertilizer, Sport, Tax, Other) are eligible for group placement.")

        eligible_farmers = conn.execute("SELECT * FROM farmers WHERE kebele_id = ? AND fee_verified = 1", (selected_k["id"],)).fetchall()

        if not eligible_farmers:
            st.warning("⚠️ No fee-verified farmers currently available to form groups.")
        else:
            col_g1, col_g2 = st.columns([1, 2])
            with col_g1:
                st.write("#### ⚙️ Group Configuration")
                group_size = st.number_input(
                    "Select Group Size (Farmers / Group)", 
                    min_value=2, max_value=20, value=5, step=1,
                    help="Default is 5. You can set it to 5, 7, 10, or any custom cluster size."
                )

                if st.button("Generate & Assign Farmers to Groups", use_container_width=True):
                    f_list = [dict(f) for f in eligible_farmers]
                    
                    group_num = 1
                    for i in range(0, len(f_list), group_size):
                        batch = f_list[i:i + group_size]
                        for f in batch:
                            conn.execute("UPDATE farmers SET group_id = ?, status = 'Grouped' WHERE id = ?", (group_num, f["id"]))
                        group_num += 1
                    conn.commit()
                    st.success(f"Successfully generated groups of size {group_size}!")
                    st.rerun()

            with col_g2:
                st.write("#### Active Distribution Groups")
                groups_db = conn.execute("SELECT DISTINCT group_id FROM farmers WHERE kebele_id = ? AND group_id IS NOT NULL ORDER BY group_id", (selected_k["id"],)).fetchall()
                
                if groups_db:
                    for g_row in groups_db:
                        g_id = g_row["group_id"]
                        members = conn.execute("SELECT * FROM farmers WHERE kebele_id = ? AND group_id = ?", (selected_k["id"], g_id)).fetchall()
                        df_members = pd.DataFrame([dict(m) for m in members])
                        
                        with st.expander(f"📦 Group Batch #{g_id} ({len(members)} Farmers Assigned)", expanded=True):
                            st.dataframe(
                                df_members[["id", "national_id", "name", "phone", "village", "requested_quintals"]],
                                use_container_width=True, hide_index=True
                            )
                            
                            csv_buf = StringIO()
                            df_members.to_csv(csv_buf, index=False, encoding='utf-8')
                            st.download_button(
                                label=f"📥 Download Group #{g_id} Manifest (CSV)",
                                data=csv_buf.getvalue(),
                                file_name=f"group_{g_id}_manifest.csv",
                                mime="text/csv",
                                key=f"dl_btn_{g_id}"
                            )

    # --- TAB 4: KEBELE DISTRIBUTION MANIFEST ---
    with tab4:
        st.subheader("📋 Complete Kebele Beneficiary Master Manifest")
        all_k_farmers = conn.execute("SELECT * FROM farmers WHERE kebele_id = ?", (selected_k["id"],)).fetchall()
        
        if all_k_farmers:
            df_master = pd.DataFrame([dict(f) for f in all_k_farmers])
            st.dataframe(
                df_master[["id", "national_id", "name", "village", "phone", "requested_quintals", "fee_verified", "status", "group_id"]],
                use_container_width=True, hide_index=True
            )

conn.close()
