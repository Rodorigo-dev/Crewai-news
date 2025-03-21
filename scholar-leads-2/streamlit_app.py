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

# Opções avançadas - colapsável
with st.expander("Opções avançadas para melhorar a busca"):
    st.markdown("Estas informações são usadas para melhorar a precisão da busca quando existem múltiplos pesquisadores com o mesmo nome.")
    email_domain = st.text_input("Domínio do email (opcional, ex: ufjf.edu.br):")
    instituicao = st.text_input("Instituição (opcional, ex: UFJF):")

# Botão para iniciar a busca
if st.button("Buscar e Analisar"):
    if pesquisador.strip():
        with st.spinner("⏳ Buscando informações no Google Scholar..."):
            try:
                # Processar inputs opcionais
                email = email_domain.strip() if email_domain.strip() else None
                institution = instituicao.strip() if instituicao.strip() else None
                
                # Executa o CrewAI
                resultado = executar(pesquisador, email, institution)
                
                # Converter o resultado para string se necessário
                if hasattr(resultado, 'raw_output'):
                    result_str = resultado.raw_output
                else:
                    result_str = str(resultado)
                
                # Tentar parsear como JSON
                try:
                    resultado_json = json.loads(result_str)
                    
                    # Verificar se há erro
                    if "error" in resultado_json:
                        st.error(f"⚠️ {resultado_json['error']}")
                        st.info("Tente ajustar os termos da busca ou adicionar mais informações como instituição ou email para encontrar o perfil.")
                        st.stop()
                    
                    # Salvar em arquivo
                    filepath = save_result(pesquisador, resultado_json)
                    
                    # Exibir os dados estruturados
                    st.success("✅ Análise concluída com sucesso!")
                    
                    # Nome do pesquisador
                    if "name" in resultado_json:
                        st.subheader("👤 Nome do Pesquisador")
                        st.info(resultado_json["name"])
    
                    # URL do perfil
                    if "profile_url" in resultado_json:
                        st.subheader("🔗 Perfil")
                        st.markdown(f"[Acessar perfil no Google Scholar]({resultado_json['profile_url']})")
    
                    # Área Principal
                    if "research_area" in resultado_json:
                        st.subheader("📚 Área Principal")
                        st.info(resultado_json["research_area"])
                    
                    # Citações
                    if "total_citations" in resultado_json:
                        st.subheader("📊 Total de Citações")
                        st.metric("Citações", resultado_json["total_citations"])
                    
                    # Artigos
                    if "articles" in resultado_json and resultado_json["articles"]:
                        st.subheader("📝 Artigos Relevantes")
                        artigos = resultado_json["articles"]
                        for artigo in artigos:
                            titulo = artigo["title"]
                            url = artigo.get("url", "")
                            if url:
                                st.markdown(f"- [{titulo}]({url})")
                            else:
                                st.markdown(f"- {titulo}")
                    
                    # Coautores
                    if "coauthors" in resultado_json and resultado_json["coauthors"]:
                        coautores = resultado_json["coauthors"]
                        st.subheader("👥 Principais Coautores")
                        
                        # Determinar quantos coautores mostrar inicialmente
                        total_coautores = len(coautores)
                        coautores_mostrados = min(5, total_coautores)  # Mostrar no máximo 5 inicialmente
                        
                        # Seção para exibir coautores
                        for i in range(coautores_mostrados):
                            coautor = coautores[i]
                            col1, col2 = st.columns([3, 2])
                            with col1:
                                nome = coautor["name"]
                                if coautor.get("profile_url"):
                                    st.markdown(f"- [{nome}]({coautor['profile_url']})")
                                else:
                                    st.markdown(f"- {nome}")
                            with col2:
                                if coautor.get("institution"):
                                    st.text(f"Instituição: {coautor['institution']}")
                                if coautor.get("email_domain"):
                                    st.text(f"Email: {coautor['email_domain']}")
                        
                        # Se houver mais de 5 coautores, mostrar botão para exibir todos
                        if total_coautores > 5:
                            with st.expander(f"Ver todos os {total_coautores} coautores"):
                                for i in range(5, total_coautores):
                                    coautor = coautores[i]
                                    col1, col2 = st.columns([3, 2])
                                    with col1:
                                        nome = coautor["name"]
                                        if coautor.get("profile_url"):
                                            st.markdown(f"- [{nome}]({coautor['profile_url']})")
                                        else:
                                            st.markdown(f"- {nome}")
                                    with col2:
                                        if coautor.get("institution"):
                                            st.text(f"Instituição: {coautor['institution']}")
                                        if coautor.get("email_domain"):
                                            st.text(f"Email: {coautor['email_domain']}")
                    
                    # Arquivo salvo
                    st.divider()
                    st.caption(f"💾 Resultado salvo em: {filepath}")
                    
                except json.JSONDecodeError:
                    st.error(f"❌ Erro ao processar os dados: Não foi possível interpretar o resultado como JSON.")
                    st.code(result_str, language="text")
                    st.info("O perfil pode não ter sido encontrado ou o formato da resposta é inválido.")
                    
            except Exception as e:
                st.error(f"❌ Erro ao processar os dados: {str(e)}")
                st.info("Talvez o perfil não exista ou houve um problema ao acessá-lo. Verifique o nome e tente novamente.")
    else:
        st.warning("⚠️ Por favor, insira um nome antes de buscar.")
