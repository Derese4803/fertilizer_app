import hashlib
import random
import sqlite3
import string
import pandas as pd
import streamlit as st

# ==================== DATABASE CONFIGURATION ====================
DB_FILE = "fertilizer_cascade_auth_v7.db"


def get_db_connection():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn


def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()


def generate_passcode(length=6) -> str:
    return "".join(random.choices(string.digits, k=length))


def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("PRAGMA foreign_keys = ON;")

    # 1. Users Table (Unique across username + role + unit_id)
    # Allows identical usernames across DIFFERENT links/units
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL,
            password_hash TEXT NOT NULL,
            role TEXT NOT NULL,
            unit_id TEXT NOT NULL,
            reg_passcode TEXT NOT NULL,
            UNIQUE(username, role, unit_id)
        )
    """)

    # 2. Administrative Structure Tables
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS regions (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            total_quota INTEGER DEFAULT 0
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS zones (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            region_id TEXT NOT NULL,
            fertilizer_quota INTEGER DEFAULT 0,
            reg_passcode TEXT NOT NULL,
            FOREIGN KEY (region_id) REFERENCES regions (id)
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS woredas (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            zone_id TEXT NOT NULL,
            fertilizer_quota INTEGER DEFAULT 0,
            fertilizer_price_per_qtl REAL DEFAULT 4500.0,
            reg_passcode TEXT NOT NULL,
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
            reg_passcode TEXT NOT NULL,
            FOREIGN KEY (woreda_id) REFERENCES woredas (id)
        )
    """)

    # 3. Fees & Farmers Tables
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS fee_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            woreda_id TEXT NOT NULL,
            fee_name TEXT NOT NULL,
            amount REAL NOT NULL,
            FOREIGN KEY (woreda_id) REFERENCES woredas (id)
        )
    """)

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

    # Seed Default Root Data
    cursor.execute("INSERT OR IGNORE INTO regions VALUES ('REG-001', 'Oromia Region', 50000)")

    admin_pw = hash_password("admin123")
    cursor.execute(
        "INSERT OR IGNORE INTO users (username, password_hash, role, unit_id, reg_passcode) VALUES (?, ?, ?, ?, ?)",
        ("reg_admin", admin_pw, "Regional Manager", "REG-001", "000000"),
    )

    cursor.execute("INSERT OR IGNORE INTO zones VALUES ('ZN-001', 'Jimma Zone', 'REG-001', 15000, '123456')")
    cursor.execute("INSERT OR IGNORE INTO woredas VALUES ('WRD-001', 'Manna Woreda', 'ZN-001', 5000, 4500.0, '654321')")
    cursor.execute("INSERT OR IGNORE INTO kebeles VALUES ('KEB-001', 'Yebu Kebele', 'WRD-001', 'Alemayehu Tadesse', 'Getachew Bekele', 1500, '112233')")

    cursor.execute("INSERT OR IGNORE INTO fee_items (id, woreda_id, fee_name, amount) VALUES (1, 'WRD-001', 'ስፖርት ክፍያ (Sport Fee)', 150.0)")
    cursor.execute("INSERT OR IGNORE INTO fee_items (id, woreda_id, fee_name, amount) VALUES (2, 'WRD-001', 'የመሬት ግብር (Land Tax)', 350.0)")

    conn.commit()
    conn.close()


# ==================== STREAMLIT CONFIG & UI STYLING ====================
st.set_page_config(
    page_title="Cascade Fertilizer Management Portal",
    page_icon="🌾",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
    <style>
    .main { background: #f8fafc; }
    .hero-banner {
        background: linear-gradient(135deg, #059669 0%, #0d9488 50%, #0f172a 100%);
        padding: 25px 30px;
        border-radius: 18px;
        color: white;
        box-shadow: 0 12px 25px -8px rgba(13, 148, 136, 0.3);
        margin-bottom: 25px;
    }
    .hero-banner h1 { color: #ffffff !important; font-size: 2rem !important; font-weight: 800 !important; margin: 0 !important; }
    .hero-banner p { color: #e2e8f0 !important; font-size: 1rem; margin-top: 5px !important; }
    .stButton>button {
        border-radius: 10px !important;
        font-weight: 700 !important;
        background: linear-gradient(135deg, #059669 0%, #0d9488 100%) !important;
        color: white !important;
        border: none !important;
        padding: 8px 18px !important;
    }
    .link-box {
        background: #f0fdf4;
        border: 2px dashed #16a34a;
        padding: 15px;
        border-radius: 12px;
        margin: 15px 0;
    }
    </style>
""",
    unsafe_allow_html=True,
)

