# MITRARR Automation Rebuild – Product Requirements Document (PRD)

## 1. Contexto e Visão
- O conjunto atual de scripts (`scripts_mitrarr`, `ws-nist`, `canaime`, `nist_downloader`, etc.) cresceu organicamente, sem uma arquitetura uniforme.
- Existem credenciais espalhadas em shell scripts, dependência explícita no ambiente da estação e ausência de cobertura de testes automatizados.
- Objetivo: reconstruir todo o ecossistema aplicando **DDD + Clean Architecture + SOLID + DRY**, sustentado por **TDD obrigatório** desde o primeiro commit.

## 2. Objetivos Funcionais
- Execução sempre em servidores Linux acessados remotamente via MobaXterm, exigindo automações que não dependam de TTY interativo.
1. **Ingestão de fontes externas** (IDNet, DETRAN-RR, CANAIME, SISMIGRA, backups FF) com normalização padronizada em lote ou streaming.
2. **Processamento interno** (adição de NISTs, relacionamentos, STIMAR, correções) em pipelines desacopladas, rastreáveis e idempotentes.
3. **Orquestração/agendamento** centralizada (substituir check+nohup improvisado por scheduler rastreável com replays).
4. **Monitoramento em tempo real** das pastas NIST e feedback operacional (watchdog + alertas).
5. **Governança de credenciais e configuração** via arquivos seguros ou secret manager, nunca embutidos em scripts.

## 3. Objetivos Não Funcionais
- **Testabilidade**: suites unitárias/integradas guiando o desenho (TDD).
- **Observabilidade**: logs estruturados, métricas (tempo de execução, itens processados), health checks.
- **Confiabilidade**: processos idempotentes e transações consistentes entre Oracle, PostgreSQL e FindFace.
- **Portabilidade**: ambientes reproduzíveis via containers/poetry/virtualenv + scripts `make` ou `just`.
- **Segurança e LGPD**: separação de permissões, rotação de segredos, uso de `.env` criptografado (e.g. `sops` ou `pass`) e cumprimento rigoroso da LGPD devido ao caráter de inteligência da operação.
- **Automação confiável**: scripts devem executar sozinhos conforme o `crontab -l` padronizado, sem depender de sessões abertas no MobaXterm.

## 4. Restrições e Premissas
- Continuará executando em servidores Linux semelhantes ao atual (`findface@ws2`), acessados via MobaXterm, com acesso a Oracle, PostgreSQL e APIs FindFace.
- Cron continuará disponível, mas a preferência é consolidar scheduling em um único **Scheduler Service**.
- Disponibilidade de Python 3.10+ e possibilidade de usar PostgreSQL/Redis auxiliares para filas.

## 5. DDD – Domínios e Bounded Contexts
1. **Acquisition Context**
   - Responsável por conectar em cada fonte (IDNet, DETRAN, SISMIGRA, etc.).
   - Entidades: `AcquisitionJob`, `SourceConnector`, `RawNistBatch`.
   - Serviços de domínio: `DetranBatchFetcher`, `IdNetCollector`.
2. **Normalization & Persistence Context**
   - Regras de validação, enriquecimento, deduplicação e persistência em Oracle/PostgreSQL.
   - Entidades: `Nist`, `Relacionamento`, `StimarRequest`.
   - Use cases: `RegisterNist`, `SyncRelationships`, `RunStimar`.
3. **Distribution Context**
   - Interage com FindFace (envio, agendamento de câmeras, exclusões específicas).
   - Entidades: `FindFaceCredential`, `ScheduleTask`, `Alert`.
4. **Monitoring & Ops Context**
   - Watchdog, notificações, logs, relatórios.
   - Entidades: `JobExecution`, `HealthCheck`, `AlertPolicy`.

Cada contexto terá seu próprio pacote e camada de aplicação (casos de uso) com interfaces bem definidas (repositories, gateways).

## 6. Clean Architecture (Camadas)
1. **Domínio (Enterprise Business Rules)**: Entidades imutáveis e serviços de domínio puros.
2. **Aplicação (Application Business Rules)**: Casos de uso implementados via TDD (ex.: `RunAcquisitionJobUseCase`).
3. **Interfaces/Adapters**: Repositórios (Oracle, PostgreSQL), conectores de APIs, CLI, HTTP, workers.
4. **Infraestrutura**: Scripts de orquestração, containers, cron/systemd, filas.

Cada camada depende apenas da imediatamente mais interna; dependências externas serão invertidas via `Dependency Inversion` (interfaces + injeção).

