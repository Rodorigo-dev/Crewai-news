#!/usr/bin/env python
import sys
import warnings

from datetime import datetime

from crew import CrawlCrew

warnings.filterwarnings("ignore", category=SyntaxWarning, module="pysbd")

def run():
    """
    Inicia a crew para busca e análise de perfil do Google Scholar.
    """
    try:
        result = CrawlCrew().crew().kickoff()
        print(result)
    except Exception as e:
        raise Exception(f"Ocorreu um erro ao executar a crew: {e}")

if __name__ == "__main__":
    run()