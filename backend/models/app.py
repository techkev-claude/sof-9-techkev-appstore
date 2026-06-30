from sqlalchemy import (
    Column,
    Integer,
    String,
    DateTime,
    Boolean,
    BigInteger,
    ForeignKey,
    UniqueConstraint,
)
from sqlalchemy.orm import declarative_base, relationship
from datetime import datetime

Base = declarative_base()


class App(Base):
    """Eine App, identifiziert durch ihren eindeutigen Package-Namen.
    Haelt die Stammdaten; konkrete APKs liegen in AppVersion (Versionsverwaltung)."""

    __tablename__ = "apps"

    id = Column(Integer, primary_key=True, index=True)
    package_name = Column(String, unique=True, index=True, nullable=False)
    display_name = Column(String, nullable=False)
    category = Column(String, default="Sonstige")
    description = Column(String, default="")
    icon_filename = Column(String, nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    versions = relationship(
        "AppVersion",
        back_populates="app",
        cascade="all, delete-orphan",
        order_by="desc(AppVersion.version_code)",
    )

    @property
    def latest_version(self):
        if not self.versions:
            return None
        return max(self.versions, key=lambda v: v.version_code)


class AppVersion(Base):
    """Eine konkrete hochgeladene APK-Version einer App, inkl. Changelog.
    Mehrere Versionen pro App werden parallel vorgehalten."""

    __tablename__ = "app_versions"
    __table_args__ = (
        UniqueConstraint("app_id", "version_code", name="uq_app_version_code"),
    )

    id = Column(Integer, primary_key=True, index=True)
    app_id = Column(Integer, ForeignKey("apps.id"), nullable=False, index=True)
    version_name = Column(String, nullable=False)
    version_code = Column(Integer, nullable=False)
    changelog = Column(String, default="")
    apk_filename = Column(String, nullable=False)
    apk_size_bytes = Column(BigInteger, nullable=False)
    min_sdk = Column(Integer, nullable=True)
    target_sdk = Column(Integer, nullable=True)
    download_count = Column(Integer, default=0)
    install_count = Column(Integer, default=0)
    uploaded_at = Column(DateTime, default=datetime.utcnow)

    app = relationship("App", back_populates="versions")
