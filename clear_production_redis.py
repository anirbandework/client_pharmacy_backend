#!/usr/bin/env python3
"""
Production Redis Cache Cleaner
Clears all Redis rate limit cache on Railway production
"""

import redis
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def clear_production_redis():
    """Clear production Redis cache"""
    try:
        # Get Redis URL from environment
        redis_url = os.getenv('REDIS_URL')
        
        if not redis_url:
            print("❌ REDIS_URL not found in .env file")
            return
        
        print(f"🔗 Connecting to Redis...")
        
        # Connect to Redis
        r = redis.from_url(redis_url, decode_responses=True)
        
        # Test connection
        r.ping()
        print("✅ Connected to Production Redis")
        
        # Get all rate limit keys
        all_keys = r.keys('rl:*')
        
        if not all_keys:
            print("ℹ️  No rate limit keys found in Redis cache")
            return
        
        print(f"🔍 Found {len(all_keys)} rate limit keys in cache")
        
        # Show key patterns
        key_patterns = {}
        for key in all_keys:
            # Extract pattern (e.g., rl:u, rl:ep, rl:org, rl:anon)
            parts = key.split(':')
            if len(parts) >= 2:
                pattern = f"{parts[0]}:{parts[1]}"
                key_patterns[pattern] = key_patterns.get(pattern, 0) + 1
        
        print("\n📊 Rate limit key breakdown:")
        for pattern, count in sorted(key_patterns.items()):
            pattern_name = {
                'rl:u': 'User rate limits',
                'rl:ep': 'Endpoint rate limits',
                'rl:org': 'Organization rate limits',
                'rl:anon': 'Anonymous rate limits',
                'rl:hf': 'High-frequency endpoint limits'
            }.get(pattern, pattern)
            print(f"   - {pattern_name}: {count} keys")
        
        # Clear all rate limit keys
        if all_keys:
            deleted = r.delete(*all_keys)
            print(f"\n🗑️  Deleted {deleted} rate limit keys from Redis cache")
        
        print("✅ Production Redis rate limit cache cleared successfully!")
        print("\nℹ️  Users can now make requests without hitting old rate limits.")
        
    except redis.ConnectionError as e:
        print(f"❌ Could not connect to Redis: {e}")
        print("Make sure REDIS_URL in .env is correct and Redis is accessible.")
    except Exception as e:
        print(f"❌ Error clearing Redis cache: {e}")

if __name__ == "__main__":
    print("\n" + "="*70)
    print("PRODUCTION REDIS CACHE CLEANER")
    print("="*70 + "\n")
    print("⚠️  This will clear all rate limit data from production Redis.")
    print("This is safe and will only reset rate limit counters.\n")
    
    response = input("Do you want to continue? (yes/no): ")
    
    if response.lower() in ['yes', 'y']:
        clear_production_redis()
    else:
        print("❌ Operation cancelled.")
