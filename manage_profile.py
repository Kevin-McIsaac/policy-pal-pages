import asyncio
from crawl4ai import BrowserProfiler, AsyncWebCrawler, BrowserConfig

# Define a function to use a profile for crawling
async def crawl_with_profile(profile_path, url):
    browser_config = BrowserConfig(
        headless=True,
        use_managed_browser=True,
        user_data_dir=profile_path
    )

    async with AsyncWebCrawler(config=browser_config) as crawler:
        result = await crawler.arun(url)
        print(result)
14

async def main():
    # Create a profiler instance
    profiler = BrowserProfiler()

    # Launch the interactive profile manager
    # Passing the crawl function as a callback adds a "crawl with profile" option
    await profiler.interactive_manager(crawl_callback=crawl_with_profile)

asyncio.run(main())