### Convenções de Código
1. Todas as classes, funções e métodos devem conter docstrings em Português do Brasil.
2. Todo código deve expor type hints completos e passar por verificadores como mypy/pyright.
3. Realizar validação de tipos em runtime quando necessário (pydantic, `isinstance`, etc.).
4. Comentários sempre em Português do Brasil e apenas quando agregarem contexto real.
5. Nomes de classes, funções, variáveis e módulos em inglês para manter consistência.

## 7. Estratégia TDD
1. **Teste de Domínio**: invariantes das entidades (`Nist` não pode ter hash vazio, `ScheduleTask` valida janelas de tempo).
2. **Teste de Casos de Uso**: mocks/stubs para repositórios validando fluxos principais e exceções.
3. **Teste de Integração**: adaptadores reais (Oracle/PostgreSQL/FindFace fake) usando containers locais (`docker-compose`).
4. **Teste de Contrato**: JSON schemas para resposta de conectores externos.
5. **Teste E2E**: pipelines completas com dados sintéticos e verificação no banco destino.

Cada user story deve iniciar como teste falhando (Red) → implementação mínima (Green) → refactor respeitando DRY e SOLID.

## 8. Plano de Refatoração
> **Processo de execução**: seguiremos fase a fase. Antes de iniciar qualquer fase, o time deve reler este PRD, verificar o que já foi concluído e obter aceite do responsável. Ao término de cada fase, marcar explicitamente no PRD (ex.: ✅ Fase concluída em DD/MM) para registrar o progresso e somente então avançar para a próxima.

1. **Fase 0 – Backups e Sandbox** — ✅ Concluída em 19/11/2025.
   - Criar `legacy_backups/<YYYYMMDD>/` na raiz contendo cópias imutáveis dos scripts atuais (`scripts_mitrarr`, `ws-nist`, etc.).
   - Automação: `./tools/backup_legacy.sh` que copia e gera checksums.
   - Nunca editar arquivos dentro de `legacy_backups`.
2. **Fase 1 – Configuração Base** — ✅ Concluída em 19/11/2025.
   - Criar monorepo `mitrarr-app/` com subpastas `acquisition/`, `normalization/`, `distribution/`, `ops-monitoring/`.
   - Definir toolchain (poetry/pdm + pre-commit + pytest + mypy + black/ruff).
   - Migrar configs sensíveis para `config/.secrets.enc`.
3. **Fase 2 – Casos de Uso Core**
   - Implementar `RegisterNist` + `SyncRelationships` + `SendToFindFace` com TDD.
   - Recriar CLI para substituir `run_*.sh` (ex.: `python -m apps.acquisition.run job=detran_diario`).
   - _19/11/2025_: Casos de uso e entidades-base implementados em `mitrarr_clean/core`.
   - _19/11/2025_: CLI inicial (`infra/cli/main.py`) + repositórios/gateway locais criados para suportar TDD.
4. **Fase 3 – Scheduler e Orquestração**
   - Introduzir serviço `scheduler` (Celery Beat, APScheduler ou Temporal) que substitua `check_and_run`, respeitando os horários definidos no crontab padronizado.
   - _19/11/2025_: CLI ganhou o comando `run-schedule` e o módulo `infra/scheduler/runner.py` que lê configurações JSON (ver `configs/schedule_template.json`).
   - Expor API REST/GraphQL para pausar/resumir jobs.
5. **Fase 4 – Monitoramento e Alertas**
   - Centralizar logs (JSON) + enviar métricas para Prometheus/ELK.
   - Substituir `.out` por loggers com `structlog` e retention.
6. **Fase 5 – Migração/Go-Live**
   - Executar pipelines em paralelo (novo x legado) e comparar resultados.
   - Trocar gradualmente crons para apontar ao novo scheduler.

## 9. Backup e Gestão de Ambientes
- Pasta `legacy_backups/` obrigatória antes de qualquer refatoração.
- Nova implementação reside em `mitrarr_clean/` (nome sugerido) evitando tocar o legado.
- Scripts de migração devem gerar relatórios no diretório `backups/reports/<timestamp>.md`.
- Plano de rollback: reativar cron do legado + restaurar arquivos a partir do backup imutável.

## 10. KPI / Métricas de Sucesso
- 100% das pipelines críticas cobertas por testes unitários + smoke tests.
- Tempo de onboarding reduzido (<1h para levantar ambiente local via `make setup`).
- Tarefas agendadas com histórico centralizado (auditoria de execuções anterior/atual).
- Nenhuma credencial em texto puro dentro do repositório.

