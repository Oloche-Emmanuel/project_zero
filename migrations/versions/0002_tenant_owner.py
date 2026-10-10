"""tenant owner

Adds tenants.owner_id so tenant records are scoped to the landlord who
manages them. Existing tenants are backfilled from their leases (the owner
of the property they lease in); tenants with no lease stay unowned and are
visible to admins only.

Revision ID: 0002
Revises: 0001
Create Date: 2026-10-10 03:01:41.933053

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '0002'
down_revision: Union[str, None] = '0001'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table('tenants', schema=None) as batch_op:
        batch_op.add_column(sa.Column('owner_id', sa.Integer(), nullable=True))
        batch_op.create_index(batch_op.f('ix_tenants_owner_id'), ['owner_id'], unique=False)
        batch_op.create_foreign_key('fk_tenants_owner_id_users', 'users', ['owner_id'], ['id'])

    op.execute(
        """
        UPDATE tenants SET owner_id = (
            SELECT MIN(properties.owner_id)
            FROM leases
            JOIN units ON units.id = leases.unit_id
            JOIN properties ON properties.id = units.property_id
            WHERE leases.tenant_id = tenants.id
        )
        WHERE owner_id IS NULL
        """
    )


def downgrade() -> None:
    with op.batch_alter_table('tenants', schema=None) as batch_op:
        batch_op.drop_constraint('fk_tenants_owner_id_users', type_='foreignkey')
        batch_op.drop_index(batch_op.f('ix_tenants_owner_id'))
        batch_op.drop_column('owner_id')
