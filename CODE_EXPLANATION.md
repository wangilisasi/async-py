# Code Explanation - Async vs Sync Demo

## What this code does
Shows how **async** (doing many things at once) is much faster than **sync** (doing one thing at a time) when making HTTP requests.

- **Sync**: Uses `requests` to make HTTP calls one after another
- **Async**: Uses `aiohttp` to make all HTTP calls at the same time
- **Test URL**: `https://httpbin.org/delay/1` - a special URL that waits 1 second before responding

## How the code works

### Settings (in `main()`)
```python
num_requests = 10  # How many requests to make
url = "https://httpbin.org/delay/1"  # URL that waits 1 second
```

### Sync version (`run_sync()`)
```python
def run_sync(num_requests: int, url: str):
    for i in range(num_requests):
        response = requests.get(url)  # Wait for this to finish...
        print(f"Request {i+1} done")   # ...then move to next one
```
- Makes requests **one at a time**
- Must wait for each request to finish before starting the next
- Total time ≈ `num_requests × 1 second` = 10 seconds for 10 requests

### Async version (`run_async()`)
```python
async def run_async(num_requests: int, url: str):
    async with aiohttp.ClientSession() as session:
        tasks = []
        for i in range(num_requests):
            task = fetch_one(session, url, i+1, num_requests)
            tasks.append(task)  # Create all tasks...
        
        await asyncio.gather(*tasks)  # ...then run them all at once!
```
- Creates **all requests at once**
- All requests happen simultaneously (concurrently)
- Total time ≈ `1 second` (since they all run together)

### Helper function (`fetch_one()`)
```python
async def fetch_one(session, url, request_num, total_requests):
    async with session.get(url) as response:
        print(f"Async request {request_num} done")
        return response.status
```
- Handles one async request
- The `async`/`await` keywords make it non-blocking

## Why async is faster
- **Sync**: Request 1 → wait 1s → Request 2 → wait 1s → Request 3 → wait 1s...
- **Async**: All requests start → all wait 1s together → all finish together

Think of it like:
- **Sync**: Washing dishes one at a time (wash → dry → put away → repeat)
- **Async**: Starting to wash all dishes, then drying them all, then putting them all away

## Key concepts for beginners
1. **`async def`**: Creates a function that can be paused and resumed
2. **`await`**: Pauses the function until something finishes (like a request)
3. **`asyncio.gather()`**: Runs multiple async functions at the same time
4. **Tasks**: Individual pieces of work that can run concurrently

## Try changing these
- Change `num_requests` to 5 or 20
- Change the URL to `https://httpbin.org/delay/2` for 2-second delays
- Notice how sync time changes but async time stays roughly the same!

## When to use async
- **Good for**: Web requests, file I/O, database calls (waiting for things)
- **Not good for**: Math calculations, image processing (CPU-heavy work)