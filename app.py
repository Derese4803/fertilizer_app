import sqlite3
import pandas as pd
import streamlit as st

# Database name definition
DB_FILE = "fertilizer_cascade_full.db"


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
            FOREIGN KEY (zone_id) REFERENCES zones (id)
        )
    """)

    # 4. Kebeles Table (Includes DA & Assistant)
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

    # 5. Service & Registration Fee Items per Woreda
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS fee_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            woreda_id TEXT NOT NULL,
            fee_name TEXT NOT NULL,
            amount REAL NOT NULL,
            FOREIGN KEY (woreda_id) REFERENCES woredas (id)
        )
    """)

    # 6. Farmers Table
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
            status TEXT DEFAULT 'Pending Fees',
            group_id INTEGER,
            FOREIGN KEY (kebele_id) REFERENCES kebeles (id)
        )
    """)

    # Seed Baseline Sample Records safely
    cursor.execute(
        "INSERT OR IGNORE INTO regions (id, name, total_quota) VALUES"
        " ('REG-001', 'Oromia Region', 50000)"
    )
    cursor.execute(
        "INSERT OR IGNORE INTO zones (id, name, region_id, fertilizer_quota)"
        " VALUES ('ZN-001', 'Jimma Zone', 'REG-001', 15000)"
    )
    cursor.execute(
        "INSERT OR IGNORE INTO zones (id, name, region_id, fertilizer_quota)"
        " VALUES ('ZN-002', 'West Shoa Zone', 'REG-001', 10000)"
    )

    cursor.execute(
        "INSERT OR IGNORE INTO woredas (id, name, zone_id, fertilizer_quota)"
        " VALUES ('WRD-001', 'Manna Woreda', 'ZN-001', 5000)"
    )
    cursor.execute(
        "INSERT OR IGNORE INTO woredas (id, name, zone_id, fertilizer_quota)"
        " VALUES ('WRD-002', 'Goma Woreda', 'ZN-001', 4000)"
    )

    cursor.execute(
        "INSERT OR IGNORE INTO kebeles (id, name, woreda_id, da_name,"
        " assistant_name, fertilizer_quota) VALUES ('KEB-001', 'Yebu Kebele',"
        " 'WRD-001', 'Alemayehu Tadesse', 'Getachew Bekele', 1500)"
    )
    cursor.execute(
        "INSERT OR IGNORE INTO kebeles (id, name, woreda_id, da_name,"
        " assistant_name, fertilizer_quota) VALUES ('KEB-002', 'Sombo Kebele',"
        " 'WRD-001', 'Mulugeta Kebede', 'Tigist Hailu', 1200)"
    )

    cursor.execute(
        "INSERT OR IGNORE INTO fee_items (id, woreda_id, fee_name, amount)"
        " VALUES (1, 'WRD-001', 'Logistics & Transport Fee', 120.0)"
    )
    cursor.execute(
        "INSERT OR IGNORE INTO fee_items (id, woreda_id, fee_name, amount)"
        " VALUES (2, 'WRD-001', 'Extension Support Service Fee', 50.0)"
    )

    seed_farmers = [
        (
            "FAR-001",
            "ETH-10293847",
            "Abebe Bikila",
            "KEB-001",
            "Gudeta",
            2.5,
            "+251911000000",
            1,
            "Grouped",
            1,
        ),
        (
            "FAR-002",
            "ETH-20394857",
            "Kebede Tessema",
            "KEB-001",
            "Gudeta",
            1.8,
            "+251911000001",
            1,
            "Grouped",
            1,
        ),
        (
            "FAR-003",
            "ETH-30495867",
            "Almaz Ayana",
            "KEB-001",
            "Boreta",
            3.0,
            "+251911000002",
            1,
            "In Queue",
            None,
        ),
        (
            "FAR-004",
            "ETH-40596877",
            "Tirunesh Dibaba",
            "KEB-001",
            "Boreta",
            1.2,
            "+251911000003",
            1,
            "In Queue",
            None,
        ),
        (
            "FAR-005",
            "ETH-50697887",
            "Haile Gebrselassie",
            "KEB-001",
            "Gudeta",
            4.1,
            "+251911000004",
            0,
            "Pending Fees",
            None,
        ),
    ]
    cursor.executemany(
        "INSERT OR IGNORE INTO farmers VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        seed_farmers,
    )

    conn.commit()
    conn.close()


# Application Setup
st.set_page_config(
    page_title="Cascade Allocation & Fertilizer Management System",
    layout="wide",
    page_icon="🌾",
)

init_db()

# Sidebar Navigation Panel
st.sidebar.title("📌 Access Control")
role = st.sidebar.selectbox(
    "Select Portal Role",
    [
        "Regional Manager",
        "Zonal Manager",
        "Woreda Manager",
        "DA Worker (Kebele Level)",
    ],
)

conn = get_db_connection()

# ==============================================================================
# 1. REGIONAL MANAGER ROLE
# ==============================================================================
if role == "Regional Manager":
    st.header("🌍 Regional Management Dashboard")
    st.markdown("---")

    tab1, tab2, tab3 = st.tabs(
        ["📊 Hierarchy Overview", "➕ Register Zone", "⚖️ Cascade Zonal Quota"]
    )

    with tab1:
        st.subheader("Regional Aggregated Cascade View")
        query_regional = """
            SELECT 
                r.name AS Region,
                r.total_quota AS Region_Total_Quota,
                z.id AS Zone_ID,
                z.name AS Zone,
                z.fertilizer_quota AS Zonal_Quota,
                w.name AS Woreda,
                w.fertilizer_quota AS Woreda_Quota,
                k.name AS Kebele,
                k.fertilizer_quota AS Kebele_Quota
            FROM regions r
            LEFT JOIN zones z ON z.region_id = r.id
            LEFT JOIN woredas w ON w.zone_id = z.id
            LEFT JOIN kebeles k ON k.woreda_id = w.id
        """
        df_all = pd.read_sql_query(query_regional, conn)
        st.dataframe(df_all, use_container_width=True)

    with tab2:
        st.subheader("Register New Zone")
        regions = pd.read_sql_query("SELECT id, name FROM regions", conn)
        region_dict = dict(zip(regions["name"], regions["id"]))

        with st.form("add_zone_form"):
            z_id = st.text_input("Zone ID (e.g., ZN-003)")
            z_name = st.text_input("Zone Name")
            reg_name = st.selectbox("Assign Region", list(region_dict.keys()))
            z_quota = st.number_input("Initial Allocated Quota (Quintals)", min_value=0, step=500)
            
            submit_zone = st.form_submit_button("Register Zone")

            if submit_zone:
                if z_id and z_name:
                    try:
                        cursor = conn.cursor()
                        cursor.execute(
                            "INSERT INTO zones (id, name, region_id, fertilizer_quota) VALUES (?, ?, ?, ?)",
                            (z_id, z_name, region_dict[reg_name], z_quota),
                        )
                        conn.commit()
                        st.success(f"Zone '{z_name}' created successfully!")
                        st.rerun()
                    except sqlite3.IntegrityError:
                        st.error(f"Zone ID '{z_id}' already exists.")
                else:
                    st.error("Please supply all mandatory fields.")

    with tab3:
        st.subheader("Update Zonal Quotas")
        zones = pd.read_sql_query("SELECT id, name, fertilizer_quota FROM zones", conn)
        
        if not zones.empty:
            selected_zone = st.selectbox("Select Zone to Re-allocate", zones["name"].tolist())
            current_q = zones[zones["name"] == selected_zone]["fertilizer_quota"].values[0]

            new_q = st.number_input(
                f"Set Allocation for {selected_zone} (Quintals)",
                min_value=0,
                value=int(current_q),
                step=100,
            )

            if st.button("Save Zonal Quota Allocation"):
                cursor = conn.cursor()
                cursor.execute(
                    "UPDATE zones SET fertilizer_quota = ? WHERE name = ?",
                    (new_q, selected_zone),
                )
                conn.commit()
                st.success(f"Updated quota for {selected_zone} to {new_q} Quintals!")
                st.rerun()

# ==============================================================================
# 2. ZONAL MANAGER ROLE
# ==============================================================================
elif role == "Zonal Manager":
    st.header("🏢 Zonal Management Portal")
    st.markdown("---")

    zones = pd.read_sql_query("SELECT id, name, fertilizer_quota FROM zones", conn)
    if not zones.empty:
        selected_zone = st.sidebar.selectbox("Select Zone Jurisdiction", zones["name"].tolist())
        zone_id = zones[zones["name"] == selected_zone]["id"].values[0]
        zone_quota = zones[zones["name"] == selected_zone]["fertilizer_quota"].values[0]

        st.metric("Total Zone Allocated Quota", f"{zone_quota} Quintals")

        tab1, tab2, tab3 = st.tabs(
            ["📋 Woreda Jurisdiction Overview", "➕ Register Woreda", "⚖️ Cascade Woreda Quota"]
        )

        with tab1:
            st.subheader(f"Jurisdiction Tree for {selected_zone}")
            df_jurisdiction = pd.read_sql_query(
                """
                SELECT 
                    w.id AS Woreda_ID, 
                    w.name AS Woreda_Name, 
                    w.fertilizer_quota AS Woreda_Quota,
                    k.id AS Kebele_ID,
                    k.name AS Kebele_Name, 
                    k.fertilizer_quota AS Kebele_Quota
                FROM woredas w
                LEFT JOIN kebeles k ON k.woreda_id = w.id
                WHERE w.zone_id = ?
            """,
                conn,
                params=(zone_id,),
            )
            st.dataframe(df_jurisdiction, use_container_width=True)

        with tab2:
            st.subheader(f"Register New Woreda in {selected_zone}")
            with st.form("add_woreda_form"):
                w_id = st.text_input("Woreda ID (e.g., WRD-003)")
                w_name = st.text_input("Woreda Name")
                w_quota = st.number_input("Initial Quota (Quintals)", min_value=0, step=100)
                submit_woreda = st.form_submit_button("Register Woreda")

                if submit_woreda:
                    if w_id and w_name:
                        try:
                            cursor = conn.cursor()
                            cursor.execute(
                                "INSERT INTO woredas (id, name, zone_id, fertilizer_quota) VALUES (?, ?, ?, ?)",
                                (w_id, w_name, zone_id, w_quota),
                            )
                            conn.commit()
                            st.success(f"Woreda '{w_name}' registered successfully!")
                            st.rerun()
                        except sqlite3.IntegrityError:
                            st.error(f"Woreda ID '{w_id}' already exists.")
                    else:
                        st.error("Please fill in all inputs.")

        with tab3:
            st.subheader("Allocate Quota to Woredas")
            woredas = pd.read_sql_query(
                "SELECT id, name, fertilizer_quota FROM woredas WHERE zone_id = ?",
                conn,
                params=(zone_id,),
            )

            if not woredas.empty:
                selected_woreda = st.selectbox("Select Target Woreda", woredas["name"].tolist())
                curr_w_quota = woredas[woredas["name"] == selected_woreda]["fertilizer_quota"].values[0]

                new_w_quota = st.number_input(
                    f"Set Quota for {selected_woreda} (Quintals)",
                    min_value=0,
                    value=int(curr_w_quota),
                )

                # Cascade check: Sum of all other woredas + new allocation cannot exceed total Zone Quota
                other_woredas_sum = pd.read_sql_query(
                    "SELECT SUM(fertilizer_quota) AS sum FROM woredas WHERE zone_id = ? AND name != ?",
                    conn,
                    params=(zone_id, selected_woreda),
                )["sum"].values[0] or 0

                total_projected = other_woredas_sum + new_w_quota

                if total_projected > zone_quota:
                    st.error(
                        f"⚠️ Allocation Error: Total allocated woredas quota ({total_projected}) exceeds available Zonal Quota ({zone_quota})!"
                    )
                else:
                    if st.button("Apply Woreda Quota"):
                        cursor = conn.cursor()
                        cursor.execute(
                            "UPDATE woredas SET fertilizer_quota = ? WHERE name = ?",
                            (new_w_quota, selected_woreda),
                        )
                        conn.commit()
                        st.success(f"Woreda Quota updated to {new_w_quota} Quintals!")
                        st.rerun()
            else:
                st.info("No woredas registered under this zone yet.")

# ==============================================================================
# 3. WOREDA MANAGER ROLE
# ==============================================================================
elif role == "Woreda Manager":
    st.header("🏛 Woreda Management Portal")
    st.markdown("---")

    woredas = pd.read_sql_query("SELECT id, name, fertilizer_quota FROM woredas", conn)

    if not woredas.empty:
        selected_woreda = st.sidebar.selectbox("Select Active Woreda", woredas["name"].tolist())
        woreda_id = woredas[woredas["name"] == selected_woreda]["id"].values[0]
        woreda_quota = woredas[woredas["name"] == selected_woreda]["fertilizer_quota"].values[0]

        st.metric("Total Woreda Allocated Quota", f"{woreda_quota} Quintals")

        tab1, tab2, tab3, tab4 = st.tabs(
            ["👥 Kebeles & Farmers Overview", "➕ Register Kebele & Agents", "💳 Manage Fee Items", "⚖️ Cascade Kebele Quota"]
        )

        with tab1:
            st.subheader("Kebele Staff & Farmer Directory")
            df_farmers = pd.read_sql_query(
                """
                SELECT 
                    f.id AS Farmer_ID, 
                    f.name AS Farmer_Name, 
                    f.village AS Village,
                    f.land_size AS Land_Size_Ha,
                    f.fee_verified AS Fees_Paid, 
                    f.status AS Status, 
                    k.name AS Kebele,
                    k.da_name AS Extension_Agent
                FROM farmers f
                JOIN kebeles k ON f.kebele_id = k.id
                WHERE k.woreda_id = ?
            """,
                conn,
                params=(woreda_id,),
            )
            st.dataframe(df_farmers, use_container_width=True)

        with tab2:
            st.subheader("Register Kebele & Assign Extension Agents")
            with st.form("add_kebele_form"):
                k_id = st.text_input("Kebele ID (e.g., KEB-003)")
                k_name = st.text_input("Kebele Name")
                da_name = st.text_input("DA Worker Lead Name")
                assistant_name = st.text_input("Assistant DA Name")
                k_quota = st.number_input("Initial Quota (Quintals)", min_value=0, step=50)
                
                submit_kebele = st.form_submit_button("Register Kebele")

                if submit_kebele:
                    if k_id and k_name and da_name:
                        try:
                            cursor = conn.cursor()
                            cursor.execute(
                                """
                                INSERT INTO kebeles (id, name, woreda_id, da_name, assistant_name, fertilizer_quota)
                                VALUES (?, ?, ?, ?, ?, ?)
                            """,
                                (k_id, k_name, woreda_id, da_name, assistant_name, k_quota),
                            )
                            conn.commit()
                            st.success(f"Kebele '{k_name}' and personnel registered successfully!")
                            st.rerun()
                        except sqlite3.IntegrityError:
                            st.error(f"Kebele ID '{k_id}' already exists.")
                    else:
                        st.error("Please supply mandatory fields.")

        with tab3:
            st.subheader("Configure Service & Registration Fee Items")
            with st.form("add_fee_form"):
                fee_name = st.text_input("Fee Description (e.g., Transport Charge)")
                fee_amount = st.number_input("Amount (ETB)", min_value=0.0, step=10.0)
                submit_fee = st.form_submit_button("Save Fee Item")

                if submit_fee and fee_name:
                    cursor = conn.cursor()
                    cursor.execute(
                        "INSERT INTO fee_items (woreda_id, fee_name, amount) VALUES (?, ?, ?)",
                        (woreda_id, fee_name, fee_amount),
                    )
                    conn.commit()
                    st.success(f"Fee item '{fee_name}' added successfully!")
                    st.rerun()

            st.subheader("Active Woreda Service Fee Schedule")
            fees_df = pd.read_sql_query(
                "SELECT id AS Item_ID, fee_name AS Fee_Description, amount AS Amount_ETB FROM fee_items WHERE woreda_id = ?",
                conn,
                params=(woreda_id,),
            )
            st.dataframe(fees_df, use_container_width=True)

        with tab4:
            st.subheader("Allocate Quota to Kebeles")
            kebeles = pd.read_sql_query(
                "SELECT id, name, fertilizer_quota FROM kebeles WHERE woreda_id = ?",
                conn,
                params=(woreda_id,),
            )

            if not kebeles.empty:
                selected_kebele = st.selectbox("Select Kebele", kebeles["name"].tolist())
                curr_k_q = kebeles[kebeles["name"] == selected_kebele]["fertilizer_quota"].values[0]

                new_k_q = st.number_input(
                    f"Set Quota for {selected_kebele} (Quintals)",
                    min_value=0,
                    value=int(curr_k_q),
                )

                # Validation
                other_kebeles_sum = pd.read_sql_query(
                    "SELECT SUM(fertilizer_quota) AS sum FROM kebeles WHERE woreda_id = ? AND name != ?",
                    conn,
                    params=(woreda_id, selected_kebele),
                )["sum"].values[0] or 0

                if (other_kebeles_sum + new_k_q) > woreda_quota:
                    st.error(
                        f"⚠️ Quota Exceeded: Kebele allocation sum ({other_kebeles_sum + new_k_q}) exceeds Woreda limit ({woreda_quota})!"
                    )
                else:
                    if st.button("Apply Kebele Quota"):
                        cursor = conn.cursor()
                        cursor.execute(
                            "UPDATE kebeles SET fertilizer_quota = ? WHERE name = ?",
                            (new_k_q, selected_kebele),
                        )
                        conn.commit()
                        st.success(f"Updated Kebele Quota to {new_k_q} Quintals!")
                        st.rerun()

# ==============================================================================
# 4. DA WORKER ROLE (KEBELE LEVEL)
# ==============================================================================
elif role == "DA Worker (Kebele Level)":
    st.header("👨‍🌾 Kebele DA Execution Portal")
    st.markdown("---")

    kebeles = pd.read_sql_query("SELECT id, name, woreda_id, da_name, assistant_name, fertilizer_quota FROM kebeles", conn)

    if not kebeles.empty:
        selected_kebele = st.sidebar.selectbox("Active Kebele Workstation", kebeles["name"].tolist())
        kebele_info = kebeles[kebeles["name"] == selected_kebele].iloc[0]
        kebele_id = kebele_info["id"]

        col1, col2, col3 = st.columns(3)
        col1.metric("Kebele Quota", f"{kebele_info['fertilizer_quota']} Quintals")
        col2.metric("Lead DA Worker", kebele_info["da_name"])
        col3.metric("Assistant DA Worker", kebele_info["assistant_name"])

        tab1, tab2, tab3, tab4 = st.tabs(
            ["📝 Farmer Registration", "💳 Fee Verification & Queue", "👥 Auto Grouping", "📋 Master Pickup List"]
        )

        with tab1:
            st.subheader("Register Beneficiary Farmer")
            with st.form("register_local_farmer"):
                c1, c2 = st.columns(2)
                f_id = c1.text_input("Farmer ID (e.g., FAR-010)")
                nat_id = c1.text_input("National ID")
                name = c1.text_input("Full Name")
                phone = c1.text_input("Phone Number")
                village = c2.text_input("Village / Gott")
                land = c2.number_input("Land Size (Hectares)", min_value=0.1, step=0.1)

                submit_farmer = st.form_submit_button("Register Farmer")

                if submit_farmer:
                    if f_id and nat_id and name:
                        try:
                            cursor = conn.cursor()
                            cursor.execute(
                                """
                                INSERT INTO farmers (id, national_id, name, kebele_id, village, land_size, phone, fee_verified, status)
                                VALUES (?, ?, ?, ?, ?, ?, ?, 0, 'Pending Fees')
                            """,
                                (f_id, nat_id, name, kebele_id, village, land, phone),
                            )
                            conn.commit()
                            st.success(f"Registered farmer {name}!")
                            st.rerun()
                        except sqlite3.IntegrityError:
                            st.error("Farmer ID or National ID already exists!")
                    else:
                        st.error("Please fill in required fields.")

        with tab2:
            st.subheader("Verify Fees & Move to Distribution Queue")
            pending_farmers = pd.read_sql_query(
                "SELECT id, name, village, land_size, phone, fee_verified FROM farmers WHERE kebele_id = ? AND status = 'Pending Fees'",
                conn,
                params=(kebele_id,),
            )

            if not pending_farmers.empty:
                st.dataframe(pending_farmers, use_container_width=True)
                farmer_to_verify = st.selectbox("Select Farmer to Process", pending_farmers["id"].tolist())

                if st.button("Confirm Service Fee Payment"):
                    cursor = conn.cursor()
                    cursor.execute(
                        "UPDATE farmers SET fee_verified = 1, status = 'In Queue' WHERE id = ?",
                        (farmer_to_verify,),
                    )
                    conn.commit()
                    st.success(f"Farmer {farmer_to_verify} verified and added to Distribution Queue!")
                    st.rerun()
            else:
                st.info("No farmers currently pending fee payment.")

        with tab3:
            st.subheader("Automated Pickup Cluster Formation")
            st.caption("Bundles fee-verified queue members into groups of up to 5 farmers for fair queue processing.")

            queued_farmers = pd.read_sql_query(
                "SELECT id, name, village, land_size FROM farmers WHERE kebele_id = ? AND status = 'In Queue' AND fee_verified = 1",
                conn,
                params=(kebele_id,),
            )

            st.write(f"Active Fee-Paid Farmers Waiting for Groups: **{len(queued_farmers)}**")
            st.dataframe(queued_farmers, use_container_width=True)

            if len(queued_farmers) > 0:
                if st.button("Form Pickup Cluster (Group of 5)"):
                    cursor = conn.cursor()
                    
                    # Compute Next Group ID
                    max_group = pd.read_sql_query("SELECT MAX(group_id) as mg FROM farmers", conn)["mg"].values[0]
                    next_group = (max_group + 1) if max_group is not None else 1

                    # Pick top 5 farmers in queue
                    ids_to_group = queued_farmers["id"].tolist()[:5]

                    for fid in ids_to_group:
                        cursor.execute(
                            "UPDATE farmers SET status = 'Grouped', group_id = ? WHERE id = ?",
                            (next_group, fid),
                        )
                    conn.commit()
                    st.success(f"Group #{next_group} formed with {len(ids_to_group)} farmers!")
                    st.rerun()

        with tab4:
            st.subheader("Kebele Master Pickup Registry")
            master_list = pd.read_sql_query(
                """
                SELECT 
                    group_id AS Cluster_Group, 
                    id AS Farmer_ID, 
                    name AS Name, 
                    village AS Village, 
                    land_size AS Land_Size_Ha, 
                    phone AS Phone, 
                    status AS Distribution_Status
                FROM farmers 
                WHERE kebele_id = ?
                ORDER BY group_id ASC, id ASC
            """,
                conn,
                params=(kebele_id,),
            )
            st.dataframe(master_list, use_container_width=True)

conn.close()
