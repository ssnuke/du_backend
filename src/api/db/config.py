from decouple import config as decouple_config
import os

DATABASE_URL = os.getenv("DATABASE_URL")
# DATABASE_URL = decouple_config("DATABASE_URL")