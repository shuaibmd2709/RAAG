import os
from dotenv import load_dotenv

load_dotenv()

ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
PARSER_MODEL = os.getenv("PARSER_MODEL", "claude-haiku-4-5")