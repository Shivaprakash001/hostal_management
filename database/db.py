from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

engine = create_engine("sqlite:///database/hostel.db")
Session = sessionmaker(bind=engine)
Base = declarative_base()


def init_db() -> None:
    import models.models
    Base.metadata.create_all(bind=engine)

def get_db():
    db = Session()
    try:
        yield db
    finally:
        db.close()