from decouple import Config, RepositoryEnv
import os

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
DOTENV_FILE = os.path.join(BASE_DIR, ".env")


config = Config(RepositoryEnv(DOTENV_FILE))


POSTGRES_USER: str = config("POSTGRES_USER", default="postgres")
POSTGRES_PASSWORD: str = config("POSTGRES_PASSWORD", default="password")
POSTGRES_HOST: str = config("POSTGRES_HOST", default="127.0.0.1")
POSTGRES_PORT: str = config("POSTGRES_PORT", default="5432")
POSTGRES_DB: str = config("POSTGRES_DB", default="apartment_rental")

DATABASE_URL: str = (
    f"postgresql+asyncpg://{POSTGRES_USER}:{POSTGRES_PASSWORD}"
    f"@{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}"
)

TELEGRAM_TOKEN = config("TELEGRAM_TOKEN")
BOT_EMAIL = config("BOT_EMAIL", default="default@example.com")
