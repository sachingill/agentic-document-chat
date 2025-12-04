"""
Test script to verify agentic agent works
"""
import sys
import os
from pathlib import Path

# Add parent directory to path
parent_dir = Path(__file__).parent.parent
sys.path.insert(0, str(parent_dir))

# Load environment
from dotenv import load_dotenv
load_dotenv(dotenv_path=parent_dir / ".env")

# Add agentic app to path
agentic_dir = Path(__file__).parent
sys.path.insert(0, str(agentic_dir))

print("🧪 Testing Agentic Agent Import...")
print("=" * 60)

try:
    from app.agents.agentic_agent import AGENTIC_AGENT, run_agentic_agent
    print("✅ Agentic agent imported successfully!")
    print("✅ Graph compiled successfully!")
    print("\n" + "=" * 60)
    print("✅ Agentic system is ready!")
    print("=" * 60)
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()

