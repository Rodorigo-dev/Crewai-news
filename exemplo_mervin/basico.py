import asyncio
from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig, CacheMode

async def main():
    # Configure browser
    browser_config = BrowserConfig(
        headless=True,
        verbose=False,
        extra_args=["--disable-gpu", "--disable-dev-shm-usage", "--no-sandbox"]
    )

    # Set crawl run configurations
    crawl_config = CrawlerRunConfig(cache_mode=CacheMode.BYPASS)

    try:
        # Use AsyncWebCrawler
        async with AsyncWebCrawler(config=browser_config) as crawler:
            result = await crawler.arun(
                url="https://scholar.google.com/citations?user=lhl7mlAAAAAJ&hl=pt-BR&oi=ao",
                config=crawl_config
            )
            
            print("\n=== Resultado do Crawl ===")
            if result.success:
                # Usa o novo atributo markdown ao invés de markdown_v2
                markdown_content = result.markdown.raw_markdown
                # Remove linhas vazias extras e formata
                formatted_content = "\n".join(line for line in markdown_content.split("\n") if line.strip())
                print(formatted_content)
            else:
                print("Falha ao fazer crawl da página")
                
    except Exception as e:
        print(f"Erro durante o crawl: {str(e)}")

if __name__ == "__main__":
    asyncio.run(main())