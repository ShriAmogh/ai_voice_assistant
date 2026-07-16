import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# API Keys
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# Judge Configuration
JUDGE_MODEL = "gemini-2.5-flash"  # Change to gemini-2.5-pro if higher accuracy is needed

# Simulation Parameters
SIMULATION_LOOPS = 1
WEBSOCKET_URL = "ws://localhost:8001/ws"

# Evaluation Rubrics and Scores
PASS_VERDICT_THRESHOLD = 70.0
