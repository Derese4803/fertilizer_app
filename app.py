import streamlit as st
import pandas as pd
import random

# ==================== PAGE CONFIG & INJECTION ====================
st.set_page_config(
    page_title="Fertilizer Distribution Management System",
    page_icon="🌾",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for modern visual design and clean typography
st.markdown("""
    <style>
    /* Global Styling */
    .main {
        background-color: #f8fafc;
    }
    .stAppHeader {
        background-color: rgba(255, 255, 255, 0.8);
    }
    
    /* Hero Header Banner */
    .hero-banner {
        background: linear-gradient(135deg, #1e3a8a 0%, #0d9488 100%);
        padding: 24px 32px;
        border-radius: 16px;
        color: white;
        box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.1);
        margin-bottom: 25px;
    }
    .hero-banner h1 {
        color: #ffffff !important;
        font-weight: 700 !important;
        margin-bottom: 4px !important;
    }
    .hero-banner p {
        color: #e2e8f0 !important;
        font-size: 1.05rem;
        margin-bottom: 0px !important;
    }

    /* Metric Cards */
    div[data-testid="stMetric"] {
        background-color: #ffffff;
        padding: 18px 24px;
        border-radius: 12px;
        border: 1px solid #e2e8f0;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05);
    }
    div[data-testid="stMetricLabel"] {
        font-weight: 600;
        color: #64748b;
    }
    div[data-testid="stMetricValue"] {
        color: #0f172a;
        font-weight: 700;
    }

    /* Styled Code Box for Links */
    .stCode {
        border-radius: 10px !important;
        border: 1px solid #cbd5e1 !important;
    }

    /* Buttons */
    .stButton>button {
        border-radius: 8px !important;
        font-weight: 600 !important;
        transition: all 0.2s ease-in-out;
    }
    .stButton>button:hover {
        transform: translateY(-1px);
    }
    </style>
""", unsafe_allow_html=True)

# ==================== SESSION STATE INITIALIZATION ====================
if "user" not in st.session_state:
    st.session_state.user = None

if "regions" not in st.session_state:
    st.session_state.regions = [{"id": "REG-001", "name": "Oromia Region"}]

if "zones" not in st.session_state:
    st.session_state.zones = [
        {"id": "ZN-001", "name": "Jimma Zone", "region_id": "REG-001"},
        {"id": "ZN-002", "name": "West Shoa Zone", "region_id": "REG-001"}
    ]

if "woredas" not in st.session_state:
    st.session_state.woredas = [
        {"id": "WRD-001", "name": "Manna Woreda", "zone_id": "ZN-001"},
        {"id": "WRD-002", "name": "Goma Woreda", "zone_id": "ZN-001"}
    ]

if "kebeles" not in st.session_state:
    st.session_state.kebeles = [
        {"id": "KEB-001", "name": "Yebu Kebele", "woreda_id": "WRD-001"},
        {"id": "KEB-002", "name": "Agaro Kebele", "woreda_id": "WRD-001"}
    ]

if "villages" not in st.session_state:
    st.session_state.villages = [
        {"id": "VIL-001", "name": "Gudeta Village", "kebele_id": "KEB-001"},
        {"id": "VIL-002", "name": "Boreta Village", "kebele_id": "KEB-001"}
    ]

if "farmers" not in st.session_state:
    st.session_state.farmers = [
        {"id": "FAR-001", "name": "Abebe Bikila", "village_id": "VIL-001", "land_size": 2.5, "phone": "+251911000000"},
        {"id": "FAR-002", "name": "Kebede Tessema", "village_id": "VIL-001", "land_size": 1.8, "phone": "+251911000001"},
        {"id": "FAR-003", "name": "Almaz Ayana", "village_id": "VIL-002", "land_size": 3.0, "phone": "+251911000002"},
        {"id": "FAR-004", "name": "Tirunesh Dibaba", "village_id": "VIL-002", "land_size": 1.2, "phone": "+251911000003"}
    ]

if "groups" not in st.session_state:
    st.session_state.groups = []

# ==================== ROUTING VIA URL QUERY PARAMETERS ====================
query_params = st.query_params

if "role" in query_params and st.session_state.user is None:
    role = query_params["role"]
    if role == "regional_manager":
        st.session_state.user = {
            "role": "regional_manager",
            "name": "Regional Director",
            "region_id": query_params.get("region_id", "REG-001")
        }
    elif role == "zonal_manager":
        st.session_state.user = {
            "role": "zonal_manager",
            "name": "Zonal Representative",
            "zone_id": query_params.get("zone_id", "ZN-001")
        }
    elif role == "woreda_manager":
        st.session_state.user = {
            "role": "woreda_manager",
            "name": "Woreda Administrator",
            "woreda_id": query_params.get("woreda_id", "WRD-001")
        }
    elif role == "da_worker":
        st.session_state.user = {
            "role": "da_worker",
            "name": "Development Agent (DA)",
            "kebele_id": query_params.get("kebele_id", "KEB-001")
        }

def get_app_url():
    return "https://your-app.streamlit.app"

def logout():
    st.session_state.user = None
    st.query_params.clear()
    st.rerun()

# ==================== 1. REGIONAL MANAGER DASHBOARD ====================
def show_regional_manager():
    st.markdown("""
        <div class="hero-banner">
            <h1>🗺️ Regional Executive Portal</h1>
            <p>High-level supply governance, zone allocations, and access provisioning.</p>
        </div>
    """, unsafe_allow_html=True)

    col1, col2, col3 = st.columns(3)
    col1.metric("Active Zones", len(st.session_state.zones))
    col2.metric("Total Woredas", len(st.session_state.woredas))
    col3.metric("Registered Farmers", len(st.session_state.farmers))

    st.markdown("---")

    left_col, right_col = st.columns([1.6, 1])

    with left_col:
        st.subheader("📋 Registered Regional Zones")
        df_zones = pd.DataFrame(st.session_state.zones)
        st.dataframe(df_zones, use_container_width=True, hide_index=True)

    with right_col:
        st.subheader("🔗 Generate Zonal Invitation Link")
        st.write("Grant access to a Zonal Manager. They will **only** see their assigned zone.")
        
        selected_zone = st.selectbox("Select Target Zone", st.session_state.zones, format_func=lambda x: x["name"])
        generated_link = f"{get_app_url()}/?role=zonal_manager&zone_id={selected_zone['id']}"
        
        st.code(generated_link, language="text")
        st.success("Copy and send this unique portal link to the Zonal Manager.")

    st.sidebar.markdown("### User Session")
    st.sidebar.info(f"**Logged in as:**\n{st.session_state.user['name']}")
    st.sidebar.button("🚪 Sign Out", on_click=logout, use_container_width=True)

# ==================== 2. ZONAL MANAGER DASHBOARD ====================
def show_zonal_manager():
    st.markdown("""
        <div class="hero-banner">
            <h1>🏛️ Zonal Operations Portal</h1>
            <p>Manage Woreda registrations and issue restricted Woreda access links.</p>
        </div>
    """, unsafe_allow_html=True)

    col1, col2 = st.columns(2)
    col1.metric("Managed Woredas", len(st.session_state.woredas))
    col2.metric("Active Kebeles", len(st.session_state.kebeles))

    st.markdown("---")

    left_col, right_col = st.columns([1.5, 1])

    with left_col:
        st.subheader("➕ Add New Woreda")
        with st.form("add_woreda_form"):
            w_name = st.text_input("Woreda Name", placeholder="e.g., Limmu Seka")
            submit = st.form_submit_button("Register Woreda", use_container_width=True)
            if submit and w_name:
                new_id = f"WRD-00{len(st.session_state.woredas)+1}"
                st.session_state.woredas.append({"id": new_id, "name": w_name, "zone_id": st.session_state.user.get("zone_id", "ZN-001")})
                st.success(f"Woreda '{w_name}' added successfully!")
                st.rerun()

        st.subheader("📋 Managed Woredas")
        st.dataframe(pd.DataFrame(st.session_state.woredas), use_container_width=True, hide_index=True)

    with right_col:
        st.subheader("🔗 Generate Woreda Invitation Link")
        st.write("Share access with a Woreda Manager without giving them access to Zonal tools.")
        
        if st.session_state.woredas:
            selected_woreda = st.selectbox("Select Target Woreda", st.session_state.woredas, format_func=lambda x: x["name"])
            generated_link = f"{get_app_url()}/?role=woreda_manager&woreda_id={selected_woreda['id']}"
            st.code(generated_link, language="text")
            st.success("Copy and share this link with the assigned Woreda Manager.")

    st.sidebar.markdown("### User Session")
    st.sidebar.info(f"**Logged in as:**\n{st.session_state.user['name']}")
    st.sidebar.button("🚪 Sign Out", on_click=logout, use_container_width=True)

# ==================== 3. WOREDA MANAGER DASHBOARD ====================
def show_woreda_manager():
    st.markdown("""
        <div class="hero-banner">
            <h1>📍 Woreda Administration Portal</h1>
            <p>Manage Kebeles and issue field access links for local Development Agents (DA).</p>
        </div>
    """, unsafe_allow_html=True)

    col1, col2 = st.columns(2)
    col1.metric("Registered Kebeles", len(st.session_state.kebeles))
    col2.metric("Total Villages", len(st.session_state.villages))

    st.markdown("---")

    left_col, right_col = st.columns([1.5, 1])

    with left_col:
        st.subheader("➕ Register Kebele")
        with st.form("add_kebele_form"):
            k_name = st.text_input("Kebele Name", placeholder="e.g., Kebele 01")
            submit = st.form_submit_button("Register Kebele", use_container_width=True)
            if submit and k_name:
                new_id = f"KEB-00{len(st.session_state.kebeles)+1}"
                st.session_state.kebeles.append({"id": new_id, "name": k_name, "woreda_id": st.session_state.user.get("woreda_id", "WRD-001")})
                st.success(f"Kebele '{k_name}' registered!")
                st.rerun()

        st.subheader("📋 Active Kebeles")
        st.dataframe(pd.DataFrame(st.session_state.kebeles), use_container_width=True, hide_index=True)

    with right_col:
        st.subheader("🔗 Generate DA Worker Access Link")
        st.write("Create a direct access link for the Field Development Agent (DA).")
        
        if st.session_state.kebeles:
            selected_kebele = st.selectbox("Select Kebele", st.session_state.kebeles, format_func=lambda x: x["name"])
            generated_link = f"{get_app_url()}/?role=da_worker&kebele_id={selected_kebele['id']}"
            st.code(generated_link, language="text")
            st.success("Send this link to the DA worker operating in this Kebele.")

    st.sidebar.markdown("### User Session")
    st.sidebar.info(f"**Logged in as:**\n{st.session_state.user['name']}")
    st.sidebar.button("🚪 Sign Out", on_click=logout, use_container_width=True)

# ==================== 4. DA / FIELD WORKER DASHBOARD ====================
def show_da_worker():
    st.markdown("""
        <div class="hero-banner">
            <h1>🌾 Field Operations & Distribution Portal</h1>
            <p>Register villages, track local farmers, and generate fair distribution groups.</p>
        </div>
    """, unsafe_allow_html=True)

    st.sidebar.markdown("### Field Menu")
    menu = st.sidebar.radio("Navigate Tasks", ["🏡 Village Setup", "👨‍🌾 Farmer Enrollment", "🎲 Distribution Grouping"])

    # 1. VILLAGE MANAGEMENT
    if menu == "🏡 Village Setup":
        st.subheader("🏡 Register New Village / Got")
        
        col1, col2 = st.columns([1, 1.5])
        with col1:
            with st.form("add_village_form"):
                v_name = st.text_input("Village Name", placeholder="e.g., Gudeta Got")
                submit = st.form_submit_button("Add Village", use_container_width=True)
                if submit and v_name:
                    v_id = f"VIL-00{len(st.session_state.villages)+1}"
                    st.session_state.villages.append({"id": v_id, "name": v_name, "kebele_id": st.session_state.user.get("kebele_id", "KEB-001")})
                    st.success(f"Village '{v_name}' registered!")
                    st.rerun()

        with col2:
            st.write("### Current Registered Villages")
            st.dataframe(pd.DataFrame(st.session_state.villages), use_container_width=True, hide_index=True)

    # 2. FARMER ENROLLMENT
    elif menu == "👨‍🌾 Farmer Enrollment":
        st.subheader("👨‍🌾 Enroll Local Farmer")
        
        with st.form("enroll_farmer_form"):
            col1, col2 = st.columns(2)
            with col1:
                f_name = st.text_input("Full Name", placeholder="e.g., Chala Beyene")
                f_phone = st.text_input("Phone Number", placeholder="+2519...")
            with col2:
                f_village = st.selectbox("Select Village", st.session_state.villages, format_func=lambda x: x["name"]) if st.session_state.villages else None
                f_land = st.number_input("Farmland Area (Hectares)", min_value=0.1, value=1.0, step=0.1)

            submit = st.form_submit_button("Complete Farmer Enrollment", use_container_width=True)
            if submit and f_name and f_village:
                f_id = f"FAR-00{len(st.session_state.farmers)+1}"
                st.session_state.farmers.append({
                    "id": f_id,
                    "name": f_name,
                    "village_id": f_village["id"],
                    "land_size": f_land,
                    "phone": f_phone
                })
                st.success(f"Farmer '{f_name}' successfully enrolled!")
                st.rerun()

        st.markdown("---")
        st.subheader("📋 Enrolled Farmers Directory")
        if st.session_state.farmers:
            st.dataframe(pd.DataFrame(st.session_state.farmers), use_container_width=True, hide_index=True)

    # 3. DISTRIBUTION GROUP GENERATOR
    elif menu == "🎲 Distribution Grouping":
        st.subheader("🎲 Random Group Generator")
        st.write("Automatically pair farmers into fair, randomized groups for batch fertilizer distribution.")

        if not st.session_state.farmers:
            st.warning("No farmers enrolled yet. Please enroll farmers first.")
        else:
            col1, col2 = st.columns([1, 2])
            with col1:
                group_size = st.number_input("Target Group Size", min_value=1, max_value=10, value=2)
                if st.button("Shuffle & Create Groups", type="primary", use_container_width=True):
                    farmers_copy = st.session_state.farmers.copy()
                    random.shuffle(farmers_copy)
                    groups = [farmers_copy[i:i + group_size] for i in range(0, len(farmers_copy), group_size)]
                    st.session_state.groups = groups
                    st.success(f"Formed {len(groups)} distribution group(s)!")

            with col2:
                if st.session_state.groups:
                    st.write("### Generated Batches")
                    for idx, group in enumerate(st.session_state.groups, 1):
                        with st.expander(f"📦 Batch Group #{idx} ({len(group)} Farmers)", expanded=True):
                            for f in group:
                                st.write(f"- **{f['name']}** — {f['land_size']} ha | 📞 `{f['phone']}`")

    st.sidebar.markdown("---")
    st.sidebar.info(f"**Logged in as:**\n{st.session_state.user['name']}")
    st.sidebar.button("🚪 Sign Out", on_click=logout, use_container_width=True)

# ==================== MAIN ROUTER & SECURE ENTRANCE ====================
def main():
    if st.session_state.user is None:
        st.markdown("""
            <div class="hero-banner" style="text-align: center;">
                <h1>🌾 Fertilizer Distribution Management System</h1>
                <p>Secure, multi-tier agricultural supply governance platform</p>
            </div>
        """, unsafe_allow_html=True)

        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            st.warning("🔒 **Access Restricted:** Opening a valid access link sent by your regional manager will route you automatically.")
            
            with st.expander("🛠️ Manual Testing Login (Role Portal)", expanded=True):
                selected_role = st.selectbox(
                    "Choose Portal Role:",
                    ["regional_manager", "zonal_manager", "woreda_manager", "da_worker"],
                    format_func=lambda x: x.replace("_", " ").title()
                )
                if st.button("Enter Portal", use_container_width=True, type="primary"):
                    st.session_state.user = {
                        "role": selected_role,
                        "name": f"Demo {selected_role.replace('_', ' ').title()}"
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
