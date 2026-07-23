import streamlit as st
import pandas as pd
import random

# ==================== PAGE CONFIG & STYLING ====================
st.set_page_config(
    page_title="Fertilizer Distribution System",
    page_icon="🌾",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Modern Responsive Styling
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
    .stCode { border-radius: 10px !important; border: 1px solid #cbd5e1 !important; }
    .stButton>button { border-radius: 8px !important; font-weight: 600 !important; }
    </style>
""", unsafe_allow_html=True)

# ==================== DYNAMIC URL DETECTION ====================
def get_app_url():
    """Dynamically detects the actual live domain to prevent 'App does not exist' errors."""
    try:
        host = st.context.headers.get("Host", "")
        if host:
            return f"https://{host}"
    except Exception:
        pass
    return "https://your-app.streamlit.app"

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
        {
            "id": "KEB-001", 
            "name": "Yebu Kebele", 
            "woreda_id": "WRD-001", 
            "da_name": "Alemayehu Tadesse", 
            "assistant_name": "Getachew Bekele", 
            "fertilizer_quota": 500  # in Quintals
        }
    ]

if "villages" not in st.session_state:
    st.session_state.villages = [
        {"id": "VIL-001", "name": "Gudeta Village", "kebele_id": "KEB-001"},
        {"id": "VIL-002", "name": "Boreta Village", "kebele_id": "KEB-001"}
    ]

if "farmers" not in st.session_state:
    st.session_state.farmers = [
        {"id": "FAR-001", "name": "Abebe Bikila", "kebele_id": "KEB-001", "village": "Gudeta", "land_size": 2.5, "phone": "+251911000000", "status": "Registered"},
        {"id": "FAR-002", "name": "Kebede Tessema", "kebele_id": "KEB-001", "village": "Gudeta", "land_size": 1.8, "phone": "+251911000001", "status": "In Queue"},
        {"id": "FAR-003", "name": "Almaz Ayana", "kebele_id": "KEB-001", "village": "Boreta", "land_size": 3.0, "phone": "+251911000002", "status": "Registered"},
        {"id": "FAR-004", "name": "Tirunesh Dibaba", "kebele_id": "KEB-001", "village": "Boreta", "land_size": 1.2, "phone": "+251911000003", "status": "In Queue"}
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
            "name": query_params.get("da_name", "Development Agent"),
            "kebele_id": query_params.get("kebele_id", "KEB-001")
        }

def logout():
    st.session_state.user = None
    st.query_params.clear()
    st.rerun()

# ==================== 1. REGIONAL MANAGER (REGISTERS ZONES) ====================
def show_regional_manager():
    st.markdown("""
        <div class="hero-banner">
            <h1>🗺️ Regional Executive Portal</h1>
            <p>Register Zones and generate access links for Zonal Managers.</p>
        </div>
    """, unsafe_allow_html=True)

    col1, col2, col3 = st.columns(3)
    col1.metric("Registered Zones", len(st.session_state.zones))
    col2.metric("Total Woredas", len(st.session_state.woredas))
    col3.metric("Total Kebeles", len(st.session_state.kebeles))

    st.markdown("---")
    left_col, right_col = st.columns([1.5, 1])

    with left_col:
        st.subheader("➕ Register New Zone")
        with st.form("add_zone_form"):
            z_name = st.text_input("Zone Name", placeholder="e.g., Jimma Zone")
            submit = st.form_submit_button("Register Zone", use_container_width=True)
            if submit and z_name:
                new_id = f"ZN-00{len(st.session_state.zones)+1}"
                st.session_state.zones.append({"id": new_id, "name": z_name, "region_id": st.session_state.user.get("region_id", "REG-001")})
                st.success(f"Zone '{z_name}' registered successfully!")
                st.rerun()

        st.subheader("📋 Registered Zones")
        st.dataframe(pd.DataFrame(st.session_state.zones), use_container_width=True, hide_index=True)

    with right_col:
        st.subheader("🔗 Send Link to Zonal Manager")
        if st.session_state.zones:
            selected_zone = st.selectbox("Select Zone", st.session_state.zones, format_func=lambda x: x["name"])
            generated_link = f"{get_app_url()}/?role=zonal_manager&zone_id={selected_zone['id']}"
            st.code(generated_link, language="text")
            st.success("Copy and share this link with the assigned Zonal Manager.")

    st.sidebar.markdown("### User Session")
    st.sidebar.info(f"**Logged in as:**\n{st.session_state.user['name']}")
    st.sidebar.button("🚪 Sign Out", on_click=logout, use_container_width=True)

# ==================== 2. ZONAL MANAGER (REGISTERS WOREDAS) ====================
def show_zonal_manager():
    st.markdown("""
        <div class="hero-banner">
            <h1>🏛️ Zonal Operations Portal</h1>
            <p>Register Woredas and generate access links for Woreda Managers.</p>
        </div>
    """, unsafe_allow_html=True)

    col1, col2 = st.columns(2)
    col1.metric("Managed Woredas", len(st.session_state.woredas))
    col2.metric("Active Kebeles", len(st.session_state.kebeles))

    st.markdown("---")
    left_col, right_col = st.columns([1.5, 1])

    with left_col:
        st.subheader("➕ Register New Woreda")
        with st.form("add_woreda_form"):
            w_name = st.text_input("Woreda Name", placeholder="e.g., Manna Woreda")
            submit = st.form_submit_button("Register Woreda", use_container_width=True)
            if submit and w_name:
                new_id = f"WRD-00{len(st.session_state.woredas)+1}"
                st.session_state.woredas.append({"id": new_id, "name": w_name, "zone_id": st.session_state.user.get("zone_id", "ZN-001")})
                st.success(f"Woreda '{w_name}' registered successfully!")
                st.rerun()

        st.subheader("📋 Managed Woredas")
        st.dataframe(pd.DataFrame(st.session_state.woredas), use_container_width=True, hide_index=True)

    with right_col:
        st.subheader("🔗 Send Link to Woreda Manager")
        if st.session_state.woredas:
            selected_woreda = st.selectbox("Select Woreda", st.session_state.woredas, format_func=lambda x: x["name"])
            generated_link = f"{get_app_url()}/?role=woreda_manager&woreda_id={selected_woreda['id']}"
            st.code(generated_link, language="text")
            st.success("Share this link with the assigned Woreda Manager.")

    st.sidebar.markdown("### User Session")
    st.sidebar.info(f"**Logged in as:**\n{st.session_state.user['name']}")
    st.sidebar.button("🚪 Sign Out", on_click=logout, use_container_width=True)

# ==================== 3. WOREDA MANAGER (REGISTERS KEBELE, DA, ASSISTANT, FERTILIZER) ====================
def show_woreda_manager():
    st.markdown("""
        <div class="hero-banner">
            <h1>📍 Woreda Administration Portal</h1>
            <p>Register Kebeles, assign Development Agents (DA), Assistants, and Fertilizer Quotas.</p>
        </div>
    """, unsafe_allow_html=True)

    col1, col2 = st.columns(2)
    col1.metric("Registered Kebeles", len(st.session_state.kebeles))
    total_quota = sum([k.get("fertilizer_quota", 0) for k in st.session_state.kebeles])
    col2.metric("Total Assigned Fertilizer", f"{total_quota} Quintals")

    st.markdown("---")
    left_col, right_col = st.columns([1.5, 1])

    with left_col:
        st.subheader("➕ Register Kebele & Assign Field Team")
        with st.form("add_kebele_full_form"):
            k_name = st.text_input("Kebele Name", placeholder="e.g., Yebu Kebele")
            da_name = st.text_input("Development Agent (DA) Name", placeholder="e.g., Alemayehu Tadesse")
            assistant_name = st.text_input("Assistant Name", placeholder="e.g., Getachew Bekele")
            f_quota = st.number_input("Assign Fertilizer Quota (Quintals)", min_value=1, value=100, step=10)

            submit = st.form_submit_button("Register Kebele & Assign Quota", use_container_width=True)
            if submit and k_name and da_name:
                new_id = f"KEB-00{len(st.session_state.kebeles)+1}"
                st.session_state.kebeles.append({
                    "id": new_id,
                    "name": k_name,
                    "woreda_id": st.session_state.user.get("woreda_id", "WRD-001"),
                    "da_name": da_name,
                    "assistant_name": assistant_name,
                    "fertilizer_quota": f_quota
                })
                st.success(f"Kebele '{k_name}' registered with DA '{da_name}' and {f_quota} Quintals fertilizer!")
                st.rerun()

        st.subheader("📋 Kebele Field Assignments")
        st.dataframe(pd.DataFrame(st.session_state.kebeles), use_container_width=True, hide_index=True)

    with right_col:
        st.subheader("🔗 Send Link to DA Worker")
        if st.session_state.kebeles:
            selected_kebele = st.selectbox("Select Kebele", st.session_state.kebeles, format_func=lambda x: f"{x['name']} (DA: {x['da_name']})")
            generated_link = f"{get_app_url()}/?role=da_worker&kebele_id={selected_kebele['id']}&da_name={selected_kebele['da_name']}"
            st.code(generated_link, language="text")
            st.success("Send this link to the DA Worker. They will only access the Field Operations portal.")

    st.sidebar.markdown("### User Session")
    st.sidebar.info(f"**Logged in as:**\n{st.session_state.user['name']}")
    st.sidebar.button("🚪 Sign Out", on_click=logout, use_container_width=True)

# ==================== 4. DA WORKER (FARMER REGISTRATION, QUEUE, REGISTERED, GROUPING) ====================
def show_da_worker():
    st.markdown("""
        <div class="hero-banner">
            <h1>🌾 Field Operations & DA Portal</h1>
            <p>Manage farmer enrollments, view queues, check registered farmers, and create distribution groups.</p>
        </div>
    """, unsafe_allow_html=True)

    # Find Kebele info
    current_kebele_id = st.session_state.user.get("kebele_id", "KEB-001")
    kebele_info = next((k for k in st.session_state.kebeles if k["id"] == current_kebele_id), None)
    
    if kebele_info:
        c1, c2, c3 = st.columns(3)
        c1.metric("Kebele Name", kebele_info["name"])
        c2.metric("Assigned Assistant", kebele_info.get("assistant_name", "N/A"))
        c3.metric("Fertilizer Quota", f"{kebele_info.get('fertilizer_quota', 0)} Quintals")

    st.sidebar.markdown("### DA Navigation")
    menu = st.sidebar.radio("Select Module", [
        "📝 Register Farmer", 
        "⏳ Farmer Queue", 
        "✅ Registered Farmers", 
        "🎲 Grouping Page"
    ])

    # 1. REGISTER FARMER
    if menu == "📝 Register Farmer":
        st.subheader("📝 Register New Farmer")
        with st.form("add_farmer_form"):
            col1, col2 = st.columns(2)
            with col1:
                f_name = st.text_input("Farmer Full Name", placeholder="e.g., Chala Beyene")
                f_phone = st.text_input("Phone Number", placeholder="+2519...")
            with col2:
                f_village = st.text_input("Village / Got Name", placeholder="e.g., Gudeta")
                f_land = st.number_input("Farmland Area (Hectares)", min_value=0.1, value=1.0, step=0.1)

            f_status = st.selectbox("Registration Mode", ["In Queue", "Registered"])

            submit = st.form_submit_button("Submit Farmer Record", use_container_width=True)
            if submit and f_name:
                f_id = f"FAR-00{len(st.session_state.farmers)+1}"
                st.session_state.farmers.append({
                    "id": f_id,
                    "name": f_name,
                    "kebele_id": current_kebele_id,
                    "village": f_village,
                    "land_size": f_land,
                    "phone": f_phone,
                    "status": f_status
                })
                st.success(f"Farmer '{f_name}' added directly to **{f_status}**!")
                st.rerun()

    # 2. FARMER QUEUE
    elif menu == "⏳ Farmer Queue":
        st.subheader("⏳ Farmer Pending Queue")
        st.write("Farmers waiting for verification or distribution approval.")
        
        queue_farmers = [f for f in st.session_state.farmers if f["kebele_id"] == current_kebele_id and f["status"] == "In Queue"]
        
        if not queue_farmers:
            st.info("No farmers currently in the queue.")
        else:
            df_queue = pd.DataFrame(queue_farmers)
            st.dataframe(df_queue, use_container_width=True, hide_index=True)
            
            st.markdown("---")
            st.write("### Approve Farmer from Queue")
            selected_farmer_id = st.selectbox("Select Farmer to Approve", [f["id"] for f in queue_farmers], format_func=lambda x: next(f["name"] for f in queue_farmers if f["id"] == x))
            if st.button("Approve & Mark as Registered", type="primary"):
                for f in st.session_state.farmers:
                    if f["id"] == selected_farmer_id:
                        f["status"] = "Registered"
                st.success("Farmer approved successfully!")
                st.rerun()

    # 3. REGISTERED FARMERS
    elif menu == "✅ Registered Farmers":
        st.subheader("✅ Fully Registered Farmers Directory")
        registered_farmers = [f for f in st.session_state.farmers if f["kebele_id"] == current_kebele_id and f["status"] == "Registered"]
        
        if not registered_farmers:
            st.warning("No fully registered farmers found.")
        else:
            st.dataframe(pd.DataFrame(registered_farmers), use_container_width=True, hide_index=True)

    # 4. GROUPING PAGE
    elif menu == "🎲 Grouping Page":
        st.subheader("🎲 Fertilizer Distribution Grouping Page")
        st.write("Randomly group registered farmers into batches for fair fertilizer pickup.")

        registered_farmers = [f for f in st.session_state.farmers if f["kebele_id"] == current_kebele_id and f["status"] == "Registered"]

        if not registered_farmers:
            st.warning("You need registered farmers before creating distribution groups.")
        else:
            col1, col2 = st.columns([1, 2])
            with col1:
                group_size = st.number_input("Target Group Size", min_value=1, max_value=10, value=2)
                if st.button("Generate Random Groups", type="primary", use_container_width=True):
                    farmers_copy = registered_farmers.copy()
                    random.shuffle(farmers_copy)
                    groups = [farmers_copy[i:i + group_size] for i in range(0, len(farmers_copy), group_size)]
                    st.session_state.groups = groups
                    st.success(f"Formed {len(groups)} distribution group(s)!")

            with col2:
                if st.session_state.groups:
                    st.write("### Generated Pickup Batches")
                    for idx, group in enumerate(st.session_state.groups, 1):
                        with st.expander(f"📦 Batch Group #{idx} ({len(group)} Farmers)", expanded=True):
                            for f in group:
                                st.write(f"- **{f['name']}** — Land: {f['land_size']} ha | 📞 `{f['phone']}`")

    st.sidebar.markdown("---")
    st.sidebar.info(f"**DA Worker:**\n{st.session_state.user['name']}")
    st.sidebar.button("🚪 Sign Out", on_click=logout, use_container_width=True)

# ==================== MAIN ROUTER & LOGIN FALLBACK ====================
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
            st.warning("🔒 **Access Restricted:** Open the unique link generated by your superior manager to access your dashboard.")
            
            with st.expander("🛠️ Manual Testing Login (Role Selection)", expanded=True):
                selected_role = st.selectbox(
                    "Select Role Portal:",
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
