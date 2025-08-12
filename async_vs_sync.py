import asyncio
import time

import requests
import aiohttp


def run_sync(num_requests: int, url: str):
    """Run HTTP requests one by one (synchronous)."""
    print("Running sync requests...")
    start_time = time.time()
    
    for i in range(num_requests):
        response = requests.get(url)
        print(f"Sync request {i+1}/{num_requests}: {response.status_code}")
    
    elapsed_time = time.time() - start_time
    return elapsed_time


async def fetch_one(session, url, request_num, total_requests):
    """Fetch one URL asynchronously."""
    async with session.get(url) as response:
        print(f"Async request {request_num}/{total_requests}: {response.status}")
        return response.status


async def run_async(num_requests: int, url: str):
    """Run HTTP requests all at once (asynchronous)."""
    print("Running async requests...")
    start_time = time.time()
    
    async with aiohttp.ClientSession() as session:
        # Create all tasks at once
        tasks = []
        for i in range(num_requests):
            task = fetch_one(session, url, i+1, num_requests)
            tasks.append(task)
        
        # Run all tasks concurrently
        await asyncio.gather(*tasks)
    
    elapsed_time = time.time() - start_time
    return elapsed_time


def main():
    # Simple settings - you can change these
    num_requests = 10
    url = "https://httpbin.org/delay/1"  # This URL waits 1 second before responding
    
    print(f"Making {num_requests} requests to: {url}")
    print("=" * 50)
    
    # Run synchronous version
    sync_time = run_sync(num_requests, url)
    print(f"\nSync total time: {sync_time:.2f} seconds")
    
    print("\n" + "=" * 50)
    
    # Run asynchronous version
    async_time = asyncio.run(run_async(num_requests, url))
    print(f"\nAsync total time: {async_time:.2f} seconds")
    
    # Show the speedup
    speedup = sync_time / async_time
    print(f"\nSpeedup: {speedup:.1f}x faster with async!")


if __name__ == "__main__":
    main()