# 17 - CONFIGURAÇÃO CENTRALIZADA (LAUNCHER.JSON)

## OBJETIVO
Definir, documentar e implementar a estrutura do arquivo de configuração central `launcher.json` do EmuRust, com seções dedicadas e independentes para cada um dos três servidores, o supervisor e o sistema de logging.

## PROBLEMA
Configurações espalhadas em múltiplos arquivos `.toml` ou `.ini` em pastas diferentes aumentavam o risco de inconsistências (como colocar a porta 7777 em um arquivo e 7778 em outro).

## CAUSA
Falta de um schema de configuração central unificado.

## ANÁLISE
Estrutura do `launcher.json`:

```json
{
  "############################################################": "LOGIN-SERVER",
  "login-server": {
    "enabled": true,
    "bind_address": "0.0.0.0",
    "client_port": 2106,
    "hq_port": 13001,
    "sts_port": 6600,
    "announce_game_server_ip": "192.168.3.184",
    "announce_game_server_port": 7777,
    "default_server_id": 23,
    "auto_create_accounts": true,
    "development_mode": true,
    "default_dev_username": "teste",
    "security": {
      "enable_rate_limit": true,
      "max_attempts_per_minute": 10,
      "temp_ban_minutes": 15
    },
    "database": {
      "path": "aion.db"
    }
  },

  "############################################################": "GAME-SERVER",
  "game-server": {
    "enabled": true,
    "bind_address": "0.0.0.0",
    "port": 7777,
    "server_id": 23,
    "server_name": "Atreia (Classic EU)",
    "tick_rate_tps": 20,
    "max_players": 1000,
    "data_path": "data/client",
    "database": {
      "path": "aion.db"
    }
  },

  "############################################################": "CHAT-SERVER",
  "chat-server": {
    "enabled": true,
    "bind_address": "0.0.0.0",
    "port": 10241,
    "max_channels": 500,
    "anti_flood_messages_per_sec": 5,
    "database": {
      "path": "aion.db"
    }
  },

  "############################################################": "LAUNCHER & SUPERVISOR",
  "launcher": {
    "autoStartLoginServer": true,
    "autoStartGameServer": true,
    "autoStartChatServer": true,
    "restartOnCrash": true,
    "crashRestartDelayMs": 2000,
    "gui": {
      "theme": "dark",
      "window_width": 1100,
      "window_height": 720
    }
  },

  "############################################################": "LOGGING & RETENTION",
  "logging": {
    "retentionDays": 10,
    "loginServerPath": "logs/login-server",
    "gameServerPath": "logs/game-server",
    "chatServerPath": "logs/chat-server"
  }
}
```

## SOLUÇÃO
Criar structs em Rust com `serde::Deserialize` e `serde::Serialize` para carregar `launcher.json` com valores padrão (`#[serde(default)]`) caso campos estejam ausentes, evitando quebras por arquivos parcialmente configurados.

## ARQUIVOS ENVOLVIDOS
* `Emulador-Rust/config/launcher.json`
* `Emulador-Rust/auto-start/src/config.rs`
* `Emulador-Rust/login-server/src/config.rs`
* `Emulador-Rust/game-server/src/config.rs`
* `Emulador-Rust/chat-server/src/config.rs`

## IMPLEMENTAÇÃO
* Implementação do deserializer compartilhado.
* Função para gerar `launcher.json` com valores padrão na primeira inicialização se o arquivo não existir.

## TESTES
* Teste unitário de parsing de `launcher.json`.
* Teste de fallback quando campos opcionais são omitidos.

## VALIDAÇÃO
* Cada servidor lê estritamente sua seção correspondente do `launcher.json` sem conflitos.

## RISCOS
* Erro de sintaxe JSON (ex: vírgula no fim de array) que impeça a inicialização.
* Mitigação: Mensagem de erro amigável na GUI informando linha e coluna do erro de formatação do JSON.

## DEPENDÊNCIAS
* `serde`, `serde_json`.

## TO-DO
- [x] Definir schema estrutural completo do `launcher.json`.
- [x] Implementar serialização/desserialização em Rust.
- [x] Criar arquivo default em `config/launcher.json`.

## STATUS
[x] TESTADO
[x] VALIDADO
STATUS: CORRIGIDO E VALIDADO
