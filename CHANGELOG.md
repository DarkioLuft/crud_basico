# Changelog — Registro de Mudanças

Este documento mantém o histórico formal de mudanças aplicadas ao sistema **CRUD de Receitas**,
servindo como evidência da etapa **A) Registro da Mudança** do pipeline de Gerência de
Configuração de Software (GCS).

Cada mudança é primeiro aberta como uma *Issue* no GitHub usando o template
[`Registro de Mudança`](.github/ISSUE_TEMPLATE/registro_mudanca.md), aprovada, implementada em uma
branch própria, validada pelo pipeline de CI (`run_ci.sh` — testes + Mess Detector + SonarQube) e,
só então, promovida para Homologação e Produção (`pipeline.sh`).

O formato segue [Keep a Changelog](https://keepachangelog.com/pt-BR/1.1.0/).

## [Não publicado]

### Adicionado
- Mess Detector / Linter (Pylint + plugin `pylint-django`) integrado ao pipeline de CI, com
  relatório consumido automaticamente pelo SonarQube (`sonar.python.pylint.reportPaths`).
- Geração de relatório de execução de testes (`test-report.xml`, formato JUnit) para estatísticas
  de aprovação/falha, além da cobertura já existente.
- Processo de Registro de Mudança via GitHub Issues (template dedicado) + este CHANGELOG.

### Corrigido
- `run_ci.sh`: contêiner efêmero de testes agora monta o código-fonte do host
  (`-v "$(pwd):/app"`), garantindo que `coverage.xml`, `test-report.xml` e
  `pylint-report.txt` sobrevivam após o `--rm` e fiquem disponíveis para o `sonar-scanner`.

<!--
Template para novas entradas (copie o bloco abaixo a cada mudança aprovada):

## [Issue #N] - AAAA-MM-DD
### Adicionado / Corrigido / Alterado / Removido
- Descrição da mudança.
- Issue: #N
- Responsável:
-->