---
name: 📝 Registro de Mudança (Change Request)
about: Formulário formal de abertura, aprovação e rastreio de uma mudança no sistema (etapa A do pipeline de GCS).
title: "[MUDANÇA] "
labels: registro-de-mudanca
assignees: ''
---

## 1. Identificação da Mudança

- **Solicitante:**
- **Data da solicitação:**
- **Tipo de mudança:** <!-- Feature | Correção (Bugfix) | Hotfix | Infraestrutura | Documentação -->
- **Prioridade:** <!-- Baixa | Média | Alta | Crítica -->

## 2. Descrição

<!-- O que precisa ser mudado e por quê? Qual problema isso resolve ou qual valor entrega? -->

## 3. Impacto Esperado

- **Ambientes afetados:** <!-- Homologação | Produção | Ambos -->
- **Afeta o banco de dados?** <!-- Sim/Não. Se sim, qual migration será criada? -->
- **Risco estimado:** <!-- Baixo | Médio | Alto -->
- **Plano de rollback:** <!-- Como desfazer a mudança caso algo dê errado? -->

## 4. Critérios de Aceite

<!-- Lista do que precisa ser verdade para considerar a mudança concluída -->
- [ ]
- [ ]

## 5. Aprovação

- [ ] Aprovado por: ____________________ (Responsável técnico)
- [ ] Testes automatizados cobrindo a mudança
- [ ] Análise de qualidade de código (SonarQube + Mess Detector) sem novos problemas críticos/bloqueadores

## 6. Rastreabilidade

- **Branch/Commit relacionado:**
- **Pull Request:**
- **Build/Pipeline (run_ci.sh):** <!-- link ou hash do log de execução -->