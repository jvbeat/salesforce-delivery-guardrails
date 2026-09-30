# salesforce-delivery-guardrails

[![Testes do sf-guard](https://github.com/jvbeat/salesforce-delivery-guardrails/actions/workflows/tests.yml/badge.svg)](https://github.com/jvbeat/salesforce-delivery-guardrails/actions/workflows/tests.yml)

Travas que uso na entrega de projetos Salesforce para que regras de plataforma já conhecidas sejam conferidas por máquina no momento do comando, e não dependam da memória de quem executa. Nenhum arquivo deste repositório contém código, metadado ou dado de cliente.

## Hook do Claude Code para o Salesforce CLI

O [sf-guard.py](claude-code/sf-guard.py) é um hook de PreToolUse e PostToolUse para o Claude Code. Antes de o agente executar um comando `sf`, o hook bloqueia deploy, retrieve, execução de Apex, atribuição de permission set e operação de dados sem `--target-org`. Quem atende vários clientes costuma ter a org padrão global apontando para outro cliente, e um comando sem alvo explícito cai nela.

Depois de um deploy ou de um describe, o hook devolve ao agente o lembrete da armadilha correspondente:

- O permission set sobe sem ser atribuído, e o próprio usuário do deploy não enxerga o campo novo.
- O Flow sobe em Draft, e a versão anterior continua ativa.
- O campo novo sobe sem FLS e não aparece na tela.
- Um deploy com falha reverte o lote inteiro, e a conferência é feita por retrieve.
- O describe responde pelo FLS do usuário da sessão, e campo ausente ali não prova que o campo não existe.

Para instalar, copie o script para `~/.claude/scripts/` e acrescente os hooks de [settings.example.json](claude-code/settings.example.json) ao `~/.claude/settings.json`. Os testes executam o hook do mesmo jeito que o Claude Code:

```
python3 -m unittest discover -s claude-code -p 'test_*.py'
```

## Gate do Code Analyzer no GitHub Actions

O [code-analyzer.yml](github-actions/code-analyzer.yml) executa o Salesforce Code Analyzer v5 a cada pull request e a cada push na main. O gate barra violação crítica em qualquer arquivo e violação alta nova nos arquivos alterados do pull request, para que a dívida antiga não trave a entrega e o código novo não entre com violação grave.

Para instalar, copie o workflow para `.github/workflows/` e o [code-analyzer-ci.yml](github-actions/code-analyzer-ci.yml) para `.github/`.

## Gate local antes de entregar

As regras de segurança do Graph Engine, como `ApexFlsViolation` e `DatabaseOperationsMustUseWithSharing`, não fazem parte do seletor `Recommended`. Por isso, antes de cada entrega, o scan local inclui os dois seletores:

```
sf code-analyzer run --workspace ./force-app --target <arquivos alterados> --rule-selector Recommended --rule-selector sfge
```

O `--workspace` recebe o projeto inteiro, porque o Graph Engine monta o grafo de chamadas a partir dele, e o `--target` limita o resultado aos arquivos alterados.

<details>
<summary>In English</summary>

Guardrails I use when delivering Salesforce projects, so that known platform pitfalls are checked by a machine at command time instead of relying on memory. No file in this repository contains client code, metadata or data.

- `claude-code/sf-guard.py` is a Claude Code hook that blocks `sf` commands touching an org (deploy, retrieve, Apex, permission set assignment, data) when `--target-org` is missing, and reminds the agent of the matching pitfall after a deploy or describe: permission sets are not assigned on deploy, Flows deploy as Draft, new fields have no FLS, a failed deploy rolls back the whole batch, and describe is filtered by the session user's FLS.
- `github-actions/code-analyzer.yml` runs Salesforce Code Analyzer v5 on every pull request and push to main, failing on any critical violation and on new high violations in changed files.
- Before every delivery, a local scan adds the Graph Engine security rules (`--rule-selector sfge`), which the `Recommended` selector does not include.

</details>
