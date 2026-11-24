# MARCOS IDE 31.0.0 — Autonomous Multi-Agent Coding System

## Novidades desta versão
- Provedor do Assistente IA substituído por Google Gemini.
- Chat, análise assistida, agente consultivo e perguntas RAG utilizam a API Gemini.
- Configuração por variável de ambiente `GEMINI_API_KEY`.
- Modelo padrão configurável por `GEMINI_MODEL`; a lista real é consultada na API para a chave atual.
- Chave de API mantida no backend Python; não é enviada ao navegador.
- Integração via API REST oficial (`generateContent`), sem SDK adicional.

## Configurar o Gemini no Windows
1. Abra `CONFIGURAR_IA_WINDOWS.txt`.
2. Crie uma chave no Google AI Studio: https://aistudio.google.com/apikey
3. No PowerShell, defina as variáveis `GEMINI_API_KEY` e `GEMINI_MODEL` conforme o guia.
4. Feche a IDE e inicie novamente com `iniciar_marcOS.bat`.
5. Verifique `http://127.0.0.1:8000/api/ai/status`.

## Instalação e inicialização
1. Execute `instalar_windows.bat`.
2. Para MLOps/DL, execute `instalar_mlops.bat` e `instalar_pytorch_cpu.bat`.
3. Para ONNX e Transformers, consulte os arquivos `requirements-*.txt`.
4. Inicie com `iniciar_marcOS.bat`.

## APIs de IA
- `GET /api/ai/status` — status do Gemini.
- `POST /api/ai/chat` — assistente de programação.
- `POST /api/rag/ask` — perguntas sobre documentos indexados, com contexto enviado ao Gemini.
- `POST /api/agents/run` — agente consultivo com ferramentas locais permitidas.

## Demais recursos
- Inferência MLP exportada para ONNX Runtime CPU.
- Avaliação de Transformers fine-tuned em dataset JSONL.
- Recursos de ciência de dados, deep learning, MLOps, RAG e análise de código.

## Segurança e limitações
- A chave Gemini é armazenada nas variáveis de ambiente do usuário do Windows.
- O código e o contexto fornecidos ao Assistente/RAG são enviados ao Google para geração de resposta.
- Não envie segredos, credenciais, dados pessoais sensíveis ou código confidencial sem autorização.
- Os agentes são consultivos: não executam código nem modificam arquivos.
- ONNX Runtime usa CPU nesta versão.
- O instalador `.exe` deve ser compilado e testado no Windows.


## Validar a conexão com o Gemini

Depois de configurar `GEMINI_API_KEY` e reiniciar a IDE, abra o Assistente Gemini e clique em **Testar conexão real com Gemini**. Também é possível enviar `POST /api/ai/test`. O endpoint faz uma chamada mínima à API e confirma chave, modelo e conectividade; `/api/ai/status` informa apenas se a variável de chave está configurada.


## MARCOS IDE 25.0 — AI Workflow Studio
- Fluxos consultivos especializados com Gemini: revisão técnica, revisão defensiva de segurança, depuração orientada e geração de testes.
- Ações disponíveis no painel do Assistente Gemini e endpoint `POST /api/ai/workflow`.
- O fluxo apenas analisa e sugere: não executa código nem altera arquivos. Revise toda sugestão antes de aplicá-la.
- Corpo JSON: `{"task":"review|security|debug|tests|refactor","code":"...","context":"..."}`.

## Testes automatizados
Execute `python -m pytest -q` no ambiente de desenvolvimento. A suíte desta entrega contém testes unitários e de integração com chamadas ao Gemini simuladas; a conexão real exige `GEMINI_API_KEY` e deve ser validada pelo endpoint `POST /api/ai/test`.


