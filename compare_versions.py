#!/usr/bin/env python3
"""
Quick demo to compare the simple vs advanced versions.
"""

print("🎯 Async vs Sync Comparison Demo")
print("=" * 50)

print("\n📝 You now have two versions:")
print("\n1️⃣  SIMPLE VERSION (async_vs_sync.py):")
print("   - Beginner-friendly")
print("   - No command-line arguments")
print("   - Basic error handling")
print("   - 10 requests, shows progress")
print("   - Just run: python async_vs_sync.py")

print("\n2️⃣  ADVANCED VERSION (async_vs_sync_advanced.py):")
print("   - Full-featured with all the bells and whistles")
print("   - Command-line arguments with argparse")
print("   - Semaphore concurrency control")
print("   - Comprehensive error handling & retries")
print("   - Progress bars and detailed statistics")
print("   - Type hints and dataclasses")
print("   - Connection pooling and timeouts")

print("\n🚀 Try the advanced version:")
print("   python async_vs_sync_advanced.py --help")
print("   python async_vs_sync_advanced.py -n 20 -c 5 --verbose")
print("   python async_vs_sync_advanced.py -u https://httpbin.org/delay/2 -n 30")

print("\n🎨 Advanced features include:")
print("   • Semaphore-controlled concurrency")
print("   • Exponential backoff retries")
print("   • Connection pooling")
print("   • Detailed performance statistics")
print("   • Progress tracking")
print("   • Request/response timing")
print("   • Success rate calculations")
print("   • Error categorization")

print("\n" + "=" * 50)