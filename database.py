# database.py

from sqlalchemy import create_engine, Column, Integer, String, Float, ForeignKey
from sqlalchemy.orm import sessionmaker, declarative_base, relationship

DB_USER = "avnadmin"          
DB_PASS = "AVNS_YMuhD0k-Wje55tNCfUd"              
DB_HOST = "mysql-228aa29b-shantonudebnath-f9bb.e.aivencloud.com"
DB_NAME = "patientdata"        

SQLALCHEMY_DATABASE_URL = f"mysql+pymysql://{DB_USER}:{DB_PASS}@{DB_HOST}/{DB_NAME}"

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
