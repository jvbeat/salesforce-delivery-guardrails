# salesforce-delivery-guardrails

[![Tests](https://github.com/jvbeat/salesforce-delivery-guardrails/actions/workflows/tests.yml/badge.svg)](https://github.com/jvbeat/salesforce-delivery-guardrails/actions/workflows/tests.yml) [![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

Guardrails I use when delivering Salesforce projects with AI agents, so that known platform pitfalls are checked by a machine at command time instead of depending on someone's memory. Nothing in this repository contains client code, metadata or data.

## Install as a Claude Code plugin

```
/plugin marketplace add jvbeat/salesforce-delivery-guardrails
/plugin install salesforce-delivery-guardrails@salesforce-delivery-guardrails
```

The plugin registers the `sf` guard below as PreToolUse and PostToolUse hooks. Python 3 must be on the PATH.

## The `sf` guard

[sf-guard.py](claude-code/sf-guard.py) runs before and after every Bash command the agent issues. Before an `sf` command, it blocks deploy, retrieve, Apex runs and tests, permission set assignment, data operations and describe when `--target-org` is missing. Anyone who serves several clients tends to have a global default org pointing at another client, and a command without an explicit target lands there.

After a deploy or a describe, the guard hands the agent the reminder that matches what just happened:

- Deploying a permission set does not assign it, so the deploying user cannot see the new field.
- A Flow deploys as Draft, and the previous version stays active.
- A new field deploys without FLS and does not show on the page.
- A failed deploy rolls back the whole batch, so the check is a retrieve, not the log.
- Describe answers with the session user's FLS, so a missing field there does not prove the field is missing.

The tests run the hook the same way Claude Code does:

```
python3 -m unittest discover -s claude-code -p 'test_*.py'
```

To wire the hook by hand instead of installing the plugin, copy the script to `~/.claude/scripts/` and merge [settings.example.json](claude-code/settings.example.json) into `~/.claude/settings.json`.

## Code Analyzer gate for GitHub Actions

[code-analyzer.yml](github-actions/code-analyzer.yml) runs Salesforce Code Analyzer v5 on every pull request and every push to main. The gate fails on any critical violation and on new high violations in the files the pull request changed, so old debt does not block delivery and new code does not ship with a serious violation.

Copy the workflow to `.github/workflows/` and [code-analyzer-ci.yml](github-actions/code-analyzer-ci.yml) to `.github/`.

## Local scan before delivery

The Graph Engine security rules, such as `ApexFlsViolation` and `DatabaseOperationsMustUseWithSharing`, are not part of the `Recommended` selector. The scan before each delivery therefore adds both selectors:

```
sf code-analyzer run --workspace ./force-app --target <changed files> --rule-selector Recommended --rule-selector sfge
```

`--workspace` takes the whole project because the Graph Engine builds the call graph from it, and `--target` limits the results to the changed files.

<details>
<summary>Em português</summary>

Travas que uso na entrega de projetos Salesforce com agentes de IA, para que armadilhas conhecidas da plataforma sejam conferidas por máquina no momento do comando, e não dependam da memória de quem executa. Nenhum arquivo deste repositório contém código, metadado ou dado de cliente.

Para instalar como plugin do Claude Code, use os dois comandos da seção "Install as a Claude Code plugin". O plugin registra o guard do `sf` como hook antes e depois de cada comando Bash.

Antes de um comando `sf`, o guard bloqueia deploy, retrieve, execução e teste de Apex, atribuição de permission set, operação de dados e describe sem `--target-org`. Quem atende vários clientes costuma ter a org padrão global apontando para outro cliente, e um comando sem alvo explícito cai nela. Depois de um deploy ou de um describe, o guard devolve ao agente o lembrete da armadilha correspondente: permission set sobe sem ser atribuído, Flow sobe em Draft, campo novo sobe sem FLS, deploy com falha reverte o lote inteiro e describe responde pelo FLS do usuário da sessão.

O workflow do Code Analyzer barra violação crítica em qualquer arquivo e violação alta nova nos arquivos alterados do pull request. Antes de cada entrega, o scan local inclui as regras de segurança do Graph Engine, que o seletor `Recommended` não traz.

</details>
