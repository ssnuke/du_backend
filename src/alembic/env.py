import sys
import os
from alembic import context
from sqlmodel import SQLModel

# Make project root importable
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, BASE_DIR)

# 🔴 IMPORT MODELS — THIS IS THE MOST IMPORTANT PART
from api.events.models import (
    IrIdModel,
    IrModel,
    TeamModel,
    TeamMemberLink,
    InfoDetailModel,
)

config = context.config

DATABASE_URL = os.getenv("DATABASE_URL")
if DATABASE_URL:
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)
    config.set_main_option("sqlalchemy.url", DATABASE_URL)

target_metadata = SQLModel.metadata