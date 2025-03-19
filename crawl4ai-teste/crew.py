from crewai import Agent, Task, Process, Crew
from tools.scholar_crawler_tool import ScholarCrawlerTool
from tools.scholar_search_tool import ScholarSearchTool
from langchain_openai import ChatOpenAI
from dotenv import load_dotenv
import os

load_dotenv()

class CrawlCrew:
	"""CrawlCrew para análise de perfis do Google Scholar"""

	def __init__(self, researcher_name: str):
		self.researcher_name = researcher_name.strip()
		self.profile_url = None

	def create_agents(self):
		"""Criar os agentes da crew"""
		
		# Agente especializado em buscar perfis
		self.buscador_scholar = Agent(
			role='Especialista em busca de perfis acadêmicos',
			goal='Encontrar o perfil correto do pesquisador no Google Scholar',
			backstory="""Você é um especialista em buscar perfis acadêmicos no Google Scholar.
			Sua missão é encontrar o perfil correto do pesquisador usando o nome fornecido.""",
			verbose=True,
			allow_delegation=False,
			tools=[ScholarSearchTool()]
		)

		# Agente especializado em analisar perfis
		self.analista_scholar = Agent(
			role='Analista de perfis acadêmicos',
			goal='Analisar detalhadamente o perfil do pesquisador',
			backstory="""Você é um analista especializado em perfis acadêmicos.
			Sua missão é extrair e analisar todas as informações relevantes do perfil.""",
			verbose=True,
			allow_delegation=False,
			tools=[ScholarCrawlerTool()]
		)

	def create_tasks(self):
		"""Criar as tasks da crew"""
		
		# Task para buscar o perfil
		self.task_busca = Task(
			description=f"Buscar o perfil de '{self.researcher_name}' no Google Scholar",
			agent=self.buscador_scholar,
			expected_output="A URL do perfil do Google Scholar do pesquisador",
			context=[
				f"Você deve buscar o perfil do pesquisador '{self.researcher_name}' no Google Scholar.",
				"Use a ferramenta de busca para encontrar a URL correta do perfil.",
				"Retorne apenas a URL encontrada."
			],
			callback=self.save_profile_url
		)

		# Task para analisar o perfil
		self.task_analise = Task(
			description=f"Analisar o perfil do Google Scholar na URL: {self.profile_url}",
			agent=self.analista_scholar,
			expected_output="Informações detalhadas do perfil em formato JSON",
			context=[
				"Você deve analisar o perfil do pesquisador na URL fornecida.",
				"Use a ferramenta de crawler para extrair todas as informações relevantes.",
				"Retorne os dados em formato JSON com: área principal, artigos relevantes e citações."
			]
		)

	def save_profile_url(self, task_output):
		"""Callback para salvar a URL do perfil"""
		url = str(task_output).strip()
		if not url.startswith('http'):
			raise ValueError(f"URL inválida: {url}")
		self.profile_url = url

	def run(self):
		"""Executar a crew"""
		
		# Criar os agentes
		self.create_agents()
		
		# Criar as tasks
		self.create_tasks()
		
		# Configurar o LLM
		llm = ChatOpenAI(
			model="gpt-4-0125-preview",
			temperature=0.7,
			verbose=True
		)
		
		# Criar e executar a crew
		crew = Crew(
			agents=[self.buscador_scholar, self.analista_scholar],
			tasks=[self.task_busca, self.task_analise],
			manager_llm=llm,
			process=Process.sequential,
			verbose=True
		)

		return crew.kickoff()