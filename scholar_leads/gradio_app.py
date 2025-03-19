import gradio as gr
import json
from crew import executar
from datetime import datetime
import os

def process_researcher(researcher_name: str):
    """
    Processa a busca do pesquisador e retorna os resultados formatados
    """
    try:
        # Executar a análise
        result = executar(researcher_name)
        
        # Converter o resultado
        if hasattr(result, 'raw_output'):
            result_str = result.raw_output
        else:
            result_str = str(result)
            
        # Parsear o JSON
        data = json.loads(result_str)
        
        # Salvar o resultado
        base_dir = os.path.dirname(os.path.abspath(__file__))
        data_dir = os.path.join(base_dir, 'data')
        os.makedirs(data_dir, exist_ok=True)
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"{researcher_name.replace(' ', '_')}_{timestamp}.json"
        filepath = os.path.join(data_dir, filename)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        # Formatar o resultado para exibição
        formatted_result = f"""
### Resultado da Análise

**Área Principal:** {data['principal_area_de_pesquisa']}

**Total de Citações:** {data['numero_total_de_citacoes']}

**Artigos Relevantes:**
"""
        for url in data['urls_artigos_relevantes']:
            formatted_result += f"- [{url}]({url})\n"
            
        formatted_result += f"\n\n💾 Resultado salvo em: {filepath}"
        
        return formatted_result
        
    except Exception as e:
        return f"❌ Erro: {str(e)}"

# Criar a interface
with gr.Blocks(title="Análise de Perfil Acadêmico", theme=gr.themes.Soft()) as demo:
    gr.Markdown("""
    # 🎓 Análise de Perfil Acadêmico
    
    Esta ferramenta analisa perfis do Google Scholar e extrai informações relevantes.
    """)
    
    with gr.Row():
        with gr.Column():
            # Input
            name_input = gr.Textbox(
                label="Nome do Pesquisador",
                placeholder="Digite o nome completo do pesquisador...",
                lines=1
            )
            
            # Botão
            search_button = gr.Button("🔍 Analisar Perfil", variant="primary")
        
    # Output    
    result_output = gr.Markdown(label="Resultados")
    
    # Configurar o fluxo
    search_button.click(
        fn=process_researcher,
        inputs=name_input,
        outputs=result_output
    )

# Iniciar a aplicação
if __name__ == "__main__":
    demo.launch(
        share=True,  # Criar um link público temporário
        server_name="0.0.0.0",  # Permitir acesso externo
        server_port=7860  # Porta padrão do Gradio
    ) 