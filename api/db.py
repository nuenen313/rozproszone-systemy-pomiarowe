import psycopg2
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# TODO: add timestamp received at

DB_HOST="database"
DB_NAME="abcd_db"
DB_USER="admin"
DB_PASSWORD="admin_pass1234"

def get_connection() :
    return psycopg2.connect(
	    host=DB_HOST,
	    dbname=DB_NAME,
	    user=DB_USER,
	    password=DB_PASSWORD
   )

DATABASE_URL = f"postgresql+psycopg2://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:5432/{DB_NAME}"

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)