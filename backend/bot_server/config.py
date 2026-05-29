import os
from pathlib import Path
from dotenv import load_dotenv

# Resolve .env at project root (3 levels up from this file)
_ENV_PATH = Path(__file__).parent.parent.parent / ".env"
load_dotenv(dotenv_path=_ENV_PATH, override=True)

# Zalo Configurations
ZALO_APP_ID          = os.getenv("ZALO_APP_ID")
ZALO_SECRET_KEY      = os.getenv("ZALO_SECRET_KEY")
ZALO_OA_ACCESS_TOKEN = os.getenv("ZALO_OA_ACCESS_TOKEN")

# Webhook URLs
WEBHOOK_URL      = os.getenv("WEBHOOK_URL")
N8N_WEBHOOK_URL  = os.getenv("N8N_WEBHOOK_URL")

# OpenAI
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Vector store path (relative to project root)
VECTOR_STORE_PATH = str(Path(__file__).parent.parent.parent / "data" / "vector_store")
