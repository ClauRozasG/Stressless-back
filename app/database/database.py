from sqlmodel import SQLModel, create_engine, Session

DATABASE_URL = "postgresql://postgres:Selenaditsy_12@localhost:5432/stressdb"

engine = create_engine(DATABASE_URL, echo=True)

def create_tables():
    SQLModel.metadata.create_all(engine)

def get_session():
    with Session(engine) as session:
        yield session