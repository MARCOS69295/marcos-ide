# Publicação no GitHub — MARCOS IDE 31.0.0

Este pacote foi preparado para versionamento. Antes de publicar, confirme que não há chaves, tokens, dados pessoais, datasets privados ou arquivos de projetos de clientes.

## Requisitos
- Git instalado
- Conta GitHub
- Python instalado para executar/testar localmente

## Criar o repositório
1. No GitHub, selecione **New repository**.
2. Nome sugerido: `marcos-ide`.
3. Escolha Public ou Private conforme sua decisão.
4. Para evitar conflitos, crie o repositório vazio (sem README, .gitignore ou licença).

## Enviar pelo PowerShell
Abra o PowerShell dentro desta pasta e execute:

```powershell
git init
git add .
git status
```

Revise a lista: não deve conter `.env`, chaves, tokens, ambientes virtuais, caches ou dados privados. Depois:

```powershell
git commit -m "Initial release: MARCOS IDE 31.0.0"
git branch -M main
git remote add origin https://github.com/SEU_USUARIO/marcos-ide.git
git push -u origin main
```

Substitua `SEU_USUARIO` pelo seu login GitHub. O Git poderá abrir o navegador para autenticação. Nunca coloque senha ou token diretamente nos comandos.

## Segurança
- Configure `GEMINI_API_KEY` como variável de ambiente local.
- Nunca publique chaves de API, `.env`, certificados privados ou dados de clientes.
- Se uma chave já foi exposta, revogue-a no provedor e gere outra.
- `.env.example` é apenas um modelo vazio; não coloque credenciais nele.

## Licença
Nenhuma licença foi escolhida automaticamente. Defina uma licença antes de permitir reutilização, distribuição ou contribuição por terceiros.
