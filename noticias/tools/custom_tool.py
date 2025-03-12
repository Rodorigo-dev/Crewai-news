from crewai.tools import BaseTool
from typing import Type
from pydantic import BaseModel, Field
import asyncio
import requests
from xml.etree import ElementTree
import time

from typing import List, Dict, Any
from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig, CacheMode




class InputFerramentaCustom(BaseModel):
    """Esquema de entrada para Ferramenta Custom."""
    url_sitemap: str = Field(..., description="URL do sitemap a ser crawleado.")


class FerramentaCustom(BaseTool):
    name: str = "Crawl sitemap"
    description: str = (
        "Essa é uma ferramenta útil para fazer crawling de um sitemap e retornar uma lista de urls a serem crawleadas."
    )
    args_schema: Type[BaseModel] = InputFerramentaCustom

    def _run(self, sitemap_url: str) -> str:
        #implementar a lógica de crawling do sitemap
        urls = get_crewai_docs_urls(sitemap_url)
        if urls:
            print(f"Encontradas {len(urls)} urls no sitemap para crawlear.")
            resultado = asyncio.run(crawl_parallel(urls, max_concurrent=5))
            print(resultado)
        else:
            print("Nenhuma url encontrada no sitemap.")

        return resultado

async def crawl_parallel(urls: List[str], max_concurrent: int = 3):
    """Executa crawling paralelo de urls."""
    browser_config=BrowserConfig(
        headless=True,
        verbose=False,
        extra_args=["--disable-gpu", "--disable-dev-shm-usage", "--no-sandbox"],
    )
    crawler_config=CrawlerRunConfig(cache_mode=CacheMode.BYPASS)

    #instancia o crawler
    crawler = AsyncWebCrawler(config=browser_config)
    await crawler.start()

    try:
        success_count = 0
        fail_count = 0
        start_time = time.time()
        print(f"Start Time: {time.ctime(start_time)}")
        for i in range(0, len(urls), max_concurrent):
            batch = urls[i : i + max_concurrent]
            tasks = []

            for j, url in enumerate(batch):
                session_id = f"parallel_session_{i + j}"
                task = crawler.arun(url=url, config=crawler_config, session_id=session_id)
                tasks.append(task)

            # Gather results
            results = await asyncio.gather(*tasks, return_exceptions=True)

            markdown_results = []
            
            for url, result in zip(batch, results):
                if isinstance(result, Exception):
                    print(f"Error crawling {url}: {result}")
                    fail_count += 1
                elif result.success:
                    print("Successfully crawled", url)
                    success_count += 1
                    markdown_results.append(result.markdown_v2.raw_markdown[:1000])
                    
                    print("--- URL ---")
                    print(url)
                    print("--- MARKDOWN ---")
                    print(result.markdown_v2.raw_markdown[:250])
                    print("--------------------------------")
                else:
                    print(f"Unsuccessful crawl of {url}")
                    fail_count += 1

        print(f"\nSummary:")
        print(f"  - Successfully crawled: {success_count}")
        print(f"  - Failed: {fail_count}")

        return markdown_results

    finally:
        end_time = time.time()
        print(f"End Time: {time.ctime(end_time)}")
        print(f"Total Time Taken: {end_time - start_time:.2f} seconds")
        print("\nClosing crawler...")
        await crawler.close()

def get_crewai_docs_urls(sitemap_url: str):
    """
    Fetches all URLs from the CrewAI documentation.
    Uses the sitemap (https://docs.crewai.com/sitemap.xml) to get these URLs.
    
    Returns:
        List[str]: List of URLs
    """            

    try:
        response = requests.get(sitemap_url)
        response.raise_for_status()
        
        # Parse the XML
        root = ElementTree.fromstring(response.content)
        
        # Extract all URLs from the sitemap
        # The namespace is usually defined in the root element
        namespace = {'ns': 'http://www.sitemaps.org/schemas/sitemap/0.9'}
        urls = [loc.text for loc in root.findall('.//ns:loc', namespace)]
        
        return urls
    except Exception as e:
        print(f"Error fetching sitemap: {e}")
        return []        

async def main():
    urls = get_crewai_docs_urls()
    if urls:
        print(f"Found {len(urls)} URLs to crawl")
        await crawl_parallel(urls, max_concurrent=10)
    else:
        print("No URLs found to crawl")    