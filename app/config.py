import os
from dotenv import load_dotenv

load_dotenv()

ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
PARSER_MODEL = os.getenv("PARSER_MODEL", "claude-haiku-4-5")

EMBED_MODEL = os.getenv("EMBED_MODEL", "sentence-transformers/all-MiniLM-L6-v2")
CHROMA_DIR = os.getenv("CHROMA_DIR", "data/chroma")

PLANNER_MODEL = os.getenv("PLANNER_MODEL", PARSER_MODEL)