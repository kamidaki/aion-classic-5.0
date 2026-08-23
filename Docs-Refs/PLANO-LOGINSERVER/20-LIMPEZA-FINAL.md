# 20 - LIMPEZA FINAL E HIGIENIZAÇÃO DO REPOSITÓRIO

## OBJETIVO
Identificar, auditar e remover com segurança executáveis obsoletos, scripts `.bat` legados, crates descontinuados (`auth-server`, `sts-server`), logs temporários e arquivos duplicados somente após a validação completa do `Auto-Start EmuRust.exe` e dos 3 novos servidores.

## PROBLEMA
Acúmulo de arquivos antigos e duplicados no repositório gera confusão sobre quais binários devem ser executados e aumenta o tamanho do repositório.

## CAUSA
Iterações de desenvolvimento anteriores sem higienização pós-refatoração.

## ANÁLISE
Critério Estrito de Remoção:
Antes de remover qualquer arquivo, aplicar a regra obrigatória:
```text
ARQUIVO -> QUEM USA? -> AINDA NECESSÁRIO? -> SUBSTITUÍDO? -> TESTADO? -> PODE REMOVER?
```

Itens Auditados para Remoção Segura:
1. `Emulador-Rust/auth-server/` -> Substituído pelo novo `login-server/`.
2. `Emulador-Rust/sts-server/` -> Substituído pelo módulo STS interno do `login-server/`.
3. `deploy/auth-server.exe` -> Substituído por `deploy/login-server.exe`.
4. `deploy/sts-server.exe` -> Substituído por `deploy/login-server.exe`.
5. Scripts obsoletos de inicialização fragmentada (`Ligar_Auth.bat`, `Ligar_STS.bat`, `Ligar_Game.bat`) -> Substituídos pelo `Auto-Start EmuRust.exe`.
6. Arquivos `.log` temporários dispersos na raiz do workspace.

Itens que Devem Ser PRESERVADOS Intactos:
* `Cliente/GFAion/aionclassic/Start_Client_Classic_EU.bat` (Entry point único do jogador).
* `data/client/` (Templates de NPCs, Itens, Skills, Spawns).
* `Emulador-Rust/aion.db` (Banco de dados SQLite compartilhado).
* `Docs-Refs/PLANO-LOGINSERVER/` (Memória técnica permanente do projeto).

* `docs/` e arquivos de documentação técnica de engenharia reversa.

## SOLUÇÃO
Executar a higienização de forma controlada após a compilação e teste do binário `Auto-Start EmuRust.exe` no diretório `deploy/`.

## ARQUIVOS ENVOLVIDOS
* `Emulador-Rust/`
* `deploy/`

## IMPLEMENTAÇÃO
* Remoção dos diretórios de código legado.
* Atualização do `.gitignore` para ignorar binários em `target/` e arquivos de logs dinâmicos.
* Atualização do `README.md` com instruções claras do novo `Auto-Start EmuRust.exe`.

## TESTES
* Executar `cargo clean && cargo build --workspace --release` em ambiente 100% limpo.
* Validar que nenhum arquivo essencial foi deletado por engano.

## VALIDAÇÃO
* O repositório está limpo, organizado e compilando sem dependências de arquivos mortos.
* O usuário precisa apenas dar 2 cliques em `Auto-Start EmuRust.exe` para ligar todo o ambiente.

## RISCOS
* Deletar dados de templates estáticos (`.xml` ou `.csv`) acidentalmente.
* Mitigação: Auditoria prévia de caminhos antes de executar comandos `Remove-Item`.

## DEPENDÊNCIAS
* PowerShell / Cargo.

## TO-DO
- [x] Auditar todos os arquivos do repositório.
- [x] Remover crates legados `auth-server` e `sts-server`.
- [x] Limpar executáveis obsoletos no `deploy/`.
- [x] Validar build em ambiente limpo.

## STATUS
[x] TESTADO
[x] VALIDADO
STATUS: CORRIGIDO E VALIDADO
