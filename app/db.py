import socket
from datetime import datetime
from sqlalchemy import create_engine, Column, Integer, String, Float, Text, DateTime, JSON
from sqlalchemy.orm import declarative_base, sessionmaker
from .config import DATABASE_URL

Base = declarative_base()


def _is_postgres_up():
    if "postgres" not in DATABASE_URL:
        return False
    try:
        # Check port 5432 directly with 0.2s timeout
        with socket.create_connection(("localhost", 5432), timeout=0.2):
            return True
    except Exception:
        return False


if _is_postgres_up():
    engine = create_engine(DATABASE_URL, pool_pre_ping=True)
else:
    # Graceful fallback to local SQLite when Docker Postgres is offline
    engine = create_engine("sqlite:///kisan.db", connect_args={"check_same_thread": False})

Session = sessionmaker(bind=engine, expire_on_commit=False)


class Farmer(Base):
    __tablename__ = "farmers"
    id = Column(Integer, primary_key=True)
    phone = Column(String(20), unique=True, index=True)
    name = Column(String(100))
    language = Column(String(5), default="hi")  # hi, mr, ta, te, en
    village = Column(String(150))
    lat = Column(Float)
    lon = Column(Float)
    crops = Column(JSON, default=list)          # crop history
    soil_test = Column(JSON, default=dict)      # e.g. {"ph": 6.5, "N": "low"}
    created_at = Column(DateTime, default=datetime.utcnow)


class QueryLog(Base):
    __tablename__ = "queries"
    id = Column(Integer, primary_key=True)
    phone = Column(String(20), index=True)
    question = Column(Text)
    answer = Column(Text)
    flags = Column(JSON, default=list, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


def init_db():
    Base.metadata.create_all(engine)
    try:
        with engine.connect() as conn:
            if "sqlite" in str(engine.url):
                cols = [c[1] for c in conn.exec_driver_sql("PRAGMA table_info(queries)").fetchall()]
                if "flags" not in cols:
                    conn.exec_driver_sql("ALTER TABLE queries ADD COLUMN flags JSON")
    except Exception as e:
        print("Warning updating queries table schema:", e)


def get_farmer(phone):
    """Return the farmer row, creating it on first contact."""
    with Session() as s:
        f = s.query(Farmer).filter_by(phone=phone).first()
        if not f:
            f = Farmer(phone=phone, crops=[], soil_test={})
            s.add(f)
            s.commit()
        return f


def update_farmer(phone, **fields):
    with Session() as s:
        f = s.query(Farmer).filter_by(phone=phone).first()
        if not f:
            f = Farmer(phone=phone, crops=[], soil_test={})
            s.add(f)
        for k, v in fields.items():
            setattr(f, k, v)
        s.commit()
        return f


def log_query(phone, question, answer, flags=None):
    with Session() as s:
        s.add(QueryLog(phone=phone, question=question, answer=answer, flags=flags or []))
        s.commit()
