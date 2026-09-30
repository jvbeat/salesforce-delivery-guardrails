"""Testes do sf-guard.py: executam o hook como o Claude Code executa, com o evento no stdin."""
import json
import subprocess
import sys
import unittest
from pathlib import Path

HOOK = Path(__file__).with_name('sf-guard.py')


def executar(evento, comando):
    entrada = {'hook_event_name': evento, 'tool_name': 'Bash', 'tool_input': {'command': comando}}
    saida = subprocess.run([sys.executable, str(HOOK)], input=json.dumps(entrada),
                           capture_output=True, text=True, check=True).stdout.strip()
    return json.loads(saida)['hookSpecificOutput'] if saida else None


class PreToolUse(unittest.TestCase):
    def test_bloqueia_deploy_sem_alvo(self):
        resultado = executar('PreToolUse', 'sf project deploy start --source-dir force-app')
        self.assertEqual(resultado['permissionDecision'], 'deny')

    def test_bloqueia_consulta_de_dados_sem_alvo(self):
        resultado = executar('PreToolUse', 'sf data query --query "SELECT Id FROM Account"')
        self.assertEqual(resultado['permissionDecision'], 'deny')

    def test_libera_deploy_com_alvo_curto(self):
        self.assertIsNone(executar('PreToolUse', 'sf project deploy start --source-dir force-app -o homolog'))

    def test_libera_deploy_com_alvo_longo_e_igual(self):
        self.assertIsNone(executar('PreToolUse', 'sf project deploy start --target-org=homolog'))

    def test_ignora_comando_que_nao_toca_org(self):
        self.assertIsNone(executar('PreToolUse', 'sf plugins install code-analyzer'))

    def test_ignora_comando_que_nao_e_sf(self):
        self.assertIsNone(executar('PreToolUse', 'git status'))


class PostToolUse(unittest.TestCase):
    def test_lembra_atribuicao_depois_de_deploy_de_permission_set(self):
        resultado = executar('PostToolUse', 'sf project deploy start -m PermissionSet:Vendas -o homolog')
        self.assertIn('sf org assign permset', resultado['additionalContext'])

    def test_lembra_ativacao_depois_de_deploy_de_flow(self):
        resultado = executar('PostToolUse', 'sf project deploy start -m Flow:Boas_Vindas -o homolog')
        self.assertIn('Draft', resultado['additionalContext'])

    def test_lembra_fls_depois_de_describe(self):
        resultado = executar('PostToolUse', 'sf sobject describe --sobject Account -o homolog')
        self.assertIn('FieldDefinition', resultado['additionalContext'])


if __name__ == '__main__':
    unittest.main()
