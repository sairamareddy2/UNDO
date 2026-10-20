from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from app.config import settings

connect_args = {"check_same_thread": False} if settings.DATABASE_URL.startswith("sqlite") else {}

engine = create_engine(
    settings.DATABASE_URL,
    connect_args=connect_args,
    echo=False
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    from app import models  # noqa: F401
    Base.metadata.create_all(bind=engine)

    # Seed baseline simulated devices/items if not present
    db = SessionLocal()
    try:
        # Seed simulated doors
        existing_doors = db.query(models.DoorLock).count()
        if existing_doors == 0:
            db.add_all([
                models.DoorLock(id="front_door", name="Front Door Lock", is_locked=True),
                models.DoorLock(id="back_door", name="Patio Back Door", is_locked=True),
                models.DoorLock(id="garage_entry", name="Garage Side Door", is_locked=True),
            ])

        # Seed initial groceries
        existing_groceries = db.query(models.GroceryItem).count()
        if existing_groceries == 0:
            db.add_all([
                models.GroceryItem(name="Organic Whole Milk", quantity=1, category="Dairy"),
                models.GroceryItem(name="Sourdough Bread", quantity=2, category="Bakery"),
            ])

        # Seed initial reminders
        existing_reminders = db.query(models.Reminder).count()
        if existing_reminders == 0:
            db.add_all([
                models.Reminder(title="Team Standup Sync", remind_at="10:00 AM", priority="medium"),
            ])

        db.commit()
    except Exception as e:
        db.rollback()
        raise e
    finally:
        db.close()
