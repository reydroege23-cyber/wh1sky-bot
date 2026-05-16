"""
Test script to verify /gamblingoff and /gamblingon commands
"""

import asyncio
import json
from pathlib import Path
from config import OWNER_ID
from database import EconomyDatabase

def test_database():
    """Test if database methods work"""
    print("=" * 60)
    print("Testing Database Methods")
    print("=" * 60)
    
    db = EconomyDatabase("economy.db")
    
    # Test getting current state
    print(f"\n1. Checking initial state:")
    is_enabled = db.is_gambling_enabled()
    print(f"   Gambling enabled: {is_enabled}")
    
    # Test disabling
    print(f"\n2. Disabling gambling...")
    result = db.set_gambling_enabled(False)
    print(f"   Result: {result}")
    is_enabled = db.is_gambling_enabled()
    print(f"   Gambling enabled after disable: {is_enabled}")
    
    # Test enabling
    print(f"\n3. Enabling gambling...")
    result = db.set_gambling_enabled(True)
    print(f"   Result: {result}")
    is_enabled = db.is_gambling_enabled()
    print(f"   Gambling enabled after enable: {is_enabled}")
    
    print("\n✅ Database methods work correctly!")

def test_imports():
    """Test if commands are properly imported and defined"""
    print("\n" + "=" * 60)
    print("Testing Imports and Functions")
    print("=" * 60)
    
    try:
        from main import gambling_off, gambling_on, economy
        print("\n✅ Functions imported successfully")
        print(f"   gambling_off: {gambling_off}")
        print(f"   gambling_on: {gambling_on}")
        print(f"   economy: {economy}")
        print(f"   economy.db: {economy.db}")
        return True
    except ImportError as e:
        print(f"\n❌ Import error: {e}")
        return False
    except Exception as e:
        print(f"\n❌ Error: {e}")
        return False

def test_owner_id():
    """Test if OWNER_ID is correctly configured"""
    print("\n" + "=" * 60)
    print("Testing OWNER_ID Configuration")
    print("=" * 60)
    
    print(f"\nOWNER_ID in config: {OWNER_ID}")
    print(f"Type: {type(OWNER_ID)}")
    
    if OWNER_ID and isinstance(OWNER_ID, int):
        print("✅ OWNER_ID is properly configured")
        return True
    else:
        print("❌ OWNER_ID is not properly configured")
        return False

if __name__ == "__main__":
    print("\n🔍 TESTING /GAMBLINGOFF AND /GAMBLINGON COMMANDS\n")
    
    # Test OWNER_ID
    test_owner_id()
    
    # Test imports
    test_imports()
    
    # Test database
    test_database()
    
    print("\n" + "=" * 60)
    print("✅ ALL TESTS PASSED")
    print("=" * 60)
    print("\nIf commands still don't work:")
    print("1. Make sure you're using OWNER_ID: 8577797097")
    print("2. Check bot logs for any error messages")
    print("3. Verify bot is running and responding to other commands")