init_db()


def get_base_url():
    try:
        host = st.context.headers.get("Host", "localhost:8501")
        return f"https://{host}"
    except Exception:
        return "http://localhost:8501"


# Session State Management
if "authenticated" not in st.session_state:
    st.session_state["authenticated"] = False
if "user_info" not in st.session_state:
    st.session_state["user_info"] = None

# Query parameters from shareable links
query_params = st.query_params
url_role = query_params.get("role", None)
url_passcode = query_params.get("passcode", None)
url_unit = query_params.get("unit_id", None)

conn = get_db_connection()

# ==================== AUTHENTICATION SYSTEM (LOGIN / REGISTER) ====================
if not st.session_state["authenticated"]:
    st.markdown("""
        <div class="hero-banner">
            <h1>🌾 National Fertilizer Cascade Management System</h1>
            <p>Secure Role-Based Portal Access & Multi-Tiered Passcode Verification</p>
        </div>
    """, unsafe_allow_html=True)

    auth_tab1, auth_tab2 = st.tabs(["🔑 Login", "📝 Register Account"])

    # LOGIN TAB
    with auth_tab1:
        st.subheader("Login to Your Administrative Portal")
        with st.form("login_form"):
            login_role = st.selectbox(
                "Select Access Role",
                ["Regional Manager", "Zonal Manager", "Woreda Manager", "DA Worker (Kebele Level)"],
                index=["Regional Manager", "Zonal Manager", "Woreda Manager", "DA Worker (Kebele Level)"].index(url_role)
                if url_role in ["Regional Manager", "Zonal Manager", "Woreda Manager", "DA Worker (Kebele Level)"]
                else 0
            )
            login_username = st.text_input("Username")
            login_password = st.text_input("Password", type="password")
            submit_login = st.form_submit_button("Sign In")

            if submit_login:
                hashed = hash_password(login_password)
                user = conn.execute(
                    "SELECT * FROM users WHERE username = ? AND password_hash = ? AND role = ?",
                    (login_username, hashed, login_role),
                ).fetchone()

                if user:
                    st.session_state["authenticated"] = True
                    st.session_state["user_info"] = dict(user)
                    st.success(f"Welcome back, {user['username']} ({user['role']})!")
                    st.rerun()
                else:
                    st.error("❌ Invalid Username, Password, or Role selection!")

    # REGISTER TAB
    with auth_tab2:
        st.subheader("Register Unit Manager Account")
        if url_passcode:
            st.info(f"🔗 Access Link Detected! Role: **{url_role}** | Passcode: `{url_passcode}`")

        with st.form("register_form"):
            target_role = st.selectbox(
                "Select Access Role",
                ["Zonal Manager", "Woreda Manager", "DA Worker (Kebele Level)"],
                index=["Zonal Manager", "Woreda Manager", "DA Worker (Kebele Level)"].index(url_role)
                if url_role in ["Zonal Manager", "Woreda Manager", "DA Worker (Kebele Level)"]
                else 0,
            )
            reg_username = st.text_input("Choose Username")
            reg_password = st.text_input("Choose Password", type="password")

            reg_passcode_input = st.text_input(
                "6-Digit Registration Passcode",
                value=url_passcode if url_passcode else "",
                help="Provided by your superior manager when creating your unit.",
            )

            submit_reg = st.form_submit_button("Register Account")

            if submit_reg:
                if reg_username and reg_password and reg_passcode_input:
                    unit = None
                    unit_name = "Selected Unit"
                    
                    if target_role == "Zonal Manager":
                        unit = conn.execute("SELECT id, name FROM zones WHERE reg_passcode = ?", (reg_passcode_input,)).fetchone()
                    elif target_role == "Woreda Manager":
                        unit = conn.execute("SELECT id, name FROM woredas WHERE reg_passcode = ?", (reg_passcode_input,)).fetchone()
                    elif target_role == "DA Worker (Kebele Level)":
                        unit = conn.execute("SELECT id, name FROM kebeles WHERE reg_passcode = ?", (reg_passcode_input,)).fetchone()

                    if unit:
                        try:
                            conn.execute(
                                """
                                INSERT INTO users (username, password_hash, role, unit_id, reg_passcode)
                                VALUES (?, ?, ?, ?, ?)
                                """,
                                (reg_username, hash_password(reg_password), target_role, unit["id"], reg_passcode_input),
                            )
                            conn.commit()
                            st.success(f"✅ Account for '{reg_username}' registered successfully under {unit['name']}! You can now log in.")
                        except sqlite3.IntegrityError:
                            st.error(f"❌ Username '{reg_username}' is already registered for this specific unit ({unit['name']}). Duplicate usernames are only allowed across DIFFERENT units/links!")
                    else:
                        st.error("❌ Invalid Registration Passcode for the selected Role!")
                else:
                    st.error("Please fill in all required fields.")

    st.stop()

