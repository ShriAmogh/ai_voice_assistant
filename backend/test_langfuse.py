import os
from dotenv import load_dotenv
from langfuse import Langfuse

load_dotenv()

print(f"Public Key: {os.getenv('LANGFUSE_PUBLIC_KEY')}")

try:
    langfuse = Langfuse()
    print("Langfuse initialized")
    
    trace = langfuse.trace(name="test_trace", user_id="test_user")
    print(f"Trace created: {trace.id}")
    
    trace.event(name="Test Event")
    print("Event added")
    
    langfuse.flush()
    print("Flushed successfully!")
except Exception as e:
    print(f"Error: {e}")
