# Deploy para Hugging Face Spaces

Guia para publicar seu agente como Space público gratuito.

## Pré-requisitos

- Conta Hugging Face ativa (gratuita) em <https://huggingface.co/join>.
- Repositório `aula07-agentes` no GitHub com tag `aula07-final`.
- Saldo na conta OpenAI (mesma chave que você usou no Codespaces).

## Passo 1 · Criar o Space

1. Acesse <https://huggingface.co/new-space>.
2. **Owner**: seu usuário.
3. **Space name**: `educiacao` ou `designmind` (sem espaços, minúsculo).
4. **License**: MIT (padrão para projetos didáticos).
5. **Space SDK**: selecione **Gradio**.
6. **Gradio template**: deixe como "Blank".
7. **Hardware**: `CPU basic · Free` (suficiente para o agente, que só chama API).
8. **Visibility**: `Public` (recomendado para portfólio) ou `Private`.
9. Clique em **Create Space**.

## Passo 2 · Configurar Secrets e Variables

Antes de subir código, configure os segredos. No Space recém-criado:

1. Clique em **Settings** (canto superior direito do Space).
2. Role até **Variables and secrets**.
3. Em **Secrets**, clique em **New secret**:
   - Name: `OPENAI_API_KEY`
   - Value: sua chave (`sk-...`)
4. Em **Variables**, clique em **New variable**:
   - Name: `PRODUCT`
   - Value: `educiacao` ou `designmind` (mesmo que você usa no `.env`)
   - Name: `OPENAI_MODEL`
   - Value: `gpt-4.1-mini`

**Importante**: Secrets ficam ocultos para visitantes. Variables aparecem no log público mas servem para config não-sensível.

## Passo 3 · Subir os arquivos

Você tem duas opções: upload manual via UI ou git push. Recomendo git.

### Opção A · git push (recomendado)

```bash
# No seu Codespaces, terminal:

# 1. Clone o repositório do Space ao lado do projeto
cd /tmp
git clone https://huggingface.co/spaces/<SEU_USER>/<NOME_SPACE>
cd <NOME_SPACE>

# 2. Copie os 3 arquivos do deploy + tudo de src/ e config/
cp -r /workspaces/aula07-agentes/deploy/* .
cp -r /workspaces/aula07-agentes/src ./src
cp -r /workspaces/aula07-agentes/config ./config

# 3. Commit e push (HF aceita push direto)
git add .
git commit -m "deploy: agente aula07 no HF Space"
git push
```

O Space vai detectar `app.py` na raiz, instalar `requirements.txt`,
e em ~2 minutos seu agente estará público.

### Opção B · upload manual via UI

1. No Space, aba **Files**.
2. Clique em **Add file → Upload files**.
3. Suba os arquivos nesta estrutura na raiz do Space:

```
<seu-space>/
├── app.py                ← do deploy/app.py
├── requirements.txt      ← do deploy/requirements.txt
├── README.md             ← este arquivo (opcional)
├── src/                   ← pasta inteira
│   ├── __init__.py
│   ├── config.py
│   ├── llm.py
│   ├── agents/
│   │   ├── __init__.py
│   │   ├── single_agent.py
│   │   └── multi_agent.py
│   └── tools/
│       └── ... (todos os 6 arquivos)
└── config/
    └── products.yaml
```

4. Commit.

## Passo 4 · Aguardar build e validar

1. Volte à aba **App** do Space.
2. Verá um log de build:

```
===== Application Startup at 2026-MM-DD HH:MM =====
Installing requirements...
Successfully installed gradio openai langgraph ...
Running on local URL:  http://0.0.0.0:7860
```

3. Quando aparecer a UI Gradio, **clique em uma das perguntas-exemplo**.
4. Confirme que retorna resposta coerente em PT-BR.

## Limitações deste Space gratuito

| Limitação | Valor | Impacto |
|---|---|---|
| Timeout por requisição | 30 segundos | Multi-agente complexo pode estourar. Use single para chat. |
| Hardware | 2 vCPU, 16GB RAM | Suficiente — agente só faz I/O ao OpenAI. |
| Persistência | Nenhuma | Histórico de conversa some entre sessões. |
| Auth | Nenhuma | Qualquer pessoa com a URL usa sua chave OpenAI. |
| Sleep | 48h sem uso | Volta a rodar em ~30s na primeira requisição depois. |
| Rate limit OpenAI | sua quota | Se viralizar e sua conta zerar, Space para de responder. |

## O que NÃO usar este Space para

- Produção comercial real (sem auth, sem SLA, sem monitoramento).
- Dados sensíveis dos usuários (não há controle de acesso).
- Workloads pesados (timeout de 30s).
- Workflows multi-step de longa duração.

## Como atualizar depois

Sempre que mudar o código local:

```bash
cd /tmp/<NOME_SPACE>
cp -r /workspaces/aula07-agentes/src/* ./src/
git add .
git commit -m "update: ..."
git push
```

O Space rebuilda automaticamente em ~1-2 minutos.

## Próximos passos pós-Space

1. **Compartilhar a URL** com colegas, recrutadores, professores.
2. **Adicionar ao seu CV**: "Construí agente conversacional em LangGraph + OpenAI, publicado em HF Spaces. Acesso público: huggingface.co/spaces/...".
3. **Iterar com feedback real**: usuários diferentes encontram bugs diferentes. Anote, ajuste persona, faça push.
4. **Migrar para produção real** quando ficar grande: Render, Railway, Fly.io, AWS App Runner. Mas só quando precisar.

## Custos esperados

| Cenário | Custo/mês |
|---|---|
| Space gratuito + você testando | USD 0 (sem chamadas) |
| Space público com 10 visitantes/mês | USD 0.50 - 2.00 |
| Space viralizado com 1000 chamadas/dia | USD 30 - 100 |

Se viralizar, **desative o Space** ou adicione rate limit antes de virar Space pago.
