from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime
from sqlalchemy.orm import sessionmaker, declarative_base

from datetime import datetime

import os


if not os.path.isdir("./dbs/"):
    os.mkdir("./dbs/")

engine = create_engine('sqlite:///database/dbs/pages.db')

Base = declarative_base()


class PageModel(Base):
    __tablename__ = 'pages'

    id = Column(Integer, primary_key=True)

    status_code = Column(Integer)
    elapsed = Column(Integer)
    crawled_at = Column(DateTime, default=datetime.utcnow)

    url = Column(String)
    domain = Column(String)
    title = Column(String)

    content = Column(Text)


Base.metadata.create_all(engine)

Session = sessionmaker(bind=engine)
