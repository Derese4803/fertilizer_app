import streamlit as st
from firebase_admin import credentials, firestore, initialize_app
import firebase_admin
import json
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
    .role-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1.5rem;
        border-radius: 15px;
        color: white;
        text-align: center;
        cursor: pointer;
        transition: transform 0.3s;
    }
    .role-card:hover {
        transform: translateY(-5px);
    }
    .metric-card {
        background: #f8f9fa;
        padding: 1.5rem;
        border-radius: 10px;
        border-left: 5px solid #1a237e;
    }
    .stButton>button {
        width: 100%;
        border-radius: 10px;
        padding: 0.75rem;
        font-weight: 600;
    }
    .success-msg {
        background: #d4edda;
        color: #155724;
        padding: 1rem;
        border-radius: 10px;
        border-left: 5px solid #28a745;
    }
    .error-msg {
        background: #f8d7da;
        color: #721c24;
        padding: 1rem;
        border-radius: 10px;
        border-left: 5px solid #dc3545;
    }
</style>
""", unsafe_allow_html=True)

# ==================== FIREBASE INITIALIZATION ====================
@st.cache_resource
def init_firebase():
    """Initialize Firebase connection"""
    try:
        if not firebase_admin._apps:
            # For deployment: use secrets
            # For local: use serviceAccountKey.json
            try:
                cred = credentials.Certificate("serviceAccountKey.json")
            except:
                # Streamlit Cloud deployment
                firebase_config = st.secrets["firebase"]
                cred = credentials.Certificate(dict(firebase_config))
            initialize_app(cred)
        return firestore.client()
    except Exception as e:
        st.error(f"Firebase init error: {e}")
        return None

db = init_firebase()

# ==================== SESSION STATE ====================
if "user" not in st.session_state:
    st.session_state.user = None
if "page" not in st.session_state:
    st.session_state.page = "login"

# ==================== AUTHENTICATION SERVICE ====================
class AuthService:
    @staticmethod
    def login(username, password, role):
        """Authenticate user and return user data"""
        try:
            # Query users collection based on role
            collection_map = {
                "regional_manager": "regional_managers",
                "zonal_manager": "zonal_managers",
                "woreda_manager": "woreda_managers",
                "da_worker": "da_workers"
            }
            
            collection_name = collection_map.get(role)
            if not collection_name:
                return None
            
            # Query by username
            users_ref = db.collection(collection_name).where("username", "==", username).limit(1)
            users = list(users_ref.stream())
            
            if not users:
                return None
            
            user_data = users[0].to_dict()
            user_data["id"] = users[0].id
            user_data["role"] = role
            
            # Verify password (in production, use hashed passwords)
            if user_data.get("password") == password:
                return user_data
            return None
            
        except Exception as e:
            st.error(f"Login error: {e}")
            return None
    
    @staticmethod
    def logout():
        """Clear session"""
        st.session_state.user = None
        st.session_state.page = "login"
        st.rerun()

# ==================== DATABASE SERVICE ====================
class DatabaseService:
    @staticmethod
    def get_regions():
        """Get all regions"""
        try:
            regions_ref = db.collection("regions").stream()
            return [{"id": r.id, **r.to_dict()} for r in regions_ref]
        except:
            # Return demo data if Firebase not connected
            return [
                {"id": "REG-01", "name": "Oromia", "total_zones": 21},
                {"id": "REG-02", "name": "Amhara", "total_zones": 12},
                {"id": "REG-03", "name": "SNNPR", "total_zones": 15},
                {"id": "REG-04", "name": "Tigray", "total_zones": 7},
            ]
    
    @staticmethod
    def get_zones(region_id=None):
        """Get zones, optionally filtered by region"""
        try:
            if region_id:
                zones_ref = db.collection("zones").where("region_id", "==", region_id).stream()
            else:
                zones_ref = db.collection("zones").stream()
            return [{"id": z.id, **z.to_dict()} for z in zones_ref]
        except:
            return [
                {"id": "ZN-001", "name": "Jimma Zone", "region_id": "REG-01", "woreda_count": 17, "farmer_count": 5400, "fertilizer_assigned": 50000, "fertilizer_distributed": 32000},
                {"id": "ZN-002", "name": "West Wellega", "region_id": "REG-01", "woreda_count": 22, "farmer_count": 7200, "fertilizer_assigned": 75000, "fertilizer_distributed": 48000},
                {"id": "ZN-003", "name": "East Wellega", "region_id": "REG-01", "woreda_count": 18, "farmer_count": 6100, "fertilizer_assigned": 62000, "fertilizer_distributed": 45000},
            ]
    
    @staticmethod
    def get_woredas(zone_id=None):
        """Get woredas, optionally filtered by zone"""
        try:
            if zone_id:
                woredas_ref = db.collection("woredas").where("zone_id", "==", zone_id).stream()
            else:
                woredas_ref = db.collection("woredas").stream()
            return [{"id": w.id, **w.to_dict()} for w in woredas_ref]
        except:
            return [
                {"id": "WRD-001", "name": "Jimma Woreda", "zone_id": "ZN-001", "kebele_count": 8, "farmer_count": 1240, "fertilizer_assigned": 5000, "fertilizer_distributed": 3200},
                {"id": "WRD-002", "name": "Seka Woreda", "zone_id": "ZN-001", "kebele_count": 6, "farmer_count": 980, "fertilizer_assigned": 4000, "fertilizer_distributed": 2800},
            ]
    
    @staticmethod
    def get_kebeles(woreda_id=None):
        """Get kebeles, optionally filtered by woreda"""
        try:
            if woreda_id:
                kebeles_ref = db.collection("kebeles").where("woreda_id", "==", woreda_id).stream()
            else:
                kebeles_ref = db.collection("kebeles").stream()
            return [{"id": k.id, **k.to_dict()} for k in kebeles_ref]
        except:
            return [
                {"id": "KEB-001", "name": "Kebele 01", "woreda_id": "WRD-001", "village_count": 3, "farmer_count": 156, "fertilizer_assigned": 600, "fertilizer_distributed": 450},
                {"id": "KEB-002", "name": "Kebele 02", "woreda_id": "WRD-001", "village_count": 4, "farmer_count": 198, "fertilizer_assigned": 800, "fertilizer_distributed": 620},
                {"id": "KEB-003", "name": "Kebele 03", "woreda_id": "WRD-001", "village_count": 3, "farmer_count": 234, "fertilizer_assigned": 800, "fertilizer_distributed": 520},
            ]
    
    @staticmethod
    def get_villages(kebele_id=None):
        """Get villages, optionally filtered by kebele"""
        try:
            if kebele_id:
                villages_ref = db.collection("villages").where("kebele_id", "==", kebele_id).stream()
            else:
                villages_ref = db.collection("villages").stream()
            return [{"id": v.id, **v.to_dict()} for v in villages_ref]
        except:
            return [
                {"id": "VIL-A", "name": "Village A", "kebele_id": "KEB-003", "farmer_count": 45},
                {"id": "VIL-B", "name": "Village B", "kebele_id": "KEB-003", "farmer_count": 67},
                {"id": "VIL-C", "name": "Village C", "kebele_id": "KEB-003", "farmer_count": 52},
            ]
    
    @staticmethod
    def get_farmers(filters=None):
        """Get farmers with optional filters"""
        try:
            farmers_ref = db.collection("farmers")
            if filters:
                for key, value in filters.items():
                    farmers_ref = farmers_ref.where(key, "==", value)
            farmers = farmers_ref.stream()
            return [{"id": f.id, **f.to_dict()} for f in farmers]
        except:
            return [
                {"id": "F-001", "name": "Abebe Kebede", "national_id": "NID-1985-4455667", "kebele_id": "KEB-003", "village_id": "VIL-B", "land_size": 8.0, "fertilizer_entitled": 16, "fertilizer_taken": 6, "phone": "+251911223344"},
                {"id": "F-002", "name": "Fatuma Mohamed", "national_id": "NID-1990-7788990", "kebele_id": "KEB-003", "village_id": "VIL-B", "land_size": 5.5, "fertilizer_entitled": 11, "fertilizer_taken": 0, "phone": "+251922334455"},
                {"id": "F-003", "name": "Dawit Tesfaye", "national_id": "NID-1982-3344556", "kebele_id": "KEB-003", "village_id": "VIL-A", "land_size": 12.0, "fertilizer_entitled": 24, "fertilizer_taken": 10, "phone": "+251933445566"},
            ]
    
    @staticmethod
    def get_managers(collection, parent_id=None, parent_field=None):
        """Get managers"""
        try:
            if parent_id and parent_field:
                ref = db.collection(collection).where(parent_field, "==", parent_id).stream()
            else:
                ref = db.collection(collection).stream()
            return [{"id": m.id, **m.to_dict()} for m in ref]
        except:
            if collection == "zonal_managers":
                return [
                    {"id": "ZM-001", "name": "Ato Kebede Wolde", "username": "zm_kebede", "region_id": "REG-01", "zone_id": "ZN-001", "phone": "+251911000111"},
                    {"id": "ZM-002", "name": "Abebe Kebede", "username": "zm_abebe", "region_id": "REG-01", "zone_id": "ZN-002", "phone": "+251922000222"},
                ]
            elif collection == "woreda_managers":
                return [
                    {"id": "WM-001", "name": "Ato Tadesse Alemu", "username": "wm_tadesse", "zone_id": "ZN-001", "woreda_id": "WRD-001", "phone": "+251911223344"},
                ]
            elif collection == "da_workers":
                return [
                    {"id": "DA-001", "name": "Dawit Kebede", "username": "da_dawit", "woreda_id": "WRD-001", "kebele_id": "KEB-003", "phone": "+251944556677"},
                ]
            return []
    
    @staticmethod
    def add_document(collection, data):
        """Add document to collection"""
        try:
            doc_ref = db.collection(collection).add(data)
            return doc_ref[1].id
        except Exception as e:
            st.error(f"Error adding document: {e}")
            return None
    
    @staticmethod
    def update_document(collection, doc_id, data):
        """Update document"""
        try:
            db.collection(collection).document(doc_id).update(data)
            return True
        except Exception as e:
            st.error(f"Error updating document: {e}")
            return False

# ==================== HELPER FUNCTIONS ====================
def calculate_fertilizer(land_size, rate=2):
    """Calculate fertilizer entitlement"""
    return land_size * rate

def format_number(num):
    """Format large numbers"""
    return f"{num:,}"

# ==================== PAGE: LOGIN ====================
def show_login():
    st.markdown('<p class="main-header">🌾 Fertilizer Distribution System</p>', unsafe_allow_html=True)
    st.markdown('<p class="sub-header">Government of Ethiopia | Ministry of Agriculture</p>', unsafe_allow_html=True)
    
    # Center the login form
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        st.markdown("### 🔐 Sign In")
        
        # Role selection with icons
        role_options = {
            "regional_manager": "🗺️ Regional Manager",
            "zonal_manager": "🏛️ Zonal Manager",
            "woreda_manager": "📍 Woreda Manager",
            "da_worker": "👤 DA / Worker"
        }
        
        role = st.selectbox(
            "Select Your Role",
            options=list(role_options.keys()),
            format_func=lambda x: role_options[x]
        )
        
        # Login form
        with st.form("login_form"):
            username = st.text_input("👤 Username", placeholder="Enter your username")
            password = st.text_input("🔑 Password", type="password", placeholder="Enter your password")
            
            # Demo credentials hint
            st.caption("💡 Demo: Use any username with password 'admin123'")
            
            submitted = st.form_submit_button("🔐 SIGN IN", use_container_width=True, type="primary")
        
        if submitted:
            with st.spinner("Authenticating..."):
                # For demo: accept any username with password 'admin123'
                if password == "admin123":
                    # Create demo user based on role
                    demo_users = {
                        "regional_manager": {
                            "id": "REGMGR-001",
                            "name": "Ato Girma Bekele",
                            "username": username,
                            "role": "regional_manager",
                            "region_id": "REG-01",
                            "region_name": "Oromia"
                        },
                        "zonal_manager": {
                            "id": "ZM-001",
                            "name": "Ato Kebede Wolde",
                            "username": username,
                            "role": "zonal_manager",
                            "region_id": "REG-01",
                            "region_name": "Oromia",
                            "zone_id": "ZN-001",
                            "zone_name": "Jimma Zone"
                        },
                        "woreda_manager": {
                            "id": "WM-001",
                            "name": "Ato Tadesse Alemu",
                            "username": username,
                            "role": "woreda_manager",
                            "region_id": "REG-01",
                            "zone_id": "ZN-001",
                            "woreda_id": "WRD-001",
                            "woreda_name": "Jimma Woreda"
                        },
                        "da_worker": {
                            "id": "DA-001",
                            "name": "Dawit Kebede",
                            "username": username,
                            "role": "da_worker",
                            "region_id": "REG-01",
                            "zone_id": "ZN-001",
                            "woreda_id": "WRD-001",
                            "kebele_id": "KEB-003",
                            "kebele_name": "Kebele 03"
                        }
                    }
                    
                    st.session_state.user = demo_users[role]
                    st.success(f"✅ Welcome, {demo_users[role]['name']}!")
                    st.rerun()
                else:
                    st.error("❌ Invalid password! Use 'admin123' for demo.")

# ==================== PAGE: REGIONAL MANAGER ====================
def show_regional_manager():
    user = st.session_state.user
    
    # Sidebar
    with st.sidebar:
        st.markdown(f"### 🗺️ {user['name']}")
        st.caption(f"Regional Manager | {user['region_name']}")
        st.divider()
        
        menu = st.radio("Menu", [
            "📊 Dashboard",
            "📦 Assign Zone + Fertilizer",
            "🏛️ Zone Management",
            "👥 Zonal Managers",
            "📈 Reports",
            "⚙️ Settings"
        ])
        
        st.divider()
        if st.button("🚪 Logout", use_container_width=True):
            AuthService.logout()
    
    # Main content
    if "Dashboard" in menu:
        st.header("📊 Regional Dashboard")
        st.caption(f"Region: {user['region_name']} | Full System Control")
        
        # Summary metrics
        zones = DatabaseService.get_zones(user['region_id'])
        
        cols = st.columns(4)
        cols[0].metric("🗺️ Zones", len(zones))
        cols[1].metric("📍 Woredas", sum(z.get('woreda_count', 0) for z in zones))
        cols[2].metric("🌾 Farmers", format_number(sum(z.get('farmer_count', 0) for z in zones)))
        cols[3].metric("🧪 Fertilizer Assigned", f"{format_number(sum(z.get('fertilizer_assigned', 0) for z in zones))} bags")
        
        # Zone overview table
        st.subheader("Zone Overview")
        import pandas as pd
        df_zones = pd.DataFrame(zones)
        if not df_zones.empty:
            df_zones['distribution_rate'] = (df_zones['fertilizer_distributed'] / df_zones['fertilizer_assigned'] * 100).round(1)
            st.dataframe(
                df_zones[['name', 'woreda_count', 'farmer_count', 'fertilizer_assigned', 'fertilizer_distributed', 'distribution_rate']],
                column_config={
                    'name': 'Zone Name',
                    'woreda_count': 'Woredas',
                    'farmer_count': 'Farmers',
                    'fertilizer_assigned': 'Assigned (bags)',
                    'fertilizer_distributed': 'Distributed (bags)',
                    'distribution_rate': st.column_config.ProgressColumn('Progress', format='%d%%', min_value=0, max_value=100)
                },
                use_container_width=True,
                hide_index=True
            )
        
        # Charts
        col1, col2 = st.columns(2)
        with col1:
            st.subheader("Fertilizer by Zone")
            import plotly.express as px
            fig = px.bar(zones, x='name', y=['fertilizer_assigned', 'fertilizer_distributed'],
                        barmode='group', labels={'value': 'Bags', 'name': 'Zone'},
                        color_discrete_map={'fertilizer_assigned': '#1a237e', 'fertilizer_distributed': '#4caf50'})
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            st.subheader("Farmers by Zone")
            fig2 = px.pie(zones, names='name', values='farmer_count')
            st.plotly_chart(fig2, use_container_width=True)
    
    elif "Assign Zone" in menu:
        st.header("📦 Assign Zone & Fertilizer")
        
        zones = DatabaseService.get_zones(user['region_id'])
        zonal_managers = DatabaseService.get_managers("zonal_managers", user['region_id'], "region_id")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("Select Zone")
            selected_zone = st.selectbox("Zone", zones, format_func=lambda x: x['name'])
            
            st.subheader("Assign Manager")
            selected_manager = st.selectbox("Zonal Manager", zonal_managers, format_func=lambda x: x['name'])
        
        with col2:
            st.subheader("Fertilizer Details")
            
            # Auto-calculate
            farmer_count = selected_zone.get('farmer_count', 0)
            needed = farmer_count * 10  # 10 bags per farmer
            
            st.metric("Farmers in Zone", farmer_count)
            st.metric("Estimated Need", f"{needed:,} bags")
            
            assign_amount = st.number_input(
                "Assign Amount (bags)",
                min_value=0,
                value=needed,
                step=100,
                help="Enter amount of fertilizer to assign"
            )
            
            st.metric("Remaining after assignment", f"{needed - assign_amount:,} bags", delta=-assign_amount)
        
        if st.button("✅ CONFIRM ASSIGNMENT", type="primary", use_container_width=True):
            st.success(f"✅ Assigned {assign_amount:,} bags to {selected_zone['name']}!")
            st.balloons()
    
    elif "Zone Management" in menu:
        st.header("🏛️ Zone Management")
        
        zones = DatabaseService.get_zones(user['region_id'])
        
        for zone in zones:
            with st.container(border=True):
                cols = st.columns([3, 2, 2, 2, 2])
                cols[0].write(f"**{zone['name']}**")
                cols[1].write(f"📍 {zone['woreda_count']} Woredas")
                cols[2].write(f"🌾 {zone['farmer_count']:,} Farmers")
                cols[3].write(f"🧪 {zone['fertilizer_assigned']:,} bags")
                progress = zone['fertilizer_distributed'] / zone['fertilizer_assigned'] * 100 if zone['fertilizer_assigned'] > 0 else 0
                cols[4].progress(progress / 100, text=f"{progress:.0f}%")
    
    elif "Zonal Managers" in menu:
        st.header("👥 Zonal Managers")
        
        managers = DatabaseService.get_managers("zonal_managers", user['region_id'], "region_id")
        
        col1, col2 = st.columns([1, 2])
        
        with col1:
            st.subheader("Register New Manager")
            with st.form("reg_manager"):
                mgr_name = st.text_input("Full Name")
                mgr_username = st.text_input("Username", value="zm_")
                mgr_phone = st.text_input("Phone")
                mgr_zone = st.selectbox("Assign Zone", zones, format_func=lambda x: x['name'])
                mgr_password = st.text_input("Password", type="password")
                
                if st.form_submit_button("✅ Register", use_container_width=True):
                    st.success(f"✅ Manager {mgr_name} registered!")
        
        with col2:
            st.subheader("Existing Managers")
            for mgr in managers:
                with st.container(border=True):
                    st.write(f"**{mgr['name']}**")
                    st.caption(f"@{mgr['username']} | 📞 {mgr['phone']}")
                    st.caption(f"Zone: {mgr.get('zone_name', 'Not assigned')}")
    
    elif "Reports" in menu:
        st.header("📈 Regional Reports")
        
        report_type = st.selectbox("Report Type", [
            "Fertilizer Distribution Summary",
            "Zone-wise Comparison",
            "Manager Performance",
            "Farmer Registration Report"
        ])
        
        if report_type == "Fertilizer Distribution Summary":
            zones = DatabaseService.get_zones(user['region_id'])
            
            import pandas as pd
            df = pd.DataFrame(zones)
            df['remaining'] = df['fertilizer_assigned'] - df['fertilizer_distributed']
            df['distribution_pct'] = (df['fertilizer_distributed'] / df['fertilizer_assigned'] * 100).round(1)
            
            st.dataframe(df[['name', 'fertilizer_assigned', 'fertilizer_distributed', 'remaining', 'distribution_pct']],
                        use_container_width=True)
            
            # Export
            csv = df.to_csv(index=False).encode('utf-8')
            st.download_button("📥 Download CSV", csv, "regional_report.csv", "text/csv")

# ==================== PAGE: ZONAL MANAGER ====================
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
            AuthService.logout()
    
    if "Dashboard" in menu:
        st.header("📊 Zonal Dashboard")
        st.caption(f"Zone: {user['zone_name']} | Manages all Woredas in this Zone")
        
        woredas = DatabaseService.get_woredas(user['zone_id'])
        
        cols = st.columns(4)
        cols[0].metric("📍 Woredas", len(woredas))
        cols[1].metric("🏘️ Kebeles", sum(w.get('kebele_count', 0) for w in woredas))
        cols[2].metric("🌾 Farmers", format_number(sum(w.get('farmer_count', 0) for w in woredas)))
        cols[3].metric("🧪 My Stock", f"{format_number(sum(w.get('fertilizer_assigned', 0) for w in woredas))} bags")
        
        # Stock summary
        total_assigned = sum(w.get('fertilizer_assigned', 0) for w in woredas)
        total_distributed = sum(w.get('fertilizer_distributed', 0) for w in woredas)
        remaining = total_assigned - total_distributed
        
        st.subheader("💰 Fertilizer Stock")
        c1, c2, c3 = st.columns(3)
        c1.metric("Received from Region", f"{total_assigned:,} bags")
        c2.metric("Distributed to Woredas", f"{total_distributed:,} bags")
        c3.metric("Remaining", f"{remaining:,} bags", delta=-total_distributed)
        
        # Woreda table
        st.subheader("Woreda Overview")
        import pandas as pd
        df = pd.DataFrame(woredas)
        if not df.empty:
            st.dataframe(df, use_container_width=True, hide_index=True)
    
    elif "Assign Woreda" in menu:
        st.header("📦 Assign Woreda & Fertilizer")
        
        woredas = DatabaseService.get_woredas(user['zone_id'])
        woreda_managers = DatabaseService.get_managers("woreda_managers", user['zone_id'], "zone_id")
        
        col1, col2 = st.columns(2)
        
        with col1:
            selected_woreda = st.selectbox("Select Woreda", woredas, format_func=lambda x: x['name'])
            selected_manager = st.selectbox("Assign Manager", woreda_managers, format_func=lambda x: x['name'])
        
        with col2:
            farmer_count = selected_woreda.get('farmer_count', 0)
            needed = farmer_count * 10
            
            st.metric("Farmers", farmer_count)
            st.metric("Estimated Need", f"{needed:,} bags")
            
            assign_amount = st.number_input("Assign Amount", min_value=0, value=needed, step=50)
        
        if st.button("✅ ASSIGN", type="primary", use_container_width=True):
            st.success(f"✅ Assigned {assign_amount:,} bags to {selected_woreda['name']}!")

# ==================== PAGE: WOREDA MANAGER ====================
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
            AuthService.logout()
    
    if "Dashboard" in menu:
        st.header("📊 Woreda Dashboard")
        st.caption(f"Woreda: {user['woreda_name']} | Control Workers & Kebeles")
        
        kebeles = DatabaseService.get_kebeles(user['woreda_id'])
        workers = DatabaseService.get_managers("da_workers", user['woreda_id'], "woreda_id")
        
        cols = st.columns(4)
        cols[0].metric("🏘️ Kebeles", len(kebeles))
        cols[1].metric("👤 Workers", len(workers))
        cols[2].metric("🌾 Farmers", format_number(sum(k.get('farmer_count', 0) for k in kebeles)))
        cols[3].metric("🧪 Stock", f"{format_number(sum(k.get('fertilizer_assigned', 0) for k in kebeles))} bags")
        
        # Stock
        total = sum(k.get('fertilizer_assigned', 0) for k in kebeles)
        distributed = sum(k.get('fertilizer_distributed', 0) for k in kebeles)
        
        st.subheader("💰 Fertilizer Stock")
        c1, c2, c3 = st.columns(3)
        c1.metric("Received from Zone", f"{total:,} bags")
        c2.metric("Distributed", f"{distributed:,} bags")
        c3.metric("Remaining", f"{total - distributed:,} bags")
    
    elif "Register Worker" in menu:
        st.header("👤 Register New Worker / DA")
        
        col1, col2 = st.columns(2)
        
        with col1:
            with st.form("register_worker"):
                st.subheader("Worker Details")
                name = st.text_input("Full Name *")
                username = st.text_input("Username *", value="da_")
                phone = st.text_input("Phone Number *")
                
                kebeles = DatabaseService.get_kebeles(user['woreda_id'])
                kebele = st.selectbox("Assign Kebele *", kebeles, format_func=lambda x: x['name'])
                
                password = st.text_input("Password *", type="password")
                confirm = st.text_input("Confirm Password *", type="password")
                
                submitted = st.form_submit_button("✅ REGISTER WORKER", use_container_width=True)
                
                if submitted:
                    if password != confirm:
                        st.error("❌ Passwords do not match!")
                    elif not all([name, username, phone, password]):
                        st.error("❌ All fields are required!")
                    else:
                        worker_data = {
                            "name": name,
                            "username": username,
                            "phone": phone,
                            "kebele_id": kebele['id'],
                            "kebele_name": kebele['name'],
                            "woreda_id": user['woreda_id'],
                            "zone_id": user['zone_id'],
                            "region_id": user['region_id'],
                            "role": "da_worker",
                            "password": password,
                            "registered_by": user['id'],
                            "created_at": datetime.now().isoformat()
                        }
                        st.success(f"✅ Worker {name} registered successfully!")
                        st.json(worker_data)
        
        with col2:
            st.subheader("Recently Registered Workers")
            workers = DatabaseService.get_managers("da_workers", user['woreda_id'], "woreda_id")
            for w in workers:
                with st.container(border=True):
                    st.write(f"**{w['name']}**")
                    st.caption(f"@{w['username']} | 📞 {w['phone']}")
                    st.caption(f"Kebele: {w.get('kebele_name', 'N/A')}")
    
    elif "Assign Kebele" in menu:
        st.header("📦 Assign Kebele & Fertilizer")
        
        kebeles = DatabaseService.get_kebeles(user['woreda_id'])
        
        col1, col2 = st.columns(2)
        
        with col1:
            selected_kebele = st.selectbox("Select Kebele", kebeles, format_func=lambda x: x['name'])
            
            farmer_count = selected_kebele.get('farmer_count', 0)
            needed = farmer_count * 10
            
            st.metric("Farmers", farmer_count)
            st.metric("Need", f"{needed:,} bags")
        
        with col2:
            assign_amount = st.number_input("Assign Amount (bags)", min_value=0, value=needed, step=25)
            
            # Auto-calculation display
            rate_per_farmer = assign_amount / farmer_count if farmer_count > 0 else 0
            st.info(f"📊 Rate: {rate_per_farmer:.1f} bags per farmer")
            
            if st.button("✅ ASSIGN TO KEBELE", type="primary", use_container_width=True):
                st.success(f"✅ Assigned {assign_amount:,} bags to {selected_kebele['name']}!")
    
    elif "Kebele Management" in menu:
        st.header("🏘️ Kebele Management")
        
        kebeles = DatabaseService.get_kebeles(user['woreda_id'])
        
        for kebele in kebeles:
            with st.container(border=True):
                cols = st.columns([3, 2, 2, 2, 2])
                cols[0].write(f"**{kebele['name']}**")
                cols[1].write(f"🏡 {kebele.get('village_count', 0)} Villages")
                cols[2].write(f"🌾 {kebele.get('farmer_count', 0)} Farmers")
                cols[3].write(f"🧪 {kebele.get('fertilizer_assigned', 0)} bags")
                progress = kebele.get('fertilizer_distributed', 0) / kebele.get('fertilizer_assigned', 1) * 100
                cols[4].progress(progress / 100, text=f"{progress:.0f}%")

# ==================== PAGE: DA WORKER ====================
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
            AuthService.logout()
    
    if "Dashboard" in menu:
        st.header("📊 DA Dashboard")
        st.caption(f"Kebele: {user['kebele_name']} | Field Worker View")
        
        # Get my farmers
        farmers = DatabaseService.get_farmers({"kebele_id": user['kebele_id']})
        
        cols = st.columns(4)
        cols[0].metric("👥 My Farmers", len(farmers))
        cols[1].metric("🌾 Total Land", f"{sum(f.get('land_size', 0) for f in farmers):.1f} ha")
        cols[2].metric("🧪 Entitled", f"{sum(f.get('fertilizer_entitled', 0) for f in farmers)} bags")
        cols[3].metric("📦 Distributed", f"{sum(f.get('fertilizer_taken', 0) for f in farmers)} bags")
        
        # Quick actions
        st.subheader("⚡ Quick Actions")
        c1, c2, c3 = st.columns(3)
        c1.button("➕ Register New Farmer", use_container_width=True)
        c2.button("📦 Give Fertilizer", use_container_width=True)
        c3.button("📊 View Reports", use_container_width=True)
    
    elif "Register Farmer" in menu:
        st.header("➕ Register New Farmer")
        
        # Location cascade (pre-filled for DA)
        col1, col2 = st.columns(2)
        
        with col1:
            st.info(f"🗺️ Region: {user['region_id']}")
            st.info(f"🏛️ Zone: {user['zone_id']}")
            st.info(f"📍 Woreda: {user['woreda_id']}")
            st.info(f"🏘️ Kebele: {user['kebele_id']}")
            
            villages = DatabaseService.get_villages(user['kebele_id'])
            selected_village = st.selectbox("Select Village *", villages, format_func=lambda x: x['name'])
        
        with col2:
            with st.form("register_farmer"):
                st.subheader("Farmer Details")
                
                national_id = st.text_input("National ID *", placeholder="NID-YYYY-XXXXXXX")
                full_name = st.text_input("Full Name *")
                phone = st.text_input("Phone Number")
                household_size = st.number_input("Household Size", min_value=1, value=5)
                
                st.subheader("🌱 Land Information")
                land_size = st.number_input("Land Size (hectares) *", min_value=0.0, value=5.0, step=0.5)
                
                # Auto-calculate fertilizer
                rate = st.selectbox("Fertilizer Rate", [("2 bags/ha", 2), ("3 bags/ha", 3)], format_func=lambda x: x[0])
                rate_value = rate[1]
                entitled = calculate_fertilizer(land_size, rate_value)
                
                st.success(f"🧪 Auto-Calculated: **{entitled} bags** ({land_size} ha × {rate_value} bags/ha)")
                
                submitted = st.form_submit_button("✅ REGISTER FARMER", use_container_width=True, type="primary")
                
                if submitted:
                    if not national_id or not full_name:
                        st.error("❌ National ID and Full Name are required!")
                    else:
                        farmer_data = {
                            "national_id": national_id,
                            "name": full_name,
                            "phone": phone,
                            "household_size": household_size,
                            "land_size": land_size,
                            "fertilizer_rate": rate_value,
                            "fertilizer_entitled": entitled,
                            "fertilizer_taken": 0,
                            "region_id": user['region_id'],
                            "zone_id": user['zone_id'],
                            "woreda_id": user['woreda_id'],
                            "kebele_id": user['kebele_id'],
                            "village_id": selected_village['id'],
                            "registered_by_da_id": user['id'],
                            "registered_by_da_name": user['name'],
                            "created_at": datetime.now().isoformat()
                        }
                        st.success(f"✅ Farmer {full_name} registered!")
                        st.balloons()
                        st.json(farmer_data)
    
    elif "Distribute" in menu:
        st.header("📦 Distribute Fertilizer")
        
        farmers = DatabaseService.get_farmers({"kebele_id": user['kebele_id']})
        
        # Filter farmers with remaining balance
        eligible = [f for f in farmers if f.get('fertilizer_entitled', 0) > f.get('fertilizer_taken', 0)]
        
        st.write(f"👥 {len(eligible)} farmers eligible for distribution")
        
        for farmer in eligible:
            remaining = farmer.get('fertilizer_entitled', 0) - farmer.get('fertilizer_taken', 0)
            with st.container(border=True):
                cols = st.columns([3, 2, 2, 2, 2])
                cols[0].write(f"**{farmer['name']}**")
                cols[0].caption(f"NID: {farmer['national_id']}")
                cols[1].write(f"🌾 {farmer['land_size']} ha")
                cols[2].write(f"🧪 Entitled: {farmer['fertilizer_entitled']}")
                cols[3].write(f"✅ Taken: {farmer['fertilizer_taken']}")
                cols[3].write(f"📦 Remaining: **{remaining}**")
                
                with cols[4]:
                    give_amount = st.number_input(
                        f"Give_{farmer['id']}",
                        min_value=0,
                        max_value=remaining,
                        value=min(remaining, 10),
                        key=f"give_{farmer['id']}",
                        label_visibility="collapsed"
                    )
                    if st.button(f"Give {give_amount}", key=f"btn_{farmer['id']}", use_container_width=True):
                        st.success(f"✅ Gave {give_amount} bags to {farmer['name']}!")
    
    elif "My Farmers" in menu:
        st.header("👥 My Registered Farmers")
        
        # Filters
        col1, col2, col3 = st.columns(3)
        villages = DatabaseService.get_villages(user['kebele_id'])
        
        with col1:
            filter_village = st.selectbox("Filter by Village", ["All"] + [v['name'] for v in villages])
        with col2:
            filter_status = st.selectbox("Status", ["All", "Fully Distributed", "Partially Distributed", "Not Distributed"])
        with col3:
            search = st.text_input("🔍 Search by name or NID")
        
        farmers = DatabaseService.get_farmers({"kebele_id": user['kebele_id']})
        
        # Apply filters
        if filter_village != "All":
            farmers = [f for f in farmers if f.get('village_name') == filter_village]
        
        st.write(f"Showing {len(farmers)} farmers")
        
        # Display
        import pandas as pd
        df = pd.DataFrame(farmers)
        if not df.empty:
            df['remaining'] = df['fertilizer_entitled'] - df['fertilizer_taken']
            df['status'] = df.apply(lambda x: '✅ Complete' if x['remaining'] == 0 else '⏳ Pending', axis=1)
            
            st.dataframe(
                df[['name', 'national_id', 'land_size', 'fertilizer_entitled', 'fertilizer_taken', 'remaining', 'status']],
                column_config={
                    'name': 'Farmer Name',
                    'national_id': 'National ID',
                    'land_size': st.column_config.NumberColumn('Land (ha)', format='%.1f'),
                    'fertilizer_entitled': 'Entitled',
                    'fertilizer_taken': 'Taken',
                    'remaining': 'Remaining',
                    'status': 'Status'
                },
                use_container_width=True,
                hide_index=True
            )

# ==================== MAIN APP ROUTING ====================
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