## 11. Riscos e Mitigações
| Risco | Impacto | Mitigação |
| --- | --- | --- |
| Falta de conhecimento do domínio em novas squads | Alto | Pairing com mantenedores atuais + documentação de casos extremos. |
| Duplicação de lógica durante fase paralela | Médio | Feature toggles e testes de regressão comparando legacy vs novo. |
| Dependência em Oracle/FindFace indisponíveis para testes | Alto | Mocks + containers simulados + ambientes de homologação isolados. |

## 12. Checklist para Cada User Story
1. Criar teste falhando absorvendo requisito.
2. Implementar caso de uso/entidade seguindo SOLID.
3. Escrever adapter/interface conforme DDD.
4. Validar com lint, mypy, pytest, integração.
5. Atualizar documentação + diagramas de sequência.
6. Planejar deployment seguro + scripts de rollback.

## 13. Tutorial Detalhado (Obrigatório)
Este tutorial precisa acompanhar o PRD para que qualquer pessoa que saiba ler, mesmo sem formação técnica, compreenda o sistema.

### 13.1 Objetivo Geral
O sistema MITRARR coleta informações de várias fontes (por exemplo DETRAN e IDNet), organiza esses dados, envia para uma base interna e também sincroniza com o serviço FindFace. Tudo isso precisa ocorrer de forma automática, segura e sem exposição indevida de dados, pois se trata de uma operação de inteligência sujeita à LGPD.

### 13.2 Componentes Principais
- **Aquisição**: programas que conectam no DETRAN, IDNet, CANAIME, SISMIGRA e outros, baixando novos arquivos ou registros.
- **Processamento**: aplicações que conferem os dados recebidos, corrigem eventuais problemas e gravam nos bancos internos (Oracle/PostgreSQL).
- **Distribuição**: componentes que enviam dados para o FindFace, ligam ou desligam câmeras, atualizam listas de observação e agendamentos.
- **Monitoramento**: ferramentas que vigiam as pastas de arquivos, verificam se os programas estão rodando e informam quando algo falha.
- **Agendamento**: sistema que garante a execução automática dos programas, seguindo horários definidos num arquivo `crontab`.

### 13.3 Arquivos e Pastas
- `scripts_mitrarr/`: hoje contém scripts shell responsáveis por iniciar cada rotina (ex.: `run_adiciona_nists.sh`). No novo desenho eles serão substituídos por comandos da nova aplicação, mas continuarão existindo na pasta de legado.
- `ws-nist/`: aplicação em Python que trata os arquivos `.nst`, adiciona dados ao banco e executa tarefas como STIMAR e envio ao FindFace.
- `canaime/`, `nist_downloader/`, `sincronizapf/`: projetos específicos para fontes externas. Cada um possui seu ambiente virtual e scripts python próprios.
- `docs/PRD.md`: este documento com todas as regras, além do tutorial.
- `legacy_backups/<data>/`: diretório obrigatório onde guardaremos cópias dos arquivos antigos antes de qualquer alteração.
- `mitrarr_clean/` (nome sugerido): nova pasta onde o sistema reescrito será desenvolvido, respeitando DDD, TDD e Clean Architecture.

### 13.4 Como o Fluxo Funciona
1. O cron agenda em horários definidos (por exemplo às 22h) a execução de um script `check_and_run_*`.
2. Esse script confere se a rotina já está rodando. Se não estiver, chama o `run_*` correspondente.
3. O `run_*` prepara variáveis de ambiente (usuários, senhas, endereços de banco) e roda um programa Python.
4. O programa Python busca dados, processa e grava resultados. Alguns escrevem arquivos `.out` com o registro do que ocorreu.
5. Se algo falhar, precisamos consultar o `.out` ou o log central para descobrir o motivo e corrigir.
6. A nova arquitetura manterá esses passos, mas com um único scheduler, logs estruturados e testes para garantir que as rotinas funcionem sempre.

### 13.5 Regras Importantes
- Toda classe ou função criada no novo sistema deve ter:
  - Docstring em Português do Brasil explicando para que serve.
  - Declaração de tipos (type hints) e validação quando necessário.
  - Comentários também em Português quando forem indispensáveis.
  - Nomes em inglês (para manter padrão com o resto do código).
