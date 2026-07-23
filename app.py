import sqlite3
import random
import threading
from io import StringIO
from flask import Flask, jsonify, request, Response
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
    
    # Enable Foreign Key Support
    cursor.execute("PRAGMA foreign_keys = ON;")
    
    # Kebeles Table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS kebeles (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            woreda_id TEXT NOT NULL,
            da_name TEXT NOT NULL,
            assistant_name TEXT NOT NULL,
            fertilizer_quota INTEGER NOT NULL
        )
    """)
    
    # Farmers Table with UNIQUE National ID constraint
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
    
    # Check if empty -> Seed Initial Data
    cursor.execute("SELECT COUNT(*) FROM kebeles")
    if cursor.fetchone()[0] == 0:
        cursor.execute("""
            INSERT INTO kebeles VALUES ('KEB-001', 'Yebu Kebele', 'WRD-001', 'Alemayehu Tadesse', 'Getachew Bekele', 500)
        """)
        
        seed_farmers = [
            ('FAR-001', 'ETH-10293847', 'Abebe Bikila', 'KEB-001', 'Gudeta', 2.5, '+251911000000', 1, 'Registered', 1),
            ('FAR-002', 'ETH-20394857', 'Kebede Tessema', 'KEB-001', 'Gudeta', 1.8, '+251911000001', 0, 'In Queue', None),
            ('FAR-003', 'ETH-30495867', 'Almaz Ayana', 'KEB-001', 'Boreta', 3.0, '+251911000002', 1, 'Registered', 1),
            ('FAR-004', 'ETH-40596877', 'Tirunesh Dibaba', 'KEB-001', 'Boreta', 1.2, '+251911000003', 0, 'In Queue', None),
            ('FAR-005', 'ETH-50697887', 'Haile Gebrselassie', 'KEB-001', 'Gudeta', 4.1, '+251911000004', 1, 'Registered', None),
        ]
        cursor.executemany("""
            INSERT INTO farmers VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, seed_farmers)
        
    conn.commit()
    conn.close()

init_db()

# ==================== REST API ENDPOINTS (FLASK INTEGRATION) ====================
api_app = Flask(__name__)

@api_app.route('/api/farmers', methods=['GET'])
def api_get_farmers():
    conn = get_db_connection()
    farmers = conn.execute("SELECT * FROM farmers").fetchall()
    conn.close()
    return jsonify([dict(f) for f in farmers])

@api_app.route('/api/verify-fee', methods=['POST'])
def api_verify_fee():
    data = request.json or {}
    national_id = data.get("national_id")
    verified = data.get("verified", 1)
    
    if not national_id:
        return jsonify({"error": "Missing national_id"}), 400
        
    conn = get_db_connection()
    conn.execute("UPDATE farmers SET fee_verified = ? WHERE national_id = ?", (verified, national_id))
    conn.commit()
    conn.close()
    return jsonify({"status": "success", "national_id": national_id, "fee_verified": verified})

@api_app.route('/api/groups/<int:group_id>/csv', methods=['GET'])
def api_group_csv(group_id):
    conn = get_db_connection()
    farmers = conn.execute("SELECT * FROM farmers WHERE group_id = ?", (group_id,)).fetchall()
    conn.close()
    
    if not farmers:
        return jsonify({"error": "No farmers found in this group"}), 404
        
    df = pd.DataFrame([dict(f) for f in farmers])
    output = df.to_csv(index=False, encoding='utf-8')
    return Response(output, mimetype="text/csv", headers={"Content-disposition": f"attachment; filename=group_{group_id}.csv"})

def run_flask():
    api_app.run(port=5000, host='0.0.0.0', debug=False, use_reloader=False)

# Start background Flask server for REST API if not already running
if "api_thread" not in st.session_state:
    thread = threading.Thread(target=run_flask, daemon=True)
    thread.start()
    st.session_state.api_thread = thread