## MARCOS IDE 25.0 — Gemini AI Developer Studio
- Perfis técnicos selecionáveis para Python, JavaScript/TypeScript, Java/Android, C/C++, C#/.NET, Web, Mobile, ML e Deep Learning.
- Modelos locais de projeto para API Python/FastAPI, aplicação Web HTML/CSS/JS, Android Java (base) e Machine Learning.
- Os modelos criam somente arquivos ausentes dentro do workspace e não sobrescrevem arquivos existentes.
- Inspeção Git local somente leitura: branch atual, status e últimos cinco commits.
- Endpoints: `POST /api/projects/scaffold` e `GET /api/git/status`.
- A integração Gemini continua exigindo `GEMINI_API_KEY`; o código enviado à IA é transmitido ao Google.


## MARCOS IDE 27.0 — Orquestração Multiagente
- Endpoint `POST /api/ai/multi-agent` coordena três análises independentes: arquitetura, segurança defensiva e qualidade de software.
- Um quarto pedido ao Gemini consolida as análises, destaca prioridades e produz um plano incremental.
- A interface do Assistente inclui o botão **Orquestrar 3 agentes IA**.
- Cada execução usa quatro chamadas à API Gemini; monitore os limites e custos da sua conta Google AI.
- O fluxo é consultivo: não executa código, não roda testes e não modifica arquivos. O código/contexto enviados são transmitidos ao Google.
- O endpoint limita a entrada a 31.000 caracteres e exige `GEMINI_API_KEY`.

### Testes
Execute `python -m pytest -q`. Os testes multiagentes simulam as quatro respostas; para validar comunicação real, configure `GEMINI_API_KEY` e use o teste de conexão.


## Execução segura na versão 27.0
A execução de código arbitrário é disponibilizada somente pelo endpoint `/api/sandbox/execute`, usando Docker instalado e ativo. Nesta versão são aceitos Python (`python:3.12-alpine`) e JavaScript (`node:22-alpine`). Para evitar downloads automáticos, as imagens devem existir localmente (`docker pull python:3.12-alpine` e `docker pull node:22-alpine`) antes de usar o recurso. O contêiner usa `--network=none`, filesystem raiz e montagem de fonte somente leitura, sem capabilities, com `no-new-privileges`, 192 MB de memória, 0,75 CPU, 32 processos e timeout de 8 segundos.

**Limites de segurança:** isso reduz bastante a superfície de risco, mas não é uma garantia absoluta contra vulnerabilidades do kernel, Docker ou runtime. Mantenha Docker atualizado, use Docker Desktop com isolamento habilitado e não execute workloads sensíveis em hosts compartilhados. A execução não é ativada automaticamente para as rotinas antigas da IDE; use especificamente o botão Sandbox. Java, C/C++ e C# não estão habilitados no sandbox 27.0.


## MARCOS IDE 28.0 — Engenharia assistida com aprovação

A versão 28.0 adiciona uma área para apresentar propostas de alterações em arquivos do workspace. A API valida caminhos e extensões, limita a proposta a 20 arquivos e 200 KB, apresenta diff unificado sem gravar arquivos e exige `approved: true` para aplicar. Cada aplicação gera um snapshot local que pode ser revertido mediante nova aprovação. A interface solicita confirmação antes de aplicar ou reverter.

**Limites:** a interface recebe propostas em JSON; a geração automática de patch diretamente pelo agente ainda é consultiva e requer que o desenvolvedor revise/forneça a proposta. O histórico de reversão fica na pasta privada `.marcos_change_history` dentro do workspace. Mantenha backup externo e não exponha a API sem autenticação em redes não confiáveis.


## Verificações da distribuição 28.0.0

A suíte local desta revisão passou com 116 testes automatizados. A compilação dos módulos Python e a verificação de sintaxe JavaScript também foram concluídas. A execução real do Docker e chamadas reais ao Gemini dependem do ambiente Windows/Docker e da chave API do usuário.


## MARCOS IDE 31.0 — Agente de implementação

O endpoint `POST /api/agents/implement` solicita ao Gemini uma proposta JSON para feature, bugfix, refactor ou testes. A resposta é validada e encaminhada ao fluxo de prévia/diff existente. O agente não grava arquivos, não executa comandos e não cria commits. A aplicação continua exigindo aprovação explícita em `/api/changes/{proposal_id}/apply`.

