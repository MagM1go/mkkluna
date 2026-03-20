from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "202603180001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "buildings",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("address", sa.String(length=255), nullable=False),
        sa.Column("latitude", sa.Float(), nullable=False),
        sa.Column("longitude", sa.Float(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("address"),
    )
    op.create_index("ix_buildings_coordinates", "buildings", ["latitude", "longitude"], unique=False)

    op.create_table(
        "activities",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("parent_id", sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(["parent_id"], ["activities.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("name", "parent_id", name="uq_activities_name_parent"),
    )
    op.create_index("ix_activities_name", "activities", ["name"], unique=False)
    op.create_index("ix_activities_parent_id", "activities", ["parent_id"], unique=False)

    op.create_table(
        "organizations",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("building_id", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["building_id"], ["buildings.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_organizations_name", "organizations", ["name"], unique=False)
    op.create_index("ix_organizations_building_id", "organizations", ["building_id"], unique=False)

    op.create_table(
        "organization_phones",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("organization_id", sa.Integer(), nullable=False),
        sa.Column("phone", sa.String(length=32), nullable=False),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_organization_phones_organization_id", "organization_phones", ["organization_id"], unique=False)
    op.create_index("ix_organization_phones_phone", "organization_phones", ["phone"], unique=False)

    op.create_table(
        "organization_activities",
        sa.Column("organization_id", sa.Integer(), nullable=False),
        sa.Column("activity_id", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["activity_id"], ["activities.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("organization_id", "activity_id"),
    )
    op.create_index("ix_organization_activities_activity_id", "organization_activities", ["activity_id"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_organization_activities_activity_id", table_name="organization_activities")
    op.drop_table("organization_activities")
    op.drop_index("ix_organization_phones_phone", table_name="organization_phones")
    op.drop_index("ix_organization_phones_organization_id", table_name="organization_phones")
    op.drop_table("organization_phones")
    op.drop_index("ix_organizations_building_id", table_name="organizations")
    op.drop_index("ix_organizations_name", table_name="organizations")
    op.drop_table("organizations")
    op.drop_index("ix_activities_parent_id", table_name="activities")
    op.drop_index("ix_activities_name", table_name="activities")
    op.drop_table("activities")
    op.drop_index("ix_buildings_coordinates", table_name="buildings")
    op.drop_table("buildings")
