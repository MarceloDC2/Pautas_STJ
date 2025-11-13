# https://mugylqevyozqsrus4a3sgt.streamlit.app/
import streamlit as st
import requests
from urllib import request
import os
import zipfile
from io import BytesIO
from datetime import datetime, date
from dateutil.relativedelta import relativedelta

# ------------------------
# Função para gerar datas no intervalo
# ------------------------
def datas_intervalo(dt_ini, dt_fim):
    dt_ini = datetime.strptime(dt_ini, '%d/%m/%Y').date()
    dt_fim = datetime.strptime(dt_fim, '%d/%m/%Y').date()
    if dt_ini > dt_fim:
        dt_ini, dt_fim = dt_fim, dt_ini
    while dt_ini <= dt_fim:
        data = f"{dt_ini.day:02d}/{dt_ini.month:02d}/{dt_ini.year}"
        dt_ini += relativedelta(days=+1)
        yield data

# ------------------------
# Interface Streamlit
# ------------------------
st.title("📄 Downloader de Pautas do STJ")

st.markdown("""
Informe a **data inicial** e a **data final** do intervalo desejado.  
O aplicativo vai buscar todas as pautas disponíveis entre essas datas e gerar um **arquivo ZIP** com os PDFs.
""")

hoje = date.today()
hoje = str(hoje.day).zfill(2) + '/' + str(hoje.month).zfill(2) + '/' + str(hoje.year)
col1, col2 = st.columns(2)
with col1:
    data_inicial = st.text_input("📅 Data inicial (DD/MM/AAAA):", hoje)
with col2:
    data_final = st.text_input("📅 Data final (DD/MM/AAAA):", hoje)

if st.button("🔍 Buscar e gerar ZIP"):
    try:
        datas = list(datas_intervalo(data_inicial, data_final))
    except ValueError:
        st.error("❌ Datas inválidas. Use o formato DD/MM/AAAA.")
        st.stop()

    with st.spinner("Baixando pautas e preparando o arquivo ZIP..."):
        temp_folder = "/tmp/pautas_stj"
        os.makedirs(temp_folder, exist_ok=True)

        total_pdfs = 0
        progresso = st.progress(0)
        total_datas = len(datas)

        for i, data in enumerate(datas, start=1):
            progresso.progress(i / total_datas)
            st.write(f"📅 Processando data: {data}")
            url = f'https://processo.stj.jus.br/processo/pauta/ver?data={data}&aplicacao=calendario&popup=TRUE'
            headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36'}
            resp = requests.get(url, headers=headers)
            conteudo_pagina = resp.text

            lista_mostrar_pauta = set()
            while conteudo_pagina.find('mostrarPauta(') > 0:
                inicio = conteudo_pagina.find('mostrarPauta(')
                conteudo_pagina = conteudo_pagina[inicio + 14 :]
                fim = conteudo_pagina.find("'")
                lista_mostrar_pauta.add(conteudo_pagina[:fim])

            for uma_pauta in lista_mostrar_pauta:
                url_pdf = f'https://processo.stj.jus.br/processo/pauta/buscar/?seq_documento={uma_pauta}'
                nome_arquivo = f"{uma_pauta}.pdf"
                caminho_pdf = os.path.join(temp_folder, nome_arquivo)
                try:
                    request.urlretrieve(url_pdf, caminho_pdf)
                    total_pdfs += 1
                except Exception as e:
                    st.write(f"❌ Erro ao baixar {nome_arquivo}: {e}")

        if total_pdfs == 0:
            st.warning("Nenhum PDF encontrado para o intervalo informado.")
        else:
            # Cria o ZIP em memória
            buffer_zip = BytesIO()
            with zipfile.ZipFile(buffer_zip, "w", zipfile.ZIP_DEFLATED) as zipf:
                for root, _, files in os.walk(temp_folder):
                    for f in files:
                        caminho_completo = os.path.join(root, f)
                        zipf.write(caminho_completo, arcname=f)
            buffer_zip.seek(0)

            st.success(f"✅ {total_pdfs} arquivos PDF adicionados ao ZIP.")

            # Botão para download do ZIP
            st.download_button(
                label="⬇️ Baixar arquivo ZIP",
                data=buffer_zip,
                file_name="pautas_stj.zip",
                mime="application/zip"
            )

    st.info("Processo concluído.")