#!/usr/bin/env python3
"""
Redis Cache Cleaner
Clears all Redis cache to resolve authentication issues
"""

import redis
import os

def clear_redis_cache():
    """Clear all Redis cache"""
    try:
        # Connect to Redis
        r = redis.from_url('redis://localhost:6379', decode_responses=True)
        
        # Test connection
        r.ping()
        print("✅ Connected to Redis")
        
        # Get all keys
        all_keys = r.keys('*')
        
        if not all_keys:
            print("ℹ️  No keys found in Redis cache")
            return
        
        print(f"🔍 Found {len(all_keys)} keys in cache:")
        
        # Show key patterns
        key_patterns = {}
        for key in all_keys:
            pattern = key.split(':')[0] if ':' in key else 'other'
            key_patterns[pattern] = key_patterns.get(pattern, 0) + 1
        
        for pattern, count in key_patterns.items():
            print(f"   - {pattern}: {count} keys")
        
        # Clear all keys
        if all_keys:
            deleted = r.delete(*all_keys)
            print(f"🗑️  Deleted {deleted} keys from Redis cache")
        
        print("✅ Redis cache cleared successfully!")
        
    except redis.ConnectionError:
        print("❌ Could not connect to Redis. Make sure Redis is running.")
    except Exception as e:
        print(f"❌ Error clearing Redis cache: {e}")

if __name__ == "__main__":
    clear_redis_cache()