# ==================== MAIN LOGGED-IN PORTAL ====================
user_info = st.session_state["user_info"]
role = user_info["role"]

st.sidebar.markdown(f"### 👤 Active User: **{user_info['username']}**")
st.sidebar.caption(f"Role: **{role}**")
if st.sidebar.button("🔒 Logout"):
    st.session_state["authenticated"] = False
    st.session_state["user_info"] = None
    st.rerun()

st.sidebar.markdown("---")

# ==============================================================================
# 1. REGIONAL MANAGER ROLE
# ==============================================================================
if role == "Regional Manager":
    st.markdown("""
        <div class="hero-banner">
            <h1>🗺️ Regional Executive Portal</h1>
            <p>Set Zonal quotas, register Zones, and generate Zonal Manager access links.</p>
        </div>
    """, unsafe_allow_html=True)

    region = conn.execute("SELECT * FROM regions WHERE id = ?", (user_info["unit_id"],)).fetchone()
    zones = conn.execute("SELECT * FROM zones WHERE region_id = ?", (region["id"],)).fetchall()

    allocated = sum([z["fertilizer_quota"] for z in zones]) if zones else 0
    remaining = region["total_quota"] - allocated

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Region", region["name"])
    c2.metric("Total Regional Stock", f"{region['total_quota']:,} Qtl")
    c3.metric("Allocated to Zones", f"{allocated:,} Qtl")
    c4.metric("Unallocated Stock", f"{remaining:,} Qtl")

    st.markdown("---")
    tab1, tab2, tab3 = st.tabs(["➕ Register Zone & Link Selector", "⚖️ Cascade Zonal Quotas", "📊 Hierarchy"])

    with tab1:
        st.subheader("1. Register New Zone")
        with st.form("reg_zone_form"):
            z_name = st.text_input("Zone Name", placeholder="e.g., East Hararghe Zone")
            z_quota = st.number_input("Initial Quota (Quintals)", min_value=0, value=1000, step=100)

            if st.form_submit_button("Register Zone") and z_name:
                new_z_id = f"ZN-00{len(zones)+1}"
                passcode = generate_passcode()
                conn.execute(
                    "INSERT INTO zones VALUES (?, ?, ?, ?, ?)",
                    (new_z_id, z_name, region["id"], z_quota, passcode),
                )
                conn.commit()
                st.success(f"Zone '{z_name}' registered successfully!")
                st.rerun()

        st.markdown("---")
        st.subheader("2. 🔗 Select Zone to View Shareable Link")
        if zones:
            selected_z_item = st.selectbox(
                "Select a Zone from the list:",
                [dict(z) for z in zones],
                format_func=lambda x: f"📍 {x['name']} (ID: {x['id']})"
            )
            
            z_link = f"{get_base_url()}?role=Zonal+Manager&passcode={selected_z_item['reg_passcode']}&unit_id={selected_z_item['id']}"
            
            st.markdown(f"""
                <div class="link-box">
                    <h4>📍 Zone: {selected_z_item['name']}</h4>
                    <p><b>6-Digit Registration Passcode:</b> <code>{selected_z_item['reg_passcode']}</code></p>
                    <p><b>Shareable Link for Zonal Manager:</b></p>
                    <code>{z_link}</code>
                </div>
            """, unsafe_allow_html=True)
            st.code(z_link, language="text")

    with tab2:
        st.subheader("Update Zonal Quotas")
        if zones:
            with st.form("set_z_quota"):
                sel_z = st.selectbox(
                    "Select Zone",
                    [dict(z) for z in zones],
                    format_func=lambda x: f"{x['name']} (Current: {x['fertilizer_quota']} Qtl)",
                )
                new_q = st.number_input("Assign Quota (Quintals)", min_value=0, value=sel_z["fertilizer_quota"], step=100)
                if st.form_submit_button("Save Allocation"):
                    conn.execute("UPDATE zones SET fertilizer_quota = ? WHERE id = ?", (new_q, sel_z["id"]))
                    conn.commit()
                    st.success("Updated successfully!")
                    st.rerun()

    with tab3:
        df_all = pd.read_sql_query("""
            SELECT z.name AS Zone, z.fertilizer_quota AS Zone_Quota, w.name AS Woreda, w.fertilizer_quota AS Woreda_Quota
            FROM zones z LEFT JOIN woredas w ON w.zone_id = z.id
        """, conn)
        st.dataframe(df_all, use_container_width=True)

