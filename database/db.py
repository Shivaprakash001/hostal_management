from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models.student import Base

engine= create_engine("sqlite:///database/hostel.db")
Session=sessionmaker(bind=engine)
session=Session()

Base.metadata.create_all(engine)
