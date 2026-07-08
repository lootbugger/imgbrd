from fastapi import Depends
from typing import Annotated
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy import create_engine


sqlite_file_name = "database.db"
sqlite_url = f"sqlite:///{sqlite_file_name}"

engine = create_engine(sqlite_url, echo=True)

SessionFactory = sessionmaker(engine)


def get_session():
    with SessionFactory() as session:
        yield session


SessionDep = Annotated[Session, Depends(get_session)]
