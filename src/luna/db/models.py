from sqlalchemy import Float
from sqlalchemy import ForeignKey
from sqlalchemy import Index
from sqlalchemy import Integer
from sqlalchemy import String
from sqlalchemy import UniqueConstraint
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column
from sqlalchemy.orm import relationship

from luna.core.database import Base


class BuildingModel(Base):
    __tablename__ = "buildings"
    __table_args__ = (
        Index("ix_buildings_coordinates", "latitude", "longitude"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    address: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    latitude: Mapped[float] = mapped_column(Float, nullable=False)
    longitude: Mapped[float] = mapped_column(Float, nullable=False)

    organizations: Mapped[list["OrganizationModel"]] = relationship(back_populates="building")


class ActivityModel(Base):
    __tablename__ = "activities"
    __table_args__ = (
        UniqueConstraint("name", "parent_id", name="uq_activities_name_parent"),
        Index("ix_activities_name", "name"),
        Index("ix_activities_parent_id", "parent_id"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    parent_id: Mapped[int | None] = mapped_column(ForeignKey("activities.id", ondelete="SET NULL"), nullable=True)

    parent: Mapped["ActivityModel | None"] = relationship(remote_side=[id], back_populates="children")
    children: Mapped[list["ActivityModel"]] = relationship(back_populates="parent")
    organization_links: Mapped[list["OrganizationActivityModel"]] = relationship(back_populates="activity", cascade="all, delete-orphan")


class OrganizationModel(Base):
    __tablename__ = "organizations"
    __table_args__ = (
        Index("ix_organizations_name", "name"),
        Index("ix_organizations_building_id", "building_id"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    building_id: Mapped[int] = mapped_column(ForeignKey("buildings.id", ondelete="RESTRICT"), nullable=False)

    building: Mapped[BuildingModel] = relationship(back_populates="organizations")
    phones: Mapped[list["OrganizationPhoneModel"]] = relationship(back_populates="organization", cascade="all, delete-orphan")
    activity_links: Mapped[list["OrganizationActivityModel"]] = relationship(back_populates="organization", cascade="all, delete-orphan")


class OrganizationPhoneModel(Base):
    __tablename__ = "organization_phones"
    __table_args__ = (
        Index("ix_organization_phones_organization_id", "organization_id"),
        Index("ix_organization_phones_phone", "phone"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    organization_id: Mapped[int] = mapped_column(ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False)
    phone: Mapped[str] = mapped_column(String(32), nullable=False)

    organization: Mapped[OrganizationModel] = relationship(back_populates="phones")


class OrganizationActivityModel(Base):
    __tablename__ = "organization_activities"
    __table_args__ = (
        Index("ix_organization_activities_activity_id", "activity_id"),
    )

    organization_id: Mapped[int] = mapped_column(ForeignKey("organizations.id", ondelete="CASCADE"), primary_key=True)
    activity_id: Mapped[int] = mapped_column(ForeignKey("activities.id", ondelete="CASCADE"), primary_key=True)

    organization: Mapped[OrganizationModel] = relationship(back_populates="activity_links")
    activity: Mapped[ActivityModel] = relationship(back_populates="organization_links")
