#!/usr/bin/env python
import sys
import warnings
from datetime import datetime
from crew import CrawlCrew
import json

warnings.filterwarnings("ignore", category=SyntaxWarning, module="pysbd")

def run():
    """
    Inicia a crew para busca e análise de perfil do Google Scholar.
    """
    try:
        # Solicitar nome do pesquisador via input
        researcher_name = input("Digite o nome do pesquisador: ")
        
        if not researcher_name.strip():
            raise ValueError("Nome do pesquisador não pode estar vazio")
            
        # Criar e executar a crew
        crew = CrawlCrew(researcher_name)
        result = crew.run()
        
        print("\nResultado da análise:")
        print(json.dumps(result, indent=2, ensure_ascii=False))
        
    except Exception as e:
        print(f"\nErro: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    run()