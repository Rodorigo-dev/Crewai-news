from crewai import Agent, Task, Crew, Process
from crewai.project import CrewBase, agent, crew, task
from tools.custom_tool import FerramentaCustom
from dotenv import load_dotenv
import os

load_dotenv()

@CrewBase
class CrawlCrew():
    """CrawlCrew Crew"""

    agents_config = 'config/agents.yaml'
    tasks_config = 'config/tasks.yaml'

    @agent
    def engenheiro_web(self) -> Agent:
        return Agent(
            config=self.agents_config['engenheiro_web'],
            tools=[FerramentaCustom()],
            verbose=True,
        )
    
    @task
    def task_analise_sitemap(self) -> Task:
        return Task(
            config = self.tasks_config['task_analise_sitemap'],
		)

    @crew
    def crew(self) -> Crew:
        """Cria a crew CrawlCrew"""
        return Crew(
            agents=self.agents,
            tasks=self.tasks,
            process=Process.sequential,
            verbose=True
            # process=Process.hierarchical, # In case you wanna use that instead https://docs.crewai.com/how-to/Hierarchical/
        )
        