# ==================== PAGE CONFIG & STYLING ====================
st.set_page_config(
    page_title="Fertilizer Distribution System",
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

# ==================== SESSION STATE INITIALIZATION ====================
if "user" not in st.session_state:
    st.session_state.user = None

def logout():
    st.session_state.user = None
    st.query_params.clear()
    st.rerun()

# ==================== DA WORKER PORTAL ====================
def show_da_worker():
    st.markdown("""
        <div class="hero-banner">
            <h1>🌾 Field Operations & DA Portal</h1>
            <p>Verify fees, register farmers, manage queues, and construct verified distribution groups.</p>
        </div>
    """, unsafe_allow_html=True)

    conn = get_db_connection()
    kebele_info = conn.execute("SELECT * FROM kebeles WHERE id = 'KEB-001'").fetchone()

    if kebele_info:
        c1, c2, c3 = st.columns(3)
        c1.metric("Kebele Name", kebele_info["name"])
        c2.metric("Assigned Assistant", kebele_info["assistant_name"])
        c3.metric("Fertilizer Quota", f"{kebele_info['fertilizer_quota']} Quintals")

    st.sidebar.markdown("### DA Navigation")
    menu = st.sidebar.radio("Select Module", [
        "💳 Fee Verification Dashboard",
        "📝 Register Farmer", 
        "⏳ Verified Farmer Queue", 
        "✅ Registered Farmers Directory", 
        "🎲 Distribution Grouping & CSV",
        "🌐 REST API Information"
    ])

    # ---------------- 1. FEE VERIFICATION DASHBOARD ----------------
    if menu == "💳 Fee Verification Dashboard":
        st.subheader("💳 DA Fee Verification Dashboard")
        st.write("Search, verify, or revoke farmer service fee verification statuses.")

        search_id = st.text_input("🔍 Search Farmer by National ID or Name", placeholder="e.g., ETH-10293847 or Abebe")

        if search_id:
            query = "SELECT * FROM farmers WHERE national_id LIKE ? OR name LIKE ?"
            results = conn.execute(query, (f"%{search_id}%", f"%{search_id}%")).fetchall()
        else:
            results = conn.execute("SELECT * FROM farmers").fetchall()

        if results:
            df_results = pd.DataFrame([dict(r) for r in results])
            st.dataframe(df_results, use_container_width=True, hide_index=True)

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
        else:
            st.info("No matching records found.")

    # ---------------- 2. REGISTER FARMER ----------------
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
                            VALUES (?, ?, ?, 'KEB-001', ?, ?, ?, ?, 'In Queue')
                        """, (f_id, f_nat_id, f_name, f_village, f_land, f_phone, fee_val))
                        conn.commit()
                        st.success(f"Farmer '{f_name}' registered successfully with National ID `{f_nat_id}`!")
                        st.rerun()
                    except sqlite3.IntegrityError:
                        st.error(f"❌ Error: A farmer with National ID `{f_nat_id}` already exists. Duplicate IDs are strictly prohibited.")

    # ---------------- 3. VERIFIED FARMER QUEUE ----------------
    elif menu == "⏳ Verified Farmer Queue":
        st.subheader("⏳ Pending Queue (Access Restricted to Fee-Verified Farmers)")
        st.caption("🔒 Access Enforcement: Only farmers with verified fee payments appear in this operational queue.")

        queue_farmers = conn.execute("SELECT * FROM farmers WHERE fee_verified = 1 AND status = 'In Queue'").fetchall()

        if not queue_farmers:
            st.warning("No fee-verified farmers are currently waiting in the queue. Complete fee verification in the Fee Dashboard first.")
        else:
            df_queue = pd.DataFrame([dict(f) for f in queue_farmers])
            st.dataframe(df_queue, use_container_width=True, hide_index=True)

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

    # ---------------- 4. REGISTERED FARMERS DIRECTORY ----------------
    elif menu == "✅ Registered Farmers Directory":
        st.subheader("✅ Fully Registered Farmers Directory")
        registered_farmers = conn.execute("SELECT * FROM farmers WHERE status = 'Registered'").fetchall()

        if not registered_farmers:
            st.warning("No fully registered farmers found.")
        else:
            st.dataframe(pd.DataFrame([dict(f) for f in registered_farmers]), use_container_width=True, hide_index=True)

    # ---------------- 5. GROUPING & CSV EXPORT ----------------
    elif menu == "🎲 Distribution Grouping & CSV":
        st.subheader("🎲 Fertilizer Distribution Grouping Engine")
        st.caption("🔒 Access Restriction: Only fee-verified and fully registered farmers can be assigned into distribution groups.")

        verified_registered = conn.execute("SELECT * FROM farmers WHERE status = 'Registered' AND fee_verified = 1").fetchall()

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
                    st.success("Groups successfully generated and updated in the database!")
                    st.rerun()

            with col2:
                grouped_data = conn.execute("SELECT DISTINCT group_id FROM farmers WHERE group_id IS NOT NULL ORDER BY group_id").fetchall()
                if grouped_data:
                    st.write("### Active Distribution Batches")
                    for g_row in grouped_data:
                        g_id = g_row["group_id"]
                        members = conn.execute("SELECT * FROM farmers WHERE group_id = ?", (g_id,)).fetchall()
                        df_members = pd.DataFrame([dict(m) for m in members])
                        
                        with st.expander(f"📦 Group Batch #{g_id} ({len(members)} Members)", expanded=True):
                            st.dataframe(df_members[["id", "national_id", "name", "phone", "village", "land_size"]], hide_index=True)
                            
                            # CSV Export Engine
                            csv_buffer = StringIO()
                            df_members.to_csv(csv_buffer, index=False, encoding='utf-8')
                            st.download_button(
                                label=f"📥 Download Group #{g_id} CSV",
                                data=csv_buffer.getvalue(),
                                file_name=f"fertilizer_group_{g_id}.csv",
                                mime="text/csv",
                                key=f"dl_g_{g_id}"
                            )

    # ---------------- 6. REST API DOCUMENTATION ----------------
    elif menu == "🌐 REST API Information":
        st.subheader("🌐 Built-in REST API Documentation")
        st.write("The system runs a background JSON REST API engine on port `5000`.")

        st.code("""
# GET List of All Farmers
curl -X GET http://localhost:5000/api/farmers

# POST Verify Fee Status
curl -X POST http://localhost:5000/api/verify-fee \\
     -H "Content-Type: application/json" \\
     -d '{"national_id": "ETH-20394857", "verified": 1}'

# GET Download Group CSV via API
curl -X GET http://localhost:5000/api/groups/1/csv -o group_1.csv
        """, language="bash")

    conn.close()
    st.sidebar.markdown("---")
    st.sidebar.button("🚪 Sign Out", on_click=logout, use_container_width=True)

# ==================== MAIN APPLICATION ROUTER ====================
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
            st.info("🔐 Access the DA Field Operations Portal below to start.")
            if st.button("Enter DA Officer Portal", use_container_width=True, type="primary"):
                st.session_state.user = {"role": "da_worker", "name": "Alemayehu Tadesse"}
                st.rerun()
    else:
        show_da_worker()

if __name__ == "__main__":
    main()