- Scripts precisam continuar executando automaticamente, sem depender do terminal MobaXterm aberto.
- Credenciais e dados sensíveis nunca devem ser colocados diretamente no código; devem ficar em arquivos seguros ou gerenciadores de segredos.
- Qualquer alteração deve respeitar a LGPD: coletar somente o necessário, proteger dados e registrar quem acessa.

### 13.6 Como Executar Localmente (exemplo simplificado)
1. Instale as dependências (Python 3.10+, poetry/pdm, docker se for usar banco local).
2. Rode `make setup` (ou comando equivalente) para criar ambientes virtuais e baixar bibliotecas.
3. Configure variáveis de ambiente usando arquivos `.env` criptografados (descrito na documentação de segurança).
4. Para testar uma rotina, rode `pytest` para validar os testes e depois `python -m apps.acquisition.run job=detran_diario` (exemplo) para executar manualmente.
5. Verifique os logs gerados no diretório configurado (ex.: `logs/acquisition/detran.log`).

### 13.7 Como Operar em Produção
1. Certifique-se de que o `crontab -l` está com as entradas corretas apontando para o novo scheduler ou scripts adaptados.
2. Após cada deploy, acompanhe os logs ou painéis de monitoramento para garantir que os jobs rodaram nos horários certos.
3. Em caso de falha, pare o job no scheduler, corrija o problema (código ou infraestrutura), rode os testes e reative.
4. Mantenha sempre o backup atualizado; qualquer alteração deve ser precedida pela cópia na pasta `legacy_backups`.

### 13.8 Dicas de Operação Diária (Passo a Passo)
**Como reiniciar o sistema via MobaXterm**
1. Abra o MobaXterm e conecte no servidor (ex.: `findface@ws2`).
2. Execute `sudo systemctl restart scheduler.service` para reiniciar o agendador principal (ou o nome do serviço definido).
3. Verifique o status com `systemctl status scheduler.service`. Caso esteja “active (running)”, o sistema voltou a funcionar.
4. Se precisar reiniciar um serviço específico (como o watchdog), troque o nome do serviço no comando acima.

**Como limpar eventos quando houver sobrecarga**
1. Identifique o diretório de filas/mensagens (ex.: `/var/lib/mitrarr/queue` ou banco Redis). Isso estará descrito na documentação da Fase 3.
2. Pause o job problemático via scheduler (`scheduler-cli pause job-name` ou comando equivalente).
3. Faça backup dos eventos (copie os arquivos para `legacy_backups/events/<data>`).
4. Após o backup, limpe a fila com o comando indicado (`scheduler-cli purge job-name` ou limpeza no banco). Nunca apague dados sem confirmar com o time responsável.
5. Reative o job (`scheduler-cli resume job-name`) e monitore os logs para garantir que a fila está vazando corretamente.

**Outros problemas comuns e soluções rápidas**
- **Log lotando disco**: remova arquivos antigos com `logrotate` ou script `tools/cleanup_logs.sh`. Sempre mantenha a última semana disponível.
- **Job preso em execução**: use `scheduler-cli stop job-name --force` e reinicie a partir do ponto seguro. Verifique os `.out` para entender o motivo.
- **Sem acesso ao banco**: confirme VPN ou túnel, teste com `sqlplus`/`psql`. Se estiver fora do ar, avise o time de banco antes de tentar novos processamentos.
- **Falha por credencial expirada**: atualize o arquivo de segredos (`config/.secrets.enc`) e reexecute `make apply-secrets`.

### 13.9 Onde Buscar Ajuda
- Documentação adicional ficará na pasta `docs/`.
- Logs e métricas estarão acessíveis via ferramentas internas (Prometheus, Grafana ou ELK conforme definido na Fase 4).
- Em caso de dúvidas sobre dados sensíveis, consultar o responsável pela operação de inteligência ou o DPO (Data Protection Officer).

Este tutorial precisa ser revisado e expandido conforme as novas funcionalidades surgirem, garantindo que qualquer pessoa consiga entender o sistema e operá-lo com segurança.

### 13.10 Glossário Simplificado
| Termo | Explicação simples |
| --- | --- |
| NIST | Arquivo com dados biométricos que precisamos tratar e guardar. |
| STIMAR | Rotina que cruza dados de várias fontes para gerar alertas. |
| Scheduler | Programa que dispara automaticamente cada atividade no horário correto. |
| Watchdog | Serviço que fica olhando pastas/arquivos e avisa quando chega algo novo. |
| `.out` | Arquivo de texto onde guardamos o histórico do que aconteceu em cada execução. |
| FindFace | Plataforma usada para reconhecimento facial que recebe parte dos dados do MITRARR. |
| LGPD | Lei Geral de Proteção de Dados, que obriga tratamento seguro e ético das informações. |

