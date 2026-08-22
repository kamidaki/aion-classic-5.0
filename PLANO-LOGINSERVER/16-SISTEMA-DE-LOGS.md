# 16 - SISTEMA DE LOGS E ROTAÇÃO FÍSICA DE 10 DIAS

## OBJETIVO
Implementar um sistema de logging profissional e estratégico em todos os servidores, com rotação diária por servidor, retenção máxima de 10 dias e streaming em tempo real para o dashboard central.

## PROBLEMA
Logs desorganizados geram arquivos gigantescos acumulados no disco sem limite de tamanho ou espalham milhares de pequenos arquivos que poluem o diretório raiz.

## CAUSA
Ausência de uma política de rotação automática diária (`daily rotation`) e de limpeza de retenção (`retention policy`).

## ANÁLISE
Estrutura física obrigatória:
```text
logs/
├── login-server/
│   ├── 2026-08-22.log
│   ├── 2026-08-21.log
│   └── ... (até 10 dias)
├── game-server/
│   ├── 2026-08-22.log
│   ├── 2026-08-21.log
│   └── ... (até 10 dias)
└── chat-server/
    ├── 2026-08-22.log
    ├── 2026-08-21.log
    └── ... (até 10 dias)
```

Regras Estritas:
1. **Formato Padrão**:
   `[TIMESTAMP] [NÍVEL] [SERVIDOR] | Mensagem explicativa (Origem: ..., ID: ...)`
   Exemplo:
   `[2026-08-22 17:30:15] [INFO] [LoginServer] | Session created for account 'teste' (IP: 127.0.0.1)`
   `[2026-08-22 17:30:18] [INFO] [GameServer] | Player 'Fire' entered world at map 110010000 (x: 1245.2, y: 1542.1, z: 210.5)`
   `[2026-08-22 17:30:19] [INFO] [ChatServer] | Player 'Fire' joined channel 'Region_Sanctum'`
2. **Separação por Servidor**: Nunca misturar linhas de servidores diferentes no mesmo arquivo físico.
3. **1 Arquivo por Dia**: Nome do arquivo no formato `YYYY-MM-DD.log`.
4. **Retenção de 10 Dias**: Um cleaner periódico verifica a pasta de logs a cada inicialização e diariamente às 00:01, removendo automaticamente arquivos com data de modificação superior a 10 dias.
5. **Anti-Spam**: Loops de alta frequência (como os 20 TPS do game loop ou os pings de 20s do STS) não devem gravar logs em nível INFO para evitar inchar o arquivo com gigabytes de texto inútil.

## SOLUÇÃO
Implementar o módulo `LogRotator` no crate `auto-start` e utilitários de logging assíncrono com a biblioteca `tracing`/`tracing-appender` ou rotacionador customizado nativo em Rust nos 3 servidores.

## ARQUIVOS ENVOLVIDOS
* `Emulador-Rust/auto-start/src/logs/mod.rs`
* `Emulador-Rust/auto-start/src/logs/rotator.rs`
* `Emulador-Rust/login-server/src/logging.rs`
* `Emulador-Rust/game-server/src/logging.rs`
* `Emulador-Rust/chat-server/src/logging.rs`

## IMPLEMENTAÇÃO
* Implementação do rotacionador com verificação de timestamp diário.
* Implementação do coletor de lixo de logs antigos (> 10 dias).

## TESTES
* Teste unitário de criação de arquivo diário.
* Teste de limpeza automática de arquivos criados com datas simuladas anteriores a 10 dias.

## VALIDAÇÃO
* Pastas `logs/login-server/`, `logs/game-server/` e `logs/chat-server/` recebem gravações ativas e arquivos com mais de 10 dias são limpos com segurança.

## RISCOS
* Bloqueio de arquivo caso o processo mantenha o descritor aberto durante a meia-noite.
* Mitigação: O rotacionador abre o arquivo em modo append (`OpenOptions::new().create(true).append(true)`) garantindo transição transparente de dia.

## DEPENDÊNCIAS
* `chrono`, `tokio::fs`.

## TO-DO
- [x] Estruturar pastas físicas de logs.
- [x] Implementar rotacionador diário.
- [x] Implementar retenção de 10 dias com remoção automática.
- [x] Conectar com o Log Center da GUI.

## STATUS
[x] TESTADO
[x] VALIDADO
STATUS: CORRIGIDO E VALIDADO
