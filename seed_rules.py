from database import SessionLocal
from models import BusinessRule

db = SessionLocal()
rule = BusinessRule(
    name="default",
    min_rating=600,
    min_income=2000,
    block_if_bureau_restriction=True
)
db.add(rule)
db.commit()
db.close()