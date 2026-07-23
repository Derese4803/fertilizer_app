import csv
import io
import sqlite3
from flask import (
    Flask,
    Response,
    flash,
    g,
    jsonify,
    redirect,
    render_template_string,
    request,
    session,
    url_for,
)

app = Flask(__name__)
app.secret_key = "da_dashboard_secure_key_2026"
DATABASE = "da_system.db"


# ==========================================
# DATABASE SETUP & SEED DATA
# ==========================================


def get_db():
    if "db" not in g:
        g.db = sqlite3.connect(DATABASE)
        g.db.row_factory = sqlite3.Row
    return g.db


@app.teardown_appcontext
def close_db(error):
    db = g.pop("db", None)
    if db is not None:
        db.close()


def init_db():
    with app.app_context():
        db = get_db()

        # 1. Farmers table (UNIQUE National ID constraint)
        db.execute(
            """
            CREATE TABLE IF NOT EXISTS farmers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                national_id TEXT UNIQUE NOT NULL,
                full_name TEXT NOT NULL,
                phone TEXT NOT NULL,
                region TEXT NOT NULL,
                is_fee_verified INTEGER DEFAULT 0
            )
        """
        )

        # 2. Queue Services table
        db.execute(
            """
            CREATE TABLE IF NOT EXISTS queue_list (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                service_name TEXT NOT NULL,
                description TEXT NOT NULL,
                capacity INTEGER DEFAULT 50
            )
        """
        )

        # 3. Farmer Groups table
        db.execute(
            """
            CREATE TABLE IF NOT EXISTS farmer_groups (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                group_name TEXT NOT NULL,
                region TEXT NOT NULL,
                created_by_farmer_id INTEGER NOT NULL,
                FOREIGN KEY (created_by_farmer_id) REFERENCES farmers(id)
            )
        """
        )

        # 4. Group Members junction table
        db.execute(
            """
            CREATE TABLE IF NOT EXISTS group_members (
                group_id INTEGER,
                farmer_id INTEGER,
                joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (group_id, farmer_id),
                FOREIGN KEY (group_id) REFERENCES farmer_groups(id),
                FOREIGN KEY (farmer_id) REFERENCES farmers(id)
            )
        """
        )

        # --- SEED INITIAL DEMO DATA IF EMPTY ---
        cur = db.execute("SELECT COUNT(*) FROM farmers")
        if cur.fetchone()[0] == 0:
            # Seed Farmers
            farmers_seed = [
                ("NID-1001", "Abebe Bikila", "+251911123456", "Amhara", 1),
                ("NID-1002", "Sara Tadesse", "+251922234567", "Oromia", 1),
                ("NID-1003", "Dawit Kebede", "+251933345678", "Amhara", 0),
                ("NID-1004", "Fatima Hassan", "+251944456789", "Somali", 1),
                ("NID-1005", "Yonas Alemu", "+251955567890", "Sidama", 0),
            ]
            db.executemany(
                "INSERT INTO farmers (national_id, full_name, phone, region, is_fee_verified) VALUES (?, ?, ?, ?, ?)",
                farmers_seed,
            )

            # Seed Queues
            queues_seed = [
                (
                    "Fertilizer Allocation Queue",
                    "Distribution of Urea and NPS fertilizers for current season.",
                    100,
                ),
                (
                    "Tractor & Machinery Rental",
                    "Scheduling shared tractors for land preparation.",
                    25,
                ),
                (
                    "Improved Seed Supply",
                    "Certified high-yield wheat and maize seed allocation.",
                    60,
                ),
            ]
            db.executemany(
                "INSERT INTO queue_list (service_name, description, capacity) VALUES (?, ?, ?)",
                queues_seed,
            )

            # Seed Groups
            db.execute(
                "INSERT INTO farmer_groups (group_name, region, created_by_farmer_id) VALUES ('North Valley Wheat Cooperative', 'Amhara', 1)"
            )
            db.execute(
                "INSERT INTO farmer_groups (group_name, region, created_by_farmer_id) VALUES ('Oromia Maize Producers', 'Oromia', 2)"
            )

            # Seed Group Members
            members_seed = [
                (1, 1),
                (1, 3),  # Group 1: Abebe, Dawit
                (2, 2),
                (2, 4),  # Group 2: Sara, Fatima
            ]
            db.executemany(
                "INSERT INTO group_members (group_id, farmer_id) VALUES (?, ?)",
                members_seed,
            )

        db.commit()


