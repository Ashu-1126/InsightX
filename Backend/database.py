import os
import sqlite3

DB_PATH = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "../Database/factory.db")
)
os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)


def get_db():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    try:
        yield conn
    finally:
        try:
            conn.close()
        except sqlite3.ProgrammingError:
            pass


def init_db():
    def ensure_column(cursor, table_name, column_name, definition):
        cursor.execute(f"PRAGMA table_info({table_name})")
        columns = {row[1] for row in cursor.fetchall()}
        if column_name not in columns:
            cursor.execute(
                f"ALTER TABLE {table_name} ADD COLUMN {column_name} {definition}"
            )

    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA synchronous=NORMAL")
        conn.execute("PRAGMA cache_size=-32000")
        conn.execute("PRAGMA temp_store=MEMORY")
        c = conn.cursor()

        # ── EXISTING TABLES ──────────────────────────────────────────────────
        c.execute("""CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT NOT NULL UNIQUE,
            password TEXT NOT NULL,
            role TEXT DEFAULT 'user',
            verified INTEGER DEFAULT 0
        )""")
        c.execute("""CREATE TABLE IF NOT EXISTS people (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            extra TEXT,
            admin INTEGER DEFAULT 0
        )""")
        c.execute("""CREATE TABLE IF NOT EXISTS incidents (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            type TEXT NOT NULL,
            description TEXT,
            status TEXT DEFAULT 'Open',
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            clip_path TEXT
        )""")
        ensure_column(c, "incidents", "source", "TEXT DEFAULT 'manual'")
        ensure_column(c, "incidents", "confidence", "REAL")
        ensure_column(c, "incidents", "evidence_image", "TEXT")
        ensure_column(c, "incidents", "report_path", "TEXT")
        ensure_column(c, "incidents", "camera_id", "INTEGER")
        ensure_column(c, "incidents", "event_id", "INTEGER")
        c.execute("""CREATE TABLE IF NOT EXISTS incident_events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            incident_type TEXT NOT NULL,
            camera_id INTEGER,
            state TEXT NOT NULL,
            started_at TEXT NOT NULL,
            last_seen_at TEXT NOT NULL,
            resolved_at TEXT,
            incident_count INTEGER DEFAULT 0
        )""")
        c.execute("""CREATE TABLE IF NOT EXISTS incident_audit (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            incident_id INTEGER,
            status TEXT,
            changed_at TEXT
        )""")
        c.execute("""CREATE TABLE IF NOT EXISTS feedback (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            incident_id INTEGER,
            comment TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )""")
        c.execute("""CREATE TABLE IF NOT EXISTS settings (
            key TEXT PRIMARY KEY,
            value TEXT
        )""")

        # ── SENTINEL AI: ZONES ───────────────────────────────────────────────
        c.execute("""CREATE TABLE IF NOT EXISTS zones (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            description TEXT,
            x REAL DEFAULT 0,
            y REAL DEFAULT 0,
            width REAL DEFAULT 150,
            height REAL DEFAULT 100,
            risk_level TEXT DEFAULT 'safe',
            camera_id INTEGER
        )""")

        # Seed zones if empty
        c.execute("SELECT COUNT(*) FROM zones")
        if c.fetchone()[0] == 0:
            zones = [
                ("zone_a", "Production Floor",    "Main manufacturing area",         50,  50,  200, 150, "safe", 1),
                ("zone_b", "Storage Area",         "Raw materials & finished goods",  300, 50,  150, 150, "safe", 2),
                ("zone_c", "Chemical Processing",  "Hazardous chemical handling",     500, 50,  180, 150, "safe", 3),
                ("zone_d", "Loading Bay",           "Truck loading & unloading",       50,  260, 180, 120, "safe", None),
                ("zone_e", "Control Room",          "Operations control center",        300, 260, 160, 120, "safe", None),
                ("zone_f", "Confined Space",        "Tank & confined space area",       520, 260, 160, 120, "safe", None),
            ]
            c.executemany(
                "INSERT INTO zones (id,name,description,x,y,width,height,risk_level,camera_id) VALUES (?,?,?,?,?,?,?,?,?)",
                zones,
            )

        # ── SENTINEL AI: SENSORS ─────────────────────────────────────────────
        c.execute("""CREATE TABLE IF NOT EXISTS sensors (
            id TEXT PRIMARY KEY,
            zone_id TEXT NOT NULL,
            name TEXT NOT NULL,
            sensor_type TEXT NOT NULL,
            unit TEXT NOT NULL,
            threshold_warning REAL,
            threshold_critical REAL,
            status TEXT DEFAULT 'active',
            FOREIGN KEY (zone_id) REFERENCES zones(id)
        )""")

        # Seed sensors
        c.execute("SELECT COUNT(*) FROM sensors")
        if c.fetchone()[0] == 0:
            sensors = []
            sensor_defs = [
                ("methane",     "Methane",              "ppm",    5.0,  10.0),
                ("temperature", "Temperature",           "°C",    45.0,  65.0),
                ("humidity",    "Humidity",              "%",     75.0,  90.0),
                ("smoke",       "Smoke Concentration",   "µg/m³", 100.0, 200.0),
                ("pressure",    "Pressure",              "bar",    6.0,   8.5),
                ("vibration",   "Vibration",             "mm/s",  15.0,  25.0),
            ]
            for zone_id in ["zone_a","zone_b","zone_c","zone_d","zone_e","zone_f"]:
                for stype, sname, unit, warn, crit in sensor_defs:
                    sid = f"{zone_id}_{stype}"
                    sensors.append((sid, zone_id, f"{sname} Sensor", stype, unit, warn, crit, "active"))
            c.executemany(
                "INSERT INTO sensors (id,zone_id,name,sensor_type,unit,threshold_warning,threshold_critical,status) VALUES (?,?,?,?,?,?,?,?)",
                sensors,
            )

        # ── SENTINEL AI: SENSOR READINGS ─────────────────────────────────────
        c.execute("""CREATE TABLE IF NOT EXISTS sensor_readings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sensor_id TEXT NOT NULL,
            zone_id TEXT NOT NULL,
            sensor_type TEXT NOT NULL,
            value REAL NOT NULL,
            unit TEXT NOT NULL,
            timestamp TEXT NOT NULL,
            is_warning INTEGER DEFAULT 0,
            is_critical INTEGER DEFAULT 0
        )""")
        c.execute("CREATE INDEX IF NOT EXISTS idx_sensor_readings_sensor_ts ON sensor_readings(sensor_id, timestamp)")
        c.execute("CREATE INDEX IF NOT EXISTS idx_sensor_readings_zone_ts ON sensor_readings(zone_id, timestamp)")
        c.execute("CREATE INDEX IF NOT EXISTS idx_sensor_readings_ts ON sensor_readings(timestamp)")
        c.execute("CREATE INDEX IF NOT EXISTS idx_incidents_created_at ON incidents(created_at)")
        c.execute("CREATE INDEX IF NOT EXISTS idx_incidents_status ON incidents(status)")
        c.execute("CREATE INDEX IF NOT EXISTS idx_incidents_type ON incidents(type)")

        # ── SENTINEL AI: PERMITS ─────────────────────────────────────────────
        c.execute("""CREATE TABLE IF NOT EXISTS permits (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            permit_number TEXT UNIQUE,
            permit_type TEXT NOT NULL,
            zone_id TEXT NOT NULL,
            worker_name TEXT NOT NULL,
            issued_by TEXT DEFAULT 'Safety Officer',
            description TEXT,
            hazards TEXT DEFAULT '[]',
            precautions TEXT DEFAULT '[]',
            start_time TEXT NOT NULL,
            end_time TEXT NOT NULL,
            status TEXT DEFAULT 'active',
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (zone_id) REFERENCES zones(id)
        )""")

        # ── SENTINEL AI: RISK ASSESSMENTS ─────────────────────────────────────
        c.execute("""CREATE TABLE IF NOT EXISTS risk_assessments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            zone_id TEXT NOT NULL,
            risk_score REAL NOT NULL,
            severity TEXT NOT NULL,
            risk_type TEXT,
            risk_category TEXT,
            probability REAL DEFAULT 0.0,
            eta_to_incident INTEGER DEFAULT 0,
            contributing_factors TEXT DEFAULT '[]',
            triggered_by TEXT DEFAULT '{}',
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            resolved_at TEXT,
            is_active INTEGER DEFAULT 1
        )""")

        # ── SENTINEL AI: EMERGENCY EVENTS ─────────────────────────────────────
        c.execute("""CREATE TABLE IF NOT EXISTS emergency_events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            risk_assessment_id INTEGER,
            zone_id TEXT NOT NULL,
            event_type TEXT NOT NULL,
            severity TEXT NOT NULL,
            action_plan TEXT DEFAULT '[]',
            evacuation_zones TEXT DEFAULT '[]',
            responders_notified TEXT DEFAULT '[]',
            status TEXT DEFAULT 'active',
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            resolved_at TEXT,
            FOREIGN KEY (risk_assessment_id) REFERENCES risk_assessments(id)
        )""")

        # Indexes for tables defined above (created after their tables exist)
        c.execute("CREATE INDEX IF NOT EXISTS idx_permits_status_zone ON permits(status, zone_id)")
        c.execute("CREATE INDEX IF NOT EXISTS idx_risk_assessments_active ON risk_assessments(is_active, created_at)")
        c.execute("CREATE INDEX IF NOT EXISTS idx_emergency_events_status ON emergency_events(status, created_at)")

        # ── SENTINEL AI: KNOWLEDGE BASE ───────────────────────────────────────
        c.execute("""CREATE TABLE IF NOT EXISTS knowledge_base (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            content TEXT NOT NULL,
            document_type TEXT DEFAULT 'general',
            tags TEXT DEFAULT '[]',
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )""")

        # Seed knowledge base with safety documents
        c.execute("SELECT COUNT(*) FROM knowledge_base")
        if c.fetchone()[0] == 0:
            kb_docs = [
                ("OISD-116: Hot Work Safety", """Hot work includes welding, cutting, grinding, and any operation producing sparks or flames.
Hot work permits must be issued 30 minutes before work begins.
Methane/gas levels must be below 10% LEL before hot work commences.
A fire watch must be maintained for 30 minutes after hot work completion.
Fire extinguisher must be within 3 meters of hot work zone.
Historical analysis: 63% of explosion incidents occurred within 2 hours of hot work commencement.
Root cause in 78% of cases: gas sensor readings ignored when permit was active.""",
                "regulation", '["hot_work","explosion","permit"]'),
                ("DGMS Circular: Confined Space Entry", """Confined space entry requires atmospheric testing before entry.
Oxygen levels must be between 19.5% and 23.5%.
Gas levels must be below 10% LEL.
A standby person must be present throughout entry.
Rescue equipment must be available at entry point.
Historical data shows 41% of confined space fatalities occur due to oxygen deficiency.
Shift change periods account for 29% of confined space incidents — critical handover period.""",
                "regulation", '["confined_space","oxygen","entry_permit"]'),
                ("Factory Act: PPE Compliance", """Personal protective equipment must be worn in all designated hazard zones.
Hard hats mandatory in zones with overhead work or material handling.
Safety vests required in all operational areas.
Masks required when smoke/chemical concentration exceeds threshold.
Non-compliance rate above 20% triggers mandatory zone shutdown.
Analysis: PPE violations increase injury risk by 340% in high-temperature zones.""",
                "regulation", '["ppe","compliance","safety_vest","hardhat"]'),
                ("Incident Pattern Analysis: Shift Changes", """Analysis of 847 incidents over 5 years reveals critical patterns:
63% of all incidents occur during shift change windows (06:00-07:00, 14:00-15:00, 22:00-23:00).
Most common cause: incomplete safety handover and sensor alarm fatigue.
Peak risk: first 20 minutes of new shift when workers are adjusting.
Recommendation: mandatory 10-minute safety briefing at each shift change.
Zones B and C show highest incident rates during shift changes (23% and 31% respectively).""",
                "incident_report", '["shift_change","pattern","risk_period"]'),
                ("Chemical Processing Zone Safety Manual", """Zone C (Chemical Processing) requires heightened monitoring.
Temperature above 55°C combined with any chemical permit is a cascade risk indicator.
Pressure above 7 bar requires immediate supervisor notification.
Simultaneous smoke detection and elevated methane (>5ppm) requires zone evacuation.
Fire suppression system activates automatically at smoke concentration >300 µg/m³.
Historical: Zone C accounts for 34% of all critical incidents despite being 12% of floor area.""",
                "safety_manual", '["chemical","zone_c","temperature","pressure"]'),
                ("Near Miss Reports: Vibration-Related Equipment Failure", """18 near-miss reports analyzed from last 24 months.
Vibration readings above 20mm/s sustained for >5 minutes predicted bearing failures in 89% of cases.
Critical finding: when vibration exceeds threshold during active maintenance permit, risk of catastrophic equipment failure increases 6x.
Recommendation: auto-suspend maintenance operations when vibration exceeds 18mm/s.
Zones A and D show highest vibration incidents — rotate equipment inspection schedule.""",
                "near_miss", '["vibration","maintenance","equipment_failure"]'),
                ("Emergency Response Protocol: Explosion Risk", """On detection of explosion risk (methane > 10ppm + hot work active):
Step 1: Immediately notify zone supervisor and safety officer (< 2 minutes).
Step 2: Evacuate all personnel from affected zone and adjacent zones.
Step 3: Halt all hot work operations immediately.
Step 4: Activate ventilation system in affected zone.
Step 5: Dispatch fire & gas team for atmospheric verification.
Step 6: Do not re-enter zone until atmospheric readings confirmed safe.
Emergency contacts: Fire Brigade ext. 100, Medical ext. 102, Control Room ext. 200.""",
                "safety_manual", '["explosion","emergency","evacuation","hot_work"]'),
            ]
            c.executemany(
                "INSERT INTO knowledge_base (title, content, document_type, tags) VALUES (?,?,?,?)",
                kb_docs,
            )

        # ── SENTINEL AI: SHIFT RECORDS ────────────────────────────────────────
        c.execute("""CREATE TABLE IF NOT EXISTS shift_records (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            shift_name TEXT NOT NULL,
            supervisor TEXT,
            start_time TEXT NOT NULL,
            end_time TEXT,
            zone_ids TEXT DEFAULT '[]',
            worker_count INTEGER DEFAULT 0,
            status TEXT DEFAULT 'active',
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )""")

        conn.commit()
