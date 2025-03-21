#!/usr/bin/env python
import sys
import warnings
import json
import os
from datetime import datetime
from crew import executar

def normalize_name(name: str) -> str:
    """
    Normaliza o nome do pesquisador para criar um caminho seguro para arquivo.
    
    Args:
        name: Nome do pesquisador
        
    Returns:
        str: Nome normalizado e seguro para uso em caminhos de arquivo
    """
    # Remove espaços extras e converte para minúsculas
    normalized = name.strip()
    
    # Substitui caracteres especiais e espaços por underscore
    import re
    normalized = re.sub(r'[^a-zA-Z0-9\s]', '', normalized)
    normalized = normalized.replace(' ', '_')
    
    return normalized

warnings.filterwarnings("ignore", category=SyntaxWarning, module="pysbd")

def save_result(researcher_name: str, data: dict):
    """Salva o resultado em um arquivo JSON"""
    # Criar diretório data se não existir
    base_dir = os.path.dirname(os.path.abspath(__file__))
    data_dir = os.path.join(base_dir, 'data')
    os.makedirs(data_dir, exist_ok=True)
    
    # Criar nome do arquivo com timestamp
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f"{normalize_name(researcher_name)}_{timestamp}.json"
    filepath = os.path.join(data_dir, filename)
    
    # Salvar arquivo
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    return filepath

def run():
    """
    Inicia a crew para busca e análise de perfil do Google Scholar.
    """
    try:
        # Solicitar nome do pesquisador via input
        researcher_name = input("Digite o nome do pesquisador: ").strip()

        if not researcher_name:
            raise ValueError("Nome do pesquisador não pode estar vazio")
        
        # Solicitar informações adicionais para a busca (opcionais)
        print("\nInformações adicionais para melhorar a busca (opcional):")
        email = input("Digite o domínio de email (ex: ufrj.br, pressione Enter para pular): ").strip() or None
        institution = input("Digite a instituição (ex: UFRJ, pressione Enter para pular): ").strip() or None
        
        # Executar o fluxo do CrewAI
        result = executar(researcher_name, email, institution)

        # Converter o resultado para string se necessário
        if hasattr(result, 'raw_output'):
            result_str = result.raw_output
        else:
            result_str = str(result)
            
        try:
            # Tentar parsear como JSON
            parsed_result = json.loads(result_str)
            
            # Salvar resultado em arquivo
            saved_file = save_result(researcher_name, parsed_result)
            
            # Exibir resultados
            print("\n🔍 Resultado da análise:\n")
            print(json.dumps(parsed_result, indent=2, ensure_ascii=False))
            print(f"\n💾 Resultado salvo em: {saved_file}")
            
        except json.JSONDecodeError:
            # Se não for JSON, mostrar como texto
            print("\n🔍 Resultado da análise (não-JSON):\n")
            print(result_str)

    except Exception as e:
        print(f"\n❌ Erro: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    run()