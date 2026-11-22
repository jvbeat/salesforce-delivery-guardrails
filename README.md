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
- A Lightning page, layout, quick action or validation rule changes the create, edit and clone windows, and a page with field sections builds those windows from its own sections, not from the layout.

The reminders also follow deploys made through the `deploy_metadata` tool of the Salesforce DX MCP server, whatever name the server has in your configuration.

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

## Custom rules: declared access mode

From API version 67.0, an Apex database operation without a declared access mode runs in user mode and enforces the running user's object and field permissions. Up to API version 66.0, the default is system mode. A trigger, scheduled job or batch that reads a field the running user cannot see then fails, and when a trigger handler catches the exception, nothing shows on screen. In client projects, failures like these went unnoticed for days, once for a month, because everyone who tested was an administrator.

[declared-access-mode.xml](code-analyzer-rules/declared-access-mode.xml) adds two PMD rules to Code Analyzer:

- `SoqlWithoutAccessMode` flags static SOQL without `WITH SYSTEM_MODE`, `WITH USER_MODE` or `WITH SECURITY_ENFORCED`.
- `DatabaseCallWithoutAccessLevel` flags `Database.insert`, `update`, `upsert`, `delete`, `undelete`, `merge`, `query`, `countQuery` and `getQueryLocator` without `AccessLevel`, unless the query text itself carries the mode.

Both skip test classes and test data factories (class name containing `TestFactory`). They only check that a mode is declared; the choice stays with the developer: system mode for automation, user mode for screen controllers. Keyword DML (`insert`, `update`) is not checked, because the PMD tree does not tell `insert as system` from a plain `insert`.

To use them in a project, copy the file to `config/code-analyzer-rules/` and reference it in `code-analyzer.yml` at the project root, for the local scan, and in `.github/code-analyzer-ci.yml`, for the workflow, where [code-analyzer-ci.yml](github-actions/code-analyzer-ci.yml) has the block ready to uncomment:

```yaml
engines:
  pmd:
    custom_rulesets:
      - "config/code-analyzer-rules/declared-access-mode.xml"
```

The rules ship with severity 3 (Moderate), so they report without blocking. Measure the existing violations, declare the mode in those classes, and then change `<priority>` to 2 (High), so the gate blocks a new violation in the files a pull request changes. Changing an API 67 class to system mode changes its behavior for users without field access, which is the point; on API 66 and earlier the declaration only makes the existing behavior explicit.

The [fixtures](code-analyzer-rules/test/fixtures) prove each rule with flagged and clean examples, and the `regras` job in the test workflow runs them on every change.

<details>
<summary>Em português</summary>

Travas que uso na entrega de projetos Salesforce com agentes de IA, para que armadilhas conhecidas da plataforma sejam conferidas por máquina no momento do comando, e não dependam da memória de quem executa. Nenhum arquivo deste repositório contém código, metadado ou dado de cliente.

Para instalar como plugin do Claude Code, use os dois comandos da seção "Install as a Claude Code plugin". O plugin registra o guard do `sf` como hook antes e depois de cada comando Bash.

Antes de um comando `sf`, o guard bloqueia deploy, retrieve, execução e teste de Apex, atribuição de permission set, operação de dados e describe sem `--target-org`. Quem atende vários clientes costuma ter a org padrão global apontando para outro cliente, e um comando sem alvo explícito cai nela. Depois de um deploy ou de um describe, o guard devolve ao agente o lembrete da armadilha correspondente: permission set sobe sem ser atribuído, Flow sobe em Draft, campo novo sobe sem FLS, deploy com falha reverte o lote inteiro e describe responde pelo FLS do usuário da sessão. Página, layout, ação rápida e regra de validação mudam as janelas de criar, editar e clonar, e o guard também lembra disso. Os lembretes valem ainda para o deploy feito pela ferramenta `deploy_metadata` do servidor MCP do Salesforce DX.

O workflow do Code Analyzer barra violação crítica em qualquer arquivo e violação alta nova nos arquivos alterados do pull request. Antes de cada entrega, o scan local inclui as regras de segurança do Graph Engine, que o seletor `Recommended` não traz.

As regras próprias de modo declarado acusam consulta SOQL e chamada `Database` sem modo de acesso. A partir da API 67, a operação sem modo declarado executa em modo de usuário, e a automação falha calada para quem não lê o campo. As regras saem com severidade Moderate: o projeto mede as violações, declara o modo nas classes acusadas e só então sobe a severidade para High.

</details>
