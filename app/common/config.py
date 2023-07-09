from os import getenv
from pathlib import Path

from sqlalchemy import MetaData, Text, create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker as Sessionmaker

from app.common.sqla import MappingBase

current_directory: Path = Path.cwd()

# indexes, unique & check constraints, foreign & primary key namings
convention = {
    "ix": "ix_%(column_0_label)s",  # noqa: WPS323
    "uq": "uq_%(table_name)s_%(column_0_name)s",  # noqa: WPS323
    "ck": "ck_%(table_name)s_%(constraint_name)s",  # noqa: WPS323
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",  # noqa: WPS323
    "pk": "pk_%(table_name)s",  # noqa: WPS323
}

db_url: str = getenv("DB_LINK", f"sqlite:///{current_directory / 'xieffect/app.db'}")
engine = create_engine(db_url, pool_recycle=280, echo=True)  # noqa: WPS432
db_meta = MetaData(naming_convention=convention)
sessionmaker = Sessionmaker(bind=engine)


class Base(DeclarativeBase, MappingBase):
    metadata = db_meta
    type_annotation_map = {str: Text}
