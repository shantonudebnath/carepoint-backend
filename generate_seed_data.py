"""Regenerate seed.sql with N patients x 15 lab tests.

Run from the backend/ directory:  python generate_seed_data.py
PID1001 (SHANTONU DEBNATH) is kept byte-for-byte identical to the original demo
data; PID1002..PID{1000+N} are synthetic but clinically plausible.
"""
import os
import random
from datetime import datetime, timedelta

random.seed(20260910)

OUT = os.path.join(os.path.dirname(__file__), "seed.sql")
N_PATIENTS = 200

# test_name -> (unit, reference_range, method, lo, hi, decimals, hard_min, hard_max)
TESTS = [
    ("Hemoglobin",           "g/dL",      "13.0-17.0", "Automated",          13.0, 17.0, 1,  6.0,  20.0),
    ("WBC Count",             "x10^3/uL",  "4.0-10.0",  "Automated",          4.0,  10.0, 1,  1.5,  30.0),
    ("Platelet Count",        "x10^3/uL",  "150-400",   "Automated",          150,  400,  0,  20,   700),
    ("ALT (SGPT)",            "U/L",       "0-40",      "IFCC",               8,    40,   0,  5,    350),
    ("AST (SGOT)",            "U/L",       "0-40",      "IFCC",               8,    40,   0,  5,    320),
    ("Alkaline Phosphatase",  "U/L",       "44-147",    "Enzymatic",          44,   147,  0,  30,   400),
    ("Total Bilirubin",       "mg/dL",     "0.1-1.2",   "Photometric",        0.2,  1.2,  1,  0.1,  6.0),
    ("Creatinine",            "mg/dL",     "0.7-1.3",   "Enzymatic",          0.7,  1.3,  1,  0.3,  6.0),
    ("Urea",                  "mg/dL",     "15-40",     "Enzymatic",          15,   40,   0,  8,    150),
    ("Fasting Glucose",       "mg/dL",     "70-100",    "Hexokinase",         72,   99,   0,  50,   320),
    ("Total Cholesterol",     "mg/dL",     "Desirable: <200; Borderline: 200-239; High: >=240", "CHOD-PAP",           140, 199, 0, 110, 330),
    ("HDL Cholesterol",       "mg/dL",     "Low: <40; Desirable: >=40",                          "Direct enzymatic",    42,  70,  0, 22,  95),
    ("LDL Cholesterol",       "mg/dL",     "Optimal: <100; Near/Above optimal: 100-129; Borderline high: 130-159", "Friedewald formula", 65, 99, 0, 45, 240),
    ("Triglycerides",         "mg/dL",     "Normal: <150; Borderline high: 150-199; High: 200-499", "Enzymatic colorimetric", 70, 149, 0, 45, 480),
    ("TSH",                   "uIU/mL",    "0.4-4.0",   "CMIA",               0.5,  3.9,  2,  0.05, 12.0),
]

FIRST_M = ["SHANTONU","RAKIBUL","TANVIR","ARIF","MEHEDI","SAKIB","NAHID","IMRAN","FAHIM","JOY",
           "RASEL","SHAKIL","ASHRAFUL","MASUD","TAREK","SOHEL","NAYEEM","ABIR","RIDOY","SIAM",
           "FARHAN","JAHID","RIFAT","SABBIR","TOWHID","ZAHIN","NOMAN","PARVEZ","SAJID","HASIB"]
FIRST_F = ["NUSRAT","TASNIM","SADIA","MARIA","LAMIA","ISRAT","FARZANA","SUMAIYA","JANNAT","RUMANA",
           "SHARMIN","AFRIN","MOUMITA","PRIYA","NAIMA","TAHMINA","RUBAIYA","MIM","ANIKA","OISHI",
           "SNEHA","BUSHRA","LABONI","RITU","SHIULY","KEYA","POPY","NADIA","TISHA","ELMA"]
LAST = ["DEBNATH","ISLAM","HOSSAIN","AHMED","RAHMAN","CHOWDHURY","AKTER","KHATUN","SARKER","MONDAL",
        "ROY","DAS","HAQUE","KABIR","ALAM","BHUIYAN","MOLLA","MIA","GHOSH","BISWAS","TALUKDER","SHEIKH"]
HOSPITALS = ["Demo Hospital","City General Hospital","Popular Diagnostic","Ibn Sina Hospital",
             "Square Hospital","Labaid Hospital","United Hospital","Central Hospital"]

COLS = ["Patient_Name","Patient_Age_Years","Patient_Gender","Hospital","Lab","Department",
        "Report_Title","Sample_Type","Sample_Date","Report_Date","Patient_ID","Test_Name",
        "Result","Unit","Reference_Range","Method"]


def esc(v):
    return "'" + str(v).replace("\\", "\\\\").replace("'", "\\'") + "'"


def fmt_num(x, decimals):
    return str(int(round(x))) if decimals == 0 else f"{x:.{decimals}f}"


