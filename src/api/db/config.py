from decouple import config as decouple_config

DATABASE_URL = decouple_config("DATABASE_URL")