# ==============================================================================
# 2. ZONAL MANAGER ROLE
# ==============================================================================
elif role == "Zonal Manager":
    st.markdown("""
        <div class="hero-banner">
            <h1>🏢 Zonal Operations Portal</h1>
            <p>Manage Woreda allocations and generate Woreda Manager access links.</p>
        </div>
    """, unsafe_allow_html=True)

    zone = conn.execute("SELECT * FROM zones WHERE id = ?", (user_info["unit_id"],)).fetchone()
    woredas = conn.execute("SELECT * FROM woredas WHERE zone_id = ?", (zone["id"],)).fetchall()

    allocated = sum([w["fertilizer_quota"] for w in woredas]) if woredas else 0
    remaining = zone["fertilizer_quota"] - allocated

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Zone Name", zone["name"])
    c2.metric("Total Zone Stock", f"{zone['fertilizer_quota']:,} Qtl")
    c3.metric("Allocated to Woredas", f"{allocated:,} Qtl")
    c4.metric("Unallocated Stock", f"{remaining:,} Qtl")

    st.markdown("---")
    tab1, tab2, tab3 = st.tabs(["➕ Register Woreda & Link Selector", "⚖️ Cascade Woreda Quota", "📊 Woredas"])

    with tab1:
        st.subheader("1. Register New Woreda")
        with st.form("add_w_form"):
            w_name = st.text_input("Woreda Name", placeholder="e.g., Limmu Seka Woreda")
            w_quota = st.number_input("Initial Quota (Quintals)", min_value=0, value=500, step=50)
            w_price = st.number_input("Fertilizer Unit Price (ETB / Qtl)", min_value=1000.0, value=4500.0, step=100.0)

            if st.form_submit_button("Register Woreda") and w_name:
                new_w_id = f"WRD-00{len(woredas)+1}"
                passcode = generate_passcode()
                conn.execute(
                    "INSERT INTO woredas VALUES (?, ?, ?, ?, ?, ?)",
                    (new_w_id, w_name, zone["id"], w_quota, w_price, passcode),
                )
                conn.commit()
                st.success(f"Woreda '{w_name}' registered!")
                st.rerun()

        st.markdown("---")
        st.subheader("2. 🔗 Select Woreda to View Shareable Link")
        if woredas:
            selected_w_item = st.selectbox(
                "Select a Woreda from the list:",
                [dict(w) for w in woredas],
                format_func=lambda x: f"📍 {x['name']} (ID: {x['id']})"
            )
            
            w_link = f"{get_base_url()}?role=Woreda+Manager&passcode={selected_w_item['reg_passcode']}&unit_id={selected_w_item['id']}"
            
            st.markdown(f"""
                <div class="link-box">
                    <h4>📍 Woreda: {selected_w_item['name']}</h4>
                    <p><b>6-Digit Registration Passcode:</b> <code>{selected_w_item['reg_passcode']}</code></p>
                    <p><b>Shareable Link for Woreda Manager:</b></p>
                    <code>{w_link}</code>
                </div>
            """, unsafe_allow_html=True)
            st.code(w_link, language="text")

    with tab2:
        if woredas:
            with st.form("set_w_q"):
                sel_w = st.selectbox(
                    "Select Woreda",
                    [dict(w) for w in woredas],
                    format_func=lambda x: f"{x['name']} (Current: {x['fertilizer_quota']} Qtl)",
                )
                new_w_q = st.number_input("Assign Quota (Quintals)", min_value=0, value=sel_w["fertilizer_quota"], step=50)
                if st.form_submit_button("Update Quota"):
                    conn.execute("UPDATE woredas SET fertilizer_quota = ? WHERE id = ?", (new_w_q, sel_w["id"]))
                    conn.commit()
                    st.success("Updated successfully!")
                    st.rerun()

    with tab3:
        st.dataframe(pd.DataFrame([dict(w) for w in woredas]), use_container_width=True)