def gen_result(lo, hi, decimals, hard_min, hard_max):
    r = random.random()
    if r < 0.68:
        val = random.uniform(lo, hi)
    elif r < 0.86:
        val = random.uniform(hi, hi + (hi - lo) * 0.6 + 1)
    elif r < 0.96:
        val = random.uniform(hi + (hi - lo) * 0.4 + 1, hard_max)
    else:
        val = random.uniform(hard_min, lo)
    return fmt_num(max(hard_min, min(hard_max, val)), decimals)


ORIGINAL_PID1001 = [
    ("Hemoglobin", "14.1"), ("WBC Count", "7.2"), ("Platelet Count", "270"),
    ("ALT (SGPT)", "42"), ("AST (SGOT)", "37"), ("Alkaline Phosphatase", "95"),
    ("Total Bilirubin", "0.9"), ("Creatinine", "1.2"), ("Urea", "38"),
    ("Fasting Glucose", "112"), ("Total Cholesterol", "205"), ("HDL Cholesterol", "44"),
    ("LDL Cholesterol", "132"), ("Triglycerides", "176"), ("TSH", "3.2"),
]
ORIG_META = dict(
    name="SHANTONU DEBNATH", age="25", gender="M", hospital="Demo Hospital",
    lab="Central Lab", dept="Biochemistry & Hematology",
    title="Complete Health Checkup (Fasting)", sample="Blood",
    sdate="20-01-2025 08:15", rdate="20-01-2025 11:20",
)
UNIT_BY_TEST = {t[0]: t for t in TESTS}

rows = []
for tname, result in ORIGINAL_PID1001:
    _, unit, ref, method, *_ = UNIT_BY_TEST[tname]
    if tname in ("WBC Count", "Platelet Count"):
        unit = "×10^3/uL"
    rows.append([ORIG_META["name"], ORIG_META["age"], ORIG_META["gender"], ORIG_META["hospital"],
                 ORIG_META["lab"], ORIG_META["dept"], ORIG_META["title"], ORIG_META["sample"],
                 ORIG_META["sdate"], ORIG_META["rdate"], "PID1001", tname, result, unit, ref, method])

for i in range(2, N_PATIENTS + 1):
    pid = f"PID{1000 + i}"
    gender = random.choice(["M", "F"])
    first = random.choice(FIRST_M if gender == "M" else FIRST_F)
    name = f"{first} {random.choice(LAST)}"
    age = str(random.randint(3, 88))
    hospital = random.choice(HOSPITALS)
    sdt = datetime(2025, 1, 1) + timedelta(days=random.randint(0, 300),
                                           hours=random.randint(6, 18),
                                           minutes=random.choice([0, 5, 10, 15, 20, 30, 40, 45, 50]))
    rdt = sdt + timedelta(hours=random.randint(2, 6), minutes=random.choice([0, 15, 30, 45]))
    sdate, rdate = sdt.strftime("%d-%m-%Y %H:%M"), rdt.strftime("%d-%m-%Y %H:%M")
    for tname, unit, ref, method, lo, hi, dec, hmin, hmax in TESTS:
        rows.append([name, age, gender, hospital, "Central Lab", "Biochemistry & Hematology",
                     "Complete Health Checkup (Fasting)", "Blood", sdate, rdate, pid, tname,
                     gen_result(lo, hi, dec, hmin, hmax), unit, ref, method])

col_list = ", ".join(f"`{c}`" for c in COLS)
values_sql = ",\n".join("(" + ", ".join(esc(v) for v in r) + ")" for r in rows)

sql = f"""-- SEED_ROWS: {len(rows)}
-- Auto-generated demo dataset: {N_PATIENTS} patients x {len(TESTS)} lab tests.
-- PID1001 matches the original patientdata.sql exactly. Regenerate: python generate_seed_data.py

DROP TABLE IF EXISTS `single_patient_15_tests`;

CREATE TABLE `single_patient_15_tests` (
  `Patient_Name` varchar(100) DEFAULT NULL,
  `Patient_Age_Years` varchar(10) DEFAULT NULL,
  `Patient_Gender` varchar(10) DEFAULT NULL,
  `Hospital` varchar(80) DEFAULT NULL,
  `Lab` varchar(80) DEFAULT NULL,
  `Department` varchar(80) DEFAULT NULL,
  `Report_Title` varchar(120) DEFAULT NULL,
  `Sample_Type` varchar(40) DEFAULT NULL,
  `Sample_Date` varchar(30) DEFAULT NULL,
  `Report_Date` varchar(30) DEFAULT NULL,
  `Patient_ID` varchar(20) DEFAULT NULL,
  `Test_Name` varchar(60) DEFAULT NULL,
  `Result` varchar(20) DEFAULT NULL,
  `Unit` varchar(20) DEFAULT NULL,
  `Reference_Range` varchar(255) DEFAULT NULL,
  `Method` varchar(60) DEFAULT NULL,
  KEY `idx_patient` (`Patient_ID`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

INSERT INTO `single_patient_15_tests` ({col_list}) VALUES
{values_sql};
"""

with open(OUT, "w", encoding="utf-8", newline="\n") as fh:
    fh.write(sql)

print(f"wrote {OUT}  ({N_PATIENTS} patients, {len(rows)} rows)")
