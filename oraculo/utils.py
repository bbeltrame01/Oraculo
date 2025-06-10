from apscheduler.schedulers.background import BackgroundScheduler
from langchain_community.document_loaders import PyPDFLoader
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_community.vectorstores import FAISS
from langchain.docstore.document import Document
from .wrapper_evolutionapi import SendMessage
from datetime import datetime, timedelta
from django.core.cache import cache
from bs4 import BeautifulSoup
from typing import List
import requests

def html_para_texto_rag(html_str: str) -> str:
  soup = BeautifulSoup(html_str, "html.parser")
  texto_final = []

  for tag in soup.find_all(["h1", "h2", "h3", "p", "li"]):
    texto = tag.get_text(strip=True)

    if not texto:
      continue

    if tag.name in ["h1", "h2", "h3"]:
      texto_formatado = f"\n\n### {texto.upper()}"
    elif tag.name == "li":
      texto_formatado = f" - {texto}"
    else:
      texto_formatado = texto

    texto_final.append(texto_formatado)

  return "\n".join(texto_final).strip()


def gerar_documentos(instance) -> List[Document]:
  documentos = []
  if instance.documento:
    extensao = instance.documento.name.split('.')[-1].lower()
    if extensao == 'pdf':
      loader = PyPDFLoader(instance.documento.path)
      pdf_doc = loader.load()
      for doc in pdf_doc:
        doc.metadata['url'] = instance.documento.url
      documentos += pdf_doc

  if instance.conteudo:
    documentos.append(Document(page_content=instance.conteudo))
  if instance.site:
    site_url = instance.site if instance.site.startswith('https://') else f'https://{instance.site}'
    content = requests.get(site_url, timeout=10).text
    content = html_para_texto_rag(content)
    documentos.append(Document(page_content=content))

  return documentos

scheduler = BackgroundScheduler()
scheduler.start()

def send_message_response(phone):
  messages = cache.get(f"wa_buffer_{phone}", [])
  if messages:
    question = "\n".join(messages)
    embeddings = OpenAIEmbeddings()
    vectordb = FAISS.load_local("banco_faiss", embeddings, allow_dangerous_deserialization=True)
    docs = vectordb.similarity_search(question, k=5)
    context = "\n\n".join([doc.page_content for doc in docs ])

    system_prompt = """
      Você é um assistente virtual especializado e treinado exclusivamente com base nos dados fornecidos por seu criador.
      Seu único objetivo é responder com precisão às perguntas sobre a empresa, produtos, serviços, processos ou qualquer outra informação que tenha sido previamente alimentada por ele.

      REGRAS E LIMITAÇÕES:
      1. Não utilize conhecimento externo, nem tente completar lacunas com informações genéricas.
      2. Se não encontrar a resposta nos dados fornecidos, diga: "Desculpe, não tenho essa informação no momento."
      3. Não invente, não assuma e não generalize. Apenas responda com base no conteúdo previamente informado.
      4. Responda de forma clara, objetiva e profissional.
      5. Nunca mencione que está usando um modelo de linguagem, como ChatGPT ou OpenAI. Assuma o papel de um assistente virtual da empresa.
      6. Sempre se baseie exclusivamente no contexto fornecido pelo usuário em cada solicitação.

      EXEMPLO DE RESPOSTA ADEQUADA:
      Pergunta: Qual é o prazo médio de entrega?
      Resposta: O prazo médio de entrega é de 3 a 5 dias úteis, conforme informado pela equipe logística.

      Se não houver contexto suficiente, informe que a informação não está disponível.
    """

    messages = [
      {"role": "system", "content": f"{system_prompt}\n\n{context}"},
      {"role": "user", "content": question}
    ]

    llm = ChatOpenAI(
      model_name="gpt-3.5-turbo",
      temperature=0,
    )

    response = llm.invoke(messages).content

    SendMessage().send_message('arcane', {
      "number": phone,
      "textMessage": {"text": response}
    })

    cache.delete(f"wa_buffer_{phone}")
    cache.delete(f"wa_timer_{phone}")

def sched_message_response(phone):
  if not cache.get(f"wa_timer_{phone}"):
    scheduler.add_job(
      send_message_response,
      'date',
      run_date=datetime.now() + timedelta(seconds=15),
      kwargs={"phone": phone},
      misfire_grace_time=60
    )
    cache.set(f"wa_timer_{phone}", True, timeout=60)