# ==============================================================================
# 3. WOREDA MANAGER ROLE
# ==============================================================================
elif role == "Woreda Manager":
    st.markdown("""
        <div class="hero-banner">
            <h1>📍 Woreda Administration Portal</h1>
            <p>Set Kebele Quotas, configure local fee items, and generate DA Worker access links.</p>
        </div>
    """, unsafe_allow_html=True)

    woreda = conn.execute("SELECT * FROM woredas WHERE id = ?", (user_info["unit_id"],)).fetchone()
    kebeles = conn.execute("SELECT * FROM kebeles WHERE woreda_id = ?", (woreda["id"],)).fetchall()
    fee_items = conn.execute("SELECT * FROM fee_items WHERE woreda_id = ?", (woreda["id"],)).fetchall()

    allocated = sum([k["fertilizer_quota"] for k in kebeles]) if kebeles else 0
    remaining = woreda["fertilizer_quota"] - allocated

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Woreda Name", woreda["name"])
    c2.metric("Total Woreda Stock", f"{woreda['fertilizer_quota']:,} Qtl")
    c3.metric("Fertilizer Price / Qtl", f"{woreda['fertilizer_price_per_qtl']:,.2f} ETB")
    c4.metric("Unallocated Stock", f"{remaining:,} Qtl")

    st.markdown("---")
    tab1, tab2, tab3, tab4 = st.tabs(["➕ Register Kebele & Link Selector", "💳 Configure Fees", "⚖️ Cascade Kebele Quota", "📊 Kebeles"])

    with tab1:
        st.subheader("1. Register New Kebele & Assign DA")
        with st.form("add_k_form"):
            c_a, c_b = st.columns(2)
            k_name = c_a.text_input("Kebele Name", placeholder="e.g., Sombo Kebele")
            da_name = c_a.text_input("Lead DA Worker", placeholder="e.g., Mulugeta Kebede")
            assistant_name = c_b.text_input("Assistant DA", placeholder="e.g., Tigist Hailu")
            k_quota = c_b.number_input("Initial Quota (Quintals)", min_value=0, value=200, step=10)

            if st.form_submit_button("Register Kebele") and k_name:
                new_k_id = f"KEB-00{len(kebeles)+1}"
                passcode = generate_passcode()
                conn.execute(
                    "INSERT INTO kebeles VALUES (?, ?, ?, ?, ?, ?, ?)",
                    (new_k_id, k_name, woreda["id"], da_name, assistant_name, k_quota, passcode),
                )
                conn.commit()
                st.success(f"Kebele '{k_name}' registered!")
                st.rerun()

        st.markdown("---")
        st.subheader("2. 🔗 Select Kebele to View DA Worker Shareable Link")
        if kebeles:
            selected_k_item = st.selectbox(
                "Select a Kebele from the list:",
                [dict(k) for k in kebeles],
                format_func=lambda x: f"📍 {x['name']} (Lead DA: {x['da_name']})"
            )
            
            da_link = f"{get_base_url()}?role=DA+Worker+(Kebele+Level)&passcode={selected_k_item['reg_passcode']}&unit_id={selected_k_item['id']}"
            
            st.markdown(f"""
                <div class="link-box">
                    <h4>📍 Kebele: {selected_k_item['name']}</h4>
                    <p><b>Lead DA:</b> {selected_k_item['da_name']} | <b>Assistant DA:</b> {selected_k_item['assistant_name']}</p>
                    <p><b>6-Digit Registration Passcode:</b> <code>{selected_k_item['reg_passcode']}</code></p>
                    <p><b>Shareable Link for DA Field Worker:</b></p>
                    <code>{da_link}</code>
                </div>
            """, unsafe_allow_html=True)
            st.code(da_link, language="text")

    with tab2:
        st.subheader("Configure Mandatory Fee Items")
        with st.form("add_fee_form"):
            fee_name_in = st.text_input("Fee Name", placeholder="e.g., ስፖርት ክፍያ (Sport Fee)")
            fee_amount_in = st.number_input("Amount (ETB)", min_value=0.0, value=150.0, step=10.0)
            if st.form_submit_button("Save Fee Item") and fee_name_in:
                conn.execute(
                    "INSERT INTO fee_items (woreda_id, fee_name, amount) VALUES (?, ?, ?)",
                    (woreda["id"], fee_name_in, fee_amount_in),
                )
                conn.commit()
                st.success("Fee item added!")
                st.rerun()

        if fee_items:
            st.dataframe(pd.DataFrame([dict(f) for f in fee_items]), use_container_width=True)

    with tab3:
        if kebeles:
            with st.form("set_k_q"):
                sel_k = st.selectbox(
                    "Select Kebele",
                    [dict(k) for k in kebeles],
                    format_func=lambda x: f"{x['name']} (Current: {x['fertilizer_quota']} Qtl)",
                )
                new_k_q = st.number_input("Set Quota (Quintals)", min_value=0, value=sel_k["fertilizer_quota"], step=10)
                if st.form_submit_button("Update Quota"):
                    conn.execute("UPDATE kebeles SET fertilizer_quota = ? WHERE id = ?", (new_k_q, sel_k["id"]))
                    conn.commit()
                    st.success("Quota updated!")
                    st.rerun()

    with tab4:
        st.dataframe(pd.DataFrame([dict(k) for k in kebeles]), use_container_width=True)

