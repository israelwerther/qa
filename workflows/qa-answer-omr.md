---
description: Gera documentos PDF de cartões resposta preenchidos (OMR) para simulação de envios e testes de pendências
---

# Workflow: Responder Cartões Resposta OMR para QA (`/qa-responder-gabarito`)

Este comando gera documentos PDF reais contendo as folhas de resposta oficiais dos alunos de uma aplicação da Lize Edu, com as bolinhas pré-preenchidas com cenários de teste controlados.

Isso elimina completamente a necessidade de abrir Canva, Photoshop ou ferramentas externas para pintar bolinhas na mão.

---

**Input**: O texto após `/qa-responder-gabarito` pode especificar a aplicação, quantidade de alunos ou modo de teste.  
*Exemplos:*
- `/qa-responder-gabarito` (Pega a aplicação mais recente e gera cartões com pendências)
- `/qa-responder-gabarito para a aplicação "Simulado Multi-Áreas"`
- `/qa-responder-gabarito -a 25ae717c-ad29-46f8-8c61-0ccb94ec1399 -sc 5`
- `/qa-responder-gabarito com 100% das questões respondidas` (Modo all-answered)

---

## Cenários de Teste Gerados por Padrão (`--mode pendings`)

Para validar perfeitamente telas de triagem de pendências (como a task ClickUp `86ak023yy`):
- **Aluno 1:** 100% respondido (não gera pendência)
- **Aluno 2:** 1 questão em branco (gera pendência por questão não respondida)
- **Aluno 3:** 1 questão com marcação dupla (gera pendência por dupla marcação)
- **Demais Alunos:** 100% respondidos

---

## Como Executar

Via atalho shell:
```bash
./.ai_qa_acervo/scripts/generators/responder-gabarito.sh [FLAGS]
```

Ou via Python:
```bash
./venv/bin/python .ai_qa_acervo/scripts/generators/answer_omr_sheets.py [FLAGS]
```

### Flags Disponíveis:
- `-a` / `--application`: UUID ou nome do caderno/aplicação (se omitido, usa a mais recente).
- `-sc` / `--students-count`: Quantidade de alunos a gerar no PDF (default: 4).
- `-m` / `--mode`:
  - `pendings`: (padrão) Gera mix com respostas corretas, questão em branco e dupla marcação.
  - `all-answered`: Todas as questões preenchidas.
  - `all-blank`: Todas as questões em branco.
- `-o` / `--output`: Caminho do arquivo PDF de saída (default: `data/gabaritos_qa/cartoes_respondidos_<nome>.pdf`).

---

## Fluxo de Uso Recomendado

1. Execute o comando para gerar o PDF preenchido.
2. O arquivo será salvo em `data/gabaritos_qa/`.
3. Abra o navegador em `/gabaritos/` (Gabaritos → Enviar respostas).
4. Clique em **"Enviar respostas"**, selecione a aplicação correspondente e anexe o PDF gerado.
5. Valide a listagem de pendências e o fluxo de resolução!
