import streamlit as st
import pandas as pd
import numpy as np
import sqlite3
import json
import re
from datetime import datetime, timedelta, date
from pathlib import Path
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, confusion_matrix, accuracy_score, f1_score
from sklearn.pipeline import Pipeline
import plotly.express as px

from spi.adapter import answer_in_session, assistant_mode_label
from spi.triage import detect_hazard as detect_hybrid_hazard
from spi.theme import css as spi_theme_css

# --------------------------- CONFIG ---------------------------
st.set_page_config(page_title="Safety Precursor Intelligence", page_icon="🛡️", layout="wide")
DB_PATH = Path("safety_precursor.db")
MODEL_CATEGORIES = [
    "Mechanical / Procedure Violation",
    "Fall & Working at Heights Hazard",
    "Chemical / Gas Leak Hazard",
    "Electrical Safety Hazard",
    "Routine / Non-Hazardous Observation",
]
SITES = ["Refinery Unit A", "Refinery Unit B", "Storage Yard Alpha", "Assembly Plant 2"]
DEPARTMENTS = ["Operations", "Maintenance", "Warehouse", "Utilities", "Production"]

# Theme styling is injected after the sidebar appearance control is created.

# --------------------------- DATABASE ---------------------------
def db():
    con = sqlite3.connect(DB_PATH, check_same_thread=False)
    con.row_factory = sqlite3.Row
    return con

def init_db():
    with db() as con:
        con.execute("""
        CREATE TABLE IF NOT EXISTS reports (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            report_code TEXT UNIQUE,
            report_date TEXT,
            site TEXT,
            department TEXT,
            shift TEXT,
            equipment TEXT,
            report_text TEXT,
            category TEXT,
            risk_level TEXT,
            risk_score INTEGER,
            model_confidence REAL,
            status TEXT DEFAULT 'Open',
            corrective_action TEXT,
            source TEXT DEFAULT 'User submitted',
            is_incident INTEGER DEFAULT 0
        )""")
        con.execute("""
        CREATE TABLE IF NOT EXISTS actions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            report_id INTEGER,
            action_text TEXT,
            owner TEXT,
            due_date TEXT,
            status TEXT DEFAULT 'Open',
            FOREIGN KEY(report_id) REFERENCES reports(id)
        )""")

def read_reports():
    with db() as con:
        return pd.read_sql_query("SELECT * FROM reports ORDER BY report_date DESC, id DESC", con)

