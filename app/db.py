from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

DATABASE_URL = (
    "mssql+pyodbc://wyny:wyny@192.168.39.203/dbProduccion"
    "?driver=ODBC+Driver+17+for+SQL+Server"
)

engine = create_engine(DATABASE_URL, echo=False)

SessionLocal = sessionmaker(bind=engine)