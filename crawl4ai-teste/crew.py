from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task
from tools.custom_tool import MyCustomTool
from dotenv import load_dotenv

load_dotenv()

@CrewBase
class CrawlCrew():
	"""CrawlCrew crew"""

	agents_config = 'config/agents.yaml'
	tasks_config = 'config/tasks.yaml'

	@agent
	def engenheiro_web(self) -> Agent:
		return Agent(
			config=self.agents_config['engenheiro_web'],
			verbose=True,
			tools=[MyCustomTool()]
		)

	
	@task
	def task_analise_sitemap(self) -> Task:
		return Task(
			config=self.tasks_config['task_analise_sitemap'],
		)

	@crew
	def crew(self) -> Crew:
		"""Cria a crew CrawlCrew"""

		return Crew(
			agents=self.agents, # Automatically created by the @agent decorator
			tasks=self.tasks, # Automatically created by the @task decorator
			process=Process.sequential,
			verbose=True,
			# process=Process.hierarchical, # In case you wanna use that instead https://docs.crewai.com/how-to/Hierarchical/
		)