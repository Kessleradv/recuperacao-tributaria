import streamlit as st
import base64
from io import BytesIO

class Empresa:
    def __init__(self, nome, cnpj, setor):
        self.nome = nome
        self.cnpj = cnpj
        self.setor = setor
        self.documentos = []
        self.resultados_analise = {}

    def adicionar_documento(self, tipo, conteudo):
        self.documentos.append((tipo, conteudo))

    def salvar_resultado(self, chave, valor):
        self.resultados_analise[chave] = valor

def aplicar_teses(dados):
    return {
        "pis_cofins_iss": {
            "base_atual": dados["receita_bruta"],
            "base_corrigida": dados["receita_bruta"] - dados["iss"],
            "credito_apuravel": round((dados["iss"] * 0.0365), 2),
            "fundamentacao": "STF RE 592.616 e RE 574.706"
        },
        "inss_indenizatorio": {
            "base_indevida": dados["verbas_indenizatorias"],
            "valor_indevido": round(dados["verbas_indenizatorias"] * 0.2, 2),
            "fundamentacao": "IN RFB 971/2009"
        },
        "fator_r": {
            "fator_r": round(dados["folha_12m"] / dados["receita_bruta"], 4) if dados["receita_bruta"] else 0,
            "regime_recomendado": "Anexo III" if dados["folha_12m"] / dados["receita_bruta"] >= 0.28 else "Anexo V",
            "fundamentacao": "LC 123/2006"
        },
        "ipva_frotistas": {
            "valor_venal": dados["valor_venal"],
            "percentual_excedente": dados["percentual_ipva"],
            "valor_questionavel": round(dados["valor_venal"] * dados["percentual_ipva"], 2),
            "fundamentacao": "Tese IPVA frotistas"
        },
        "insumos_necessarios": {
            "valor_total_compras": dados["compras"],
            "percentual_insumos_essenciais": dados["percentual_insumos"],
            "credito_estimado": round(dados["compras"] * dados["percentual_insumos"], 2),
            "fundamentacao": "STJ Tema 779"
        }
    }

def gerar_relatorio_texto(empresa, teses_aplicadas):
    relatorio = f"Relatório de Diagnóstico Tributário\nEmpresa: {empresa.nome}\nCNPJ: {empresa.cnpj}\nSetor: {empresa.setor}\n\n"
    for nome_tese, resultado in teses_aplicadas.items():
        relatorio += f"--- {nome_tese.upper()} ---\n"
        for chave, valor in resultado.items():
            relatorio += f"{chave.replace('_', ' ').capitalize()}: {valor}\n"
        relatorio += "\n"
    return relatorio

def gerar_download(relatorio_texto, nome_arquivo):
    buffer = BytesIO()
    buffer.write(relatorio_texto.encode())
    buffer.seek(0)
    b64 = base64.b64encode(buffer.read()).decode()
    href = f'<a href="data:file/txt;base64,{b64}" download="{nome_arquivo}">📄 Baixar Relatório em TXT</a>'
    return href

st.title("Diagnóstico Tributário Interativo")
with st.form("formulario"):
    nome = st.text_input("Nome da empresa", "Clínica Multisaúde LTDA")
    cnpj = st.text_input("CNPJ", "42.193.486/0001-71")
    setor = st.text_input("Setor de atuação", "Serviços médicos")
    receita_bruta = st.number_input("Receita bruta anual (R$)", value=500000.0)
    iss = st.number_input("ISS destacado no ano (R$)", value=30000.0)
    verbas_indenizatorias = st.number_input("Verbas indenizatórias anuais (R$)", value=80000.0)
    folha_12m = st.number_input("Total da folha de 12 meses (R$)", value=147500.0)
    valor_venal = st.number_input("Valor venal do veículo (R$)", value=120000.0)
    percentual_ipva = st.number_input("% tributos anteriores no IPVA", value=0.12)
    compras = st.number_input("Total de compras anuais (R$)", value=250000.0)
    percentual_insumos = st.number_input("% de insumos essenciais (0 a 1)", value=0.4)
    submitted = st.form_submit_button("Aplicar Teses")

if submitted:
    empresa = Empresa(nome, cnpj, setor)
    dados = {
        "receita_bruta": receita_bruta,
        "iss": iss,
        "verbas_indenizatorias": verbas_indenizatorias,
        "folha_12m": folha_12m,
        "valor_venal": valor_venal,
        "percentual_ipva": percentual_ipva,
        "compras": compras,
        "percentual_insumos": percentual_insumos
    }
    teses = aplicar_teses(dados)
    st.header(f"Resultados para {empresa.nome} ({empresa.cnpj})")
    for nome_tese, resultado in teses.items():
        with st.expander(f"{nome_tese.upper()} - Ver detalhes"):
            for chave, valor in resultado.items():
                st.write(f"**{chave.replace('_', ' ').capitalize()}:** {valor}")

    total_credito = sum(
        resultado.get("credito_apuravel", 0) +
        resultado.get("valor_indevido", 0) +
        resultado.get("valor_prescrito", 0) +
        resultado.get("valor_questionavel", 0) +
        resultado.get("credito_estimado", 0)
        for resultado in teses.values()
    )
    st.markdown("---")
    st.subheader(f"Total Potencial de Recuperação: R$ {round(total_credito, 2):,.2f}")
    relatorio = gerar_relatorio_texto(empresa, teses)
    st.markdown(gerar_download(relatorio, "relatorio_tributario.txt"), unsafe_allow_html=True)
