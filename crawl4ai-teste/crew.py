from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task
from tools.custom_tool import ScholarCrawlerTool
from tools.scholar_search_tool import ScholarSearchTool
import pandas as pd
import os
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI

load_dotenv()

@CrewBase
class CrawlCrew():
	"""CrawlCrew para análise de perfis do Google Scholar"""

	agents_config = 'config/agents.yaml'
	tasks_config = 'config/tasks.yaml'

	def __init__(self):
		super().__init__()
		# Obter o caminho absoluto para o arquivo CSV
		current_dir = os.path.dirname(os.path.abspath(__file__))
		self.csv_path = os.path.join(current_dir, 'data', 'researchers.csv')
		
		try:
			# Especificar os tipos das colunas
			dtype_dict = {
				'nome': str,
				'profile_url': str
			}
			self.researchers_df = pd.read_csv(self.csv_path, dtype=dtype_dict)
			self.researcher_name = self.researchers_df['nome'].iloc[0].strip()
		except FileNotFoundError:
			raise Exception(f"Arquivo CSV não encontrado em: {self.csv_path}")
		except Exception as e:
			raise Exception(f"Erro ao ler o arquivo CSV: {e}")

	def save_profile_url(self, task_output):
		"""Salva a URL do perfil no CSV"""
		try:
			# Converter o TaskOutput para string e limpar
			url = str(task_output).strip()
			print(f"Salvando URL no CSV: {url}")  # Debug
			
			# Verificar se a URL é válida
			if not url.startswith('http'):
				raise ValueError(f"URL inválida: {url}")
			
			# Atualizar o DataFrame
			self.researchers_df.loc[0, 'profile_url'] = url
			
			# Salvar no CSV
			self.researchers_df.to_csv(self.csv_path, index=False)
			
			# Recarregar o DataFrame para garantir
			self.researchers_df = pd.read_csv(self.csv_path, dtype={'nome': str, 'profile_url': str})
			
		except Exception as e:
			print(f"Erro ao salvar URL no CSV: {e}")
			raise e

	@agent
	def analista_scholar(self) -> Agent:
		return Agent(
			config=self.agents_config['analista_scholar'],
			verbose=True,
			tools=[ScholarCrawlerTool()]
		)

	@agent
	def buscador_scholar(self) -> Agent:
		return Agent(
			config=self.agents_config['buscador_scholar'],
			verbose=True,
			tools=[ScholarSearchTool()]
		)

	@task
	def task_busca_perfil(self) -> Task:
		return Task(
			description=f"Buscar o perfil de '{self.researcher_name}' no Google Scholar",
			expected_output="A URL do perfil do Google Scholar do pesquisador",
			agent=self.buscador_scholar(),
			context=[
				{
					"researcher_name": self.researcher_name,
					"description": f"Buscar o perfil de '{self.researcher_name}' no Google Scholar",
					"instruction": f"Use a ferramenta Google Scholar Search para buscar exatamente este nome: '{self.researcher_name}'",
					"expected_output": "A URL do perfil encontrado no Google Scholar"
				}
			],
			callback=self.save_profile_url  # Callback para salvar a URL no CSV
		)

	@task
	def task_analise_scholar(self) -> Task:
		# Ler a URL do CSV e garantir que é string
		profile_url = str(self.researchers_df['profile_url'].iloc[0])
		
		# Verificar se a URL é válida
		if pd.isna(profile_url) or profile_url.strip() == '':
			raise Exception("URL do perfil não encontrada no CSV")
		
		return Task(
			description=f"Analisar o perfil do Google Scholar na URL: {profile_url}",
			expected_output="Informações detalhadas do perfil em formato JSON",
			agent=self.analista_scholar(),
			context=[
				{
					"description": "Analisar o perfil e extrair informações relevantes",
					"instruction": "Use a ferramenta Google Scholar Crawler com a URL fornecida",
					"expected_output": "JSON com área principal, artigos e citações",
					"profile_url": profile_url
				}
			]
		)

	@crew
	def crew(self) -> Crew:
		"""Cria a crew CrawlCrew"""
		# Criar o LLM que será usado como manager
		manager_llm = ChatOpenAI(
			model="gpt-4o-mini",
			temperature=0,
			verbose=True
		)

		return Crew(
			agents=[self.buscador_scholar(), self.analista_scholar()],
			tasks=[self.task_busca_perfil(), self.task_analise_scholar()],
			process=Process.sequential,
			manager_llm=manager_llm,
			verbose=True
		)