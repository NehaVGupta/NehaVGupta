"""PostgreSQL/PostGIS-ready entity model (SQLAlchemy + GeoAlchemy2).

NOT used at runtime by the prototype (which persists JSON via Repository). This file documents the
target schema for the production path: User, Dataset, Image, Analysis, Query, Detection,
Segmentation, ChangeRegion, Evidence. Install `sqlalchemy geoalchemy2 psycopg[binary]` to use it.
"""
try:
    from geoalchemy2 import Geometry
    from sqlalchemy import JSON, Column, DateTime, Float, ForeignKey, Integer, String, func
    from sqlalchemy.orm import declarative_base

    Base = declarative_base()

    class User(Base):
        __tablename__ = "users"
        id = Column(Integer, primary_key=True)
        name = Column(String(120), nullable=False)
        email = Column(String(254), unique=True, nullable=False, index=True)
        password_hash = Column(String(255), nullable=False)
        role = Column(String, default="analyst")
        created_at = Column(DateTime, server_default=func.now())
        updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    class Dataset(Base):
        __tablename__ = "datasets"
        id = Column(Integer, primary_key=True)
        name = Column(String)
        synthetic = Column(Integer, default=0)

    class Image(Base):
        __tablename__ = "images"
        id = Column(String, primary_key=True)
        dataset_id = Column(ForeignKey("datasets.id"))
        storage_key = Column(String)
        crs = Column(String)
        footprint = Column(Geometry("POLYGON", srid=4326))
        meta = Column(JSON)

    class Analysis(Base):
        __tablename__ = "analyses"
        id = Column(String, primary_key=True)
        image_id = Column(ForeignKey("images.id"))
        image_b_id = Column(ForeignKey("images.id"), nullable=True)
        analysis_type = Column(String)
        engine = Column(String)
        confidence = Column(Float)
        created = Column(DateTime, server_default=func.now())

    class Query(Base):
        __tablename__ = "queries"
        id = Column(Integer, primary_key=True)
        analysis_id = Column(ForeignKey("analyses.id"))
        text = Column(String)
        intent = Column(String)

    class Detection(Base):
        __tablename__ = "detections"
        id = Column(Integer, primary_key=True)
        analysis_id = Column(ForeignKey("analyses.id"))
        label = Column(String)
        confidence = Column(Float)
        geom = Column(Geometry("POLYGON"))

    class Segmentation(Base):
        __tablename__ = "segmentations"
        id = Column(Integer, primary_key=True)
        analysis_id = Column(ForeignKey("analyses.id"))
        label = Column(String)
        area_m2 = Column(Float)
        geom = Column(Geometry("MULTIPOLYGON"))

    class ChangeRegion(Base):
        __tablename__ = "change_regions"
        id = Column(Integer, primary_key=True)
        analysis_id = Column(ForeignKey("analyses.id"))
        change_type = Column(String)
        significant = Column(Integer)
        confidence = Column(Float)
        geom = Column(Geometry("POLYGON"))

    class Evidence(Base):
        __tablename__ = "evidence"
        id = Column(Integer, primary_key=True)
        analysis_id = Column(ForeignKey("analyses.id"))
        payload = Column(JSON)
except ImportError:  # dependencies are optional for the prototype
    Base = None
