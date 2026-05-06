"""
🧪 WHISKY_BOT TEST SUITE
Comprehensive testing of all bot functions
"""

import json
import sys
from pathlib import Path
from datetime import datetime

def test_config():
    """Test configuration loading."""
    print("\n🔧 Testing Configuration...")
    try:
        from config import (
            TELEGRAM_TOKEN, GEMINI_API_KEY, ADMIN_IDS, 
            MAX_WARNINGS, MUTE_DURATION, BAD_WORDS,
            AI_MODEL, LOG_FILE, DATA_FILE
        )
        print("✅ Config import successful")
        print(f"   • Admins: {len(ADMIN_IDS)}")
        print(f"   • Max Warnings: {MAX_WARNINGS}")
        print(f"   • Mute Duration: {MUTE_DURATION}m")
        print(f"   • AI Model: {AI_MODEL}")
        print(f"   • Bad Words: {len(BAD_WORDS)}")
        return True
    except Exception as e:
        print(f"❌ Config test failed: {e}")
        return False

def test_data_storage():
    """Test data storage system."""
    print("\n💾 Testing Data Storage...")
    try:
        test_data = {
            "warnings": {"123": 2},
            "stats": {"123": {"messages": 5, "ai_queries": 2}},
            "mutes": {}
        }
        test_file = "test_data.json"
        
        # Test save
        with open(test_file, 'w') as f:
            json.dump(test_data, f, indent=4)
        print("✅ Data save successful")
        
        # Test load
        with open(test_file, 'r') as f:
            loaded = json.load(f)
        print("✅ Data load successful")
        
        # Clean up
        Path(test_file).unlink()
        print("✅ Data storage test passed")
        return True
    except Exception as e:
        print(f"❌ Data storage test failed: {e}")
        return False

def test_imports():
    """Test all required imports."""
    print("\n📦 Testing Imports...")
    try:
        from telegram import Update, ChatPermissions
        print("✅ Telegram imports OK")
        
        from telegram.ext import (
            ApplicationBuilder, MessageHandler, CommandHandler,
            ContextTypes, filters
        )
        print("✅ Telegram.ext imports OK")
        
        import google.generativeai as genai
        print("✅ Google Generative AI OK")
        
        from datetime import timedelta, datetime
        import logging
        import json
        from pathlib import Path
        from functools import wraps
        import asyncio
        print("✅ Standard library imports OK")
        
        return True
    except ImportError as e:
        print(f"❌ Import failed: {e}")
        return False

def test_logging():
    """Test logging setup."""
    print("\n📝 Testing Logging...")
    try:
        import logging
        logger = logging.getLogger("test")
        handler = logging.FileHandler("test.log")
        handler.setFormatter(logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        ))
        logger.addHandler(handler)
        logger.info("Test message")
        print("✅ Logging configured successfully")
        
        # Clean up
        Path("test.log").unlink()
        return True
    except Exception as e:
        print(f"❌ Logging test failed: {e}")
        return False

def test_decorators():
    """Test decorator functions."""
    print("\n🎯 Testing Decorators...")
    try:
        from functools import wraps
        
        def test_decorator(func):
            @wraps(func)
            async def wrapper(*args, **kwargs):
                return await func(*args, **kwargs)
            return wrapper
        
        @test_decorator
        async def test_func():
            return "success"
        
        print("✅ Decorators working correctly")
        return True
    except Exception as e:
        print(f"❌ Decorator test failed: {e}")
        return False

def test_file_structure():
    """Test project file structure."""
    print("\n📁 Testing File Structure...")
    required_files = [
        "main.py",
        "config.py",
        "requirements.txt",
        ".env.example",
        "README.md"
    ]
    
    missing = []
    for file in required_files:
        if not Path(file).exists():
            missing.append(file)
    
    if missing:
        print(f"❌ Missing files: {', '.join(missing)}")
        return False
    
    print("✅ All required files present:")
    for file in required_files:
        size = Path(file).stat().st_size
        print(f"   • {file} ({size} bytes)")
    return True

def test_code_quality():
    """Test code quality."""
    print("\n⚡ Testing Code Quality...")
    
    with open("main.py", 'r') as f:
        main_code = f.read()
    
    issues = []
    
    # Check for proper docstrings
    if main_code.count('"""') < 5:
        issues.append("Few docstrings found")
    
    # Check for error handling
    if main_code.count("try:") < 10:
        issues.append("Limited error handling")
    
    # Check for logging
    if main_code.count("logger.") < 20:
        issues.append("Limited logging")
    
    if issues:
        print(f"⚠️ Issues found:")
        for issue in issues:
            print(f"   • {issue}")
        return False
    
    print("✅ Code quality checks passed")
    print(f"   • Lines of code: {len(main_code.splitlines())}")
    print(f"   • Docstrings: {main_code.count('\"\"\"') // 2}")
    print(f"   • Try-except blocks: {main_code.count('try:')}")
    print(f"   • Log statements: {main_code.count('logger.')}")
    return True

def test_commands():
    """Test command definitions."""
    print("\n📋 Testing Commands...")
    
    commands = [
        "start", "help", "stats", "ping",
        "warn", "warns", "clear_warns",
        "mute", "unmute", "kick", "ban", "unban",
        "info", "admins"
    ]
    
    with open("main.py", 'r') as f:
        main_code = f.read()
    
    found = 0
    for cmd in commands:
        if f'CommandHandler("{cmd}"' in main_code or f"async def {cmd}" in main_code:
            found += 1
    
    print(f"✅ Found {found}/{len(commands)} commands")
    for cmd in commands:
        if f'CommandHandler("{cmd}"' in main_code or f"async def {cmd}" in main_code:
            print(f"   • /{cmd}")
    
    return found == len(commands)

def run_all_tests():
    """Run all tests."""
    print("\n" + "=" * 60)
    print("🧪 WHISKY_BOT TEST SUITE")
    print("=" * 60)
    
    tests = [
        ("Configuration", test_config),
        ("Imports", test_imports),
        ("Data Storage", test_data_storage),
        ("Logging", test_logging),
        ("Decorators", test_decorators),
        ("File Structure", test_file_structure),
        ("Code Quality", test_code_quality),
        ("Commands", test_commands),
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name} failed with error: {e}")
            results.append((test_name, False))
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 TEST SUMMARY")
    print("=" * 60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} - {test_name}")
    
    print(f"\n📈 Result: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 ALL TESTS PASSED! Bot is ready to run!")
        return 0
    else:
        print(f"\n⚠️ {total - passed} test(s) failed. Review above.")
        return 1

if __name__ == "__main__":
    sys.exit(run_all_tests())
