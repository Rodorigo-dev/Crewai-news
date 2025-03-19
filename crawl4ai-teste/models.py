from typing import List
from pydantic import BaseModel, Field, HttpUrl

class Article(BaseModel):
    """Modelo para representar um artigo acadêmico"""
    title: str = Field(..., description="Título do artigo")
    url: HttpUrl = Field(..., description="URL do artigo no Google Scholar")

class ScholarProfile(BaseModel):
    """Modelo para representar o perfil completo do Google Scholar"""
    name: str = Field(..., description="Nome do pesquisador")
    profile_url: HttpUrl = Field(..., description="URL do perfil no Google Scholar")
    main_area: str = Field(..., description="Área principal de pesquisa")
    total_citations: int = Field(..., description="Número total de citações")
    relevant_articles: List[Article] = Field(
        ..., 
        description="Lista dos artigos mais relevantes",
        max_items=5
    )
