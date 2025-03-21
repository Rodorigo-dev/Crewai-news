from typing import List, Optional
from pydantic import BaseModel, Field, HttpUrl

class Article(BaseModel):
    """Modelo para representar um artigo academico"""
    title: str = Field(..., description="article title")
    url: HttpUrl = Field(..., description="article URL")
    summary: Optional[str] = None  # O resumo pode não estar disponível

class ScholarProfile(BaseModel):
    """Modelo para representar o perfil completo do Google Scholar"""
    name: str = Field(..., description="researcher name")
    profile_url: HttpUrl = Field(..., description="Google Scholar Profile URL")
    email_domain: str = Field(..., description="researcher email domain")
    institution: str = Field(..., description="researcher institution")
    research_area: str = Field(..., description="researcher main research area")
    total_citations: int = Field(..., description="total number of citations")
    articles: List[Article] = Field(
        ..., 
        description="list of most relevant articles",
        max_items=5
    )

class Coauthor(BaseModel):
    """Modelo para representar um coautor"""
    name: str = Field(..., description="coauthor name")
    profile_url: HttpUrl = Field(..., description="coauthor Google Scholar Profile URL")
    email_domain: str = Field(..., description="coauthor email domain")
    institution: str = Field(..., description="coauthor institution")

class CamposPesquisa(BaseModel):
    """Modelo para guiar o agente na busca de perfis de pesquisadores,
    Além do nome, o agente pode ou não usar informações opcionais fornecidas
    pelo usuário para garantir a melhor busca possível
    Dentre as informações opcionais temos:
    - email do pesquisador - opcional - Neste caso, sabe-se que o google scholar mostra apenas o domínio do email,
    por exemplo: "joaodasilva@ufjf.edu.br" é mostrado como "E-mail confirmado em ufjf.edu.br"
    - Instituição de ensino - opcional - Pode ser uma ou mais instituições de ensino
    - Coautor - opcional - Sabendo que o pesquisador que está sendo buscado é um coautor de um artigo,
    o agente pode usar a url do perfil do coautor para buscar o perfil do pesquisador na seção de coautores do perfil do pesquisador.
    """
    name: str = Field(..., description="researcher name")
    email: Optional[str] = Field(None, description="researcher email")
    institution: Optional[str] = Field(None, description="researcher institution")
    coauthor: Optional[HttpUrl] = Field(None, description="coauthor url")