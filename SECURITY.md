# Segurança e divulgação responsável

- Não execute arquivos `.marc` de origem desconhecida.
- Não exponha o servidor FastAPI da IDE à rede; a configuração desktop usa loopback local.
- Não armazene certificados PFX, senhas ou chaves privadas no repositório.
- Use secrets do GitHub Actions para certificados de assinatura e limite o acesso a quem pode editar workflows.
- Reporte vulnerabilidades ao mantenedor do projeto por um canal privado antes de publicação pública.
- A VM MARCOS é experimental e não deve ser tratada como sandbox para código hostil.


## Recursos do Laboratório 16.0
- O servidor local deve escutar apenas em `127.0.0.1`; não publique a porta da IDE na rede.
- O executor Python roda código com os privilégios do usuário atual. O timeout de 15 segundos não constitui sandbox. Execute apenas código confiável.
- O scanner de segurança é heurístico e não substitui ferramentas SAST/DAST profissionais, revisão manual, testes e análise de dependências.
- O JupyterLab inicia em loopback e utiliza token aleatório. Não compartilhe a URL contendo o token.
- A integração Git cria commits somente após confirmação explícita na interface. Revise o status do repositório antes de confirmar.
- O workspace oculta `.git`, `.venv`, `.marcos_models`, `__pycache__` e checkpoints do explorador e impede a API de arquivos de acessar essas pastas internas.
- Os modelos são serializados com Joblib. Carregar arquivos `.joblib` não confiáveis pode executar código; mantenha a pasta `.marcos_models` protegida e não importe artefatos de terceiros.


## Deep Learning

Os modelos neurais usam arquivos de pesos `state_dict` e metadados JSON; o carregamento exige `weights_only=True`. Não substitua esse fluxo por carregamento de checkpoints arbitrários. Proteja a pasta `.marcos_dl_models`, mantenha a API vinculada a localhost e não exponha previsões sem autenticação, limitação de taxa e validação de autorização. Os modelos e datasets podem conter informações sensíveis.


## RAG e agentes — versão 16.0

- A base vetorial é armazenada em `.marcos_rag` dentro do workspace e não deve ser exposta por servidor público.
- A indexação aceita somente arquivos `.txt` e `.md`, com limites de quantidade e tamanho.
- A indexação é local. Perguntas RAG e agentes podem enviar trechos selecionados e código para o provedor de IA configurado.
- Agentes possuem ferramentas em allowlist e não executam código nem alteram arquivos.
- Vetores por hashing são recursos lexicais/estatísticos; para embeddings densos configure um modelo local previamente instalado.
- Não indexe dados sigilosos ou pessoais sem base legal e autorização.


## ONNX Runtime e avaliação Transformer — versão 23.0
- ONNX Runtime nesta versão executa inferência em CPU e deve consumir somente artefatos ONNX gerados e mantidos no diretório de modelos da IDE.
- A comparação PyTorch/ONNX verifica proximidade numérica de logits; não certifica a qualidade do modelo.
- A avaliação de Transformers usa modelo e tokenizer locais, `local_files_only=True` e `trust_remote_code=False`.
- Use dataset de avaliação independente do treinamento; resultados sobre os mesmos dados usados no fine-tuning não estimam generalização.
- Modelos e datasets podem conter dados pessoais ou confidenciais; restrinja acesso ao workspace.