# Initialize database
init_db()


# ==========================================
# EMBEDDED HTML TEMPLATE
# ==========================================

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Digital Agriculture (DA) Portal</title>
    <style>
        * { box-sizing: border-box; }
        body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; margin: 0; padding: 20px; background-color: #f0f4f1; color: #2c3e50; }
        .container { max-width: 1000px; margin: 0 auto; background: white; padding: 25px; border-radius: 10px; box-shadow: 0 4px 12px rgba(0,0,0,0.08); }
        header { border-bottom: 2px solid #2e7d32; padding-bottom: 15px; margin-bottom: 20px; }
        h1, h2, h3 { color: #1b5e20; margin-top: 0; }
        .nav { display: flex; gap: 10px; background: #e8f5e9; padding: 12px; border-radius: 6px; margin-bottom: 20px; flex-wrap: wrap; }
        .nav a { text-decoration: none; color: #2e7d32; font-weight: bold; padding: 6px 12px; border-radius: 4px; }
        .nav a:hover { background: #c8e6c9; }
        .flash { padding: 12px; background: #ffebee; color: #c62828; margin-bottom: 20px; border-radius: 6px; border-left: 5px solid #c62828; }
        .flash-success { background: #e8f5e9; color: #2e7d32; border-left-color: #2e7d32; }
        table { width: 100%; border-collapse: collapse; margin-top: 15px; }
        table, th, td { border: 1px solid #e0e0e0; padding: 12px; text-align: left; }
        th { background-color: #2e7d32; color: white; }
        tr:nth-child(even) { background-color: #f9f9f9; }
        .btn { background: #2e7d32; color: white; padding: 8px 14px; border: none; border-radius: 4px; text-decoration: none; cursor: pointer; display: inline-block; font-size: 14px; }
        .btn:hover { background: #1b5e20; }
        .btn-warning { background: #e65100; }
        .btn-warning:hover { background: #b23c00; }
        .card { background: #fafafa; border: 1px solid #e0e0e0; padding: 20px; border-radius: 8px; margin-bottom: 20px; }
        .badge { padding: 5px 10px; border-radius: 12px; font-weight: bold; font-size: 12px; text-transform: uppercase; }
        .badge-verified { background: #c8e6c9; color: #1b5e20; }
        .badge-pending { background: #ffcdd2; color: #b71c1c; }
        input, select { width: 100%; padding: 10px; margin: 8px 0 16px; border: 1px solid #ccc; border-radius: 4px; }
        .form-group { max-width: 500px; }
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>Digital Agriculture (DA) Portal</h1>
            <small>DA Fee Verification & Group Management System</small>
        </header>

        <div class="nav">
            <a href="{{ url_for('index') }}">Home / Login</a>
            <a href="{{ url_for('register') }}">Farmer Registration</a>
            <a href="{{ url_for('da_dashboard') }}">DA Admin Dashboard</a>
            {% if session.get('farmer_id') %}
                <a href="{{ url_for('farmer_portal') }}">Farmer Portal</a>
                <a href="{{ url_for('logout') }}" style="margin-left: auto; color: #c62828;">Logout ({{ session.get('farmer_name') }})</a>
            {% endif %}
        </div>

        {% with messages = get_flashed_messages(with_categories=true) %}
            {% if messages %}
                {% for category, message in messages %}
                    <div class="flash {% if category == 'success' %}flash-success{% endif %}">{{ message }}</div>
                {% endfor %}
            {% endif %}
        {% endwith %}

        {% block content %}{% endblock %}
    </div>
</body>
</html>
"""


# ==========================================
# UI ROUTES & LOGIC
# ==========================================


@app.route("/")
def index():
    return render_template_string(
        HTML_TEMPLATE
        + """
        <h2>System Login</h2>
        <div class="card form-group">
            <h3>Farmer Login</h3>
            <form action="{{ url_for('login') }}" method="POST">
                <label>Enter National ID:</label>
                <input type="text" name="national_id" placeholder="e.g. NID-1001" required>
                <button type="submit" class="btn">Login to Portal</button>
            </form>
        </div>
        
        <div class="card">
            <h3>Quick Demo Accounts</h3>
            <p><strong>Verified Farmer (Full Access):</strong> National ID = <code>NID-1001</code></p>
            <p><strong>Unverified Farmer (Restricted):</strong> National ID = <code>NID-1003</code></p>
        </div>
    """
    )


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        national_id = request.form.get("national_id").strip()
        full_name = request.form.get("full_name").strip()
        phone = request.form.get("phone").strip()
        region = request.form.get("region").strip()

        db = get_db()
        try:
            # Enforces UNIQUE constraint on national_id
            db.execute(
                "INSERT INTO farmers (national_id, full_name, phone, region, is_fee_verified) VALUES (?, ?, ?, ?, 0)",
                (national_id, full_name, phone, region),
            )
            db.commit()
            flash("Registration successful! Login below using your National ID.", "success")
            return redirect(url_for("index"))
        except sqlite3.IntegrityError:
            flash(
                "Error: A farmer with this National ID is ALREADY registered!",
                "error",
            )

    return render_template_string(
        HTML_TEMPLATE
        + """
        <h2>New Farmer Registration</h2>
        <div class="card form-group">
            <form method="POST">
                <label>National ID:</label>
                <input type="text" name="national_id" required>
                
                <label>Full Name:</label>
                <input type="text" name="full_name" required>
                
                <label>Phone Number:</label>
                <input type="text" name="phone" required>
                
                <label>Region / District:</label>
                <input type="text" name="region" required>
                
                <button type="submit" class="btn">Register Farmer</button>
            </form>
        </div>
    """
    )


@app.route("/login", methods=["POST"])
def login():
    national_id = request.form.get("national_id").strip()
    db = get_db()
    farmer = db.execute(
        "SELECT * FROM farmers WHERE national_id = ?", (national_id,)
    ).fetchone()

    if farmer:
        session["farmer_id"] = farmer["id"]
        session["farmer_name"] = farmer["full_name"]
        return redirect(url_for("farmer_portal"))
    else:
        flash("National ID not found. Please check or register first.", "error")
        return redirect(url_for("index"))


@app.route("/logout")
def logout():
    session.clear()
    flash("Logged out successfully.", "success")
    return redirect(url_for("index"))


# --- DA ADMIN DASHBOARD (Fee Verification) ---


@app.route("/da-dashboard", methods=["GET", "POST"])
def da_dashboard():
    db = get_db()

    # Verify/Revoke fee verification status
    if request.method == "POST":
        farmer_id = request.form.get("farmer_id")
        new_status = request.form.get("status")
        db.execute(
            "UPDATE farmers SET is_fee_verified = ? WHERE id = ?",
            (new_status, farmer_id),
        )
        db.commit()
        flash("Farmer fee status updated successfully!", "success")
        return redirect(url_for("da_dashboard"))

    farmers = db.execute("SELECT * FROM farmers ORDER BY id DESC").fetchall()

    return render_template_string(
        HTML_TEMPLATE
        + """
        <h2>DA Officer Dashboard - Fee Verification</h2>
        <p>Verify farmer payments to unlock access to Queues and Group Creation tools.</p>
        
        <table>
            <tr>
                <th>ID</th>
                <th>National ID</th>
                <th>Full Name</th>
                <th>Phone</th>
                <th>Region</th>
                <th>Fee Status</th>
                <th>Action</th>
            </tr>
            {% for f in farmers %}
            <tr>
                <td>{{ f.id }}</td>
                <td><strong>{{ f.national_id }}</strong></td>
                <td>{{ f.full_name }}</td>
                <td>{{ f.phone }}</td>
                <td>{{ f.region }}</td>
                <td>
                    {% if f.is_fee_verified %}
                        <span class="badge badge-verified">Verified</span>
                    {% else %}
                        <span class="badge badge-pending">Pending</span>
                    {% endif %}
                </td>
                <td>
                    <form method="POST" style="display:inline;">
                        <input type="hidden" name="farmer_id" value="{{ f.id }}">
                        {% if f.is_fee_verified %}
                            <input type="hidden" name="status" value="0">
                            <button type="submit" class="btn btn-warning">Revoke Fee</button>
                        {% else %}
                            <input type="hidden" name="status" value="1">
                            <button type="submit" class="btn">Verify Fee</button>
                        {% endif %}
                    </form>
                </td>
            </tr>
            {% endfor %}
        </table>
    """,
        farmers=farmers,
    )


# --- FARMER PORTAL & ACCESS CONTROL ---


@app.route("/farmer-portal", methods=["GET", "POST"])
def farmer_portal():
    if "farmer_id" not in session:
        return redirect(url_for("index"))

    db = get_db()
    farmer = db.execute(
        "SELECT * FROM farmers WHERE id = ?", (session["farmer_id"],)
    ).fetchone()

    # Create Group Handler (Verified farmers ONLY)
    if request.method == "POST" and "create_group" in request.form:
        if not farmer["is_fee_verified"]:
            flash(
                "Access Denied: You must complete fee verification on the DA dashboard first.",
                "error",
            )
            return redirect(url_for("farmer_portal"))

        group_name = request.form.get("group_name").strip()
        cur = db.execute(
            "INSERT INTO farmer_groups (group_name, region, created_by_farmer_id) VALUES (?, ?, ?)",
            (group_name, farmer["region"], farmer["id"]),
        )
        group_id = cur.lastrowid
        # Creator automatically becomes first member
        db.execute(
            "INSERT INTO group_members (group_id, farmer_id) VALUES (?, ?)",
            (group_id, farmer["id"]),
        )
        db.commit()
        flash("New group created successfully!", "success")
        return redirect(url_for("farmer_portal"))

    # Join Group Handler
    if request.method == "POST" and "join_group" in request.form:
        group_id = request.form.get("group_id")
        try:
            db.execute(
                "INSERT INTO group_members (group_id, farmer_id) VALUES (?, ?)",
                (group_id, farmer["id"]),
            )
            db.commit()
            flash("Joined group successfully!", "success")
        except sqlite3.IntegrityError:
            flash("You are already a member of this group.", "error")
        return redirect(url_for("farmer_portal"))

    # Query Data if Fee Verified
    queues = []
    groups = []
    if farmer["is_fee_verified"]:
        queues = db.execute("SELECT * FROM queue_list").fetchall()
        groups = db.execute(
            """
            SELECT fg.id, fg.group_name, fg.region, COUNT(gm.farmer_id) as member_count 
            FROM farmer_groups fg
            LEFT JOIN group_members gm ON fg.id = gm.group_id
            GROUP BY fg.id
        """
        ).fetchall()

    return render_template_string(
        HTML_TEMPLATE
        + """
        <h2>Farmer Portal</h2>
        
        <div class="card">
            <h3>Profile Summary</h3>
            <p><strong>Name:</strong> {{ farmer.full_name }}</p>
            <p><strong>National ID:</strong> {{ farmer.national_id }}</p>
            <p><strong>Region:</strong> {{ farmer.region }}</p>
            <p><strong>Fee Status:</strong> 
                {% if farmer.is_fee_verified %}
                    <span class="badge badge-verified">Fee Verified - Full Access</span>
                {% else %}
                    <span class="badge badge-pending">Payment Pending - Restricted</span>
                {% endif %}
            </p>
        </div>

        {% if not farmer.is_fee_verified %}
            <div class="card" style="border-left: 5px solid #c62828;">
                <h3>Access Restricted</h3>
                <p>Fee verification is required to view the Queue list, join farmer groups, or create new groups and export CSV data.</p>
                <p><em>Please complete payment or contact a DA officer to verify your fee.</em></p>
            </div>
        {% else %}
            <!-- UNLOCKED UNIFIED DASHBOARD -->
            <div class="card">
                <h3>Available Services Queue List</h3>
                <table>
                    <tr>
                        <th>Queue Service</th>
                        <th>Description</th>
                        <th>Capacity</th>
                    </tr>
                    {% for q in queues %}
                    <tr>
                        <td><strong>{{ q.service_name }}</strong></td>
                        <td>{{ q.description }}</td>
                        <td>{{ q.capacity }} Farmers</td>
                    </tr>
                    {% endfor %}
                </table>
            </div>

            <div class="card">
                <h3>Create New Farmer Group</h3>
                <form method="POST" class="form-group">
                    <input type="text" name="group_name" placeholder="Enter Group Name" required>
                    <button type="submit" name="create_group" class="btn">Create & Register Group</button>
                </form>
            </div>

            <div class="card">
                <h3>Active Farmer Groups & Export</h3>
                <table>
                    <tr>
                        <th>Group ID</th>
                        <th>Group Name</th>
                        <th>Region</th>
                        <th>Members</th>
                        <th>Actions</th>
                    </tr>
                    {% for g in groups %}
                    <tr>
                        <td>G-{{ g.id }}</td>
                        <td><strong>{{ g.group_name }}</strong></td>
                        <td>{{ g.region }}</td>
                        <td>{{ g.member_count }}</td>
                        <td>
                            <form method="POST" style="display:inline;">
                                <input type="hidden" name="group_id" value="{{ g.id }}">
                                <button type="submit" name="join_group" class="btn" style="background:#0288d1;">Join Group</button>
                            </form>
                            <a href="{{ url_for('export_group_csv', group_id=g.id) }}" class="btn">Download CSV</a>
                        </td>
                    </tr>
                    {% endfor %}
                </table>
            </div>
        {% endif %}
    """,
        farmer=farmer,
        queues=queues,
        groups=groups,
    )


# --- CSV EXPORT ROUTE ---


@app.route("/export-group-csv/<int:group_id>")
def export_group_csv(group_id):
    if "farmer_id" not in session:
        return redirect(url_for("index"))

    db = get_db()
    farmer = db.execute(
        "SELECT * FROM farmers WHERE id = ?", (session["farmer_id"],)
    ).fetchone()

    # Rule Check: Restricted if fee not verified
    if not farmer["is_fee_verified"]:
        flash("Verification required to export CSV group data.", "error")
        return redirect(url_for("farmer_portal"))

    group = db.execute(
        "SELECT * FROM farmer_groups WHERE id = ?", (group_id,)
    ).fetchone()

    # Query group members
    members = db.execute(
        """
        SELECT f.id, f.national_id, f.full_name, f.phone, f.region, f.is_fee_verified, gm.joined_at
        FROM farmers f
        JOIN group_members gm ON f.id = gm.farmer_id
        WHERE gm.group_id = ?
    """,
        (group_id,),
    ).fetchall()

    # Construct CSV File Buffer
    output = io.StringIO()
    writer = csv.writer(output)

    # Header Row
    writer.writerow(
        [
            "Group ID",
            "Group Name",
            "Farmer Name",
            "National ID",
            "Phone",
            "Region",
            "Fee Status",
            "Joined Date",
        ]
    )

    # Data Rows
    for m in members:
        status = "Verified" if m["is_fee_verified"] else "Pending"
        writer.writerow(
            [
                f"G-{group['id']}",
                group["group_name"],
                m["full_name"],
                m["national_id"],
                m["phone"],
                m["region"],
                status,
                m["joined_at"],
            ]
        )

    output.seek(0)
    filename = f"{group['group_name'].replace(' ', '_')}_members.csv"

    return Response(
        output.getvalue(),
        mimetype="text/csv",
        headers={"Content-Disposition": f"attachment;filename={filename}"},
    )


# ==========================================
# REST API ENDPOINTS (For Mobile/External Apps)
# ==========================================


@app.route("/api/farmers", methods=["GET"])
def api_get_farmers():
    db = get_db()
    farmers = db.execute("SELECT * FROM farmers").fetchall()
    return jsonify([dict(f) for f in farmers])


@app.route("/api/verify-fee", methods=["POST"])
def api_verify_fee():
    data = request.json or {}
    farmer_id = data.get("farmer_id")
    status = data.get("status", 1)

    if not farmer_id:
        return jsonify({"error": "farmer_id required"}), 400

    db = get_db()
    db.execute(
        "UPDATE farmers SET is_fee_verified = ? WHERE id = ?",
        (status, farmer_id),
    )
    db.commit()
    return jsonify({"success": True, "farmer_id": farmer_id, "is_fee_verified": status})


@app.route("/api/groups/<int:group_id>/members", methods=["GET"])
def api_group_members(group_id):
    db = get_db()
    members = db.execute(
        """
        SELECT f.id, f.national_id, f.full_name, f.phone, f.is_fee_verified
        FROM farmers f
        JOIN group_members gm ON f.id = gm.farmer_id
        WHERE gm.group_id = ?
    """,
        (group_id,),
    ).fetchall()
    return jsonify([dict(m) for m in members])


# ==========================================
# APP EXECUTION ENTRYPOINT
# ==========================================

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
