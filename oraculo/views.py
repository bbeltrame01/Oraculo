from .models import Treinamentos, Pergunta, DataTreinamento
from django.http import HttpResponse, JsonResponse, StreamingHttpResponse
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from django.views.decorators.csrf import csrf_exempt
from langchain_community.vectorstores import FAISS
from django.shortcuts import render, redirect
from .utils import sched_message_response
from django.core.cache import cache
from django_q.models import Task
from django.conf import settings
from pathlib import Path
import json

def treinar_ia(request):
  if request.method == 'GET':
    tasks = Task.objects.all()
    return render(request, 'treinar_ia.html', {'tasks': tasks})
  elif request.method == 'POST':
    site = request.POST.get('site')
    conteudo = request.POST.get('conteudo')
    documento = request.FILES.get('documento')

    treinamento = Treinamentos(
      site=site,
      conteudo=conteudo,
      documento=documento,
    )

    treinamento.save()

    return redirect('treinar_ia')

@csrf_exempt
def chat(request):
  if request.method == 'GET':
    return render(request, 'chat.html')
  elif request.method == 'POST':
    pergunta_user = request.POST.get('pergunta')
    if not pergunta_user:
      return JsonResponse({'error': 'Pergunta não pode ser vazia.'}, status=400)

    pergunta = Pergunta(
      pergunta=pergunta_user
    )

    pergunta.save()
    return JsonResponse({'id': pergunta.id})

@csrf_exempt
def stream_response(request):
  id_pergunta = request.POST.get('id_pergunta')
  pergunta = Pergunta.objects.get(id=id_pergunta)
  def stream_generator():
    embeddings = OpenAIEmbeddings(openai_api_key=settings.OPENAI_API_KEY)
    vectordb = FAISS.load_local('banco_faiss', embeddings, allow_dangerous_deserialization=True)

    docs = vectordb.similarity_search(pergunta.pergunta, k=5)
    for doc in docs:
      dt = DataTreinamento.objects.create(
        metadata=doc.metadata,
        texto=doc.page_content,
      )
      pergunta.data_treinamento.add(dt)

    contexto = "\n\n".join([
      f"Material: {Path(doc.metadata.get('source', 'Desconhecido')).name}\n{doc.page_content}"
      for doc in docs
    ])

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
      {"role": "system", "content": f"{system_prompt}\n\n{contexto}"},
      {"role": "user", "content": f'{pergunta.pergunta}'}
    ]

    llm = ChatOpenAI(
      openai_api_key=settings.OPENAI_API_KEY,
      model_name="gpt-3.5-turbo",
      streaming=True,
      temperature=0,
    )

    for chunk in llm.stream(messages):
      token = chunk.content
      if token:
        yield token

  return StreamingHttpResponse(stream_generator(), content_type='text/plain; charset=utf-8')

def ver_fontes(request, id):
  pergunta = Pergunta.objects.get(id=id)
  for i in pergunta.data_treinamento.all():
    print(i.metadata)
    print(i.texto)
    print('---')
  print(pergunta.pergunta)

  return render(request, 'ver_fontes.html', {'pergunta': pergunta})

@csrf_exempt
def webhook_whatsapp(request):
  data = json.loads(request.body)
  phone = data.get('data').get('key').get('remoteJid').split('@')[0]
  message = data.get('data').get('message').get('extendedTextMessage').get('text')

  buffer = cache.get(f"wa_buffer_{phone}", [])
  buffer.append(message)

  cache.set(f"wa_buffer_{phone}", buffer, timeout=120)

  sched_message_response(phone)
  print(buffer)
  return HttpResponse()