### 13.11 Visão Textual do Fluxo
1. Uma fonte externa (DETRAN, IDNet, etc.) gera novos dados.
2. Um coletor (job de aquisição) baixa esse conteúdo e salva localmente.
3. O processamento normaliza, corrige e grava no banco interno.
4. Dados validados são enviados ao FindFace e demais destinos necessários.
5. Logs e métricas são atualizados para que o time saiba o que aconteceu.
6. Se algo falhar, alertas são emitidos e o operador segue o tutorial para resolver.

### 13.12 FAQ Operacional
- **O cron não rodou no horário esperado. E agora?** Verifique `crontab -l`, confirme timezone e consulte o log do scheduler. Use `systemctl status scheduler.service` para checar se o serviço está ativo. Se estiver parado, reinicie conforme item 13.8.
- **Como vejo se novos NISTs chegaram?** Consulte os dashboards ou rode `python cli/status.py --job nist` (novo sistema) para ver contadores por dia.
- **Posso rodar um job manualmente?** Sim, pausar o agendamento, executar `python -m apps.<context>.run --job <nome>` e acompanhar os logs. Só retome o cron após validar o resultado.
- **Apaguei dados sem querer, o que faço?** Pare os jobs, avise imediatamente o responsável e restaure a partir do backup mais recente. Nunca reescreva arquivos sem antes fazer cópia.

### 13.13 Checklist Pós-Implantação
1. Conferir se o `scheduler.service` está ativo e se registrou o próximo disparo.
2. Validar conexões com Oracle, PostgreSQL e FindFace (scripts de health check).
3. Checar se os painéis de monitoramento estão recebendo dados (logs/métricas).
4. Rodar manualmente um job crítico (ex.: `RegisterNist`) em modo de teste e revisar a saída.
5. Atualizar o time de operações confirmando que não houve regressões.

## 14. Estratégia Anti-Estagnação e Monitoramento Proativo
- **Heartbeats automáticos**: cada job deve publicar a hora da última execução bem-sucedida em um repositório central (banco ou Prometheus). Um alarme dispara se passar mais de 7 dias sem atualização.
    - _19/11/2025_: Implementado monitor de heartbeats (`infra/monitoring/heartbeats.py`) integrado à CLI para registrar as execuções.
- **Validação de volume**: criar tarefas diárias que comparam o número de registros processados com médias históricas; se ficar abaixo de um limite, deve gerar alerta.
    - _19/11/2025_: Criado `VolumeValidator` em `infra/monitoring/volume_guard.py` com testes (`tests/infra/monitoring/test_volume_guard.py`).
- **Auto-recovery**: o scheduler deve tentar religar jobs com `Retry` configurado e, após N falhas, abrir chamado automático (e-mail/Telegram).
    - _19/11/2025_: Implementado `RetryRunner` (`infra/auto_recovery/retry_runner.py`) e comando CLI `run-with-retry` para encapsular tentativas.
- **Verificações do cron**: script `cron_guardian.sh` roda a cada hora, lista o `crontab`, valida timestamps (`last_run_at`) e envia alerta se algum job estiver atrasado em mais de 7 dias.
    - _19/11/2025_: Disponibilizado `infra/monitoring/cron_guardian.py` para ser executado via cron e alertar jobs atrasados.
- **Scheduler unificado**: CLI `run-schedule` e módulo `infra/scheduler/runner.py` criados para executar os jobs definidos em JSON (substitui check_and_run).
- **Teste sintético**: gerar arquivos de exemplo semanalmente para garantir que o pipeline está aceitando entradas. Se o arquivo de teste não chegar ao destino, o sistema dispara alerta.
- **Auditoria de cargas FindFace**: scripts periódicos comparam o total de registros locais vs FindFace; divergência acima de 5% aciona análise.
- **Playbook de contingência**: manter instruções claras (item 13.8) para reiniciar serviços, limpar filas e rodar jobs manualmente, garantindo que o sistema não fique meses parado sem ninguém notar.

---
Este PRD serve como “contrato” para a reescrita completa do sistema, guiando todas as squads a seguirem TDD rigoroso, princípios SOLID/DDD e mantendo rastreabilidade através de backups e documentação contínua.
