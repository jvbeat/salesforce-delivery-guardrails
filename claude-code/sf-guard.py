#!/usr/bin/env python3
"""Guard mecânico para comandos `sf` executados pelo Claude Code (hook de Bash).

Regra escrita em prosa não é consultada na hora do comando. Este script confere
as armadilhas do Salesforce CLI no momento em que o agente vai executar o comando.

PreToolUse: bloqueia deploy, retrieve, apex run, org assign e data (query, import, delete...)
sem --target-org ou -o. Quem atende vários clientes costuma ter a org padrão global
apontando para outro cliente, e um comando sem alvo explícito cai nela.

PostToolUse: depois de deploy ou describe, devolve o lembrete que corresponde ao que subiu
(permission set não se atribui sozinho, Flow sobe em Draft, campo novo sobe sem FLS,
describe é cego por FLS).
"""
import json
import re
import sys

EXIGE_ALVO = re.compile(r'\bsf\s+(project\s+(deploy|retrieve)|apex\s+(run|test)|org\s+assign|data\s+\w+|sobject\s+describe)\b')
TEM_ALVO = re.compile(r'(^|\s)(-o|--target-org)(\s|=)')


def main():
    try:
        dados = json.load(sys.stdin)
    except Exception:
        return 0
    if dados.get('tool_name') != 'Bash':
        return 0
    cmd = (dados.get('tool_input') or {}).get('command', '') or ''
    evento = dados.get('hook_event_name', '')
    if not re.search(r'\bsf\s', cmd):
        return 0

    if evento == 'PreToolUse':
        if EXIGE_ALVO.search(cmd) and not TEM_ALVO.search(cmd):
            print(json.dumps({'hookSpecificOutput': {
                'hookEventName': 'PreToolUse',
                'permissionDecision': 'deny',
                'permissionDecisionReason': 'sf sem --target-org: o comando cairia na org padrão global, que pode ser de outro cliente. Repetir com -o <alias>.'}},
                ensure_ascii=False))
        return 0

    if evento == 'PostToolUse':
        avisos = []
        if re.search(r'sf\s+project\s+deploy', cmd):
            if re.search(r'permissionset|PermissionSet', cmd):
                avisos.append('Deploy de permission set não atribui: rodar sf org assign permset -n <nome> -o <alias>, senão o próprio usuário não enxerga campo custom e a suíte quebra por permissão.')
            if re.search(r'\bflows?\b|\bFlow\b', cmd):
                avisos.append('Deploy de Flow sobe em Draft e a versão antiga segue ativa: ativar por FlowDefinition (activeVersionNumber).')
            if re.search(r'\bfields?\b|CustomField|objects/', cmd):
                avisos.append('Campo novo sobe sem FLS: existe, entra no layout e não aparece. Dar FLS no permission set e atribuir.')
            avisos.append('Deploy Failed reverte o lote inteiro: conferir por retrieve o que ficou na org, não pelo log.')
        if re.search(r'sf\s+sobject\s+describe', cmd):
            avisos.append('Describe responde pelo FLS do usuário da sessão: campo ausente aqui não prova ausência. Confirmar por Tooling API em FieldDefinition.')
        if avisos:
            print(json.dumps({'hookSpecificOutput': {'hookEventName': 'PostToolUse',
                              'additionalContext': 'Guard sf: ' + ' '.join(avisos)}}, ensure_ascii=False))
    return 0


if __name__ == '__main__':
    sys.exit(main())