# ==============================================================================
# 4. DA WORKER ROLE (KEBELE LEVEL)
# ==============================================================================
elif role == "DA Worker (Kebele Level)":
    st.markdown("""
        <div class="hero-banner">
            <h1>🌾 DA Field Workstation</h1>
            <p>Register farmers, check fee items, and form custom distribution groups.</p>
        </div>
    """, unsafe_allow_html=True)

    kebele = conn.execute(
        "SELECT k.*, w.fertilizer_price_per_qtl, w.id as woreda_id FROM kebeles k JOIN woredas w ON k.woreda_id = w.id WHERE k.id = ?",
        (user_info["unit_id"],),
    ).fetchone()

    fee_items = conn.execute("SELECT * FROM fee_items WHERE woreda_id = ?", (kebele["woreda_id"],)).fetchall()
    fixed_fees_total = sum([f["amount"] for f in fee_items]) if fee_items else 0.0

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Kebele Name", kebele["name"])
    c2.metric("DA Lead", kebele["da_name"])
    c3.metric("Assistant DA", kebele["assistant_name"])
    c4.metric("Kebele Quota Stock", f"{kebele['fertilizer_quota']:,} Qtl")

    st.markdown("---")
    tab1, tab2, tab3, tab4 = st.tabs(["📝 Register Farmer", "💳 Verification & Fees", "🎲 Dynamic Grouping", "📋 Distribution List"])

    with tab1:
        st.subheader("Register Farmer & Initial Fee Checklist")
        with st.form("da_reg_farmer"):
            col1, col2 = st.columns(2)
            f_name = col1.text_input("Full Name")
            f_nat_id = col1.text_input("National ID")
            f_phone = col1.text_input("Phone Number")
            f_qtl = col1.number_input("Requested Fertilizer (Qtl)", min_value=0.5, value=1.0, step=0.5)

            f_village = col2.text_input("Village / Got")
            f_land = col2.number_input("Land Size (Ha)", min_value=0.1, value=1.5, step=0.1)
            
            f_paid_fert = col2.checkbox("Fertilizer Paid")
            f_paid_sport = col2.checkbox("ስፖርት ክፍያ (Sport Fee Paid)")
            f_paid_tax = col2.checkbox("የመሬት ግብር (Land Tax Paid)")
            f_paid_other = col2.checkbox("Other Fees Paid")

            if st.form_submit_button("Register Farmer") and f_name and f_nat_id:
                all_v = 1 if (f_paid_fert and f_paid_sport and f_paid_tax and f_paid_other) else 0
                status_str = "In Queue" if all_v else "Pending Fees"
                new_f_id = f"FAR-00{conn.execute('SELECT COUNT(*) FROM farmers').fetchone()[0] + 1}"
                
                try:
                    conn.execute("""
                        INSERT INTO farmers (id, national_id, name, kebele_id, village, land_size, phone, requested_quintals, 
                                             fertilizer_paid, sport_fee_paid, tax_paid, other_fee_paid, fee_verified, status)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (new_f_id, f_nat_id, f_name, kebele["id"], f_village, f_land, f_phone, f_qtl,
                          1 if f_paid_fert else 0, 1 if f_paid_sport else 0, 1 if f_paid_tax else 0, 1 if f_paid_other else 0,
                          all_v, status_str))
                    conn.commit()
                    st.success(f"Farmer '{f_name}' registered!")
                    st.rerun()
                except sqlite3.IntegrityError:
                    st.error("National ID already exists!")

    with tab2:
        st.subheader("Fee Status & Detailed Calculation")
        farmers_list = conn.execute("SELECT * FROM farmers WHERE kebele_id = ?", (kebele["id"],)).fetchall()
        
        if farmers_list:
            df_f = pd.DataFrame([dict(f) for f in farmers_list])
            df_f["Total_Due_ETB"] = (df_f["requested_quintals"] * kebele["fertilizer_price_per_qtl"]) + fixed_fees_total
            st.dataframe(df_f[["id", "national_id", "name", "village", "requested_quintals", "Total_Due_ETB", "fee_verified", "status"]], use_container_width=True)

            selected_fid = st.selectbox("Select Farmer to Update Checklist", [f["id"] for f in farmers_list])
            f_curr = next(f for f in farmers_list if f["id"] == selected_fid)

            with st.form("update_f_fee"):
                chk_fert = st.checkbox("Fertilizer Paid", value=bool(f_curr["fertilizer_paid"]))
                chk_sport = st.checkbox("Sport Fee Paid", value=bool(f_curr["sport_fee_paid"]))
                chk_tax = st.checkbox("Land Tax Paid", value=bool(f_curr["tax_paid"]))
                chk_other = st.checkbox("Other Fees Paid", value=bool(f_curr["other_fee_paid"]))

                if st.form_submit_button("Update Status"):
                    all_p = 1 if (chk_fert and chk_sport and chk_tax and chk_other) else 0
                    st_str = "In Queue" if all_p else "Pending Fees"
                    conn.execute("""
                        UPDATE farmers SET fertilizer_paid = ?, sport_fee_paid = ?, tax_paid = ?, other_fee_paid = ?, 
                                           fee_verified = ?, status = ? WHERE id = ?
                    """, (1 if chk_fert else 0, 1 if chk_sport else 0, 1 if chk_tax else 0, 1 if chk_other else 0, all_p, st_str, selected_fid))
                    conn.commit()
                    st.success("Updated fee status!")
                    st.rerun()

    with tab3:
        st.subheader("Dynamic Grouping Engine (Fee-Paid Only)")
        group_size = st.number_input("Select Group Size (5, 7, 10, etc.)", min_value=2, max_value=20, value=5)
        
        eligible = conn.execute("SELECT * FROM farmers WHERE kebele_id = ? AND fee_verified = 1", (kebele["id"],)).fetchall()
        
        if st.button("Form Groups") and eligible:
            f_list = [dict(f) for f in eligible]
            g_num = 1
            for i in range(0, len(f_list), group_size):
                batch = f_list[i:i + group_size]
                for f in batch:
                    conn.execute("UPDATE farmers SET group_id = ?, status = 'Grouped' WHERE id = ?", (g_num, f["id"]))
                g_num += 1
            conn.commit()
            st.success("Groups formed successfully!")
            st.rerun()

    with tab4:
        all_k = conn.execute("SELECT * FROM farmers WHERE kebele_id = ?", (kebele["id"],)).fetchall()
        if all_k:
            st.dataframe(pd.DataFrame([dict(f) for f in all_k]), use_container_width=True)

conn.close()
