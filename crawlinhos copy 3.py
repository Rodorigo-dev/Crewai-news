from pydantic import BaseModel
import asyncio
import os
import json
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig, CacheMode
from crawl4ai.extraction_strategy import JsonCssExtractionStrategy
import re
from typing import List

class Coauthor(BaseModel):
    name: str
    institution: str
    email_domain: str

class Article(BaseModel):
    title: str
    abstract: str
    url: str

class Researcher(BaseModel):
    name: str
    institution: str
    research_area: str
    total_citations: str
    email_domain: str
    articles: List[Article]
    coauthors: List[Coauthor]

async def main():
    # Define a schema for extracting researcher information
    schema = {
        "name": "Google Scholar Profile",
        "baseSelector": "body",  # We'll extract everything from the page
        "fields": [
            {
                "name": "name",
                "selector": "div#gsc_prf_in",
                "type": "text"
            },
            {
                "name": "institution",
                "selector": "div.gsc_prf_il:first-of-type",
                "type": "text"
            },
            {
                "name": "research_area",
                "selector": "div.gsc_prf_il a",
                "type": "list",
                "fields": [
                    {"name": "area", "type": "text"}
                ]
            },
            {
                "name": "total_citations",
                "selector": "table.gsc_rsb_std .gsc_rsb_sc1:first-child + .gsc_rsb_std",
                "type": "text"
            },
            {
                "name": "email_domain",
                "selector": "div#gsc_prf_ivh",  # This might need post-processing to extract domain
                "type": "text"
            },
            {
                "name": "articles",
                "selector": "tr.gsc_a_tr",
                "type": "nested_list",
                "fields": [
                    {
                        "name": "title", 
                        "selector": "a.gsc_a_at", 
                        "type": "text"
                    },
                    {
                        "name": "url", 
                        "selector": "a.gsc_a_at", 
                        "type": "attribute",
                        "attribute": "href"
                    },
                    # Abstract might require additional requests for each article
                    {
                        "name": "abstract",
                        "selector": "", 
                        "type": "text",
                        "default": ""
                    }
                ]
            },
            {
                "name": "coauthors",
                "selector": "div.gsc_rsb_aa",
                "type": "nested_list",
                "fields": [
                    {
                        "name": "name", 
                        "selector": "span", 
                        "type": "text"
                    },
                    {
                        "name": "institution",
                        "selector": "", 
                        "type": "text",
                        "default": ""  # To be populated in post-processing if available
                    },
                    {
                        "name": "email_domain",
                        "selector": "", 
                        "type": "text",
                        "default": ""  # To be populated in post-processing if available
                    }
                ]
            }
        ]
    }
    
    # Create the extraction strategy
    css_strategy = JsonCssExtractionStrategy(schema, verbose=True)
    
    # Configure the crawler
    crawl_config = CrawlerRunConfig(
        extraction_strategy=css_strategy, 
        cache_mode=CacheMode.BYPASS,
        wait_for="css:.gsc_rsb_std"  # Wait for citation stats to load
    )
    
    async with AsyncWebCrawler(verbose=True) as crawler:
        result = await crawler.arun(
            url="https://scholar.google.com/citations?user=V_F8eIwAAAAJ&hl=pt-BR", 
            config=crawl_config
        )
        
        if result.success:
            # Parse the extracted content
            raw_data = json.loads(result.extracted_content)
            
            # Post-process the data to fit your model
            researcher = process_raw_data(raw_data)
            
            # Save the processed data
            output_path = "scholar_data.json"
            with open(output_path, "w", encoding="utf-8") as f:
                json.dump(researcher.dict(), f, ensure_ascii=False, indent=4)
            
            print(f"Result saved to: {output_path}")
        else:
            print(f"Extraction failed: {result.error_message}")

def process_raw_data(raw_data):
    """Process the raw extracted data to fit the Researcher model"""
    # Se raw_data for uma lista, pegue o primeiro item
    if isinstance(raw_data, list):
        if not raw_data:  # Se a lista estiver vazia
            raise ValueError("Nenhum dado foi extraído")
        raw_data = raw_data[0]  # Pega o primeiro item da lista
    
    # Extract email domain from contact info
    email_domain = ""
    if raw_data.get("email_domain"):
        # Use regex to extract email domain if present
        email_match = re.search(r'@([^\s]+)', raw_data.get("email_domain", ""))
        if email_match:
            email_domain = email_match.group(1)
    
    # Convert research areas from list of dicts to comma-separated string
    research_areas = []
    if raw_data.get("research_area"):
        research_areas = [area.get("area", "") for area in raw_data.get("research_area", [])]
    
    # Create articles list
    articles = []
    for article_data in raw_data.get("articles", []):
        articles.append(Article(
            title=article_data.get("title", ""),
            abstract=article_data.get("abstract", ""),
            url=article_data.get("url", "")
        ))
    
    # Create coauthors list
    coauthors = []
    for coauthor_data in raw_data.get("coauthors", []):
        coauthors.append(Coauthor(
            name=coauthor_data.get("name", ""),
            institution=coauthor_data.get("institution", ""),
            email_domain=coauthor_data.get("email_domain", "")
        ))
    
    # Create the researcher object
    researcher = Researcher(
        name=raw_data.get("name", ""),
        institution=raw_data.get("institution", ""),
        research_area=", ".join(research_areas),
        total_citations=raw_data.get("total_citations", ""),
        email_domain=email_domain,
        articles=articles,
        coauthors=coauthors
    )
    
    return researcher

if __name__ == "__main__":
    asyncio.run(main())

#For Abstracts: You might need a second pass to get article abstracts:
async def fetch_article_abstracts(crawler, articles):
    """Fetch abstracts for each article by visiting their individual pages"""
    for article in articles:
        if article.url:
            # Create a URL for the article's page
            article_url = f"https://scholar.google.com{article.url}"
            
            # Define a schema for extracting just the abstract
            abstract_schema = {
                "name": "Article Abstract",
                "baseSelector": "div.gsh_csp",
                "fields": [
                    {
                        "name": "abstract",
                        "selector": "div.gsh_small",
                        "type": "text"
                    }
                ]
            }
            
            abstract_strategy = JsonCssExtractionStrategy(abstract_schema)
            abstract_config = CrawlerRunConfig(extraction_strategy=abstract_strategy)
            
            # Fetch and extract the abstract
            result = await crawler.arun(url=article_url, config=abstract_config)
            if result.success:
                abstract_data = json.loads(result.extracted_content)
                article.abstract = abstract_data.get("abstract", "")


# #For Coauthor Information: Similarly, you might need to visit each coauthor's page:
# async def fetch_coauthor_info(crawler, coauthors):
#     """Fetch additional information for each coauthor"""
#     for coauthor in coauthors:
#         # ... similar approach to fetch institution and email from coauthor pages


