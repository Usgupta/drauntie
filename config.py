"""Configuration file for API keys and settings.

This module loads environment variables and configures API clients.
All API keys should be stored in a .env file (not committed to git).

Required APIs:
    - Telegram Bot: For bot communication
    - Groq: Ultra-fast LLM inference
    - Gemini: Vision AI for lab report extraction
    - Mem0: Persistent health memory
    - Supabase: Database storage

Optional APIs:
    - fal.ai: Video generation (primary)
    - OpenAI: Video generation fallback
    - ElevenLabs: Audio generation fallback
"""
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# ==================== REQUIRED API KEYS ====================

# Telegram Bot Token (from @BotFather)
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

# Groq API Key (lightning-fast LLM inference)
# Get from: https://console.groq.com
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

# Google Gemini API Key (vision AI for lab reports)
# Get from: https://makersuite.google.com/app/apikey
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# Mem0 API Key (persistent health memory)
# Get from: https://app.mem0.ai
MEM0_API_KEY = os.getenv("MEM0_API_KEY")

# Supabase Configuration (database storage)
# Get from: https://supabase.com/dashboard
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

# ==================== OPTIONAL API KEYS ====================

# Fal.ai API Key (video generation - primary)
# Get from: https://fal.ai/dashboard
FAL_API_KEY = os.getenv("FAL_API_KEY")
FAL_KEY = os.getenv("FAL_KEY")  # fal_client library expects FAL_KEY

# OpenAI API Key (video generation fallback)
# Get from: https://platform.openai.com/api-keys
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# ElevenLabs API Key (audio generation fallback)
# Get from: https://elevenlabs.io/app/settings/api-keys
ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY")

# ==================== MODEL CONFIGURATION ====================

# Groq Model: Llama 3.3 70B (fastest, most capable)
GROQ_MODEL = "llama-3.3-70b-versatile"

# Gemini Model: 2.0 Flash Exp (optimized for speed)
GEMINI_MODEL = "gemini-2.0-flash-exp"

# ==================== VALIDATION ====================

# Required environment variables (bot won't work without these)
REQUIRED_VARS = [
    "TELEGRAM_BOT_TOKEN",
    "GROQ_API_KEY",
    "GEMINI_API_KEY",
    "MEM0_API_KEY",
    "SUPABASE_URL",
    "SUPABASE_KEY",
]

# Optional but recommended (for enhanced features)
OPTIONAL_VARS = [
    "FAL_API_KEY",
    "OPENAI_API_KEY",
    "ELEVENLABS_API_KEY",
]

# Check for missing required variables
missing_vars = [var for var in REQUIRED_VARS if not os.getenv(var)]
if missing_vars:
    print("\n" + "="*60)
    print("⚠️  CONFIGURATION ERROR")
    print("="*60)
    print(f"Missing required environment variables:")
    for var in missing_vars:
        print(f"  ❌ {var}")
    print("\n📝 TO FIX:")
    print("1. Copy env_template.txt to .env")
    print("2. Fill in all required API keys")
    print("3. Restart the bot")
    print("="*60 + "\n")

# Check for optional variables
missing_optional = [var for var in OPTIONAL_VARS if not os.getenv(var)]
if missing_optional:
    print(f"💡 Optional features disabled (missing: {', '.join(missing_optional)})")
    print("   Video/audio generation may not work without these keys.")

