# 🔮 Oráculo - Chatbot com IA (RAG + Django + OpenAI)

O **Oráculo** é um assistente virtual baseado em **RAG (Retrieval-Augmented Generation)** que combina busca semântica com geração de texto utilizando a API da OpenAI. A aplicação permite consultas inteligentes sobre conteúdos previamente alimentados, como documentos PDF, sendo ideal para empresas que desejam um atendimento automatizado com base em seu próprio conhecimento.

## 🧠 Como funciona?

1. **Treinamento de Base**  
   - O usuário alimenta o sistema com conteúdos (texto ou arquivos).
   - Os dados são processados em **chunks** com sobreposição e convertidos em **embeddings vetoriais** com `OpenAIEmbeddings`.
   - Esses embeddings são armazenados no banco vetorial local com o **FAISS**.

2. **Consulta (Chat com o Oráculo)**  
   - Quando uma pergunta é enviada, o sistema busca os `k` chunks mais relevantes com **KNN**.
   - Os textos encontrados são enviados como **contexto** ao modelo da OpenAI.
   - O modelo gera uma resposta personalizada com base exclusivamente nesses dados.

3. **Restrições do Assistente**  
   - O oráculo não responde com base em dados externos.
   - Quando a informação não estiver nos dados carregados, ele admite: _"Desculpe, não tenho essa informação no momento."_

---

## ⚙️ Tecnologias utilizadas

- [Python](https://www.python.org/)
- [Django](https://www.djangoproject.com/)
- [LangChain](https://www.langchain.com/)
- [FAISS](https://github.com/facebookresearch/faiss)
- [OpenAI API](https://platform.openai.com/)
- [Django Q](https://django-q.readthedocs.io/en/latest/) (para tarefas assíncronas)
- [Redis](https://redis.io/) (cache)
- [WhatsApp Webhook] (integração básica com mensagens recebidas)

---

## 🚀 Funcionalidades

- Upload e indexação de conteúdos via painel web
- Interface para consulta via chat
- Streaming de respostas do modelo
- Visualização das fontes utilizadas para cada resposta
- Integração inicial com WhatsApp (webhook)

---

## 📂 Estrutura do Projeto

- `treinar_ia/` — interface de upload de conteúdo e treinamento
- `chat/` — interface de chat com o oráculo
- `stream_response/` — endpoint para geração contínua da resposta
- `ver_fontes/` — visualização dos documentos usados na resposta
- `webhook_whatsapp/` — endpoint para capturar mensagens de usuários via WhatsApp

---

## 🔐 Prompt do Assistente

```text
Você é um assistente virtual especializado e treinado exclusivamente com base nos dados fornecidos por seu criador. 
Seu único objetivo é responder com precisão às perguntas sobre a empresa, produtos, serviços, processos ou qualquer 
outra informação que tenha sido previamente alimentada por ele.

REGRAS:
1. Não use conhecimento externo.
2. Se não tiver a resposta, diga que não possui essa informação.
3. Não invente.
4. Seja claro, objetivo e profissional.
5. Não mencione que usa IA ou modelos de linguagem.
````

---

## 🧪 Exemplo de Uso

**Pergunta:**

> Qual é o prazo médio de entrega?

**Resposta esperada:**

> O prazo médio de entrega é de 3 a 5 dias úteis, conforme informado pela equipe logística.

---

## 📦 Instalação e Execução

```bash
# Clone o repositório
git clone https://github.com/bbeltrame01/Oraculo.git
cd Oraculo

# Instale as dependências
pip install -r requirements.txt

# Configure as variáveis de ambiente
export OPENAI_API_KEY="sua-chave-da-openai"

# Execute as migrações
python manage.py migrate

# Inicie o servidor
python manage.py runserver

# Para treiná-lo deve executar o cluster
python manage.py qcluster
```

## 📱 Integração com WhatsApp (opcional)

Para integrar o sistema ao WhatsApp, deve-se criar uma conta e configurá-la na plataforma Evolution API.

```bash
# Configure as variáveis de ambiente
AUTHENTICATION_API_KEY="sua-chave-da-evolution-api"
```
