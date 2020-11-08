
import logging
import os

import sqlalchemy
from sqlalchemy.orm import sessionmaker

from ..configuration import default_conf
from ..dataclasses.model import Base

logging.info(f"{[i for i in default_conf]}")
DB_PREFIX = "sqlite:///"
DB_URL = "data/bibler.db"
if os.path.exists(DB_URL) and default_conf["production"] == "false":
    logging.warn("Removing existing database")
    os.remove(DB_URL)
engine = sqlalchemy.create_engine(
    f"{DB_PREFIX}{DB_URL}",
    echo=True,
    connect_args={"check_same_thread": False}
)
Session = sessionmaker(bind=engine)
Base.metadata.create_all(engine)