A validação automatizada usa respostas Gemini simuladas; para uso real configure `GEMINI_API_KEY`.


## MARCOS IDE 31.0 — Autonomous AI Engineering Workbench

- Modelo padrão configurável por `GEMINI_MODEL` (padrão desta entrega: `gemini-3.8-flash`, ajustável conforme modelos listados para sua chave).
- Política de novas tentativas limitada para erros transitórios HTTP 500, 502, 503 e 504; HTTP 429 não é repetido cegamente para evitar consumo inútil quando há quota esgotada.
- Espera progressiva configurável por `GEMINI_RETRY_ATTEMPTS` e `GEMINI_RETRY_BASE_SECONDS`.
- Fallback de modelo opcional via `GEMINI_FALLBACK_MODELS`, separado por vírgulas; permanece desativado se não configurado.
- `GET /api/ai/models` lista modelos visíveis à chave que anunciam `generateContent`; isso não garante disponibilidade instantânea.
- `POST /api/ai/model` seleciona um modelo listado para o processo atual. Para persistir, configure `GEMINI_MODEL` nas variáveis do Windows e reinicie a IDE.
- `GET /api/ai/connection/status` informa configuração e política de retry sem expor a chave.
- A interface permite listar e selecionar modelos. A seleção não testa geração; use o botão de teste real.

### Configuração opcional no Windows

```powershell
[Environment]::SetEnvironmentVariable("GEMINI_MODEL", "modelo-listado-no-seu-AI-Studio", "User")
[Environment]::SetEnvironmentVariable("GEMINI_RETRY_ATTEMPTS", "3", "User")
[Environment]::SetEnvironmentVariable("GEMINI_RETRY_BASE_SECONDS", "2", "User")
# Opcional: fallback somente se você confirmar que esses modelos estão acessíveis à sua chave
[Environment]::SetEnvironmentVariable("GEMINI_FALLBACK_MODELS", "modelo-alternativo-1,modelo-alternativo-2", "User")
```

O retry ajuda com indisponibilidade transitória, mas não corrige quota, chave inválida, permissão negada ou indisponibilidade persistente do provedor. Não há garantia de que uma repetição será bem-sucedida.

## MARCOS IDE 31.0 — Autonomous AI Engineering Workbench

### Monitoramento de uso e diagnóstico

- `GET /api/ai/usage`: apresenta chamadas bem-sucedidas, erros, acertos de cache, tokens de entrada/saída e modelos vistos desde a inicialização do servidor.
- `GET /api/ai/diagnostics`: apresenta modelo selecionado, tentativas, fallbacks e último erro sanitizado, sem retornar a chave.
- O uso de tokens é baseado em `usageMetadata` quando o Google inclui esses dados na resposta. A aplicação não calcula valores em dinheiro.

### Cache opcional

O cache fica **desativado por padrão** porque prompts podem conter código ou dados privados. Para habilitar conscientemente, configure `GEMINI_CACHE_ENABLED=1` e, opcionalmente, `GEMINI_CACHE_TTL_SECONDS=300` (máximo 3600). O cache é em memória, limitado a 200 entradas e desaparece quando o servidor reinicia. Evite habilitá-lo para prompts com segredos ou dados sensíveis.

### Modelos por agente (opcional)

O multiagente pode usar modelos distintos configurados por variável de ambiente: `GEMINI_MODEL_ARCHITECT`, `GEMINI_MODEL_SECURITY`, `GEMINI_MODEL_QUALITY` e `GEMINI_MODEL_COORDINATOR`. Cada modelo precisa estar disponível para a chave da API. Se as variáveis não forem definidas, todos usam `GEMINI_MODEL`.

### Limites importantes

- A telemetria é local e temporária; não é um relatório oficial de faturamento do Google.
- O fallback continua explícito por `GEMINI_FALLBACK_MODELS`.
- Erros HTTP 503 podem continuar ocorrendo por indisponibilidade do provedor; retry não garante sucesso.
- O cache não é persistente e não substitui controles de privacidade do projeto.
