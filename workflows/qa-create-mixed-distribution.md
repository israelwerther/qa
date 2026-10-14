---
description: Cria cadernos e aplicações sincronizadas (ou o próprio ensalamento) para testes de ensalamento misto e malote
---

# Workflow: Criar Dados para Ensalamento Misto (`/qa-criar-ensalamento-misto`)

Este comando gera uma massa de dados completa e sincronizada para testar a funcionalidade de **Ensalamento Misto com Cartão por Caderno** (Task `#86ak8wuvc`):
1. **Caderno 1 — Somatório até 15 questões (`10Q`)**: Prova com proposições binárias para testar o cartão somatório tradicional (folha única).
2. **Caderno 2 — Somatório Amplo (`18Q Somatório + 5Q Objetivas`)**: Prova com mais de 15 questões de somatório para testar o cartão somatório expandido e folha Lize adicional.
3. **Caderno 3 — Apenas Objetivas (`10Q`)**: Prova de múltipla escolha tradicional (A-E) para testar o modelo de cartão escolhido no modal (Lize, ENEM ou Bolhas Ampliadas).
4. **Caderno 4 — Discursiva / Redação**: Prova discursiva para validar a geração de folha de respostas textual na mesma sala.
5. **Caderno 5 — Formato PAS (Bloqueio)**: Prova no formato PAS para validar o teste negativo de bloqueio inegociável.
6. **Aplicações Presenciais Sincronizadas**: Criadas para o mesmo dia e mesmo horário (14:00 às 18:00), vinculadas à mesma turma e coordenação.
7. *(Opcional)* **Criação do Ensalamento (`--ensalar`)**: Cria o objeto `RoomDistribution` no banco com as 4 aplicações mistas alocadas nas salas e distribui os alunos, deixando pronto para testar diretamente o modal de impressão de malote.

---

**Input**: O texto passado após `/qa-criar-ensalamento-misto` pode conter data, cliente ou instruções para já ensalar.  
*Exemplos:*
- `/qa-criar-ensalamento-misto` (Gera aplicações para a data de hoje no cliente da sessão ativa)
- `/qa-criar-ensalamento-misto para 2026-10-15` (Gera para uma data específica)
- `/qa-criar-ensalamento-misto para amanhã` (Gera para o dia seguinte)
- `/qa-criar-ensalamento-misto já criando o ensalamento` (Passa `--ensalar` para gerar direto no banco)
- `/qa-criar-ensalamento-misto no cliente "Rede Decisão"` (Direciona para um cliente específico)
- `/qa-criar-ensalamento-misto um ensalamento de cada tipo` (Passa `--all-types` para gerar ensalamento misto, somatório puro, objetivas puras e aplicações livres)
- `/qa-criar-ensalamento-misto com 2 alunos por aplicação e já ensalado`

---

## Passos de Execução para a IA

### 1. Interpretar a Solicitação do Usuário

Analise o texto fornecido pelo usuário e extraia os seguintes parâmetros:
- **Data (`--date` / `-d`)**: Data da prova. Aceita `YYYY-MM-DD`, `hoje`, `amanha`, `+1`, etc. Se omitido, usa a data atual.
- **Cliente (`--client` / `-c`)**: Nome ou UUID do cliente (ex.: "Rede Decisão"). Se omitido, o script detecta automaticamente a sessão ativa do navegador.
- **Horário Inicial (`--start` / `-s`)**: Default `14:00`.
- **Horário Final (`--end` / `-e`)**: Default `18:00`.
- **Turma (`--turma`)**: Nome da turma. Se omitido, usa a primeira turma da coordenação.
- **Alunos por Aplicação (`--students-per-app`)**: Quantidade de alunos por prova (default: `2`).
- **Suíte Completa / Todos os Tipos (`--all-types` ou `--type all`)**: Ativar se o usuário pedir "todos os tipos", "um de cada tipo", "suíte completa", "cenários completos". Gera os 3 tipos de ensalamentos prontos (misto, 100% somatório, 100% objetivas) + aplicações livres.
- **Tipo Específico (`--type` / `-t`)**: `mixed` (default), `sum` (só somatório), `choice` (só objetivas).
- **Criar Ensalamento Pronto (`--ensalar`)**: Ativar se o usuário mencionar "já ensalar", "criar ensalamento", "testar malote", "pronto para malote", "já distribuir salas".
- **Manter Aplicações Livres (`--keep-free-apps`)**: Ativar se o usuário quiser testar a criação na UI mesmo com `--ensalar`.

---

### 2. Executar o Script

Verifique o ambiente de execução:

#### Opção A — Docker (quando o container `web` estiver em execução)
```bash
docker compose exec --no-TTY web python /code/.ai_qa_acervo/scripts/generators/create_mixed_distribution_data.py [FLAGS]
```

#### Opção B — Local via venv (ambiente padrão de QA)
```bash
./venv/bin/python .ai_qa_acervo/scripts/generators/create_mixed_distribution_data.py [FLAGS]
```
*(ou usando o wrapper executável: `./.ai_qa_acervo/scripts/generators/create-mixed-distribution.sh [FLAGS]`)*

*Exemplo comum:*
```bash
./venv/bin/python .ai_qa_acervo/scripts/generators/create_mixed_distribution_data.py --date hoje
```

*Exemplo com ensalamento automático criado:*
```bash
./venv/bin/python .ai_qa_acervo/scripts/generators/create_mixed_distribution_data.py --date hoje --ensalar
```

---

### 3. Apresentar o Resultado e Próximos Passos de QA

Ao concluir a execução do script:
1. Informe a **Data**, o **Cliente**, a **Coordenação** e os **Cadernos/Aplicações** criados.
2. Se **NÃO** usou `--ensalar`:
   - Forneça o link direto para a tela de cadastro: `http://127.0.0.1:8000/ensalamento/criar/?date=AAAA-MM-DD`.
   - Instrua o usuário a marcar o Caderno 1 (Somatório) e o Caderno 3 (Objetivas) para validar a ausência de alerta de bloqueio.
   - Instrua a marcar o Caderno 5 (PAS) para validar o alerta impeditivo (teste negativo).
3. Se usou `--ensalar`:
   - Forneça o ID do ensalamento gerado e o link da listagem: `http://127.0.0.1:8000/ensalamento/`.
   - Oriente a clicar no botão de **Imprimir Malote** e conferir os rádios disponíveis (Folha Lize, ENEM, bolhas ampliadas) e o aviso informativo de somatório automático.
