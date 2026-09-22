from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import declarative_base, sessionmaker, Session
from app.core.config import settings

connect_args = {}
if settings.DATABASE_URL.startswith("sqlite"):
    connect_args["check_same_thread"] = False

engine = create_engine(
    settings.DATABASE_URL,
    connect_args=connect_args,
    echo=False
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    db: Session = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def ensure_schema() -> None:
    """轻量级增量迁移：为已存在的旧表补齐新增列（SQLite/MySQL 通用 ALTER TABLE ADD COLUMN）。

    Base.metadata.create_all 只会创建缺失的表，不会为已存在的表新增列，
    因此新增字段需要通过这里补齐，避免旧库升级后查询报 "no such column"。
    """
    required_columns = {
        "interviews": {
            "resume_id": "INTEGER",
            "jd_text": "TEXT",
        },
        "learning_tasks": {
            "stage": "VARCHAR(100)",
        },
    }
    inspector = inspect(engine)
    existing_tables = set(inspector.get_table_names())
    with engine.begin() as conn:
        for table, columns in required_columns.items():
            if table not in existing_tables:
                continue
            current = {c["name"] for c in inspector.get_columns(table)}
            for col_name, col_type in columns.items():
                if col_name not in current:
                    conn.execute(text(f"ALTER TABLE {table} ADD COLUMN {col_name} {col_type}"))
