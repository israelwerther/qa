# Diretrizes e Regras do Acervo de QA

## 🚨 SEGURANÇA GIT: PROIBIÇÃO DE COMMIT E PUSH AUTÔNOMO

1. **JAMAIS DAR GIT PUSH:** É terminantemente proibido executar `git push` para qualquer repositório remoto.
2. **JAMAIS COMMITAR SEM PEDIDO DO USUÁRIO:** A IA nunca deve executar `git commit` por conta própria. Toda e qualquer alteração deve ser apresentada ao usuário para revisão prévia. O commit só pode ocorrer sob ordem expressa no chat.
3. **ISOLAMENTO TOTAL DO LIZEEDU:** NUNCA commitar ou adicionar arquivos deste acervo no repositório principal `lizeedu`. Toda integração local deve residir estritamente em `.git/info/exclude`.

## 🛡️ PREVENÇÃO DE FALSOS POSITIVOS: SCHEMA DRIFT DE BANCO DE DADOS

1. **IDENTIFICAÇÃO DE RESÍDUOS DE OUTRAS BRANCHS:** Ao se deparar com erros de integridade (`IntegrityError`, `NotNullViolation`, `UndefinedColumn`), verifique SEMPRE se o campo existe no modelo Django (`models.py`) da branch atual.
2. **PROIBIDO IMPUTAR COMO BUG DA FEATURE:** Se a coluna não pertence ao código desta branch, NUNCA registre o erro como bug no Plano de Testes. Trata-se de contaminação de banco local por migrations de outras branches paralelas.
3. **ZERO MUTAÇÃO AUTÔNOMA DE BANCO:** A IA está terminantemente proibida de executar comandos `DROP COLUMN`, `ALTER TABLE` ou manipulações DDL no banco de dados por iniciativa própria.
4. **COMUNICAR PARA DECISÃO DO USUÁRIO:** A IA deve apenas relatar a coluna e tabela residual identificada e fornecer o comando SQL sugerido para o desenvolvedor auditar e executar manualmente.
