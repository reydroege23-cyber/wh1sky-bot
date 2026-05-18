#!/usr/bin/env python3
"""Quick diagnostic to find startup errors."""

import traceback
import sys

try:
    print("✅ Testing imports...")
    from main import setup_bot, TELEGRAM_TOKEN
    
    print("✅ Checking token...")
    if not TELEGRAM_TOKEN or TELEGRAM_TOKEN == "8771300086:AAHpos-PeRziKVr3za4XbMq0_MibJUVOznA":
        print("⚠️  WARNING: Using default/dummy token. Set TELEGRAM_TOKEN env var.")
    else:
        print("✅ Token is set")
    
    print("✅ Building bot...")
    app = setup_bot()
    print("✅ Bot setup successful!")
    print(f"✅ Bot app type: {type(app)}")
    print(f"✅ Ready to run_polling()")
    
except Exception as e:
    print(f"\n❌ ERROR FOUND:")
    print(f"   Type: {type(e).__name__}")
    print(f"   Message: {e}")
    print(f"\n📋 Full traceback:")
    traceback.print_exc()
    sys.exit(1)
