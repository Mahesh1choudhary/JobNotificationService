
from sqlalchemy import Column, Integer, String, DateTime, UniqueConstraint, event
from sqlalchemy.ext.declarative import declarative_base
import hashlib

Base = declarative_base()

def compute_hash(description: str) -> str:
    return hashlib.sha256(description.encode("utf-8")).hexdigest()

class JobModel(Base):
    __tablename__ = "jobs"

    id = Column(Integer, primary_key=True)

    company = Column(String, nullable=False)
    job_link = Column(String, nullable=False)

    job_id = Column(String)
    job_description = Column(String)

    description_hash = Column(String)

    created_at = Column(DateTime)

    __table_args__ = (
        UniqueConstraint('company', 'job_link', 'description_hash', name='uq_job_unique'),
    )


@event.listens_for(JobModel, "before_insert")
def set_hash_before_insert(mapper, connection, target):
    target.description_hash = compute_hash(target.job_description or "")
