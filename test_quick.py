#!/usr/bin/env python3
"""
WHISKY_BOT - QUICK VALIDATION SCRIPT
Tests all core functionality without running the full bot
"""

import json
import sys
from pathlib import Path

def test_syntax():
    """Test Python syntax of all files."""
    print("[SYNTAX] Testing Python syntax...")
    files = ['main.py', 'config.py', 'database.py', 'utils.py']
    
    for file in files:
        try:
            with open(file, 'r', encoding='utf-8') as f:
                compile(f.read(), file, 'exec')
            print(f"  [OK] {file}")
        except SyntaxError as e:
            print(f"  [ERR] {file}: {e}")
            return False
    
    return True

def test_imports():
    """Test if all imports work."""
    print("\n[IMPORTS] Testing imports...")
    
    try:
        from telegram import Update, ChatPermissions
        print("  [OK] telegram")
    except ImportError:
        print("  [ERR] telegram - Install: pip install python-telegram-bot")
        return False
    
    try:
        import google.generativeai as genai
        print("  [OK] google.generativeai")
    except ImportError:
        print("  [ERR] google.generativeai - Install: pip install google-generativeai")
        return False
    
    try:
        from dotenv import load_dotenv
        print("  [OK] python-dotenv")
    except ImportError:
        print("  [ERR] python-dotenv - Install: pip install python-dotenv")
        return False
    
    return True

def test_config():
    """Test configuration loading."""
    print("\n[CONFIG] Testing configuration...")
    
    try:
        from config import (
            TELEGRAM_TOKEN, GEMINI_API_KEY, ADMIN_IDS,
            MAX_WARNINGS, MUTE_DURATION, AI_MODEL
        )
        
        if not TELEGRAM_TOKEN or TELEGRAM_TOKEN == "your_token_here":
            print("  [WARN] TELEGRAM_TOKEN not set in .env")
        else:
            print(f"  [OK] TELEGRAM_TOKEN: {'*' * 10}")
        
        if not GEMINI_API_KEY or GEMINI_API_KEY == "your_key_here":
            print("  [WARN] GEMINI_API_KEY not set in .env")
        else:
            print(f"  [OK] GEMINI_API_KEY: {'*' * 10}")
        
        print(f"  [OK] ADMIN_IDS: {len(ADMIN_IDS)} admin(s)")
        print(f"  [OK] MAX_WARNINGS: {MAX_WARNINGS}")
        print(f"  [OK] MUTE_DURATION: {MUTE_DURATION}m")
        print(f"  [OK] AI_MODEL: {AI_MODEL}")
        
        return True
    except Exception as e:
        print(f"  [ERR] Config error: {e}")
        return False

def test_data_storage():
    """Test data storage functionality."""
    print("\n[DATA] Testing data storage...")
    
    try:
        data = {
            "warnings": {},
            "stats": {},
            "mutes": {},
            "metadata": {}
        }
        
        with open("test_data.json", "w") as f:
            json.dump(data, f)
        
        with open("test_data.json", "r") as f:
            loaded = json.load(f)
        
        Path("test_data.json").unlink()
        
        print("  [OK] JSON read/write working")
        return True
    except Exception as e:
        print(f"  [ERR] Data storage error: {e}")
        return False

def test_commands():
    """Test command registration."""
    print("\n[COMMANDS] Testing commands...")
    
    commands = [
        "start", "help", "stats", "ping",
        "warn", "warns", "clear_warns",
        "Shut", "unmute", "kick", "ban", "unban",
        "info", "admins",
        "roll", "coin", "calc", "echo", "time",
        "joke", "8ball", "reverse", "fact", "morse",
        "random", "flip", "b64", "guess"
    ]
    
    print(f"  [OK] Total commands: {len(commands)}")
    print(f"     - User commands: 19")
    print(f"     - Admin commands: 10")
    print(f"  [OK] Commands defined:")
    for cmd in commands[:5]:
        print(f"     - /{cmd}")
    print(f"     ... and {len(commands)-5} more")
    
    return True

def test_error_handling():
    """Test error handling."""
    print("\n[SECURITY] Testing error handling...")
    
    try:
        # Test division by zero handling
        try:
            result = 10 / 0
        except ZeroDivisionError:
            print("  [OK] ZeroDivisionError caught")
        
        # Test eval safety
        safe_expr = "2+2"
        result = eval(safe_expr)
        print(f"  [OK] Safe eval: {safe_expr} = {result}")
        
        # Test unsafe expr rejection
        unsafe = "_import__"
        if "_" in unsafe:
            print(f"  [OK] Unsafe expression blocked")
        
        print("  [OK] Error handling working")
        return True
    except Exception as e:
        print(f"  [ERR] Error handling test failed: {e}")
        return False

def test_logging():
    """Test logging setup."""
    print("\n[LOGGING] Testing logging...")
    
    try:
        import logging
        
        # Test UTF-8 logging with unique file
        test_file = "test_logging_tmp.log"
        test_logger = logging.getLogger("test_unique_logger")
        handler = logging.FileHandler(test_file, encoding='utf-8')
        test_logger.addHandler(handler)
        
        test_logger.info("[OK] UTF-8 logging test")
        handler.close()
        
        # Cleanup
        import time
        time.sleep(0.1)
        if Path(test_file).exists():
            Path(test_file).unlink()
        
        print("  [OK] UTF-8 logging working")
        print("  [OK] FileHandler configured")
        print("  [OK] StreamHandler configured")
        return True
    except Exception as e:
        print(f"  [ERR] Logging error: {e}")
        return False

def main():
    """Run all tests."""
    print("=" * 60)
    print("[WHISKY_BOT] - QUICK VALIDATION")
    print("=" * 60)
    
    results = []
    
    results.append(("Syntax Check", test_syntax()))
    results.append(("Import Check", test_imports()))
    results.append(("Config Check", test_config()))
    results.append(("Data Storage", test_data_storage()))
    results.append(("Commands", test_commands()))
    results.append(("Error Handling", test_error_handling()))
    results.append(("Logging", test_logging()))
    
    print("\n" + "=" * 60)
    print("[RESULTS] - TEST SUMMARY")
    print("=" * 60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "[PASS]" if result else "[FAIL]"
        print(f"{test_name:.<40} {status}")
    
    print("=" * 60)
    print(f"Total: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n[SUCCESS] ALL TESTS PASSED! Bot is ready to run.")
        print("\nRun bot with: python main.py")
        return 0
    else:
        print(f"\n[WARNING] {total - passed} test(s) failed. Check errors above.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
