import streamlit as st
import pandas as pd
import random

# ==================== PAGE CONFIG ====================
st.set_page_config(
    page_title="🌾 Fertilizer Distribution Management System",
    page_icon="🌾",
    layout="wide"
)

# ==================== SESSION STATE INITIALIZATION ====================
# Initialize default data structures in session state so data persists during the session
if "user" not in st.session_state:
    st.session_state.user = None

if "regions" not in st.session_state:
    st.session_state.regions = [{"id": "REG-001", "name": "Oromia"}]

if "zones" not in st.session_state:
    st.session_state.zones = [{"id": "ZN-001", "name": "Jimma Zone", "region_id": "REG-001"}]

if "woredas" not in st.session_state:
    st.session_state.woredas = [{"id": "WRD-001", "name": "Manna Woreda", "zone_id": "ZN-001"}]

if "kebeles" not in st.session_state:
    st.session_state.kebeles = [{"id": "KEB-001", "name": "Yebu Kebele", "woreda_id": "WRD-001"}]

if "villages" not in st.session_state:
    st.session_state.villages = [
        {"id": "VIL-001", "name": "Village 01", "kebele_id": "KEB-001"},
        {"id": "VIL-002", "name": "Village 02", "kebele_id": "KEB-001"}
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

# ==================== URL QUERY PARAMETER ROUTING ====================
# Streamlit reads parameters from the URL (e.g. ?role=da_worker&kebele_id=KEB-001)
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
    # Replace this string with your deployed app URL (e.g., https://your-app.streamlit.app)
    return "https://your-app.streamlit.app"

def logout():
    st.session_state.user = None
    st.query_params.clear()
    st.rerun()

# ==================== 1. REGIONAL MANAGER DASHBOARD ====================
def show_regional_manager():
    st.title("🗺️ Regional Manager Dashboard")
    st.caption(f"Logged in as: **{st.session_state.user['name']}** | Region ID: {st.session_state.user.get('region_id', 'REG-001')}")
    st.markdown("---")

    col1, col2 = st.columns([2, 1])

    with col1:
        st.subheader("📊 Region Overview")
        st.metric("Total Zones", len(st.session_state.zones))
        st.metric("Total Woredas", len(st.session_state.woredas))
        st.metric("Total Registered Farmers", len(st.session_state.farmers))

        st.write("### Registered Zones")
        st.dataframe(pd.DataFrame(st.session_state.zones), use_container_width=True)

    with col2:
        st.subheader("🔗 Send Access Link to Zonal Manager")
        selected_zone = st.selectbox("Select Target Zone", st.session_state.zones, format_func=lambda x: x["name"])
        
        generated_link = f"{get_app_url()}/?role=zonal_manager&zone_id={selected_zone['id']}"
        
        st.code(generated_link, language="text")
        st.info("📋 **Instructions:** Copy and send this unique link to the Zonal Manager. Opening this link will give them direct access ONLY to their Zonal Dashboard.")

    st.sidebar.button("🚪 Logout", on_click=logout)

# ==================== 2. ZONAL MANAGER DASHBOARD ====================
def show_zonal_manager():
    st.title("🏛️ Zonal Manager Dashboard")
    st.caption(f"Logged in as: **{st.session_state.user['name']}** | Restricted to Zonal Scope")
    st.markdown("---")

    col1, col2 = st.columns([2, 1])

    with col1:
        st.subheader("➕ Add New Woreda")
        w_name = st.text_input("Woreda Name")
        if st.button("Register Woreda"):
            if w_name:
                new_id = f"WRD-00{len(st.session_state.woredas)+1}"
                st.session_state.woredas.append({"id": new_id, "name": w_name, "zone_id": st.session_state.user.get("zone_id", "ZN-001")})
                st.success(f"Woreda '{w_name}' successfully added!")
                st.rerun()

        st.write("### Managed Woredas")
        st.dataframe(pd.DataFrame(st.session_state.woredas), use_container_width=True)

    with col2:
        st.subheader("🔗 Send Access Link to Woreda Manager")
        if st.session_state.woredas:
            selected_woreda = st.selectbox("Select Target Woreda", st.session_state.woredas, format_func=lambda x: x["name"])
            generated_link = f"{get_app_url()}/?role=woreda_manager&woreda_id={selected_woreda['id']}"
            
            st.code(generated_link, language="text")
            st.info("📋 **Instructions:** Send this link to the Woreda Manager. They will not be able to view Regional or Zonal settings.")

    st.sidebar.button("🚪 Logout", on_click=logout)

# ==================== 3. WOREDA MANAGER DASHBOARD ====================
def show_woreda_manager():
    st.title("📍 Woreda Manager Dashboard")
    st.caption(f"Logged in as: **{st.session_state.user['name']}** | Restricted to Woreda Scope")
    st.markdown("---")

    col1, col2 = st.columns([2, 1])

    with col1:
        st.subheader("➕ Add New Kebele")
        k_name = st.text_input("Kebele Name")
        if st.button("Register Kebele"):
            if k_name:
                new_id = f"KEB-00{len(st.session_state.kebeles)+1}"
                st.session_state.kebeles.append({"id": new_id, "name": k_name, "woreda_id": st.session_state.user.get("woreda_id", "WRD-001")})
                st.success(f"Kebele '{k_name}' registered successfully!")
                st.rerun()

        st.write("### Managed Kebeles")
        st.dataframe(pd.DataFrame(st.session_state.kebeles), use_container_width=True)

    with col2:
        st.subheader("🔗 Send Access Link to DA Worker")
        if st.session_state.kebeles:
            selected_kebele = st.selectbox("Select Target Kebele", st.session_state.kebeles, format_func=lambda x: x["name"])
            generated_link = f"{get_app_url()}/?role=da_worker&kebele_id={selected_kebele['id']}"
            
            st.code(generated_link, language="text")
            st.info("📋 **Instructions:** Share this link with the assigned Development Agent (DA). They will only access the Field Operations & Registration tools.")

    st.sidebar.button("🚪 Logout", on_click=logout)

# ==================== 4. DA / FIELD WORKER DASHBOARD ====================
def show_da_worker():
    st.title("🌾 Field Operations — DA Dashboard")
    st.caption(f"Logged in as: **{st.session_state.user['name']}** | Kebele Scope")
    st.markdown("---")

    menu = st.sidebar.radio("Navigation", ["🏡 Village Management", "👨‍🌾 Farmer Registration", "🎲 Fertilizer Group Generator"])

    # 1. VILLAGE MANAGEMENT
    if menu == "🏡 Village Management":
        st.subheader("Register New Village")
        v_name = st.text_input("Village / Got Name")
        if st.button("Add Village"):
            if v_name:
                v_id = f"VIL-00{len(st.session_state.villages)+1}"
                st.session_state.villages.append({"id": v_id, "name": v_name, "kebele_id": st.session_state.user.get("kebele_id", "KEB-001")})
                st.success(f"Village '{v_name}' added!")
                st.rerun()

        st.write("### Current Villages")
        st.dataframe(pd.DataFrame(st.session_state.villages), use_container_width=True)

    # 2. FARMER REGISTRATION
    elif menu == "👨‍🌾 Farmer Registration":
        st.subheader("Register New Farmer")
        col1, col2 = st.columns(2)
        
        with col1:
            f_name = st.text_input("Full Name")
            f_phone = st.text_input("Phone Number")
        with col2:
            f_village = st.selectbox("Select Village", st.session_state.villages, format_func=lambda x: x["name"]) if st.session_state.villages else None
            f_land = st.number_input("Land Size (Hectares)", min_value=0.1, value=1.0, step=0.1)

        if st.button("Register Farmer"):
            if f_name and f_village:
                f_id = f"FAR-00{len(st.session_state.farmers)+1}"
                st.session_state.farmers.append({
                    "id": f_id,
                    "name": f_name,
                    "village_id": f_village["id"],
                    "land_size": f_land,
                    "phone": f_phone
                })
                st.success(f"Farmer '{f_name}' registered successfully!")
                st.rerun()

        st.write("### Registered Farmers")
        if st.session_state.farmers:
            df_farmers = pd.DataFrame(st.session_state.farmers)
            st.dataframe(df_farmers, use_container_width=True)

    # 3. FERTILIZER GROUP GENERATOR
    elif menu == "🎲 Fertilizer Group Generator":
        st.subheader("Generate Random Distribution Groups")
        st.write("Group farmers together randomly for fair fertilizer distribution batches.")

        if not st.session_state.farmers:
            st.warning("No farmers registered yet. Please register farmers first.")
        else:
            group_size = st.number_input("Target Group Size (Farmers per Group)", min_value=1, max_value=20, value=2)
            
            if st.button("Generate Random Groups"):
                farmers_copy = st.session_state.farmers.copy()
                random.shuffle(farmers_copy)
                
                groups = [farmers_copy[i:i + group_size] for i in range(0, len(farmers_copy), group_size)]
                st.session_state.groups = groups
                st.success(f"Successfully generated {len(groups)} distribution group(s)!")

            if st.session_state.groups:
                st.write("### Distribution Group Assignment")
                for idx, group in enumerate(st.session_state.groups, 1):
                    with st.expander(f"📦 Group {idx} ({len(group)} Farmers)", expanded=True):
                        for f in group:
                            st.write(f"- **{f['name']}** (ID: {f['id']}, Land: {f['land_size']} ha, Phone: {f['phone']})")

    st.sidebar.button("🚪 Logout", on_click=logout)

# ==================== MAIN ROUTER & LOGIN FALLBACK ====================
def main():
    if st.session_state.user is None:
        st.title("🌾 Fertilizer Distribution System")
        st.subheader("🔑 Access Restricted")
        st.info("Please click the specific access link sent to you by your superior manager.")
        st.markdown("---")
        
        st.write("### Manual Fallback Login (Testing Purpose Only)")
        selected_role = st.selectbox(
            "Select Role to Enter:",
            ["regional_manager", "zonal_manager", "woreda_manager", "da_worker"],
            format_func=lambda x: x.replace("_", " ").title()
        )
        
        if st.button("Enter Dashboard"):
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
