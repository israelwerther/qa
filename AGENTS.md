# Diretrizes e Regras do Acervo de QA

## 🚨 SEGURANÇA GIT: PROIBIÇÃO DE COMMIT E PUSH AUTÔNOMO

1. **JAMAIS DAR GIT PUSH:** É terminantemente proibido executar `git push` para qualquer repositório remoto.
2. **JAMAIS COMMITAR SEM PEDIDO DO USUÁRIO:** A IA nunca deve executar `git commit` por conta própria. Toda e qualquer alteração deve ser apresentada ao usuário para revisão prévia. O commit só pode ocorrer sob ordem expressa no chat.
3. **ISOLAMENTO TOTAL DO LIZEEDU:** NUNCA commitar ou adicionar arquivos deste acervo no repositório principal `lizeedu`. Toda integração local deve residir estritamente em `.git/info/exclude`.
