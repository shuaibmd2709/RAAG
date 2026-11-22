import os
from dotenv import load_dotenv

load_dotenv()

ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
PARSER_MODEL = os.getenv("PARSER_MODEL", "claude-haiku-4-5")

EMBED_MODEL = os.getenv("EMBED_MODEL", "sentence-transformers/all-MiniLM-L6-v2")
CHROMA_DIR = os.getenv("CHROMA_DIR", "data/chroma")

PLANNER_MODEL = os.getenv("PLANNER_MODEL", PARSER_MODEL)

GENERATOR_MODEL = os.getenv("GENERATOR_MODEL", PARSER_MODEL)

ADMIN_KEY = os.getenv("ADMIN_KEY")
MAX_UPLOAD_MB = int(os.getenv("MAX_UPLOAD_MB", "5"))
DEFAULT_MENU = os.getenv("DEFAULT_MENU", "data/sample_menu.json")
RATE_LIMIT_PER_MIN = int(os.getenv("RATE_LIMIT_PER_MIN", "10"))
DAILY_ASK_CAP = int(os.getenv("DAILY_ASK_CAP", "300"))