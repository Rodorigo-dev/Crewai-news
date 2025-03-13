import asyncio
from crawl4ai import AsyncWebCrawler

async def main():
    # Create an instance of AsyncWebCrawler
    async with AsyncWebCrawler() as crawler:
        # Run the crawler on a URL
        result = await crawler.arun(url="https://scholar.google.com/citations?user=lhl7mlAAAAAJ&hl=pt-BR&oi=ao")

        # Print the extracted content
        print(result.markdown)

# Run the async main function
asyncio.run(main())