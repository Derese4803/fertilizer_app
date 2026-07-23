import streamlit as st
import pandas as pd
import random
from datetime import datetime

# ==================== PAGE CONFIG ====================
st.set_page_config(
    page_title="🌾 Fertilizer Distribution System",
    page_icon="🌾",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ==================== CUSTOM CSS ====================
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: 800;
        color: #1a237e;
        text-align: center;
        margin-bottom: 0.5rem;
    }
    .sub-header {
        font-size: 1.1rem;
        color: #666;
        text-align: center;
        margin-bottom: 2rem;
    }
</style>
""", unsafe_allow_html=True)

# ==================== DYNAMIC DATA SESSION STATE ====================
if "user" not in st.session_state:
    st.session_state.user = None

if "regions" not in st.session_state:
    st.session_state.regions = [
        {"id": "REG-01", "name": "Oromia", "zones": 21, "woredas": 340, "farmers": 45200, "fertilizer": 904000},
        {"id": "REG-02", "name": "Amhara", "zones": 12, "woredas": 180, "farmers": 38000, "fertilizer": 760000},
        {"id": "REG-03", "name": "SNNPR", "zones": 15, "woredas": 200, "farmers": 41000, "fertilizer": 820000},
    ]

if "zones" not in st.session_state:
    st.session_state.zones = [
        {"id": "ZN-001", "name": "Jimma Zone", "region_id": "REG-01", "woredas": 17, "farmers": 5400, "assigned": 50000, "distributed": 32000},
        {"id": "ZN-002", "name": "West Wellega", "region_id": "REG-01", "woredas": 22, "farmers": 7200, "assigned": 75000, "distributed": 48000},
    ]

if "woredas" not in st.session_state:
    st.session_state.woredas = [
        {"id": "WRD-001", "name": "Jimma Woreda", "zone_id": "ZN-001", "kebeles": 8, "farmers": 1240, "assigned": 5000, "distributed": 3200},
        {"id": "WRD-002", "name": "Seka Woreda", "zone_id": "ZN-001", "kebeles": 6, "farmers": 980, "assigned": 4000, "distributed": 2800},
    ]

if "kebeles" not in st.session_state:
    st.session_state.kebeles = [
        {"id": "KEB-001", "name": "Kebele 01", "woreda_id": "WRD-001", "villages": 3, "farmers": 156, "assigned": 600, "distributed": 450},
        {"id": "KEB-002", "name": "Kebele 02", "woreda_id": "WRD-001", "villages": 4, "farmers": 198, "assigned": 800, "distributed": 620},
        {"id": "KEB-003", "name": "Kebele 03", "woreda_id": "WRD-001", "villages": 3, "farmers": 234, "assigned": 800, "distributed": 520},
    ]

if "villages" not in st.session_state:
    st.session_state.villages = [
        {"id": "VIL-A", "name": "Village A", "kebele_id": "KEB-003", "farmers": 45},
        {"id": "VIL-B", "name": "Village B", "kebele_id": "KEB-003", "farmers": 67},
        {"id": "VIL-C", "name": "Village C", "kebele_id": "KEB-003", "farmers": 52},
    ]

if "farmers" not in st.session_state:
    st.session_state.farmers = [
        {"id": "F-001", "name": "Abebe Kebede", "national_id": "NID-1985-4455667", "kebele_id": "KEB-003", "village_id": "VIL-B", "land_size": 8.0, "entitled": 16, "taken": 6, "phone": "+251911223344"},
        {"id": "F-002", "name": "Fatuma Mohamed", "national_id": "NID-1990-7788990", "kebele_id": "KEB-003", "village_id": "VIL-B", "land_size": 5.5, "entitled": 11, "taken": 0, "phone": "+251922334455"},
        {"id": "F-003", "name": "Dawit Tesfaye", "national_id": "NID-1982-3344556", "kebele_id": "KEB-003", "village_id": "VIL-A", "land_size": 12.0, "entitled": 24, "taken": 10, "phone": "+251933445566"},
        {"id": "F-004", "name": "Hanna Tadesse", "national_id": "NID-1995-1122334", "kebele_id": "KEB-003", "village_id": "VIL-B", "land_size": 6.0, "entitled": 12, "taken": 5, "phone": "+251944556677"},
        {"id": "F-005", "name": "Mulugeta Alemu", "national_id": "NID-1988-2233445", "kebele_id": "KEB-003", "village_id": "VIL-B", "land_size": 4.0, "entitled": 8, "taken": 0, "phone": "+251955667788"},
        {"id": "F-006", "name": "Chaltu Dibaba", "national_id": "NID-1992-6677889", "kebele_id": "KEB-003", "village_id": "VIL-B", "land_size": 7.0, "entitled": 14, "taken": 0, "phone": "+251966778899"},
    ]

if "managers" not in st.session_state:
    st.session_state.managers = {
        "zonal": [
            {"id": "ZM-001", "name": "Ato Kebede Wolde", "username": "zm_kebede", "zone_id": "ZN-001", "region_id": "REG-01"},
        ],
        "woreda": [
            {"id": "WM-001", "name": "Ato Tadesse Alemu", "username": "wm_tadesse", "woreda_id": "WRD-001", "zone_id": "ZN-001"},
        ],
        "da": [
            {"id": "DA-001", "name": "Dawit Kebede", "username": "da_dawit", "kebele_id": "KEB-003", "woreda_id": "WRD-001"},
        ]
    }

# ==================== HELPER FUNCTIONS ====================
def calc_fertilizer(land_size, rate=2):
    return int(land_size * rate)

def format_num(num):
    return f"{num:,}"

# ==================== LOGIN PAGE ====================
def show_login():
    st.markdown('<p class="main-header">🌾 Fertilizer Distribution System</p>', unsafe_allow_html=True)
    st.markdown('<p class="sub-header">Government of Ethiopia | Ministry of Agriculture</p>', unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        st.markdown("### 🔐 Sign In")
        
        role = st.selectbox(
            "Select Your Role",
            ["regional_manager", "zonal_manager", "woreda_manager", "da_worker"],
            format_func=lambda x: {
                "regional_manager": "🗺️ Regional Manager",
                "zonal_manager": "🏛️ Zonal Manager",
                "woreda_manager": "📍 Woreda Manager",
                "da_worker": "👤 DA / Worker"
            }[x]
        )
        
        with st.form("login_form"):
            username = st.text_input("👤 Username", placeholder="Enter username")
            password = st.text_input("🔑 Password", type="password", placeholder="Enter password")
            st.caption("💡 Demo password: **admin123**")
            submitted = st.form_submit_button("🔐 SIGN IN", use_container_width=True, type="primary")
        
        if submitted:
            if password == "admin123":
                demo_users = {
                    "regional_manager": {
                        "id": "REGMGR-001", "name": "Ato Girma Bekele", "username": username,
                        "role": "regional_manager", "region_id": "REG-01", "region_name": "Oromia"
                    },
                    "zonal_manager": {
                        "id": "ZM-001", "name": "Ato Kebede Wolde", "username": username,
                        "role": "zonal_manager", "region_id": "REG-01", "region_name": "Oromia",
                        "zone_id": "ZN-001", "zone_name": "Jimma Zone"
                    },
                    "woreda_manager": {
                        "id": "WM-001", "name": "Ato Tadesse Alemu", "username": username,
                        "role": "woreda_manager", "region_id": "REG-01", "zone_id": "ZN-001",
                        "zone_name": "Jimma Zone", "woreda_id": "WRD-001", "woreda_name": "Jimma Woreda"
                    },
                    "da_worker": {
                        "id": "DA-001", "name": "Dawit Kebede", "username": username,
                        "role": "da_worker", "region_id": "REG-01", "zone_id": "ZN-001",
                        "woreda_id": "WRD-001", "kebele_id": "KEB-003", "kebele_name": "Kebele 03"
                    }
                }
                st.session_state.user = demo_users[role]
                st.success(f"✅ Welcome, {demo_users[role]['name']}!")
                st.rerun()
            else:
                st.error("❌ Invalid password! Use: **admin123**")

# ==================== REGIONAL MANAGER ====================
def show_regional_manager():
    user = st.session_state.user
    
    with st.sidebar:
        st.markdown(f"### 🗺️ {user['name']}")
        st.caption(f"Regional Manager | {user['region_name']}")
        st.divider()
        menu = st.radio("Menu", ["📊 Dashboard", "📦 Assign Zone + Fertilizer", "🏛️ Zone Management"])
        st.divider()
        if st.button("🚪 Logout", use_container_width=True):
            st.session_state.user = None
            st.rerun()
    
    if "Dashboard" in menu:
        st.header("📊 Regional Dashboard")
        zones = [z for z in st.session_state.zones if z["region_id"] == user["region_id"]]
        cols = st.columns(4)
        cols[0].metric("🗺️ Zones", len(zones))
        cols[1].metric("📍 Woredas", sum(z.get('woredas', 0) for z in zones))
        cols[2].metric("🌾 Farmers", format_num(sum(z.get('farmers', 0) for z in zones)))
        cols[3].metric("🧪 Fertilizer", f"{format_num(sum(z.get('assigned', 0) for z in zones))} bags")
        
        df = pd.DataFrame(zones)
        if not df.empty:
            st.dataframe(df[['name', 'woredas', 'farmers', 'assigned', 'distributed']], use_container_width=True, hide_index=True)

# ==================== ZONAL MANAGER ====================
def show_zonal_manager():
    user = st.session_state.user
    
    with st.sidebar:
        st.markdown(f"### 🏛️ {user['name']}")
        st.caption(f"Zonal Manager | {user['zone_name']}")
        st.divider()
        menu = st.radio("Menu", ["📊 Dashboard", "➕ Register Woreda", "📦 Assign Woreda + Fertilizer"])
        st.divider()
        if st.button("🚪 Logout", use_container_width=True):
            st.session_state.user = None
            st.rerun()
    
    if "Dashboard" in menu:
        st.header("📊 Zonal Dashboard")
        woredas = [w for w in st.session_state.woredas if w["zone_id"] == user["zone_id"]]
        cols = st.columns(4)
        cols[0].metric("📍 Woredas", len(woredas))
        cols[1].metric("🏘️ Kebeles", sum(w.get('kebeles', 0) for w in woredas))
        cols[2].metric("🌾 Farmers", format_num(sum(w.get('farmers', 0) for w in woredas)))
        cols[3].metric("🧪 Stock", f"{format_num(sum(w.get('assigned', 0) for w in woredas))} bags")
        
        df = pd.DataFrame(woredas)
        if not df.empty:
            st.dataframe(df[['name', 'kebeles', 'farmers', 'assigned', 'distributed']], use_container_width=True, hide_index=True)
            
    elif "Register Woreda" in menu:
        st.header("➕ Register New Woreda")
        col1, col2 = st.columns(2)
        
        with col1:
            with st.form("reg_woreda_form"):
                woreda_name = st.text_input("Woreda Name *", placeholder="e.g. Mana Woreda")
                est_kebeles = st.number_input("Estimated Kebeles", min_value=1, value=5)
                est_farmers = st.number_input("Estimated Farmers", min_value=0, value=500)
                
                if st.form_submit_button("✅ REGISTER WOREDA", use_container_width=True, type="primary"):
                    if not woreda_name:
                        st.error("❌ Please enter Woreda Name!")
                    else:
                        new_id = f"WRD-{len(st.session_state.woredas) + 1:03d}"
                        st.session_state.woredas.append({
                            "id": new_id,
                            "name": woreda_name,
                            "zone_id": user["zone_id"],
                            "kebeles": est_kebeles,
                            "farmers": est_farmers,
                            "assigned": 0,
                            "distributed": 0
                        })
                        st.success(f"✅ Woreda **{woreda_name}** successfully registered!")
                        st.rerun()
                        
        with col2:
            st.subheader("Registered Woredas in Zone")
            woredas = [w for w in st.session_state.woredas if w["zone_id"] == user["zone_id"]]
            for w in woredas:
                st.info(f"📍 **{w['name']}** (ID: {w['id']}) | {w['kebeles']} Kebeles")

# ==================== WOREDA MANAGER ====================
def show_woreda_manager():
    user = st.session_state.user
    
    with st.sidebar:
        st.markdown(f"### 📍 {user['name']}")
        st.caption(f"Woreda Manager | {user['woreda_name']}")
        st.divider()
        menu = st.radio("Menu", ["📊 Dashboard", "🏘️ Register Kebele", "👤 Register Worker/DA", "📦 Assign Kebele"])
        st.divider()
        if st.button("🚪 Logout", use_container_width=True):
            st.session_state.user = None
            st.rerun()
    
    if "Dashboard" in menu:
        st.header("📊 Woreda Dashboard")
        kebeles = [k for k in st.session_state.kebeles if k["woreda_id"] == user["woreda_id"]]
        cols = st.columns(3)
        cols[0].metric("🏘️ Kebeles", len(kebeles))
        cols[1].metric("🌾 Farmers", format_num(sum(k.get('farmers', 0) for k in kebeles)))
        cols[2].metric("🧪 Stock", f"{format_num(sum(k.get('assigned', 0) for k in kebeles))} bags")
        
        df = pd.DataFrame(kebeles)
        if not df.empty:
            st.dataframe(df[['name', 'villages', 'farmers', 'assigned', 'distributed']], use_container_width=True, hide_index=True)
            
    elif "Register Kebele" in menu:
        st.header("🏘️ Register New Kebele")
        col1, col2 = st.columns(2)
        
        with col1:
            with st.form("reg_kebele_form"):
                kebele_name = st.text_input("Kebele Name *", placeholder="e.g. Kebele 05")
                est_villages = st.number_input("Estimated Villages", min_value=1, value=3)
                est_farmers = st.number_input("Estimated Farmers", min_value=0, value=200)
                
                if st.form_submit_button("✅ REGISTER KEBELE", use_container_width=True, type="primary"):
                    if not kebele_name:
                        st.error("❌ Please enter Kebele Name!")
                    else:
                        new_id = f"KEB-{len(st.session_state.kebeles) + 1:03d}"
                        st.session_state.kebeles.append({
                            "id": new_id,
                            "name": kebele_name,
                            "woreda_id": user["woreda_id"],
                            "villages": est_villages,
                            "farmers": est_farmers,
                            "assigned": 0,
                            "distributed": 0
                        })
                        st.success(f"✅ Kebele **{kebele_name}** successfully registered!")
                        st.rerun()
                        
        with col2:
            st.subheader("Registered Kebeles")
            kebeles = [k for k in st.session_state.kebeles if k["woreda_id"] == user["woreda_id"]]
            for k in kebeles:
                st.info(f"🏘️ **{k['name']}** (ID: {k['id']}) | {k['farmers']} Farmers")

# ==================== DA WORKER ====================
def show_da_worker():
    user = st.session_state.user
    
    with st.sidebar:
        st.markdown(f"### 👤 {user['name']}")
        st.caption(f"DA Worker | {user['kebele_name']}")
        st.divider()
        menu = st.radio("Menu", [
            "📊 Dashboard",
            "🏡 Register Village",
            "➕ Register Farmer",
            "🎲 Group Generator",
            "📦 Distribute Fertilizer",
            "👥 My Farmers"
        ])
        st.divider()
        if st.button("🚪 Logout", use_container_width=True):
            st.session_state.user = None
            st.rerun()
    
    if "Dashboard" in menu:
        st.header("📊 DA Dashboard")
        my_farmers = [f for f in st.session_state.farmers if f["kebele_id"] == user["kebele_id"]]
        cols = st.columns(4)
        cols[0].metric("👥 My Farmers", len(my_farmers))
        cols[1].metric("🌾 Total Land", f"{sum(f.get('land_size', 0) for f in my_farmers):.1f} ha")
        cols[2].metric("🧪 Entitled", f"{sum(f.get('entitled', 0) for f in my_farmers)} bags")
        cols[3].metric("📦 Distributed", f"{sum(f.get('taken', 0) for f in my_farmers)} bags")

    elif "Register Village" in menu:
        st.header("🏡 Register New Village")
        col1, col2 = st.columns(2)
        
        with col1:
            with st.form("reg_village_form"):
                village_name = st.text_input("Village Name *", placeholder="e.g. Village D")
                est_farmers = st.number_input("Estimated Farmers", min_value=0, value=50)
                
                if st.form_submit_button("✅ REGISTER VILLAGE", use_container_width=True, type="primary"):
                    if not village_name:
                        st.error("❌ Please enter Village Name!")
                    else:
                        new_id = f"VIL-{chr(65 + len(st.session_state.villages))}"
                        st.session_state.villages.append({
                            "id": new_id,
                            "name": village_name,
                            "kebele_id": user["kebele_id"],
                            "farmers": est_farmers
                        })
                        st.success(f"✅ Village **{village_name}** successfully registered!")
                        st.rerun()
                        
        with col2:
            st.subheader("Registered Villages in Kebele")
            villages = [v for v in st.session_state.villages if v["kebele_id"] == user["kebele_id"]]
            for v in villages:
                st.info(f"🏡 **{v['name']}** (ID: {v['id']})")

    elif "Register Farmer" in menu:
        st.header("➕ Register New Farmer")
        villages = [v for v in st.session_state.villages if v["kebele_id"] == user["kebele_id"]]
        
        if not villages:
            st.warning("⚠️ Please register a village first under 'Register Village' menu!")
            return
            
        col1, col2 = st.columns(2)
        with col1:
            selected_village = st.selectbox("Select Village *", villages, format_func=lambda x: x['name'])
            
        with col2:
            with st.form("reg_farmer"):
                national_id = st.text_input("National ID *", placeholder="NID-YYYY-XXXXXXX")
                full_name = st.text_input("Full Name *")
                phone = st.text_input("Phone Number")
                land_size = st.number_input("Land Size (ha) *", min_value=0.5, value=2.0, step=0.5)
                entitled = calc_fertilizer(land_size, rate=2)
                
                st.info(f"🧪 Entitled Fertilizer: **{entitled} bags**")
                
                if st.form_submit_button("✅ REGISTER FARMER", use_container_width=True, type="primary"):
                    if not national_id or not full_name:
                        st.error("❌ National ID and Name are required!")
                    else:
                        st.session_state.farmers.append({
                            "id": f"F-{len(st.session_state.farmers) + 1:03d}",
                            "name": full_name,
                            "national_id": national_id,
                            "phone": phone,
                            "land_size": land_size,
                            "entitled": entitled,
                            "taken": 0,
                            "kebele_id": user["kebele_id"],
                            "village_id": selected_village["id"]
                        })
                        st.success(f"✅ Farmer {full_name} registered!")
                        st.balloons()

    elif "Group Generator" in menu:
        st.header("🎲 Auto Random Farmer Group Selection")
        st.caption("Organize registered farmers into random groups before distribution by village.")
        
        villages = [v for v in st.session_state.villages if v["kebele_id"] == user["kebele_id"]]
        if not villages:
            st.warning("⚠️ No villages found.")
            return

        col1, col2 = st.columns(2)
        with col1:
            sel_village = st.selectbox("Select Village", villages, format_func=lambda x: x['name'])
            village_farmers = [f for f in st.session_state.farmers if f.get("village_id") == sel_village["id"]]
            
            st.info(f"👥 Total Farmers in {sel_village['name']}: **{len(village_farmers)}**")
            
            group_size = st.number_input("Number of Farmers per Group", min_value=1, max_value=max(1, len(village_farmers)), value=min(5, max(1, len(village_farmers))))
            
            if st.button("🔀 GENERATE RANDOM GROUPS", type="primary", use_container_width=True):
                if len(village_farmers) == 0:
                    st.error("No registered farmers found in this village!")
                else:
                    shuffled_farmers = village_farmers.copy()
                    random.shuffle(shuffled_farmers)
                    
                    groups = [shuffled_farmers[i:i + group_size] for i in range(0, len(shuffled_farmers), group_size)]
                    st.session_state.generated_groups = groups
                    st.success(f"✅ Successfully created {len(groups)} group(s)!")

        with col2:
            st.subheader("📋 Group Selection Results")
            if "generated_groups" in st.session_state and st.session_state.generated_groups:
                for idx, group in enumerate(st.session_state.generated_groups, start=1):
                    with st.expander(f"📦 Group #{idx} ({len(group)} Farmers)", expanded=True):
                        for f in group:
                            st.write(f"- **{f['name']}** (NID: {f['national_id']}) — 🧪 {f['entitled']} bags")
            else:
                st.info("Set the group size and click 'Generate Random Groups'.")

    elif "Distribute" in menu:
        st.header("📦 Distribute Fertilizer")
        my_farmers = [f for f in st.session_state.farmers if f["kebele_id"] == user["kebele_id"]]
        eligible = [f for f in my_farmers if f.get('entitled', 0) > f.get('taken', 0)]
        
        st.write(f"👥 **{len(eligible)}** farmers eligible for distribution")
        
        for farmer in eligible:
            remaining = farmer['entitled'] - farmer['taken']
            with st.container(border=True):
                c = st.columns([3, 2, 2, 3])
                c[0].write(f"**{farmer['name']}**\n\nNID: {farmer['national_id']}")
                c[1].write(f"🌾 {farmer['land_size']} ha")
                c[2].write(f"Remaining: **{remaining} bags**")
                
                with c[3]:
                    give = st.number_input("Amount", min_value=1, max_value=remaining, value=remaining, key=f"g_{farmer['id']}")
                    if st.button("Confirm", key=f"btn_{farmer['id']}"):
                        farmer['taken'] += give
                        st.success(f"Gave {give} bags to {farmer['name']}!")
                        st.rerun()

    elif "My Farmers" in menu:
        st.header("👥 My Registered Farmers")
        my_farmers = [f for f in st.session_state.farmers if f["kebele_id"] == user["kebele_id"]]
        if my_farmers:
            df = pd.DataFrame(my_farmers)
            st.dataframe(df[['name', 'national_id', 'land_size', 'entitled', 'taken']], use_container_width=True, hide_index=True)

# ==================== MAIN ROUTING ====================
def main():
    if st.session_state.user is None:
        show_login()
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
