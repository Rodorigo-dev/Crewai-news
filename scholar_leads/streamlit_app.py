import streamlit as st
import json
from crew import executar
import os
from utils import save_result

# Configuração da página
st.set_page_config(page_title="Google Scholar Leads Search", page_icon="🔍", layout="centered")

# Título do app
st.title("🔍 Google Scholar Leads Search")

# Campo de input para o nome do pesquisador
pesquisador = st.text_input("Digite o nome do pesquisador:")

# Botão para iniciar a busca
if st.button("Buscar e Analisar"):
    if pesquisador.strip():
        with st.spinner("⏳ Buscando informações no Google Scholar..."):
            try:
                # Executa o CrewAI
                resultado = executar(pesquisador)
                
                # Converter o resultado para string se necessário
                if hasattr(resultado, 'raw_output'):
                    result_str = resultado.raw_output
                else:
                    result_str = str(resultado)
                
                # Parsear o JSON
                resultado_json = json.loads(result_str)
                
                # Salvar em arquivo
                filepath = save_result(pesquisador, resultado_json)
                
                # Exibir os dados estruturados
                st.success("✅ Análise concluída com sucesso!")
                
                # Nome do pesquisador
                st.subheader("👤 Nome do Pesquisador")
                st.info(resultado_json["name"])

                # Área Principal
                st.subheader("📚 Área Principal")
                st.info(resultado_json["research_area"])

                # Instituição
                st.subheader("📚 Instituição")
                st.info(resultado_json["institution"])

                # Dominio do Email
                st.subheader("📧 Dominio do Email")
                st.info(resultado_json["email_domain"])

                # Citações
                st.subheader("📊 Total de Citações")
                st.metric("Citações", resultado_json["total_citations"])
                
                # Artigos
                st.subheader("📝 Artigos Relevantes")
                artigos = resultado_json["articles"]
                for artigo in artigos:
                    titulo = artigo["title"]
                    url = artigo["url"]
                    st.markdown(f"- [{titulo}]({url})")
                
                # Arquivo salvo
                st.divider()
                st.caption(f"💾 Resultado salvo em: {filepath}")

            except Exception as e:
                st.error(f"❌ Erro ao processar os dados: {str(e)}")
    else:
        st.warning("⚠️ Por favor, insira um nome antes de buscar.")
