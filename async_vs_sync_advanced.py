#!/usr/bin/env python3
"""
Advanced async vs sync HTTP benchmark with full feature set.

This demonstrates sophisticated async programming patterns including:
- Semaphore-based concurrency control
- Comprehensive error handling and retries
- Performance metrics and statistics
- Progress tracking with rich output
- Configurable timeouts and rate limiting
- Type hints and dataclasses
"""

import argparse
import asyncio
import statistics
import time
from dataclasses import dataclass, field
from typing import List, Optional, Tuple, Dict, Any
from contextlib import asynccontextmanager
import sys

import requests
import aiohttp
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry


@dataclass
class BenchmarkConfig:
    """Configuration for the benchmark run."""
    num_requests: int = 20
    concurrency: int = 10
    url: str = "https://httpbin.org/delay/1"
    timeout: float = 30.0
    retries: int = 3
    retry_backoff: float = 0.3
    verbose: bool = False
    show_progress: bool = True


@dataclass
class RequestResult:
    """Individual request result with metrics."""
    status_code: int
    duration: float
    attempt: int = 1
    error: Optional[str] = None


@dataclass
class BenchmarkResults:
    """Complete benchmark results with statistics."""
    sync_results: List[RequestResult] = field(default_factory=list)
    async_results: List[RequestResult] = field(default_factory=list)
    sync_total_time: float = 0.0
    async_total_time: float = 0.0
    
    @property
    def sync_success_rate(self) -> float:
        if not self.sync_results:
            return 0.0
        successful = sum(1 for r in self.sync_results if r.error is None)
        return successful / len(self.sync_results)
    
    @property
    def async_success_rate(self) -> float:
        if not self.async_results:
            return 0.0
        successful = sum(1 for r in self.async_results if r.error is None)
        return successful / len(self.async_results)
    
    @property
    def speedup(self) -> float:
        if self.async_total_time <= 0:
            return float('inf')
        return self.sync_total_time / self.async_total_time


