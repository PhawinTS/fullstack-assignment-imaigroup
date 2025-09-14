from sqlmodel import SQLModel, create_engine, Session

DATABASE_URL = "postgresql://devuser:devpass@localhost:5432/devdb"
engine = create_engine(DATABASE_URL, echo=True)

def init_db():
    # Fixed imports for your current structure
    from app.models import User, Photo  # Changed from backend.models to app.models
    SQLModel.metadata.create_all(engine)

def get_session():
    with Session(engine) as session:
        yield session