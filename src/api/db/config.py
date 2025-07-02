from decouple import config as decouple_config

DATABASE_URL = "postgresql+psycopg://db_user:db_password@db_service:5432/dreamersunited_db"
#decouple_config("DATABASE_URL")