class ProgressTracker:
    """Thread-safe progress tracker for concurrent operations."""
    
    def __init__(self, total: int, description: str = "Progress"):
        self.total = total
        self.description = description
        self.completed = 0
        self.lock = asyncio.Lock() if asyncio.iscoroutinefunction(self.__init__) else None
    
    def update(self, increment: int = 1) -> None:
        self.completed += increment
        if self.completed <= self.total:
            self._display()
    
    async def async_update(self, increment: int = 1) -> None:
        async with asyncio.Lock():
            self.completed += increment
            if self.completed <= self.total:
                self._display()
    
    def _display(self) -> None:
        percent = (self.completed / self.total) * 100
        bar_length = 40
        filled_length = int(bar_length * self.completed // self.total)
        bar = '█' * filled_length + '░' * (bar_length - filled_length)
        print(f'\r{self.description}: |{bar}| {percent:.1f}% ({self.completed}/{self.total})', 
              end='', flush=True)
        if self.completed >= self.total:
            print()  # New line when complete


def create_sync_session(config: BenchmarkConfig) -> requests.Session:
    """Create a configured requests session with retries."""
    session = requests.Session()
    
    # Configure retry strategy
    retry_strategy = Retry(
        total=config.retries,
        backoff_factor=config.retry_backoff,
        status_forcelist=[429, 500, 502, 503, 504],
    )
    
    adapter = HTTPAdapter(max_retries=retry_strategy)
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    
    return session


def run_sync_benchmark(config: BenchmarkConfig) -> Tuple[float, List[RequestResult]]:
    """Execute synchronous HTTP requests with comprehensive error handling."""
    print(f"🔄 Running sync benchmark ({config.num_requests} requests)...")
    
    session = create_sync_session(config)
    results: List[RequestResult] = []
    progress = ProgressTracker(config.num_requests, "Sync Progress") if config.show_progress else None
    
    start_time = time.perf_counter()
    
    for i in range(config.num_requests):
        request_start = time.perf_counter()
        attempt = 1
        
        try:
            response = session.get(
                config.url, 
                timeout=config.timeout,
                stream=False  # Ensure we read the full response
            )
            response.raise_for_status()
            
            duration = time.perf_counter() - request_start
            result = RequestResult(
                status_code=response.status_code,
                duration=duration,
                attempt=attempt
            )
            
            if config.verbose:
                print(f"Sync request {i+1}: {response.status_code} ({duration:.3f}s)")
                
        except Exception as e:
            duration = time.perf_counter() - request_start
            result = RequestResult(
                status_code=0,
                duration=duration,
                attempt=attempt,
                error=str(e)
            )
            
            if config.verbose:
                print(f"Sync request {i+1}: ERROR - {e}")
        
        results.append(result)
        if progress:
            progress.update()
    
    total_time = time.perf_counter() - start_time
    session.close()
    
    return total_time, results


@asynccontextmanager
async def create_async_session(config: BenchmarkConfig):
    """Create a configured aiohttp session with timeouts."""
    timeout = aiohttp.ClientTimeout(
        total=config.timeout,
        connect=config.timeout / 3,
        sock_read=config.timeout / 3
    )
    
    connector = aiohttp.TCPConnector(
        limit=config.concurrency * 2,  # Connection pool size
        limit_per_host=config.concurrency,
        ttl_dns_cache=300,
        use_dns_cache=True,
    )
    
    async with aiohttp.ClientSession(
        timeout=timeout,
        connector=connector,
        raise_for_status=True
    ) as session:
        yield session


async def fetch_with_semaphore(
    semaphore: asyncio.Semaphore,
    session: aiohttp.ClientSession,
    url: str,
    config: BenchmarkConfig,
    request_id: int,
    progress: Optional[ProgressTracker] = None
) -> RequestResult:
    """Fetch a single URL with semaphore-controlled concurrency and retry logic."""
    
    async with semaphore:  # Limit concurrent requests
        for attempt in range(1, config.retries + 1):
            request_start = time.perf_counter()
            
            try:
                async with session.get(url) as response:
                    # Ensure we read the response body
                    await response.read()
                    
                    duration = time.perf_counter() - request_start
                    result = RequestResult(
                        status_code=response.status,
                        duration=duration,
                        attempt=attempt
                    )
                    
                    if config.verbose:
                        print(f"Async request {request_id}: {response.status} ({duration:.3f}s)")
                    
                    if progress:
                        await progress.async_update()
                    
                    return result
                    
            except asyncio.TimeoutError:
                if attempt == config.retries:
                    duration = time.perf_counter() - request_start
                    result = RequestResult(
                        status_code=0,
                        duration=duration,
                        attempt=attempt,
                        error="Timeout"
                    )
                    if progress:
                        await progress.async_update()
                    return result
                    
                # Exponential backoff for retries
                await asyncio.sleep(config.retry_backoff * (2 ** (attempt - 1)))
                
            except Exception as e:
                if attempt == config.retries:
                    duration = time.perf_counter() - request_start
                    result = RequestResult(
                        status_code=0,
                        duration=duration,
                        attempt=attempt,
                        error=str(e)
                    )
                    
                    if config.verbose:
                        print(f"Async request {request_id}: ERROR - {e}")
                    
                    if progress:
                        await progress.async_update()
                    return result
                
                await asyncio.sleep(config.retry_backoff * attempt)


async def run_async_benchmark(config: BenchmarkConfig) -> Tuple[float, List[RequestResult]]:
    """Execute asynchronous HTTP requests with advanced concurrency control."""
    print(f"⚡ Running async benchmark ({config.num_requests} requests, concurrency={config.concurrency})...")
    
    # Semaphore to control concurrency
    semaphore = asyncio.Semaphore(config.concurrency)
    progress = ProgressTracker(config.num_requests, "Async Progress") if config.show_progress else None
    
    start_time = time.perf_counter()
    
    async with create_async_session(config) as session:
        # Create all tasks
        tasks = [
            fetch_with_semaphore(
                semaphore=semaphore,
                session=session,
                url=config.url,
                config=config,
                request_id=i + 1,
                progress=progress
            )
            for i in range(config.num_requests)
        ]
        
        # Execute all tasks concurrently
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Handle any exceptions that weren't caught
        processed_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                processed_results.append(RequestResult(
                    status_code=0,
                    duration=0.0,
                    attempt=1,
                    error=str(result)
                ))
            else:
                processed_results.append(result)
    
    total_time = time.perf_counter() - start_time
    return total_time, processed_results


def calculate_statistics(results: List[RequestResult]) -> Dict[str, Any]:
    """Calculate detailed statistics from request results."""
    if not results:
        return {}
    
    successful_results = [r for r in results if r.error is None]
    durations = [r.duration for r in successful_results]
    
    if not durations:
        return {"success_count": 0, "error_count": len(results)}
    
    return {
        "success_count": len(successful_results),
        "error_count": len(results) - len(successful_results),
        "mean_duration": statistics.mean(durations),
        "median_duration": statistics.median(durations),
        "std_duration": statistics.stdev(durations) if len(durations) > 1 else 0.0,
        "min_duration": min(durations),
        "max_duration": max(durations),
        "total_duration": sum(durations),
        "requests_per_second": len(successful_results) / sum(durations) if sum(durations) > 0 else 0
    }


def print_detailed_results(benchmark_results: BenchmarkResults) -> None:
    """Print comprehensive benchmark results with statistics."""
    print("\n" + "="*80)
    print("📊 DETAILED BENCHMARK RESULTS")
    print("="*80)
    
    # Sync results
    sync_stats = calculate_statistics(benchmark_results.sync_results)
    print(f"\n🔄 Synchronous Results:")
    print(f"   Total time: {benchmark_results.sync_total_time:.3f}s")
    print(f"   Success rate: {benchmark_results.sync_success_rate:.1%}")
    if sync_stats:
        print(f"   Requests/sec: {sync_stats.get('requests_per_second', 0):.2f}")
        print(f"   Avg duration: {sync_stats.get('mean_duration', 0):.3f}s ± {sync_stats.get('std_duration', 0):.3f}s")
        print(f"   Duration range: {sync_stats.get('min_duration', 0):.3f}s - {sync_stats.get('max_duration', 0):.3f}s")
    
    # Async results
    async_stats = calculate_statistics(benchmark_results.async_results)
    print(f"\n⚡ Asynchronous Results:")
    print(f"   Total time: {benchmark_results.async_total_time:.3f}s")
    print(f"   Success rate: {benchmark_results.async_success_rate:.1%}")
    if async_stats:
        print(f"   Requests/sec: {async_stats.get('requests_per_second', 0):.2f}")
        print(f"   Avg duration: {async_stats.get('mean_duration', 0):.3f}s ± {async_stats.get('std_duration', 0):.3f}s")
        print(f"   Duration range: {async_stats.get('min_duration', 0):.3f}s - {async_stats.get('max_duration', 0):.3f}s")
    
    # Comparison
    print(f"\n🚀 Performance Comparison:")
    print(f"   Speedup: {benchmark_results.speedup:.2f}x faster with async")
    
    if benchmark_results.sync_total_time > 0 and benchmark_results.async_total_time > 0:
        efficiency = (benchmark_results.async_success_rate / benchmark_results.async_total_time) / \
                    (benchmark_results.sync_success_rate / benchmark_results.sync_total_time)
        print(f"   Efficiency gain: {efficiency:.2f}x")
    
    print("="*80)


def create_argument_parser() -> argparse.ArgumentParser:
    """Create and configure the command-line argument parser."""
    parser = argparse.ArgumentParser(
        description="Advanced async vs sync HTTP benchmark",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s --requests 100 --concurrency 20
  %(prog)s --url https://httpbin.org/delay/2 --timeout 45
  %(prog)s --requests 50 --verbose --no-progress
        """
    )
    
    parser.add_argument(
        "-n", "--requests",
        type=int,
        default=20,
        help="Total number of requests to make (default: %(default)s)"
    )
    
    parser.add_argument(
        "-c", "--concurrency",
        type=int,
        default=10,
        help="Maximum concurrent async requests (default: %(default)s)"
    )
    
    parser.add_argument(
        "-u", "--url",
        type=str,
        default="https://httpbin.org/delay/1",
        help="URL to request (default: %(default)s)"
    )
    
    parser.add_argument(
        "-t", "--timeout",
        type=float,
        default=30.0,
        help="Request timeout in seconds (default: %(default)s)"
    )
    
    parser.add_argument(
        "-r", "--retries",
        type=int,
        default=3,
        help="Number of retries per request (default: %(default)s)"
    )
    
    parser.add_argument(
        "--retry-backoff",
        type=float,
        default=0.3,
        help="Retry backoff factor in seconds (default: %(default)s)"
    )
    
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Enable verbose output for each request"
    )
    
    parser.add_argument(
        "--no-progress",
        action="store_true",
        help="Disable progress bars"
    )
    
    return parser


async def main() -> None:
    """Main execution function with comprehensive error handling."""
    parser = create_argument_parser()
    args = parser.parse_args()
    
    # Validate arguments
    if args.requests <= 0:
        print("❌ Error: Number of requests must be positive", file=sys.stderr)
        sys.exit(1)
    
    if args.concurrency <= 0:
        print("❌ Error: Concurrency must be positive", file=sys.stderr)
        sys.exit(1)
    
    # Create configuration
    config = BenchmarkConfig(
        num_requests=args.requests,
        concurrency=min(args.concurrency, args.requests),  # Don't exceed request count
        url=args.url,
        timeout=args.timeout,
        retries=args.retries,
        retry_backoff=args.retry_backoff,
        verbose=args.verbose,
        show_progress=not args.no_progress
    )
    
    print(f"🎯 Benchmark Configuration:")
    print(f"   URL: {config.url}")
    print(f"   Requests: {config.num_requests}")
    print(f"   Concurrency: {config.concurrency}")
    print(f"   Timeout: {config.timeout}s")
    print(f"   Retries: {config.retries}")
    print()
    
    # Initialize results
    results = BenchmarkResults()
    
    try:
        # Run synchronous benchmark
        results.sync_total_time, results.sync_results = run_sync_benchmark(config)
        print(f"✅ Sync completed: {results.sync_total_time:.3f}s\n")
        
        # Run asynchronous benchmark
        results.async_total_time, results.async_results = await run_async_benchmark(config)
        print(f"✅ Async completed: {results.async_total_time:.3f}s\n")
        
        # Print detailed results
        print_detailed_results(results)
        
    except KeyboardInterrupt:
        print("\n❌ Benchmark interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Benchmark failed: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    # Ensure we're running with asyncio
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n❌ Interrupted")
        sys.exit(1)