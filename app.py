import streamlit as st
import pandas as pd
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
    .metric-card {
        background: #f8f9fa;
        padding: 1.5rem;
        border-radius: 10px;
        border-left: 5px solid #1a237e;
    }
    .success-msg {
        background: #d4edda;
        color: #155724;
        padding: 1rem;
        border-radius: 10px;
        border-left: 5px solid #28a745;
    }
    .info-box {
        background: #e7f3ff;
        padding: 1rem;
        border-radius: 10px;
        border-left: 5px solid #2196F3;
    }
</style>
""", unsafe_allow_html=True)

# ==================== DEMO DATA (NO DATABASE) ====================
REGIONS = [
    {"id": "REG-01", "name": "Oromia", "zones": 21, "woredas": 340, "farmers": 45200, "fertilizer": 904000},
    {"id": "REG-02", "name": "Amhara", "zones": 12, "woredas": 180, "farmers": 38000, "fertilizer": 760000},
    {"id": "REG-03", "name": "SNNPR", "zones": 15, "woredas": 200, "farmers": 41000, "fertilizer": 820000},
]

ZONES = [
    {"id": "ZN-001", "name": "Jimma Zone", "region_id": "REG-01", "woredas": 17, "farmers": 5400, "assigned": 50000, "distributed": 32000},
    {"id": "ZN-002", "name": "West Wellega", "region_id": "REG-01", "woredas": 22, "farmers": 7200, "assigned": 75000, "distributed": 48000},
    {"id": "ZN-003", "name": "East Wellega", "region_id": "REG-01", "woredas": 18, "farmers": 6100, "assigned": 62000, "distributed": 45000},
]

WOREDAS = [
    {"id": "WRD-001", "name": "Jimma Woreda", "zone_id": "ZN-001", "kebeles": 8, "farmers": 1240, "assigned": 5000, "distributed": 3200},
    {"id": "WRD-002", "name": "Seka Woreda", "zone_id": "ZN-001", "kebeles": 6, "farmers": 980, "assigned": 4000, "distributed": 2800},
    {"id": "WRD-003", "name": "Agaro Woreda", "zone_id": "ZN-002", "kebeles": 10, "farmers": 1500, "assigned": 6000, "distributed": 4200},
]

KEBELES = [
    {"id": "KEB-001", "name": "Kebele 01", "woreda_id": "WRD-001", "villages": 3, "farmers": 156, "assigned": 600, "distributed": 450},
    {"id": "KEB-002", "name": "Kebele 02", "woreda_id": "WRD-001", "villages": 4, "farmers": 198, "assigned": 800, "distributed": 620},
    {"id": "KEB-003", "name": "Kebele 03", "woreda_id": "WRD-001", "villages": 3, "farmers": 234, "assigned": 800, "distributed": 520},
    {"id": "KEB-004", "name": "Kebele 04", "woreda_id": "WRD-002", "villages": 5, "farmers": 180, "assigned": 700, "distributed": 500},
]

VILLAGES = [
    {"id": "VIL-A", "name": "Village A", "kebele_id": "KEB-003", "farmers": 45},
    {"id": "VIL-B", "name": "Village B", "kebele_id": "KEB-003", "farmers": 67},
    {"id": "VIL-C", "name": "Village C", "kebele_id": "KEB-003", "farmers": 52},
]

FARMERS = [
    {"id": "F-001", "name": "Abebe Kebede", "national_id": "NID-1985-4455667", "kebele_id": "KEB-003", "village_id": "VIL-B", "land_size": 8.0, "entitled": 16, "taken": 6, "phone": "+251911223344"},
    {"id": "F-002", "name": "Fatuma Mohamed", "national_id": "NID-1990-7788990", "kebele_id": "KEB-003", "village_id": "VIL-B", "land_size": 5.5, "entitled": 11, "taken": 0, "phone": "+251922334455"},
    {"id": "F-003", "name": "Dawit Tesfaye", "national_id": "NID-1982-3344556", "kebele_id": "KEB-003", "village_id": "VIL-A", "land_size": 12.0, "entitled": 24, "taken": 10, "phone": "+251933445566"},
    {"id": "F-004", "name": "Hanna Tadesse", "national_id": "NID-1995-1122334", "kebele_id": "KEB-001", "village_id": "VIL-A", "land_size": 6.0, "entitled": 12, "taken": 5, "phone": "+251944556677"},
]

MANAGERS = {
    "zonal": [
        {"id": "ZM-001", "name": "Ato Kebede Wolde", "username": "zm_kebede", "zone_id": "ZN-001", "region_id": "REG-01"},
        {"id": "ZM-002", "name": "Abebe Kebede", "username": "zm_abebe", "zone_id": "ZN-002", "region_id": "REG-01"},
    ],
    "woreda": [
        {"id": "WM-001", "name": "Ato Tadesse Alemu", "username": "wm_tadesse", "woreda_id": "WRD-001", "zone_id": "ZN-001"},
        {"id": "WM-002", "name": "Dawit Tesfaye", "username": "wm_dawit", "woreda_id": "WRD-002", "zone_id": "ZN-001"},
    ],
    "da": [
        {"id": "DA-001", "name": "Dawit Kebede", "username": "da_dawit", "kebele_id": "KEB-003", "woreda_id": "WRD-001"},
        {"id": "DA-002", "name": "Hanna Tadesse", "username": "da_hanna", "kebele_id": "KEB-001", "woreda_id": "WRD-001"},
    ]
}

# ==================== SESSION STATE ====================
if "user" not in st.session_state:
    st.session_state.user = None
if "registered_workers" not in st.session_state:
    st.session_state.registered_workers = []
if "registered_farmers" not in st.session_state:
    st.session_state.registered_farmers = []

# ==================== HELPER FUNCTIONS ====================
def calc_fertilizer(land_size, rate=2):
    return int(land_size * rate)

def format_num(num):
    return f"{num:,}"

def get_remaining(entitled, taken):
    return entitled - taken

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
        
        menu = st.radio("Menu", [
            "📊 Dashboard",
            "📦 Assign Zone + Fertilizer",
            "🏛️ Zone Management",
            "👥 Zonal Managers",
            "📈 Reports"
        ])
        
        st.divider()
        if st.button("🚪 Logout", use_container_width=True):
            st.session_state.user = None
            st.rerun()
    
    if "Dashboard" in menu:
        st.header("📊 Regional Dashboard")
        st.caption(f"Region: {user['region_name']} | Full System Control")
        
        zones = [z for z in ZONES if z["region_id"] == user["region_id"]]
        
        cols = st.columns(4)
        cols[0].metric("🗺️ Zones", len(zones))
        cols[1].metric("📍 Woredas", sum(z.get('woredas', 0) for z in zones))
        cols[2].metric("🌾 Farmers", format_num(sum(z.get('farmers', 0) for z in zones)))
        cols[3].metric("🧪 Fertilizer", f"{format_num(sum(z.get('assigned', 0) for z in zones))} bags")
        
        st.subheader("Zone Overview")
        df = pd.DataFrame(zones)
        if not df.empty:
            df['progress'] = (df['distributed'] / df['assigned'] * 100).round(1)
            st.dataframe(
                df[['name', 'woredas', 'farmers', 'assigned', 'distributed', 'progress']],
                column_config={
                    'name': 'Zone Name',
                    'woredas': 'Woredas',
                    'farmers': st.column_config.NumberColumn('Farmers', format='%d'),
                    'assigned': 'Assigned (bags)',
                    'distributed': 'Distributed (bags)',
                    'progress': st.column_config.ProgressColumn('Progress %', format='%.1f%%', min_value=0, max_value=100)
                },
                use_container_width=True,
                hide_index=True
            )
    
    elif "Assign Zone" in menu:
        st.header("📦 Assign Zone & Fertilizer")
        
        zones = [z for z in ZONES if z["region_id"] == user["region_id"]]
        managers = [m for m in MANAGERS["zonal"] if m["region_id"] == user["region_id"]]
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("Zone Selection")
            selected_zone = st.selectbox("Select Zone", zones, format_func=lambda x: x['name'])
            st.info(f"📍 {selected_zone['woredas']} Woredas | 🌾 {selected_zone['farmers']} Farmers")
            
            st.subheader("Manager Assignment")
            selected_manager = st.selectbox("Assign Zonal Manager", managers, format_func=lambda x: x['name'])
        
        with col2:
            st.subheader("Fertilizer Calculation")
            farmer_count = selected_zone['farmers']
            needed = farmer_count * 10
            
            st.metric("Total Farmers", farmer_count)
            st.metric("Estimated Need", f"{needed:,} bags")
            
            assign_amount = st.number_input("Assign Amount (bags)", min_value=0, value=needed, step=100)
            
            remaining = needed - assign_amount
            if remaining >= 0:
                st.success(f"✅ Within budget. Remaining: {remaining:,} bags")
            else:
                st.warning(f"⚠️ Over budget by {abs(remaining):,} bags")
        
        if st.button("✅ CONFIRM ASSIGNMENT", type="primary", use_container_width=True):
            st.success(f"🎉 Assigned {assign_amount:,} bags to **{selected_zone['name']}**!")
            st.balloons()
    
    elif "Zone Management" in menu:
        st.header("🏛️ Zone Management")
        zones = [z for z in ZONES if z["region_id"] == user["region_id"]]
        
        for zone in zones:
            with st.container(border=True):
                c = st.columns([3, 2, 2, 2, 3])
                c[0].write(f"**{zone['name']}**")
                c[1].write(f"📍 {zone['woredas']} Woredas")
                c[2].write(f"🌾 {zone['farmers']:,} Farmers")
                c[3].write(f"🧪 {zone['assigned']:,} bags")
                progress = zone['distributed'] / zone['assigned'] * 100 if zone['assigned'] > 0 else 0
                c[4].progress(progress / 100, text=f"{progress:.0f}%")
    
    elif "Zonal Managers" in menu:
        st.header("👥 Zonal Managers")
        managers = [m for m in MANAGERS["zonal"] if m["region_id"] == user["region_id"]]
        zones = [z for z in ZONES if z["region_id"] == user["region_id"]]
        
        col1, col2 = st.columns([1, 2])
        
        with col1:
            st.subheader("Register New Manager")
            with st.form("reg_mgr"):
                name = st.text_input("Full Name")
                username = st.text_input("Username", value="zm_")
                phone = st.text_input("Phone")
                zone = st.selectbox("Assign Zone", zones, format_func=lambda x: x['name'])
                pwd = st.text_input("Password", type="password")
                
                if st.form_submit_button("✅ Register", use_container_width=True):
                    st.success(f"✅ Manager {name} registered!")
        
        with col2:
            st.subheader("Existing Managers")
            for m in managers:
                with st.container(border=True):
                    st.write(f"**{m['name']}**")
                    st.caption(f"@{m['username']} | Zone: {m['zone_id']}")

# ==================== ZONAL MANAGER ====================
def show_zonal_manager():
    user = st.session_state.user
    
    with st.sidebar:
        st.markdown(f"### 🏛️ {user['name']}")
        st.caption(f"Zonal Manager | {user['zone_name']}")
        st.divider()
        
        menu = st.radio("Menu", [
            "📊 Dashboard",
            "📦 Assign Woreda + Fertilizer",
            "📍 Woreda Management",
            "👥 Woreda Managers",
            "📈 Reports"
        ])
        
        st.divider()
        if st.button("🚪 Logout", use_container_width=True):
            st.session_state.user = None
            st.rerun()
    
    if "Dashboard" in menu:
        st.header("📊 Zonal Dashboard")
        st.caption(f"Zone: {user['zone_name']} | Manages all Woredas")
        
        woredas = [w for w in WOREDAS if w["zone_id"] == user["zone_id"]]
        
        cols = st.columns(4)
        cols[0].metric("📍 Woredas", len(woredas))
        cols[1].metric("🏘️ Kebeles", sum(w.get('kebeles', 0) for w in woredas))
        cols[2].metric("🌾 Farmers", format_num(sum(w.get('farmers', 0) for w in woredas)))
        cols[3].metric("🧪 Total Stock", f"{format_num(sum(w.get('assigned', 0) for w in woredas))} bags")
        
        # Stock summary
        total_assigned = sum(w.get('assigned', 0) for w in woredas)
        total_distributed = sum(w.get('distributed', 0) for w in woredas)
        
        c1, c2, c3 = st.columns(3)
        c1.metric("📦 Received from Region", f"{total_assigned:,} bags")
        c2.metric("📤 Distributed", f"{total_distributed:,} bags")
        c3.metric("💰 Remaining", f"{total_assigned - total_distributed:,} bags")
        
        st.subheader("Woreda Overview")
        df = pd.DataFrame(woredas)
        if not df.empty:
            df['progress'] = (df['distributed'] / df['assigned'] * 100).round(1)
            st.dataframe(
                df[['name', 'kebeles', 'farmers', 'assigned', 'distributed', 'progress']],
                column_config={
                    'name': 'Woreda Name',
                    'kebeles': 'Kebeles',
                    'farmers': 'Farmers',
                    'assigned': 'Assigned',
                    'distributed': 'Distributed',
                    'progress': st.column_config.ProgressColumn('Progress', format='%.1f%%', min_value=0, max_value=100)
                },
                use_container_width=True,
                hide_index=True
            )
    
    elif "Assign Woreda" in menu:
        st.header("📦 Assign Woreda & Fertilizer")
        
        woredas = [w for w in WOREDAS if w["zone_id"] == user["zone_id"]]
        managers = [m for m in MANAGERS["woreda"] if m["zone_id"] == user["zone_id"]]
        
        col1, col2 = st.columns(2)
        
        with col1:
            selected_woreda = st.selectbox("Select Woreda", woredas, format_func=lambda x: x['name'])
            selected_manager = st.selectbox("Assign Manager", managers, format_func=lambda x: x['name'])
        
        with col2:
            farmer_count = selected_woreda['farmers']
            needed = farmer_count * 10
            st.metric("Farmers", farmer_count)
            st.metric("Need", f"{needed:,} bags")
            assign_amount = st.number_input("Assign Amount", min_value=0, value=needed, step=50)
        
        if st.button("✅ ASSIGN", type="primary", use_container_width=True):
            st.success(f"✅ {assign_amount:,} bags assigned to {selected_woreda['name']}!")

# ==================== WOREDA MANAGER ====================
def show_woreda_manager():
    user = st.session_state.user
    
    with st.sidebar:
        st.markdown(f"### 📍 {user['name']}")
        st.caption(f"Woreda Manager | {user['woreda_name']}")
        st.divider()
        
        menu = st.radio("Menu", [
            "📊 Dashboard",
            "👤 Register Worker/DA",
            "📦 Assign Kebele + Fertilizer",
            "🏘️ Kebele Management",
            "👥 My Workers",
            "📈 Reports"
        ])
        
        st.divider()
        if st.button("🚪 Logout", use_container_width=True):
            st.session_state.user = None
            st.rerun()
    
    if "Dashboard" in menu:
        st.header("📊 Woreda Dashboard")
        st.caption(f"Woreda: {user['woreda_name']} | Control Workers & Kebeles")
        
        kebeles = [k for k in KEBELES if k["woreda_id"] == user["woreda_id"]]
        workers = [w for w in MANAGERS["da"] if w["woreda_id"] == user["woreda_id"]]
        
        cols = st.columns(4)
        cols[0].metric("🏘️ Kebeles", len(kebeles))
        cols[1].metric("👤 Workers", len(workers))
        cols[2].metric("🌾 Farmers", format_num(sum(k.get('farmers', 0) for k in kebeles)))
        cols[3].metric("🧪 Stock", f"{format_num(sum(k.get('assigned', 0) for k in kebeles))} bags")
        
        total = sum(k.get('assigned', 0) for k in kebeles)
        distributed = sum(k.get('distributed', 0) for k in kebeles)
        
        c1, c2, c3 = st.columns(3)
        c1.metric("📦 Received", f"{total:,} bags")
        c2.metric("📤 Distributed", f"{distributed:,} bags")
        c3.metric("💰 Remaining", f"{total - distributed:,} bags")
    
    elif "Register Worker" in menu:
        st.header("👤 Register New Worker / DA")
        
        col1, col2 = st.columns(2)
        
        with col1:
            with st.form("reg_worker"):
                st.subheader("Worker Details")
                name = st.text_input("Full Name *")
                username = st.text_input("Username *", value="da_")
                phone = st.text_input("Phone Number")
                
                kebeles = [k for k in KEBELES if k["woreda_id"] == user["woreda_id"]]
                kebele = st.selectbox("Assign Kebele *", kebeles, format_func=lambda x: x['name'])
                
                password = st.text_input("Password *", type="password")
                confirm = st.text_input("Confirm Password *", type="password")
                
                submitted = st.form_submit_button("✅ REGISTER WORKER", use_container_width=True)
                
                if submitted:
                    if password != confirm:
                        st.error("❌ Passwords don't match!")
                    elif not all([name, username, password]):
                        st.error("❌ Fill all required fields!")
                    else:
                        worker = {
                            "name": name, "username": username, "phone": phone,
                            "kebele_id": kebele['id'], "kebele_name": kebele['name'],
                            "woreda_id": user['woreda_id'], "role": "da_worker"
                        }
                        st.session_state.registered_workers.append(worker)
                        st.success(f"✅ Worker {name} registered!")
                        st.json(worker)
        
        with col2:
            st.subheader("Registered Workers")
            all_workers = [w for w in MANAGERS["da"] if w["woreda_id"] == user["woreda_id"]] + st.session_state.registered_workers
            for w in all_workers:
                with st.container(border=True):
                    st.write(f"**{w['name']}**")
                    st.caption(f"@{w['username']} | Kebele: {w.get('kebele_name', w.get('kebele_id', 'N/A'))}")
    
    elif "Assign Kebele" in menu:
        st.header("📦 Assign Kebele & Fertilizer")
        
        kebeles = [k for k in KEBELES if k["woreda_id"] == user["woreda_id"]]
        
        col1, col2 = st.columns(2)
        
        with col1:
            selected_kebele = st.selectbox("Select Kebele", kebeles, format_func=lambda x: x['name'])
            farmer_count = selected_kebele['farmers']
            needed = farmer_count * 10
            st.metric("Farmers", farmer_count)
            st.metric("Need", f"{needed:,} bags")
        
        with col2:
            assign_amount = st.number_input("Assign Amount", min_value=0, value=needed, step=25)
            rate = assign_amount / farmer_count if farmer_count > 0 else 0
            st.info(f"📊 Rate: {rate:.1f} bags per farmer")
            
            if st.button("✅ ASSIGN TO KEBELE", type="primary", use_container_width=True):
                st.success(f"✅ {assign_amount:,} bags to {selected_kebele['name']}!")
    
    elif "Kebele Management" in menu:
        st.header("🏘️ Kebele Management")
        kebeles = [k for k in KEBELES if k["woreda_id"] == user["woreda_id"]]
        
        for kebele in kebeles:
            with st.container(border=True):
                c = st.columns([3, 2, 2, 2, 3])
                c[0].write(f"**{kebele['name']}**")
                c[1].write(f"🏡 {kebele['villages']} Villages")
                c[2].write(f"🌾 {kebele['farmers']} Farmers")
                c[3].write(f"🧪 {kebele['assigned']} bags")
                progress = kebele['distributed'] / kebele['assigned'] * 100 if kebele['assigned'] > 0 else 0
                c[4].progress(progress / 100, text=f"{progress:.0f}%")

# ==================== DA WORKER ====================
def show_da_worker():
    user = st.session_state.user
    
    with st.sidebar:
        st.markdown(f"### 👤 {user['name']}")
        st.caption(f"DA Worker | {user['kebele_name']}")
        st.divider()
        
        menu = st.radio("Menu", [
            "📊 Dashboard",
            "➕ Register Farmer",
            "📦 Distribute Fertilizer",
            "👥 My Farmers",
            "📈 My Reports"
        ])
        
        st.divider()
        if st.button("🚪 Logout", use_container_width=True):
            st.session_state.user = None
            st.rerun()
    
    if "Dashboard" in menu:
        st.header("📊 DA Dashboard")
        st.caption(f"Kebele: {user['kebele_name']} | Field Worker")
        
        my_farmers = [f for f in FARMERS if f["kebele_id"] == user["kebele_id"]] + \
                     [f for f in st.session_state.registered_farmers if f.get("kebele_id") == user["kebele_id"]]
        
        cols = st.columns(4)
        cols[0].metric("👥 My Farmers", len(my_farmers))
        cols[1].metric("🌾 Total Land", f"{sum(f.get('land_size', 0) for f in my_farmers):.1f} ha")
        cols[2].metric("🧪 Entitled", f"{sum(f.get('entitled', 0) for f in my_farmers)} bags")
        cols[3].metric("📦 Distributed", f"{sum(f.get('taken', 0) for f in my_farmers)} bags")
        
        st.subheader("⚡ Quick Actions")
        c1, c2, c3 = st.columns(3)
        if c1.button("➕ Register Farmer", use_container_width=True):
            st.session_state.page = "reg_farmer"
        if c2.button("📦 Give Fertilizer", use_container_width=True):
            st.session_state.page = "distribute"
        if c3.button("📊 View Reports", use_container_width=True):
            st.session_state.page = "reports"
    
    elif "Register Farmer" in menu:
        st.header("➕ Register New Farmer")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("#### 📍 Location (Auto-filled)")
            st.info(f"🗺️ Region: {user['region_id']}")
            st.info(f"🏛️ Zone: {user['zone_id']}")
            st.info(f"📍 Woreda: {user['woreda_id']}")
            st.info(f"🏘️ Kebele: {user['kebele_id']}")
            
            villages = [v for v in VILLAGES if v["kebele_id"] == user["kebele_id"]]
            selected_village = st.selectbox("Select Village *", villages, format_func=lambda x: x['name'])
        
        with col2:
            with st.form("reg_farmer"):
                st.subheader("Farmer Details")
                national_id = st.text_input("National ID *", placeholder="NID-YYYY-XXXXXXX")
                full_name = st.text_input("Full Name *")
                phone = st.text_input("Phone Number")
                household = st.number_input("Household Size", min_value=1, value=5)
                
                st.subheader("🌱 Land Information")
                land_size = st.number_input("Land Size (hectares) *", min_value=0.0, value=5.0, step=0.5)
                
                rate = st.selectbox("Fertilizer Rate", [(2, "2 bags/ha"), (3, "3 bags/ha")], format_func=lambda x: x[1])[0]
                entitled = calc_fertilizer(land_size, rate)
                
                st.success(f"🧪 Auto-Calculated: **{entitled} bags** ({land_size} ha × {rate} bags/ha)")
                
                if st.form_submit_button("✅ REGISTER FARMER", use_container_width=True, type="primary"):
                    if not national_id or not full_name:
                        st.error("❌ National ID and Name are required!")
                    else:
                        farmer = {
                            "id": f"F-{len(st.session_state.registered_farmers) + 100}",
                            "name": full_name,
                            "national_id": national_id,
                            "phone": phone,
                            "household_size": household,
                            "land_size": land_size,
                            "fertilizer_rate": rate,
                            "entitled": entitled,
                            "taken": 0,
                            "kebele_id": user["kebele_id"],
                            "village_id": selected_village["id"],
                            "registered_by": user["id"],
                            "registered_at": datetime.now().strftime("%Y-%m-%d %H:%M")
                        }
                        st.session_state.registered_farmers.append(farmer)
                        st.success(f"✅ Farmer {full_name} registered!")
                        st.balloons()
    
    elif "Distribute" in menu:
        st.header("📦 Distribute Fertilizer")
        
        all_farmers = [f for f in FARMERS if f["kebele_id"] == user["kebele_id"]] + \
                      [f for f in st.session_state.registered_farmers if f.get("kebele_id") == user["kebele_id"]]
        
        eligible = [f for f in all_farmers if f.get('entitled', 0) > f.get('taken', 0)]
        
        st.write(f"👥 {len(eligible)} farmers eligible for distribution")
        
        for farmer in eligible:
            remaining = farmer.get('entitled', 0) - farmer.get('taken', 0)
            with st.container(border=True):
                c = st.columns([3, 2, 2, 2, 3])
                c[0].write(f"**{farmer['name']}**")
                c[0].caption(f"NID: {farmer['national_id']}")
                c[1].write(f"🌾 {farmer['land_size']} ha")
                c[2].write(f"🧪 Entitled: {farmer['entitled']}")
                c[3].write(f"✅ Taken: {farmer['taken']}\n📦 Remaining: **{remaining}**")
                
                with c[4]:
                    give = st.number_input(f"Amount", min_value=0, max_value=remaining, value=min(remaining, 10), key=f"give_{farmer['id']}", label_visibility="collapsed")
                    if st.button(f"Give {give}", key=f"btn_{farmer['id']}", use_container_width=True):
                        st.success(f"✅ Gave {give} bags to {farmer['name']}!")
    
    elif "My Farmers" in menu:
        st.header("👥 My Registered Farmers")
        
        all_farmers = [f for f in FARMERS if f["kebele_id"] == user["kebele_id"]] + \
                      [f for f in st.session_state.registered_farmers if f.get("kebele_id") == user["kebele_id"]]
        
        villages = [v for v in VILLAGES if v["kebele_id"] == user["kebele_id"]]
        village_names = ["All"] + [v['name'] for v in villages]
        
        col1, col2, col3 = st.columns(3)
        filter_village = col1.selectbox("Village", village_names)
        filter_status = col2.selectbox("Status", ["All", "Complete", "Pending"])
        search = col3.text_input("🔍 Search")
        
        if filter_village != "All":
            all_farmers = [f for f in all_farmers if f.get('village_name') == filter_village or f.get('village_id') in [v['id'] for v in villages if v['name'] == filter_village]]
        
        st.write(f"Showing {len(all_farmers)} farmers")
        
        df = pd.DataFrame(all_farmers)
        if not df.empty:
            df['remaining'] = df['entitled'] - df['taken']
            df['status'] = df.apply(lambda x: '✅ Complete' if x['remaining'] <= 0 else '⏳ Pending', axis=1)
            st.dataframe(
                df[['name', 'national_id', 'land_size', 'entitled', 'taken', 'remaining', 'status']],
                column_config={
                    'name': 'Farmer Name',
                    'national_id': 'National ID',
                    'land_size': st.column_config.NumberColumn('Land (ha)', format='%.1f'),
                    'entitled': 'Entitled',
                    'taken': 'Taken',
                    'remaining': 'Remaining',
                    'status': 'Status'
                },
                use_container_width=True,
                hide_index=True
            )

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
