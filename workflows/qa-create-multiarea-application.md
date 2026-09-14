---
description: Cria aplicação multi-área (Natureza, Humanas, Matemática) com 4 disciplinas, 30 questões reais e respostas calibradas para testes da tela de resultados do aluno
---

# Workflow: Criar Aplicação Multi-Área para QA (`/qa-create-multiarea-application`)

Este comando gera uma aplicação multi-área completa para testes das telas de resultados por área de conhecimento do aluno no Lize Edu, calibrada com 4 disciplinas (Biologia, Química, História e Matemática) e 30 questões 100% reais do banco de dados, com acertos e erros calibrados para popular as abas de desempenho, navegação restrita por área ("Visualizar") e a aba "Questões para revisar".

---

## 🎯 Finalidade do Cenário
- **4 Disciplinas agrupadas em 3 Áreas de Conhecimento:**
  - `Ciências da Natureza e suas Tecnologias` (Biologia + Química - 15 questões)
  - `Ciências Humanas e Sociais Aplicadas` (História - 8 questões)
  - `Matemática e suas Tecnologias` (Matemática - 7 questões)
- **30 Questões Reais**:
  - Habilita paginação completa de resultados no frontend (15 por página: Página 1 = Q1 a Q15, Página 2 = Q16 a Q30)
- **Aluna Alvo**:
  - `sarah-guimaraes-monteiro-515-515@email-temp.com.br` (SARAH GUIMARAES MONTEIRO)
  - ID da aplicação student fixo (`c58df2c4-5994-41c4-cf79-136db4e3946f`) para facilitar links diretos no navegador
- **Respostas Calibradas**:
  - Sarah erra 2 questões em cada matéria para validar a aba `"Questões para revisar"`, exibição de percentual de acertos da turma e abertura do painel lateral restrito àquela área.

---

## Passos de Execução para a IA

### 1. Executar o Gerador Multi-Área

Execute o comando via terminal:

```bash
./venv/bin/python .ai_qa_acervo/scripts/generators/create_multiarea_exam_application.py
```

Se o usuário especificar outro e-mail de aluno, utilize a flag:
```bash
./venv/bin/python .ai_qa_acervo/scripts/generators/create_multiarea_exam_application.py --student-email "<email_do_aluno>"
```

### 2. Apresentar o Resumo ao Usuário

Exiba:
1. ✅ **Confirmação da criação**: Nome do caderno, total de 30 questões e aluna vinculada.
2. 📊 **Distribuição das disciplinas e áreas**.
3. 🔗 **Link direto para o app do aluno**: `http://localhost:5173/painel/minhas-provas/c58df2c4-5994-41c4-cf79-136db4e3946f`.
