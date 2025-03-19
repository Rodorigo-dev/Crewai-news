import os
import json
import yaml
from crewai import Agent, Task, Crew, Process
from tools.scholar_search_tool import ScholarSearchTool
from tools.scholar_crawler_tool import ScholarCrawlerTool
from llm_config import llm
from langchain_openai import ChatOpenAI

# Obter o diretório base do projeto
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_DIR = os.path.join(os.path.dirname(BASE_DIR), 'crawl4ai-teste/config')

def load_yaml(file_path):
    """Carrega arquivo YAML usando caminho absoluto"""
    absolute_path = os.path.join(CONFIG_DIR, os.path.basename(file_path))
    with open(absolute_path, 'r') as file:
        return yaml.safe_load(file)

def create_agents():
    """Criar os agentes da crew"""
    agents_config = load_yaml('agents.yaml')
    
    # Agente buscador
    buscador = Agent(
        role=agents_config['buscador_scholar']['role'],
        goal=agents_config['buscador_scholar']['goal'],
        backstory=agents_config['buscador_scholar']['backstory'],
        verbose=True,
        allow_delegation=False,
        tools=[ScholarSearchTool()]
    )
    
    # Agente analista
    analista = Agent(
        role=agents_config['analista_scholar']['role'],
        goal=agents_config['analista_scholar']['goal'],
        backstory=agents_config['analista_scholar']['backstory'],
        verbose=True,
        allow_delegation=False,
        tools=[ScholarCrawlerTool()]
    )
    
    return [buscador, analista]

def create_tasks(agents, researcher_name):
    """Criar as tasks da crew"""
    tasks_config = load_yaml('tasks.yaml')
    
    # Task de busca
    task_busca = Task(
        description=tasks_config['task_busca_perfil']['description'].format(
            researcher_name=researcher_name
        ),
        agent=agents[0],  # buscador
        expected_output=tasks_config['task_busca_perfil']['expected_output'],
        output_key = "perfil_url" # Captura a saída como variável para a próxima task
    )
    
    # Task de análise
    task_analise = Task(
        description=tasks_config['task_analise_scholar']['description'],
        agent=agents[1],  # analista
        expected_output=tasks_config['task_analise_scholar']['expected_output'],
        inputs={"perfil_url": "{{ perfil_url }}"}  # Usa a saída da task anterior
    )
    
    return [task_busca, task_analise]

def executar(nome_pesquisador):
    """Executar o fluxo do CrewAI"""
    # Criar agentes
    agents = create_agents()
    
    # Criar tasks
    tasks = create_tasks(agents, nome_pesquisador)
    
    # Configurar LLM
    llm = ChatOpenAI(
        model="gpt-4o-mini",
        temperature=1,
        verbose=True
    )
    
    # Criar e executar crew
    crew = Crew(
        agents=agents,
        tasks=tasks,
        manager_llm=llm,
        process=Process.sequential,
        verbose=True
    )

    return crew.kickoff()

if __name__ == "__main__":
    nome_pesquisador = input("Digite o nome do pesquisador: ")
    result = executar(nome_pesquisador)

    try:
        # Se for JSON, formatar bonitinho
        parsed_result = json.loads(result)
        print(json.dumps(parsed_result, indent=2, ensure_ascii=False))
    except json.JSONDecodeError:
        print(result)  # Caso tenha erro, exibir normalmente