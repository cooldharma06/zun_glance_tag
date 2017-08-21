# Licensed under the Apache License, Version 2.0 (the "License");
#    you may not use this file except in compliance with the License.
#    You may obtain a copy of the License at
#
#        http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS,
#    WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#    See the License for the specific language governing permissions and
#    limitations under the License.

"""Add image_tag support - zun create

Revision ID: 5056c495abc2
Revises: 945569b3669f
Create Date: 2017-08-31 18:30:20.869495

"""

# revision identifiers, used by Alembic.
revision = '5056c495abc2'
down_revision = '945569b3669f'
branch_labels = None
depends_on = None

from alembic import op
import sqlalchemy as sa

import zun


def upgrade():
    op.add_column('container',
                  sa.Column('image_tag',
                            zun.db.sqlalchemy.models.JSONEncodedList(),
                            nullable=True))
