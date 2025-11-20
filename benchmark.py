import asyncio
import aiohttp
import time
import argparse
import statistics

# Default configuration
DEFAULT_URL = "http://127.0.0.1:8000/triage"
DEFAULT_CONCURRENT_USERS = 10
DEFAULT_TOTAL_REQUESTS = 50

SAMPLE_PAYLOAD = {
    "description": "I cannot login to my account, getting error 500"
}

async def make_request(session, url, request_id):
    start_time = time.time()
    try:
        async with session.post(url, json=SAMPLE_PAYLOAD) as response:
            await response.text()
            status = response.status
    except Exception as e:
        status = "Error"
    
    end_time = time.time()
    duration = end_time - start_time
    return status, duration

async def run_benchmark(url, concurrent_users, total_requests):
    print(f"Starting benchmark against {url}")
    print(f"Concurrent Users: {concurrent_users}")
    print(f"Total Requests: {total_requests}")
    
    async with aiohttp.ClientSession() as session:
        tasks = []
        start_time = time.time()
        
        # We will run requests in batches of 'concurrent_users'
        # or just launch all and limit concurrency with a semaphore
        
        semaphore = asyncio.Semaphore(concurrent_users)
        
        async def bounded_request(idx):
            async with semaphore:
                return await make_request(session, url, idx)

        tasks = [bounded_request(i) for i in range(total_requests)]
        results = await asyncio.gather(*tasks)
        
        total_time = time.time() - start_time
        
    statuses = [r[0] for r in results]
    durations = [r[1] for r in results]
    
    success_count = statuses.count(200)
    error_count = len(statuses) - success_count
    
    print("\n--- Results ---")
    print(f"Total Time Taken: {total_time:.2f} seconds")
    print(f"Requests per Second: {total_requests / total_time:.2f}")
    print(f"Average Request Latency: {statistics.mean(durations):.4f} seconds")
    print(f"Median Request Latency: {statistics.median(durations):.4f} seconds")
    print(f"Max Request Latency: {max(durations):.4f} seconds")
    print(f"Successful Requests: {success_count}")
    print(f"Failed Requests: {error_count}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Benchmark Support Ticket Agent")
    parser.add_argument("--url", default=DEFAULT_URL, help="Target URL")
    parser.add_argument("--users", type=int, default=DEFAULT_CONCURRENT_USERS, help="Number of concurrent users")
    parser.add_argument("--requests", type=int, default=DEFAULT_TOTAL_REQUESTS, help="Total number of requests to send")
    
    args = parser.parse_args()
    
    asyncio.run(run_benchmark(args.url, args.users, args.requests))
