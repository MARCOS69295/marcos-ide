## 31.0.0 — Autonomous AI Engineering Workbench

- Adicionada listagem de modelos Gemini acessíveis com suporte declarado a `generateContent`.
- Adicionada seleção de modelo em tempo de execução, validada contra a listagem da chave.
- Adicionado status detalhado de conexão sem exposição de credenciais.
- Implementadas tentativas limitadas com espera progressiva para erros transitórios HTTP 500/502/503/504.
- Fallback opcional e explícito por `GEMINI_FALLBACK_MODELS`; não troca de modelo silenciosamente por padrão.
- Interface do Assistente ganhou controles para listar e selecionar modelos.
- Mantida a chave exclusivamente no backend.

## 31.0.0 — Autonomous Multi-Agent Coding System

- Novo endpoint `/api/agents/implement` para geração de propostas de implementação, correção, refatoração e testes com Gemini.
- Saída estruturada em JSON validado antes de ser aceita.
- Propostas passam pelo mecanismo de diff da versão 28.0; nenhum arquivo é gravado sem aprovação explícita.
- Limites de entrada, quantidade de arquivos e tamanho de proposta.
- Testes automatizados para validação, resposta inválida e ausência de gravação automática.

## Segurança

O agente não executa comandos, não aplica alterações e não faz commits. O desenvolvedor deve revisar o diff e aprovar a aplicação pela API de alterações.

## 31.0.0 — Autonomous AI Engineering Workbench

- Adicionado painel de métricas locais de chamadas e tokens, usando `usageMetadata` quando retornado pelo Gemini.
- Adicionado endpoint de diagnóstico da integração sem expor a chave da API.
- Adicionado cache de respostas opcional, em memória, com TTL configurável; permanece desativado por padrão para evitar armazenar prompts/código sem consentimento.
- Adicionados controles de uso e diagnóstico no Assistente Gemini.
- Multiagente agora aceita modelos especializados opcionais por papel: `GEMINI_MODEL_ARCHITECT`, `GEMINI_MODEL_SECURITY`, `GEMINI_MODEL_QUALITY` e `GEMINI_MODEL_COORDINATOR`; na ausência deles, usa o modelo principal.
- Métricas são locais à execução do servidor e não estimam custos monetários, pois preços e faturamento dependem do modelo, região e condições da conta.