def save_report(row):
    with db() as con:
        con.execute("""
        INSERT INTO reports
        (report_code, report_date, site, department, shift, equipment, report_text,
         category, risk_level, risk_score, model_confidence, status, corrective_action, source, is_incident)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            row["report_code"], row["report_date"], row["site"], row["department"],
            row["shift"], row["equipment"], row["report_text"], row["category"],
            row["risk_level"], int(row["risk_score"]), float(row["model_confidence"]),
            row["status"], row["corrective_action"], row["source"], int(row["is_incident"])
        ))

def seed_demo_data():
    with db() as con:
        count = con.execute("SELECT COUNT(*) FROM reports").fetchone()[0]
    if count:
        return
    rng = np.random.default_rng(27)
    samples = {
        MODEL_CATEGORIES[0]: [
            "Operator removed the press machine guard while the machine was running.",
            "Maintenance team bypassed the conveyor interlock during troubleshooting.",
            "Technician started pump maintenance without applying lockout tagout.",
            "Forklift was operated above the marked speed limit in the loading bay.",
            "Machine emergency stop was obstructed by stored material.",
            "Worker reached into moving equipment to clear a jam.",
            "Safety procedure was skipped before restarting the compressor.",
            "A contractor used a machine without completing the required permit."
        ],
        MODEL_CATEGORIES[1]: [
            "Scaffold platform has a loose plank and missing toe board at height.",
            "Worker used a ladder with a damaged side rail near the tank.",
            "Open floor edge on the mezzanine has no guardrail or warning barrier.",
            "Harness lanyard was not connected while working on the elevated platform.",
            "Access ladder to the roof is unsecured and shifts under load.",
            "Materials are stored close to an unprotected floor opening.",
            "Scaffolding inspection tag is missing from the work area.",
            "Worker was standing on an unstable surface to reach overhead piping."
        ],
        MODEL_CATEGORIES[2]: [
            "Chemical smell was reported near the chlorine cylinder valve.",
            "Small solvent leak was observed below the transfer pump flange.",
            "Gas detector alarm activated near the storage manifold.",
            "Corrosion is visible on the chemical dosing line connection.",
            "Unlabelled chemical container was found leaking in the storage area.",
            "Operator noticed vapour escaping from a damaged process hose.",
            "Acid transfer hose has a wet patch around the coupling.",
            "Ventilation was not operating in the chemical handling room."
        ],
        MODEL_CATEGORIES[3]: [
            "Damaged insulation was found on a temporary welding power cable.",
            "Electrical panel door was open with exposed terminals accessible.",
            "Extension lead is routed through standing water near the workshop.",
            "Grounding cable is disconnected from the portable welding machine.",
            "Burn marks were observed around the distribution board socket.",
            "A temporary cable has exposed copper strands near the walkway.",
            "Circuit breaker cover is missing from the utility panel.",
            "Worker reported a tingling sensation after touching metal equipment."
        ],
        MODEL_CATEGORIES[4]: [
            "Shift handover completed and all routine checks were recorded.",
            "Work area was clean and access routes remained unobstructed.",
            "Scheduled inspection completed with no abnormal findings.",
            "PPE stock was replenished and stored in the designated cabinet.",
            "Routine toolbox talk was completed before the morning shift.",
            "Fire extinguishers were inspected and tags were up to date.",
            "Production readings remained within normal operating limits.",
            "Housekeeping inspection found no safety observations."
        ]
    }
    modifiers = [
        " during the morning shift", " during night shift", " near the north access gate",
        " after routine maintenance", " during a contractor activity", " beside line 3",
        " during equipment cleaning", " before the scheduled shutdown"
    ]
    rows = []
    today = date.today()
    for i in range(240):
        cat = rng.choice(MODEL_CATEGORIES, p=[.23, .22, .19, .19, .17])
        txt = str(rng.choice(samples[cat])) + str(rng.choice(modifiers))
        days_ago = int(rng.integers(0, 90))
        risk = 1 if cat == MODEL_CATEGORIES[4] else int(rng.choice([2, 3, 4, 5], p=[.12, .28, .40, .20]))
        if risk <= 2: level = "Low"
        elif risk <= 3: level = "Medium"
        else: level = "High"
        rows.append({
            "report_code": f"DEMO-{1000+i}", "report_date": (today-timedelta(days=days_ago)).isoformat(),
            "site": str(rng.choice(SITES)), "department": str(rng.choice(DEPARTMENTS)),
            "shift": str(rng.choice(["Day", "Evening", "Night"])),
            "equipment": str(rng.choice(["Conveyor", "Pump", "Compressor", "Scaffold", "Panel", "General"])),
            "report_text": txt, "category": cat, "risk_level": level,
            "risk_score": risk*20, "model_confidence": 0.0, "status": str(rng.choice(["Open","In Progress","Closed"], p=[.35,.25,.40])),
            "corrective_action": "Review observation and apply site safety procedure.",
            "source": "Synthetic demonstration data", "is_incident": 0
        })
    with db() as con:
        con.executemany("""
        INSERT OR IGNORE INTO reports
        (report_code, report_date, site, department, shift, equipment, report_text, category,
         risk_level, risk_score, model_confidence, status, corrective_action, source, is_incident)
        VALUES (:report_code,:report_date,:site,:department,:shift,:equipment,:report_text,:category,
         :risk_level,:risk_score,:model_confidence,:status,:corrective_action,:source,:is_incident)
        """, rows)

init_db()
seed_demo_data()

# --------------------------- MODEL DATA ---------------------------
@st.cache_resource
def train_classifier():
    # Varied demonstration text generated from labelled sentence patterns.
    rng = np.random.default_rng(91)
    templates = {
        MODEL_CATEGORIES[0]: [
            "operator bypassed the safety interlock on the {machine}",
            "worker entered the danger zone while {machine} was operating",
            "lockout tagout was not applied before servicing the {machine}",
            "machine guard was removed during {task}",
            "emergency stop was blocked near the {machine}",
            "forklift was driven above the permitted speed in the {area}",
            "contractor restarted equipment without an approved permit"
        ],
        MODEL_CATEGORIES[1]: [
            "scaffold plank was loose and toe boards were missing at {area}",
            "worker was at height without connecting the fall arrest harness",
            "floor opening near {area} had no protective cover",
            "ladder was damaged and unsecured during overhead work",
            "guardrail was missing from the elevated {area}",
            "materials were stacked near an unprotected platform edge",
            "scaffold inspection tag was missing before access"
        ],
        MODEL_CATEGORIES[2]: [
            "chemical vapour was detected near the {equipment} valve",
            "solvent leak was observed below the {equipment} flange",
            "gas detector alarm activated in the {area}",
            "corrosion was found on the chemical transfer hose",
            "unknown liquid was leaking from a chemical container",
            "chlorine odour was reported near the storage manifold",
            "ventilation failed in the chemical handling room"
        ],
        MODEL_CATEGORIES[3]: [
            "damaged insulation exposed wires on the {equipment} cable",
            "electrical panel had exposed terminals near {area}",
            "extension cable was lying in water beside the {equipment}",
            "ground wire was disconnected from the welding machine",
            "burn marks were visible around the distribution board",
            "circuit breaker cover was missing in the utility room",
            "temporary power cable had exposed copper strands"
        ],
        MODEL_CATEGORIES[4]: [
            "routine shift handover was completed without abnormal findings",
            "work area was clean and walkways were unobstructed",
            "scheduled equipment inspection found no issues",
            "toolbox talk was completed before the shift started",
            "fire extinguishers were inspected and tags were current",
            "personal protective equipment stock was replenished",
            "operating readings remained within normal limits"
        ]
    }
    machines = ["press machine", "conveyor", "pump", "compressor", "forklift"]
    tasks = ["cleaning", "maintenance", "production", "troubleshooting"]
    areas = ["sector 4", "loading bay", "workshop", "tank farm", "assembly line"]
    equipment = ["pump", "welding unit", "control panel", "transfer line", "motor"]
    texts, labels = [], []
    for cat, patterns in templates.items():
        for _ in range(350):
            pattern = str(rng.choice(patterns))
            texts.append(pattern.format(machine=rng.choice(machines), task=rng.choice(tasks),
                                        area=rng.choice(areas), equipment=rng.choice(equipment)))
            labels.append(cat)
    X_train, X_test, y_train, y_test = train_test_split(
        texts, labels, test_size=.25, random_state=42, stratify=labels
    )
    pipe = Pipeline([
        ("tfidf", TfidfVectorizer(ngram_range=(1,2), min_df=2, max_features=6000, sublinear_tf=True)),
        ("clf", LogisticRegression(max_iter=1200, class_weight="balanced"))
    ])
    pipe.fit(X_train, y_train)
    pred = pipe.predict(X_test)
    return pipe, X_test, y_test, pred

model, X_test, y_test, y_pred = train_classifier()

# --------------------------- INTELLIGENCE ---------------------------
def assess_risk(category, text):
    t = text.lower()
    if category == MODEL_CATEGORIES[4]:
        score = 10
    else:
        score = 38
    severe_terms = ["exposed", "gas detector alarm", "chlorine", "fall", "unprotected",
                    "electric shock", "fire", "explosion", "bypass", "without harness",
                    "moving equipment", "leak", "confined space"]
    if any(term in t for term in severe_terms):
        score += 32
    if any(term in t for term in ["near miss", "injury", "alarm", "failed", "damaged", "missing"]):
        score += 15
    score = min(score, 100)
    level = "Low" if score < 35 else "Medium" if score < 65 else "High"
    return score, level

def recommended_action(category):
    actions = {
        MODEL_CATEGORIES[0]: "Stop unsafe operation; isolate equipment; apply lockout/tagout; verify guards and permits before restart.",
        MODEL_CATEGORIES[1]: "Restrict access; install edge protection; inspect scaffold/ladder; verify fall-arrest equipment before work.",
        MODEL_CATEGORIES[2]: "Isolate the source if safe; follow site emergency procedure; use trained responders and verify atmospheric conditions.",
        MODEL_CATEGORIES[3]: "Keep personnel clear; isolate electrical supply through authorized staff; repair and test before reuse.",
        MODEL_CATEGORIES[4]: "Record the observation and continue routine monitoring."
    }
    return actions[category]

def get_alerts(df):
    alerts = []
    if df.empty:
        return alerts
    nonroutine = df[df["category"] != MODEL_CATEGORIES[4]]
    for site, group in nonroutine.groupby("site"):
        recent = group[pd.to_datetime(group["report_date"], errors="coerce") >= (pd.Timestamp.today().normalize()-pd.Timedelta(days=30))]
        high = int((recent["risk_level"] == "High").sum())
        total = len(recent)
        if high >= 3:
            alerts.append({"site": site, "level": "High", "count": high,
                           "message": f"{high} high-risk observations in the last 30 days."})
        elif total >= 5:
            alerts.append({"site": site, "level": "Medium", "count": total,
                           "message": f"{total} hazard reports in the last 30 days; review recurring patterns."})
    return alerts

def safe_date_series(df):
    out = df.copy()
    out["report_date"] = pd.to_datetime(out["report_date"], errors="coerce")
    return out.dropna(subset=["report_date"])


# --------------------------- NLP CHATBOT INTELLIGENCE ---------------------------
# The chatbot combines the existing TF-IDF report classifier with intent matching,
# hazard-specific guidance and live SQLite-backed answers. It is not a substitute
# for the site's emergency plan or a qualified HSE professional.

HAZARD_KNOWLEDGE = {
    "electrical": {
        "terms": ["exposed wire", "exposed wires", "exposed cable", "electrical wire", "electric shock",
                  "electrical panel", "live wire", "sparking", "burning smell", "tingling sensation"],
        "title": "Electrical hazard",
        "category": MODEL_CATEGORIES[3],
        "risk": "Potentially high",
        "why": "Contact with live parts, damaged insulation, moisture or arcing can cause electric shock, burns or fire.",
        "now": ["Keep people away and do not touch the wire, panel or affected equipment.",
                "Warn nearby workers and notify the site control room / authorized electrical team.",
                "Only an authorized person should isolate the supply using the approved site procedure.",
                "Do not restart or use the equipment until it has been inspected and declared safe."],
        "prevent": "Use inspected cables, suitable protection, proper earthing, barriers and authorized electrical work permits."
    },
    "chemical": {
        "terms": ["chemical leak", "chemical leakage", "solvent leak", "acid leak", "chemical smell",
                  "vapour", "vapor", "chlorine", "unknown liquid", "chemical spill", "drum leaking"],
        "title": "Chemical release or spill",
        "category": MODEL_CATEGORIES[2],
        "risk": "Potentially high; substance and quantity are unknown",
        "why": "A release may expose workers to toxic, corrosive, flammable or oxygen-displacing substances.",
        "now": ["Do not touch, smell closely or attempt an untrained cleanup.",
                "Move away, warn others and follow the site's chemical-spill / emergency procedure.",
                "Notify the control room and trained spill-response team; share the container label if it can be read safely.",
                "Use the site's evacuation or isolation instructions if an alarm is raised."],
        "prevent": "Maintain labelled, compatible containers; inspect hoses and connections; keep safety data sheets accessible."
    },
    "gas": {
        "terms": ["gas leak", "gas alarm", "gas detector", "gas smell", "gas cylinder", "flammable gas"],
        "title": "Possible gas release",
        "category": MODEL_CATEGORIES[2],
        "risk": "Potentially high / emergency",
        "why": "Some gases are toxic, flammable or can displace oxygen. Smell alone cannot establish whether an area is safe.",
        "now": ["Move away immediately and warn nearby personnel.",
                "Do not operate switches, start vehicles or create ignition sources in the suspected area.",
                "Raise the alarm and follow the site's gas-release / evacuation procedure.",
                "Let trained responders assess the atmosphere with approved equipment."],
        "prevent": "Keep gas detection, ventilation, alarms and inspection routines maintained under site procedures."
    },
    "working_at_height": {
        "terms": ["working at height", "working at heights", "scaffold", "scaffolding", "ladder",
                  "harness", "fall arrest", "guardrail", "floor opening", "roof edge", "toe board"],
        "title": "Fall / working-at-height hazard",
        "category": MODEL_CATEGORIES[1],
        "risk": "Potentially high",
        "why": "An unsecured ladder, incomplete scaffold, open edge or disconnected fall-arrest system can result in a serious fall.",
        "now": ["Stop the affected work and keep people away from the unprotected edge or access equipment.",
                "Notify the supervisor and competent person responsible for work at height.",
                "Do not use the ladder or scaffold until it has been inspected and released for use.",
                "Confirm approved access, edge protection and fall-protection arrangements before restarting."],
        "prevent": "Use inspected access equipment, suitable edge protection, permits and a task-specific fall-prevention plan."
    },
    "machine": {
        "terms": ["machine guard", "safety guard", "interlock", "moving machine", "moving equipment",
                  "conveyor", "press machine", "machine jam", "emergency stop", "bypass guard"],
        "title": "Machinery / guarding hazard",
        "category": MODEL_CATEGORIES[0],
        "risk": "Potentially high",
        "why": "Moving parts and defeated guards or interlocks can cause entanglement, crushing or amputation injuries.",
        "now": ["Keep clear of the danger zone and do not reach into moving equipment.",
                "Stop the task and notify the supervisor / maintenance team.",
                "Use the approved isolation and lockout/tagout process before inspection or jam clearing.",
                "Do not bypass guards or restart until the guard and safety functions are verified by authorized staff."],
        "prevent": "Inspect guards and interlocks, follow lockout/tagout, and train operators on safe jam-clearing procedures."
    },
    "forklift": {
        "terms": ["forklift", "fork lift", "vehicle near miss", "pedestrian near miss", "reversing vehicle",
                  "speeding forklift", "loading bay vehicle"],
        "title": "Vehicle / forklift interaction",
        "category": MODEL_CATEGORIES[0],
        "risk": "Potentially high",
        "why": "A vehicle-pedestrian conflict can cause crushing injuries, especially at blind corners and loading areas.",
        "now": ["Move to a safe location and keep clear of the vehicle route.",
                "Report the event or unsafe driving to the supervisor immediately.",
                "Preserve details such as time, location, vehicle ID and pedestrian route without entering the hazard area.",
                "Ask the site team to review traffic separation, visibility and vehicle controls."],
        "prevent": "Separate pedestrian and vehicle routes, enforce speed limits, use trained operators and maintain visibility controls."
    },
    "slip_trip": {
        "terms": ["slipped", "slip", "trip", "wet floor", "oil on floor", "oil spill", "blocked walkway",
                  "tripping hazard", "uneven floor"],
        "title": "Slip, trip or housekeeping hazard",
        "category": MODEL_CATEGORIES[4],
        "risk": "Depends on the substance, location and exposure",
        "why": "Wet or contaminated floors, loose cables and blocked walkways can cause falls and may create secondary hazards.",
        "now": ["Warn others and prevent access to the affected area if this can be done safely.",
                "Report the condition and arrange cleanup by personnel trained for the material involved.",
                "Do not clean an unknown chemical or oil spill without the correct procedure and equipment.",
                "If anyone fell or was hurt, follow the site's incident and first-aid reporting process."],
        "prevent": "Use prompt housekeeping, spill controls, cable management and routine walkway inspections."
    },
    "fire": {
        "terms": ["fire", "smoke", "flames", "burning smell", "sparks", "overheating motor", "overheated motor"],
        "title": "Fire / overheating warning",
        "category": MODEL_CATEGORIES[0],
        "risk": "Potentially high / emergency",
        "why": "Smoke, flames, abnormal heat or sparking may indicate ignition, electrical failure or equipment malfunction.",
        "now": ["Raise the alarm and follow the site's fire emergency and evacuation procedure.",
                "Move away and keep access routes clear.",
                "Do not investigate or attempt firefighting unless trained, authorized and it is safe under site rules.",
                "Notify the control room and emergency response team."],
        "prevent": "Maintain equipment, control ignition sources, keep fire routes clear and complete required inspections."
    },
    "confined_space": {
        "terms": ["confined space", "tank entry", "vessel entry", "manhole entry", "oxygen level",
                  "low oxygen", "confined space permit"],
        "title": "Confined-space concern",
        "category": MODEL_CATEGORIES[0],
        "risk": "Potentially high / emergency",
        "why": "A confined space may contain a hazardous atmosphere or other life-threatening conditions that cannot be judged by sight or smell.",
        "now": ["Do not enter or attempt an unplanned rescue.",
                "Raise the alarm and contact the site's trained confined-space rescue team.",
                "Keep others away and follow the permit and emergency procedure.",
                "Entry must only occur under the site's authorized controls and atmospheric testing requirements."],
        "prevent": "Use an approved permit, isolation, atmospheric testing, standby person and rescue arrangements."
    },
    "ppe": {
        "terms": ["helmet", "hard hat", "safety shoes", "safety shoe", "gloves", "goggles", "face shield",
                  "ear protection", "respirator", "not wearing ppe", "without ppe"],
        "title": "Personal protective equipment (PPE)",
        "category": MODEL_CATEGORIES[0],
        "risk": "Task-dependent",
        "why": "Missing or unsuitable PPE can increase exposure to impact, chemicals, noise, dust, heat or other task hazards.",
        "now": ["Pause the task if required PPE is missing or unsuitable.",
                "Ask the supervisor to confirm the task-specific PPE requirements.",
                "Use only approved, correctly fitted and inspected PPE.",
                "Do not treat PPE as a replacement for eliminating or controlling the hazard."],
        "prevent": "Use the site's task risk assessment and PPE matrix; inspect, maintain and replace damaged PPE."
    },
    "lifting": {
        "terms": ["crane", "lifting operation", "suspended load", "load fell", "rigging", "sling",
                  "lifting gear", "overloaded", "load swinging"],
        "title": "Lifting operation hazard",
        "category": MODEL_CATEGORIES[0],
        "risk": "Potentially high",
        "why": "A dropped or swinging load, unsuitable lifting gear or people under a suspended load can cause severe injury.",
        "now": ["Keep out of the lifting zone and never stand beneath a suspended load.",
                "Stop and report an unsafe lift to the lift supervisor.",
                "Do not handle damaged lifting gear; have it checked by a competent person.",
                "Resume only after the lift plan, load, equipment and exclusion zone are verified."],
        "prevent": "Use approved lift plans, inspected gear, competent operators and clearly controlled exclusion zones."
    },
    "noise": {
        "terms": ["loud noise", "excessive noise", "hearing protection", "noise level", "hearing loss"],
        "title": "Noise exposure",
        "category": MODEL_CATEGORIES[4],
        "risk": "Depends on measured exposure and duration",
        "why": "Repeated or high noise exposure can damage hearing and may interfere with warning signals.",
        "now": ["Report unusually high or changing noise to the supervisor.",
                "Keep clear of equipment if the noise suggests a developing mechanical fault.",
                "Use the hearing protection specified by the site's assessment.",
                "Request an authorized noise assessment where required."],
        "prevent": "Maintain equipment, use engineering noise controls and follow the site's hearing-conservation programme."
    },
    "ergonomic": {
        "terms": ["manual handling", "heavy lifting", "back pain", "awkward posture", "repetitive work",
                  "lifting heavy", "muscle strain"],
        "title": "Manual handling / ergonomic concern",
        "category": MODEL_CATEGORIES[4],
        "risk": "Task-dependent",
        "why": "Repeated, awkward or heavy handling can contribute to strains and musculoskeletal injuries.",
        "now": ["Pause and report the task if it cannot be performed safely.",
                "Use available mechanical aids or team-lifting arrangements approved by the site.",
                "Ask the supervisor to review the load, route and working posture.",
                "Report pain or injury through the site's occupational health process."],
        "prevent": "Reduce load weight, improve workstation layout and use suitable handling aids and task rotation."
    },
    "near_miss": {
        "terms": ["near miss", "almost hit", "almost fell", "nobody injured", "no one injured",
                  "missed me", "just missed", "nearly struck", "fell but no injury"],
        "title": "Near miss",
        "category": MODEL_CATEGORIES[0],
        "risk": "Needs review based on the credible potential consequence",
        "why": "A near miss is an unplanned event that did not cause injury or damage this time but could have done so.",
        "now": ["Report it even if nobody was injured.",
                "Record what happened, where and when, and what could have been struck or harmed.",
                "Preserve relevant details and notify the supervisor.",
                "Ask the site team to identify causes and corrective actions before a repeat event."],
        "prevent": "Investigate contributing factors and track corrective actions to completion."
    }
}

SAFETY_EXAMPLES = [
    "report an unsafe condition at the plant", "classify this safety observation",
    "there is a chemical leak near the pump", "worker not wearing helmet",
    "forklift almost hit a pedestrian", "exposed electrical wire in workshop",
    "how many incidents happened this month", "show repeated hazards at site A",
    "what should I do during a gas leak", "explain lockout tagout",
    "show previous reports for conveyor", "are near misses increasing",
    "machine guard was removed", "scaffold has a loose plank",
    "oil spilled on the floor", "motor is overheating and smoking",
    "someone slipped but was not injured", "what PPE is required",
    "report a safety issue", "show high risk reports", "which department has most reports",
    "what are the safety risks of working at height", "how to report an incident",
    "blocked emergency exit", "chemical container is leaking", "confined space entry concern",
    "crane load is swinging", "excessive noise in the workshop", "heavy manual lifting concern"
]
@st.cache_resource
def build_chat_relevance_model():
    vec = TfidfVectorizer(ngram_range=(1, 2), stop_words="english", sublinear_tf=True)
    matrix = vec.fit_transform(SAFETY_EXAMPLES)
    return vec, matrix

chat_vectorizer, chat_example_matrix = build_chat_relevance_model()

SAFETY_DOMAIN_TERMS = {
    term for item in HAZARD_KNOWLEDGE.values() for term in item["terms"]
}
SAFETY_DOMAIN_TERMS.update({
    "safety", "hazard", "incident", "accident", "risk", "unsafe", "injury", "injured",
    "machine", "equipment", "maintenance", "near miss", "precursor", "hse", "ppe",
    "procedure", "inspection", "fire", "emergency", "permit", "audit",
    "corrective action", "trend"
})

def normalize_text(text):
    return re.sub(r"[^a-z0-9\s/-]", " ", str(text).lower()).strip()

def detect_hazard_case(text):
    t = normalize_text(text)
    # Specific cases first to avoid generic terms masking a more useful answer.
    priority = ["gas", "chemical", "electrical", "confined_space", "working_at_height",
                "forklift", "machine", "fire", "lifting", "near_miss", "slip_trip",
                "ppe", "noise", "ergonomic"]
    for key in priority:
        item = HAZARD_KNOWLEDGE[key]
        if any(term in t for term in item["terms"]):
            return key, item
    return None, None

def is_safety_related(text):
    t = normalize_text(text)
    if not t or len(t.split()) < 2:
        return False, 0.0
    # Direct domain terms permit short, natural worker descriptions.
    if any(term in t for term in SAFETY_DOMAIN_TERMS):
        return True, 1.0
    # Permit narrowly scoped database questions without requiring a hazard keyword.
    if re.search(r"\\b(how many|count|number of|total)\\b", t) and re.search(r"\\breports?\\b", t):
        return True, 1.0
    if re.search(r"\\b(which site|which department|most reports|highest number)\\b", t) and "report" in t:
        return True, 1.0
    try:
        query_vec = chat_vectorizer.transform([t])
        similarity = float((query_vec @ chat_example_matrix.T).toarray().max())
        return similarity >= 0.075, similarity
    except Exception:
        return False, 0.0

def classify_safety_text(text):
    probabilities = model.predict_proba([text])[0]
    order = np.argsort(probabilities)[::-1]
    return model.classes_[order[0]], float(probabilities[order[0]]), {
        model.classes_[i]: float(probabilities[i]) for i in order
    }

def period_filter(frame, text):
    if frame.empty:
        return frame
    now = pd.Timestamp.today().normalize()
    t = normalize_text(text)
    dates = pd.to_datetime(frame["report_date"], errors="coerce")
    if "today" in t:
        return frame[dates.dt.date == now.date()]
    if "this week" in t or "last 7 days" in t:
        return frame[dates >= now - pd.Timedelta(days=7)]
    if "last month" in t:
        start = (now - pd.offsets.MonthBegin(1)).normalize()
        end = now - pd.Timedelta(days=1)
        return frame[(dates >= start) & (dates <= end)]
    if "this month" in t or "month" in t:
        return frame[(dates.dt.year == now.year) & (dates.dt.month == now.month)]
    if "last 30 days" in t:
        return frame[dates >= now - pd.Timedelta(days=30)]
    return frame

def legacy_chatbot_answer(user_text, reports_df):
    raw = str(user_text).strip()
    t = normalize_text(raw)
    relevant, relevance = is_safety_related(raw)
    if not relevant:
        return ("I’m the HSE Safety Assistant, so I can only help with workplace safety, hazards, incident reports, "
                "near misses, risk screening and safety trends. I can’t help with that unrelated topic.\\n\\n"
                "Try asking: **“What should I do if I find exposed electrical wires?”** or "
                "**“How many near misses were reported this month?”**", None)

    # Database-backed questions: always calculate from the saved records.
    data = reports_df.copy()
    filtered = period_filter(data, raw)
    if any(x in t for x in ["how many", "count", "number of", "total reports", "how much"]):
        if "high risk" in t or "high-risk" in t:
            subset = filtered[filtered["risk_level"] == "High"]
            label = "high-risk reports"
        elif "near miss" in t:
            subset = filtered[filtered["report_text"].str.contains("near miss|almost|nearly", case=False, regex=True, na=False)]
            label = "near-miss-related reports"
        else:
            key, hazard = detect_hazard_case(raw)
            if key and hazard:
                subset = filtered[filtered["category"] == hazard["category"]]
                label = f"{hazard['title'].lower()} category reports"
            else:
                subset = filtered
                label = "saved reports"
        site_match = next((site for site in SITES if site.lower() in t), None)
        if site_match:
            subset = subset[subset["site"] == site_match]
        return (f"**Record lookup: {label}**\\n\\nI found **{len(subset)}** matching {label} "
                f"{'at ' + site_match if site_match else ''} in the selected time period. "
                f"This number is calculated from the reports currently stored in this prototype database. "
                f"{'The database contains synthetic demo records as well as any reports you submit.' if 'Synthetic demonstration data' in data.get('source', pd.Series(dtype=str)).values else ''}", None)

    if any(x in t for x in ["trend", "increasing", "decreasing", "recurring", "repeated", "most common", "top hazard"]):
        if filtered.empty:
            return ("There are no saved reports in that time period to compare. Submit reports or choose a wider period.", None)
        counts = filtered[filtered["category"] != MODEL_CATEGORIES[4]]["category"].value_counts()
        if counts.empty:
            return ("I found no hazard-category reports in that period. The available records are routine observations.", None)
        top = counts.head(3)
        lines = [f"- **{cat}:** {int(n)} reports" for cat, n in top.items()]
        return ("**Recurring hazard pattern from saved records**\\n\\n" + "\\n".join(lines) +
                "\\n\\nThese are reporting patterns, not proof that an accident will occur. Review the underlying reports, site conditions and corrective-action status with the HSE team.", None)

    if any(x in t for x in ["which site", "which area", "which department", "most reports", "highest number"]):
        if filtered.empty:
            return ("No records are available for that comparison yet.", None)
        group_col = "department" if "department" in t else "site"
        counts = filtered.groupby(group_col).size().sort_values(ascending=False)
        best = counts.index[0]
        return (f"**{group_col.title()} comparison**\\n\\n**{best}** has the most saved reports in this period (**{int(counts.iloc[0])}**). "
                "This reflects reporting volume, not necessarily the true level of danger; reporting rates and exposure should also be considered.", None)

    if any(x in t for x in ["previous report", "history", "similar report", "show reports", "last incident", "past incident"]):
        key, hazard = detect_hazard_case(raw)
        subset = filtered
        if key and hazard:
            subset = subset[subset["category"] == hazard["category"]]
        if subset.empty:
            return ("I couldn't find matching historical reports in the current database. You can submit a new observation using the report form below.", None)
        rows = subset.sort_values("report_date", ascending=False).head(5)
        lines = [f"- **{r.report_code}** · {r.report_date} · {r.site} · {r.category}: {str(r.report_text)[:150]}" for r in rows.itertuples()]
        return ("**Matching saved reports**\\n\\n" + "\\n".join(lines) +
                "\\n\\nOnly records currently stored in this prototype are shown.", None)

    key, hazard = detect_hazard_case(raw)
    if key and hazard:
        category, confidence, probs = classify_safety_text(raw)
        response = (f"**{hazard['title']} identified**\\n\\n"
                    f"**Likely report category:** {hazard['category']}\\n"
                    f"**Screening priority:** {hazard['risk']}\\n\\n"
                    f"**Why it matters:** {hazard['why']}\\n\\n"
                    "**What to do now**\\n" + "\\n".join([f"{i+1}. {x}" for i, x in enumerate(hazard["now"])]) +
                    f"\\n\\n**Prevention:** {hazard['prevent']}\\n\\n"
                    f"**NLP classification:** {category} (model confidence {confidence:.0%}). "
                    "The category is a model estimate; it is not a measured probability of injury. "
                    "Follow your site's approved procedures and contact the supervisor / HSE team.")
        return response, {"hazard_key": key, "category": hazard["category"], "risk": hazard["risk"]}

    if any(x in t for x in ["what is", "meaning", "define", "explain", "how to report", "report a"]):
        if "near miss" in t:
            return ("A **near miss** is an unplanned event that caused no injury or damage this time but had the potential to do so. "
                    "It should still be reported so the causes can be reviewed and recurrence prevented.", None)
        if "lockout" in t or "tagout" in t or "loto" in t:
            return ("**Lockout/Tagout (LOTO)** is a controlled process used to isolate hazardous energy and prevent equipment from being unexpectedly energized during work. "
                    "Only trained and authorized personnel should apply the site's approved LOTO procedure.", None)
        if "unsafe act" in t:
            return ("An **unsafe act** is a person's action or failure to follow a required safe method that could expose someone to harm, such as bypassing a machine guard. "
                    "Report the condition factually and avoid blaming language.", None)
        if "unsafe condition" in t:
            return ("An **unsafe condition** is a hazardous workplace state, such as exposed wiring, a leaking chemical line or an unprotected floor opening. "
                    "Record its location, time and immediate controls.", None)

    category, confidence, probs = classify_safety_text(raw)
    if confidence < 0.34:
        return ("I understand this is related to workplace safety, but I don't have enough context to classify it reliably. "
                "Please describe **what happened, where it happened, and whether anyone was exposed or injured**. "
                "For example: “Oil is leaking from the pump flange in the loading area.”", None)
    score, level = assess_risk(category, raw)
    return (f"**Safety observation analysis**\\n\\n"
            f"- **Predicted category:** {category}\\n"
            f"- **Screening level:** {level}\\n"
            f"- **Screening score:** {score}/100\\n"
            f"- **Model confidence:** {confidence:.0%}\\n\\n"
            f"**Suggested next step:** {recommended_action(category)}\\n\\n"
            "This is an initial text-based screening only. A competent site representative must verify the hazard and decide the actual controls.", None)

def chatbot_answer(user_text, reports_df):
    """Route incident language through the hybrid assistant; retain DB analytics."""
    raw = str(user_text).strip()
    normalized = normalize_text(raw)
    state = st.session_state.get("spi_conversation_state")
    pending = getattr(state, "pending_intent", None)
    analytics_question = any(term in normalized for term in [
        "how many", "count", "number of", "total reports", "which site",
        "which department", "most reports", "highest number", "trend", "reports this",
        "repeated hazard", "repeated electrical", "repeatedly reported", "several workers", "same area", "appearing in the reports", "recurring", "saved reports", "report history",
        "recorded this month", "most common"
    ])
    # Explicit questions about saved-report counts, sites or recurring trends must
    # query the report database first, even when the wording contains a hazard term.
    if analytics_question:
        return legacy_chatbot_answer(raw, reports_df)
    if detect_hybrid_hazard(raw) or pending in {"electric_shock", "fatigue", "unconsciousness", "fire", "gas_release", "chemical_spill"}:
        result = answer_in_session(raw, st.session_state, use_generation=True)
        return result.text, {"hazard_key": result.hazard.key if result.hazard else None,
                             "category": result.hazard.category if result.hazard else None,
                             "risk": result.hazard.severity if result.hazard else None,
                             "assistant_source": result.source}
    return legacy_chatbot_answer(raw, reports_df)


def save_chat_report(report_text, site, department, equipment):
    category, confidence, _ = classify_safety_text(report_text)
    score, level = assess_risk(category, report_text)
    code = f"CHAT-{datetime.now().strftime('%y%m%d%H%M%S%f')}"
    row = {
        "report_code": code, "report_date": date.today().isoformat(), "site": site,
        "department": department, "shift": "Not specified", "equipment": equipment or "Not specified",
        "report_text": report_text.strip(), "category": category, "risk_level": level,
        "risk_score": score, "model_confidence": confidence, "status": "Open",
        "corrective_action": recommended_action(category), "source": "Chatbot submitted",
        "is_incident": 0
    }
    save_report(row)
    return code, row


# --------------------------- SIDEBAR ---------------------------
st.sidebar.title("🛡️ HSE Intelligence")
st.sidebar.caption("Safety Precursor Detection System")
st.sidebar.markdown("<div class='sidebar-kicker'>WORKPLACE SAFETY CONSOLE</div>", unsafe_allow_html=True)
ui_theme = st.sidebar.radio("Appearance", ["Light", "Dark"], horizontal=True, key="ui_theme")
page = st.sidebar.radio("Navigation", [
    "Executive Dashboard", "AI Report Analyzer", "AI Safety Chatbot", "Precursor Intelligence",
    "Site Risk Monitor", "Audit & Corrective Actions", "Model Evaluation"
])
st.sidebar.divider()
st.sidebar.caption("Data mode")
st.sidebar.info("Synthetic demonstration records are clearly labelled. Add verified site data for operational validation.")

# Consistent typography and component colors in both appearance modes.
if ui_theme == "Dark":
    palette = {
        "bg": "#0b1220", "panel": "#111c2e", "panel2": "#17243a", "text": "#e8eef8",
        "muted": "#a5b4c8", "border": "#29384f", "accent": "#5ba8ff", "accent_hover": "#83bdff",
        "input": "#101a2b", "sidebar": "#0e192a", "shadow": "rgba(0,0,0,.24)"
    }
else:
    palette = {
        "bg": "#f4f7fb", "panel": "#ffffff", "panel2": "#edf3fa", "text": "#172338",
        "muted": "#61718a", "border": "#dce5f0", "accent": "#1769d2", "accent_hover": "#0e55b5",
        "input": "#ffffff", "sidebar": "#eaf0f7", "shadow": "rgba(24,45,78,.07)"
    }

# Keep Plotly charts readable when the user switches appearance.
px.defaults.template = "plotly_dark" if ui_theme == "Dark" else "plotly_white"

st.markdown(f"""
<style>
:root {{ color-scheme: {'dark' if ui_theme == 'Dark' else 'light'}; }}
html, body, [data-testid="stAppViewContainer"], .stApp {{
  background: {palette['bg']} !important; color: {palette['text']} !important;
  font-family: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif !important;
}}
.block-container {{max-width: 1500px; padding-top: 1.25rem; padding-bottom: 2.4rem;}}
[data-testid="stHeader"] {{background: transparent;}}
[data-testid="stSidebar"] {{background: {palette['sidebar']} !important; border-right: 1px solid {palette['border']};}}
[data-testid="stSidebar"] * {{font-family: Inter, ui-sans-serif, system-ui, "Segoe UI", sans-serif;}}
[data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p,
[data-testid="stSidebar"] label {{color: {palette['text']} !important;}}
[data-testid="stSidebar"] [data-testid="stRadio"] label {{font-weight: 600;}}
h1, h2, h3, h4, h5, h6, p, li, label, [data-testid="stMarkdownContainer"] {{color: {palette['text']};}}
h1 {{font-weight: 800 !important; letter-spacing: -0.035em;}}
h2, h3 {{font-weight: 750 !important; letter-spacing: -0.02em;}}
[data-testid="stCaptionContainer"], .small-muted {{color: {palette['muted']} !important;}}
[data-testid="stMetric"] {{background: {palette['panel']} !important; border: 1px solid {palette['border']} !important;
  padding: 15px 17px !important; border-radius: 16px !important; box-shadow: 0 5px 18px {palette['shadow']};}}
[data-testid="stMetricLabel"] p {{color: {palette['muted']} !important; font-weight: 650;}}
[data-testid="stMetricValue"] {{color: {palette['text']} !important; font-weight: 800;}}
[data-testid="stMetricDelta"] {{font-weight: 650;}}
[data-testid="stTextInput"] input, [data-testid="stTextArea"] textarea,
[data-testid="stNumberInput"] input, [data-testid="stDateInput"] input,
[data-testid="stSelectbox"] div[data-baseweb="select"] > div,
[data-testid="stMultiSelect"] div[data-baseweb="select"] > div {{
  background: {palette['input']} !important; color: {palette['text']} !important;
  border-color: {palette['border']} !important; border-radius: 10px !important;
}}
input, textarea {{color: {palette['text']} !important;}}
[data-testid="stDataFrame"], [data-testid="stTable"] {{border: 1px solid {palette['border']}; border-radius: 12px; overflow: hidden;}}
div.stButton > button, div.stDownloadButton > button, button[kind="primary"] {{
  border-radius: 11px !important; font-weight: 700 !important; padding: .55rem 1rem !important;
  transition: transform .16s ease, box-shadow .16s ease, background .16s ease !important;
}}
div.stButton > button:hover, div.stDownloadButton > button:hover {{transform: translateY(-2px); box-shadow: 0 7px 18px {palette['shadow']};}}
[data-testid="stForm"] {{background: {palette['panel']}; border: 1px solid {palette['border']}; padding: 18px; border-radius: 16px;}}
hr {{border-color: {palette['border']} !important;}}
.sidebar-kicker {{font-size:.67rem; letter-spacing:.14em; font-weight:800; color:{palette['muted']}; margin:.3rem 0 .8rem;}}
.livebar {{display:flex; align-items:center; justify-content:space-between; gap:12px; padding:11px 15px; margin:0 0 1.2rem;
  background:linear-gradient(105deg, {palette['panel']}, {palette['panel2']}); border:1px solid {palette['border']};
  border-radius:14px; box-shadow:0 5px 20px {palette['shadow']};}}
.live-left {{display:flex; align-items:center; gap:10px; font-weight:750; color:{palette['text']};}}
.live-dot {{width:9px; height:9px; border-radius:50%; background:#22c55e; box-shadow:0 0 0 0 rgba(34,197,94,.55); animation:pulse 1.8s infinite;}}
.live-meta {{font-size:.78rem; color:{palette['muted']}; font-weight:600;}}
@keyframes pulse {{0% {{box-shadow:0 0 0 0 rgba(34,197,94,.5)}} 70% {{box-shadow:0 0 0 8px rgba(34,197,94,0)}} 100% {{box-shadow:0 0 0 0 rgba(34,197,94,0)}}}}
@media (prefers-reduced-motion: reduce) {{*, *::before, *::after {{animation-duration:.01ms !important; transition-duration:.01ms !important;}}}}
</style>
""", unsafe_allow_html=True)

# Shared design tokens keep spacing, surfaces, typography and chat bubbles consistent.
st.markdown(spi_theme_css(ui_theme), unsafe_allow_html=True)

df = read_reports()
if not df.empty:
    df_dates = safe_date_series(df)
else:
    df_dates = df

live_col, refresh_col = st.columns([5, 1])
with live_col:
    st.markdown(
        f"<div class='livebar'><div class='live-left'><span class='live-dot'></span> LIVE SAFETY MONITORING <span class='live-meta'>• {len(df):,} records loaded</span></div><div class='live-meta'>Last refreshed {datetime.now().strftime('%d %b %Y · %H:%M:%S')}</div></div>",
        unsafe_allow_html=True
    )
with refresh_col:
    if st.button("↻ Refresh", use_container_width=True, help="Reload the latest saved safety reports"):
        st.rerun()

# --------------------------- DASHBOARD ---------------------------
if page == "Executive Dashboard":
    st.title("🛡️ Safety Precursor Intelligence")
    st.caption("HSE overview | Report-driven operational risk monitoring")
    total = len(df)
    high = int((df["risk_level"] == "High").sum()) if total else 0
    open_count = int((df["status"] != "Closed").sum()) if total else 0
    sites = int(df["site"].nunique()) if total else 0
    c1,c2,c3,c4 = st.columns(4)
    c1.metric("Total reports", f"{total:,}")
    c2.metric("High-risk reports", f"{high:,}")
    c3.metric("Open actions / reports", f"{open_count:,}")
    c4.metric("Sites represented", sites)
    st.divider()
    left,right = st.columns([1.3,1])
    with left:
        st.subheader("Report volume over time")
        if not df_dates.empty:
            daily = df_dates.groupby(df_dates["report_date"].dt.date).size().reset_index(name="Reports")
            st.line_chart(daily.set_index("report_date"))
        else:
            st.info("No dated reports available.")
    with right:
        st.subheader("Hazard category distribution")
        if total:
            cat_counts = df["category"].value_counts().reset_index()
            cat_counts.columns = ["Category","Reports"]
            fig = px.pie(cat_counts, names="Category", values="Reports", hole=.45)
            st.plotly_chart(fig, use_container_width=True)
    st.subheader("Latest high-priority observations")
    latest = df[df["risk_level"] == "High"].head(8)
    if latest.empty:
        st.success("No high-risk reports currently recorded.")
    else:
        st.dataframe(latest[["report_code","report_date","site","category","risk_score","status","report_text"]], use_container_width=True, hide_index=True)
    st.caption("Dashboard values are calculated from records stored in the local SQLite database.")

# --------------------------- ANALYZER ---------------------------
elif page == "AI Report Analyzer":
    st.title("📝 AI Safety Report Analyzer")
    st.write("Submit a field observation. The NLP model classifies the text; the risk engine provides a separate rule-based screening score.")
    with st.form("report_form", clear_on_submit=False):
        col1,col2,col3 = st.columns(3)
        site = col1.selectbox("Site", SITES)
        dept = col2.selectbox("Department", DEPARTMENTS)
        shift = col3.selectbox("Shift", ["Day","Evening","Night"])
        col4,col5 = st.columns(2)
        report_date = col4.date_input("Observation date", value=date.today())
        equipment = col5.text_input("Equipment / area", "Conveyor")
        report_text = st.text_area("Field report", height=140,
            placeholder="Example: Worker noticed damaged insulation on a temporary cable near the pump...")
        submitted = st.form_submit_button("Analyze and save report", type="primary", use_container_width=True)
    if submitted:
        if len(report_text.strip()) < 12:
            st.error("Please enter a meaningful report (at least 12 characters).")
        else:
            probabilities = model.predict_proba([report_text])[0]
            order = np.argsort(probabilities)[::-1]
            category = model.classes_[order[0]]
            confidence = float(probabilities[order[0]])
            score, level = assess_risk(category, report_text)
            action = recommended_action(category)
            code = f"HSE-{datetime.now().strftime('%y%m%d%H%M%S')}"
            row = {
                "report_code": code, "report_date": report_date.isoformat(), "site": site,
                "department": dept, "shift": shift, "equipment": equipment,
                "report_text": report_text.strip(), "category": category,
                "risk_level": level, "risk_score": score, "model_confidence": confidence,
                "status": "Open", "corrective_action": action, "source": "User submitted",
                "is_incident": 0
            }
            try:
                save_report(row)
                st.session_state["last_analysis"] = row
                st.success(f"Report {code} analyzed and saved successfully.")
            except sqlite3.IntegrityError:
                st.error("Could not save this report because its report ID already exists. Please submit again.")
    if "last_analysis" in st.session_state:
        r = st.session_state["last_analysis"]
        st.divider()
        st.subheader("Analysis result")
        a,b,c = st.columns(3)
        a.metric("Predicted category", r["category"])
        b.metric("Risk level", r["risk_level"])
        c.metric("Risk screening score", f'{r["risk_score"]}/100')
        st.write(f"**Model confidence:** {r['model_confidence']:.1%}")
        st.write("**Recommended action:**", r["corrective_action"])
        st.caption("Confidence is the model's estimated class probability, not the probability that an accident will occur.")
        st.subheader("Class probabilities")
        probs = model.predict_proba([r["report_text"]])[0]
        prob_df = pd.DataFrame({"Category":model.classes_,"Probability":probs})
        st.bar_chart(prob_df.set_index("Category"))


# --------------------------- AI SAFETY CHATBOT ---------------------------
elif page == "AI Safety Chatbot":
    st.title("💬 HSE Safety Assistant")
    st.caption("Version 3.0 • Humanised HSE conversations • Hazard guidance • Report lookup • Precursor trends • New reports")
    st.info("Ask in everyday language. The assistant is limited to workplace safety topics and uses the local report database for historical counts.")
    st.caption("Humanised conversation coverage: 50,000 synthetic examples across 10 hazard groups. These examples improve phrasing coverage; they are not real incident records or model-accuracy evidence.")

    with st.expander("Suggested questions — click to use"):
        suggestions = [
            "A worker is operating a machine without its safety guard. What should I do?",
            "I found exposed electrical wires near the control panel.",
            "A forklift almost hit a pedestrian but nobody was injured. Is this a near miss?",
            "There is a chemical smell near the storage area. What should I do?",
            "How many high-risk reports were recorded this month?",
            "Which site has the most safety reports?",
            "Are repeated electrical hazards appearing in the reports?",
            "Explain lockout tagout in simple words."
        ]
        cols = st.columns(2)
        for i, question in enumerate(suggestions):
            if cols[i % 2].button(question, key=f"chat_suggestion_{i}", use_container_width=True):
                st.session_state["chat_pending_question"] = question

    if "hse_chat_history" not in st.session_state:
        st.session_state["hse_chat_history"] = [{
            "role": "assistant",
            "content": "Hello! I’m your HSE Safety Assistant. I can identify workplace hazards, explain safe next steps, classify near misses, search saved reports and analyse recurring patterns. What would you like to check?"
        }]

    for message in st.session_state["hse_chat_history"]:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    pending = st.session_state.pop("chat_pending_question", None)
    user_prompt = st.chat_input("Describe a hazard or ask a workplace safety question...")
    if pending:
        user_prompt = pending
    if user_prompt:
        st.session_state["hse_chat_history"].append({"role": "user", "content": user_prompt})
        answer, metadata = chatbot_answer(user_prompt, read_reports())
        st.session_state["hse_chat_history"].append({"role": "assistant", "content": answer})
        st.rerun()

    c1, c2 = st.columns([1, 4])
    with c1:
        if st.button("Clear conversation", use_container_width=True):
            st.session_state["hse_chat_history"] = []
            st.session_state.pop("spi_conversation_state", None)
            st.rerun()
    with c2:
        st.caption("For immediate danger, raise the site alarm and follow emergency procedures first. Do not wait for a chatbot response.")

    st.divider()
    st.subheader("📝 Submit a new safety observation")
    st.write("Workers can also create a report directly from the chatbot page. The report is classified and saved to the dashboard database.")
    with st.form("chat_report_form", clear_on_submit=True):
        report_text = st.text_area("Describe what you observed", placeholder="Example: A chemical container is leaking near the transfer pump...")
        x1, x2, x3 = st.columns(3)
        report_site = x1.selectbox("Site", SITES, key="chat_report_site")
        report_department = x2.selectbox("Department", DEPARTMENTS, key="chat_report_department")
        report_equipment = x3.text_input("Equipment / area", placeholder="e.g. Transfer pump")
        report_submit = st.form_submit_button("Classify and save safety report", type="primary", use_container_width=True)
    if report_submit:
        if len(report_text.strip()) < 12:
            st.error("Please provide at least 12 characters so the NLP model has enough context.")
        elif not is_safety_related(report_text)[0]:
            st.warning("This does not appear to be a workplace safety report. Please describe a workplace hazard, unsafe act, near miss or safety observation.")
        else:
            try:
                code, saved = save_chat_report(report_text, report_site, report_department, report_equipment)
                st.success(f"Saved as {code}.")
                m1, m2, m3 = st.columns(3)
                m1.metric("Predicted category", saved["category"])
                m2.metric("Risk screening", saved["risk_level"])
                m3.metric("Screening score", f'{saved["risk_score"]}/100')
                st.write("**Suggested next step:**", saved["corrective_action"])
                st.caption("The report is now available in Executive Dashboard, Precursor Intelligence and Audit Logs.")
            except Exception as exc:
                st.error(f"Could not save the report: {exc}")


# --------------------------- PRECURSOR INTELLIGENCE ---------------------------
elif page == "Precursor Intelligence":
    st.title("📈 Precursor Trend Intelligence")
    st.caption("Pattern-based screening of repeated hazards. Alerts indicate elevated reporting patterns, not certainty of a future accident.")
    alerts = get_alerts(df)
    if alerts:
        for alert in alerts:
            if alert["level"] == "High":
                st.error(f"🔴 {alert['site']}: {alert['message']}")
            else:
                st.warning(f"🟠 {alert['site']}: {alert['message']}")
    else:
        st.success("No site currently meets the configured alert thresholds.")
    st.subheader("Hazard reports by site and category")
    nonroutine = df[df["category"] != MODEL_CATEGORIES[4]]
    if not nonroutine.empty:
        pivot = pd.crosstab(nonroutine["site"], nonroutine["category"])
        st.dataframe(pivot, use_container_width=True)
        fig = px.bar(nonroutine, x="site", color="category", barmode="stack",
                     title="Recorded hazard observations by site")
        st.plotly_chart(fig, use_container_width=True)
    st.subheader("Weekly hazard trend")
    if not df_dates.empty:
        hazards = df_dates[df_dates["category"] != MODEL_CATEGORIES[4]].copy()
        if not hazards.empty:
            hazards["week"] = hazards["report_date"].dt.to_period("W").astype(str)
            weekly = hazards.groupby("week").size().reset_index(name="Hazard reports")
            st.line_chart(weekly.set_index("week"))
        else:
            st.info("No hazard reports found.")
    st.info("Precursor lead time is not calculated from synthetic observations. To calculate it, import real dated precursor reports and subsequent incident records linked by site or event.")

# --------------------------- SITE MONITOR ---------------------------
elif page == "Site Risk Monitor":
    st.title("🚨 Site Risk Monitor")
    st.caption("Site risk indicators are calculated from saved report records.")
    if df.empty:
        st.info("No reports available.")
    else:
        summary = df.groupby("site").agg(
            Reports=("report_code","count"),
            High_Risk=("risk_level",lambda s: int((s=="High").sum())),
            Average_Score=("risk_score","mean"),
            Open=("status",lambda s: int((s!="Closed").sum()))
        ).reset_index()
        summary["Average_Score"] = summary["Average_Score"].round(1)
        summary["Risk_Band"] = summary["Average_Score"].apply(lambda x: "High" if x>=65 else "Medium" if x>=35 else "Low")
        st.dataframe(summary, use_container_width=True, hide_index=True)
        fig = px.density_heatmap(df, x="site", y="category", z="risk_score",
                                 histfunc="avg", color_continuous_scale="RdYlGn_r",
                                 title="Average risk screening score by site and category")
        st.plotly_chart(fig, use_container_width=True)
        st.subheader("Threshold-based alerts")
        for alert in get_alerts(df):
            if alert["level"] == "High": st.error(f"{alert['site']} — {alert['message']}")
            else: st.warning(f"{alert['site']} — {alert['message']}")

# --------------------------- AUDIT LOGS ---------------------------
elif page == "Audit & Corrective Actions":
    st.title("📋 Audit Logs & Corrective Actions")
    col1,col2,col3 = st.columns(3)
    search = col1.text_input("Search report text / ID")
    site_filter = col2.selectbox("Filter site", ["All"] + SITES)
    status_filter = col3.selectbox("Filter status", ["All","Open","In Progress","Closed"])
    filtered = df.copy()
    if search:
        mask = filtered["report_text"].str.contains(search, case=False, regex=False, na=False) | filtered["report_code"].str.contains(search, case=False, regex=False, na=False)
        filtered = filtered[mask]
    if site_filter != "All": filtered = filtered[filtered["site"] == site_filter]
    if status_filter != "All": filtered = filtered[filtered["status"] == status_filter]
    st.dataframe(filtered[["report_code","report_date","site","department","category","risk_level","risk_score","status","source","report_text"]], use_container_width=True, hide_index=True)
    st.download_button("⬇️ Export filtered audit logs (CSV)", filtered.to_csv(index=False).encode("utf-8"),
                       file_name="hse_audit_logs.csv", mime="text/csv")
    st.divider()
    st.subheader("Update report status")
    if not df.empty:
        selected = st.selectbox("Select report", df["report_code"].tolist())
        new_status = st.selectbox("New status", ["Open","In Progress","Closed"])
        if st.button("Save status update"):
            with db() as con:
                con.execute("UPDATE reports SET status=? WHERE report_code=?", (new_status,selected))
            st.success(f"{selected} updated to {new_status}.")
            st.rerun()
    else:
        st.info("No reports to update.")

# --------------------------- EVALUATION ---------------------------
elif page == "Model Evaluation":
    st.title("🧪 Model Evaluation")
    st.caption("Metrics below are calculated on a held-out split of the generated demonstration corpus. They are not real-world validation results.")
    acc = accuracy_score(y_test, y_pred)
    macro = f1_score(y_test, y_pred, average="macro")
    weighted = f1_score(y_test, y_pred, average="weighted")
    c1,c2,c3 = st.columns(3)
    c1.metric("Holdout accuracy", f"{acc:.3f}")
    c2.metric("Macro F1", f"{macro:.3f}")
    c3.metric("Weighted F1", f"{weighted:.3f}")
    report = classification_report(y_test, y_pred, output_dict=True, zero_division=0)
    metric_df = pd.DataFrame(report).T
    st.subheader("Per-class precision, recall and F1")
    st.dataframe(metric_df.loc[MODEL_CATEGORIES, ["precision","recall","f1-score","support"]].round(3), use_container_width=True)
    cm = confusion_matrix(y_test, y_pred, labels=MODEL_CATEGORIES)
    fig = px.imshow(cm, x=MODEL_CATEGORIES, y=MODEL_CATEGORIES, text_auto=True,
                    color_continuous_scale="Blues", labels=dict(x="Predicted", y="Actual", color="Count"))
    fig.update_layout(title="Confusion matrix", xaxis_tickangle=-35)
    st.plotly_chart(fig, use_container_width=True)
    st.subheader("Keyword baseline comparison")
    KEYWORDS = {
        MODEL_CATEGORIES[0]: ["interlock","lockout","bypass","machine guard","forklift","emergency stop"],
        MODEL_CATEGORIES[1]: ["scaffold","harness","ladder","guardrail","floor opening","height"],
        MODEL_CATEGORIES[2]: ["chemical","gas","vapour","chlorine","solvent","leak","valve"],
        MODEL_CATEGORIES[3]: ["electrical","cable","wire","insulation","panel","grounding","circuit"],
        MODEL_CATEGORIES[4]: ["routine","handover","housekeeping","normal","no issues","toolbox talk"]
    }
    def keyword_predict(text):
        t = text.lower()
        scores = {cat: sum(1 for kw in kws if kw in t) for cat,kws in KEYWORDS.items()}
        return max(scores, key=scores.get)
    base_pred = [keyword_predict(x) for x in X_test]
    base_f1 = f1_score(y_test, base_pred, average="macro")
    comparison = pd.DataFrame({
        "Method":["Keyword baseline","TF-IDF + Logistic Regression"],
        "Macro F1":[base_f1,macro]
    })
    st.dataframe(comparison.round(3), use_container_width=True, hide_index=True)
    st.bar_chart(comparison.set_index("Method"))
    st.warning("Because the corpus is synthetic and generated from templates, these scores are only a software demonstration. For a defensible CA3 result, evaluate on manually labelled, unseen real reports.")

st.sidebar.divider()
st.sidebar.caption("Safety Precursor Intelligence 3.0 • Humanised HSE chatbot + NLP + precursor analytics")
# Before (example of how it is currently rendering):
# with st.chat_message("assistant"):
#     st.markdown(message["content"])

# After (add .replace("\\n", "\n") before rendering):
with st.chat_message("assistant"):
    clean_text = str(message["content"]).replace("\\n", "\n")
    st.markdown(clean_text)
