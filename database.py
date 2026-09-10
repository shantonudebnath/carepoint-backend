# database.py

import os

from sqlalchemy import create_engine, Column, Integer, String, Float, ForeignKey
from sqlalchemy.orm import sessionmaker, declarative_base, relationship


def _build_database_url() -> str:
    # Railway (and most hosts) provide a single connection string.
    url = os.getenv("DATABASE_URL") or os.getenv("MYSQL_URL")
    if url:
        # SQLAlchemy needs an explicit driver; Railway gives a bare mysql:// URL.
        if url.startswith("mysql://"):
            url = url.replace("mysql://", "mysql+pymysql://", 1)
        return url

    # Local development fallback (XAMPP / phpMyAdmin).
    db_user = os.getenv("DB_USER", "root")
    db_pass = os.getenv("DB_PASS", "")
    db_host = os.getenv("DB_HOST", "localhost")
    db_port = os.getenv("DB_PORT", "3306")
    db_name = os.getenv("DB_NAME", "patientdata")
    return f"mysql+pymysql://{db_user}:{db_pass}@{db_host}:{db_port}/{db_name}"


SQLALCHEMY_DATABASE_URL = _build_database_url()

engine = create_engine(SQLALCHEMY_DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

class LabTest(Base):
    __tablename__ = "single_patient_15_tests"  # your table

    Patient_ID = Column(String(50), primary_key=True)
    Patient_Name = Column(String(100))
    Patient_Age_Years = Column(Float)
    Patient_Gender = Column(String(10))

    Report_Title = Column(String(200))
    Lab = Column(String(200))
    Department = Column(String(200))
    Sample_Type = Column(String(100))
    Sample_Date = Column(String(50))
    Report_Date = Column(String(50))

    Test_Name = Column(String(200), primary_key=True)
    Result = Column(String(100))
    Unit = Column(String(50))
    Reference_Range = Column(String(200))
    Method = Column(String(200))


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def seed_if_empty() -> str:
    """Load the demo dataset from seed.sql when the DB doesn't match it.

    Runs on startup so a fresh database (e.g. a new Railway MySQL) is usable
    without a manual import. seed.sql starts with a `-- SEED_ROWS: <n>` header;
    if the table already has exactly that many rows nothing happens, otherwise
    the file (which begins with DROP TABLE) rebuilds and reloads it.
    """
    import re

    from sqlalchemy import text

    seed_path = os.path.join(os.path.dirname(__file__), "seed.sql")
    if not os.path.exists(seed_path):
        return "seed.sql not found; skipped"

    with open(seed_path, "r", encoding="utf-8") as fh:
        raw = fh.read()

    m = re.search(r"SEED_ROWS:\s*(\d+)", raw)
    expected = int(m.group(1)) if m else None

    # Split into statements, dropping full-line SQL comments.
    body = "\n".join(
        ln for ln in raw.splitlines() if not ln.lstrip().startswith("--")
    )
    statements = [s.strip() for s in body.split(";\n") if s.strip()]

    with engine.begin() as conn:
        try:
            count = conn.execute(
                text("SELECT COUNT(*) FROM single_patient_15_tests")
            ).scalar()
        except Exception:
            count = 0

        if count and (expected is None or count == expected):
            return f"already populated ({count} rows)"

        for stmt in statements:
            conn.exec_driver_sql(stmt.rstrip(";"))

        count = conn.execute(
            text("SELECT COUNT(*) FROM single_patient_15_tests")
        ).scalar()

    return f"seeded ({count} rows)"