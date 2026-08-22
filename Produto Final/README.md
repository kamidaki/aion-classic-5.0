# Aion Classic EU — Pacote de Produção (Deploy)

Ambiente de produção e execução do **EmuRust**, o emulador em Rust de alta performance para o Aion Classic EU (cliente x64).

---

## 🚀 Como Iniciar o Emulador

Basta executar com **2 cliques**:

```text
Auto-Start EmuRust.exe
```

Ao iniciar, o painel do gerenciador abrirá automaticamente no seu navegador padrão em:

👉 **`http://127.0.0.1:18080`**

---

## 🖥️ Recursos do Dashboard (Gerenciador Central)

*   **3 Cards de Controle Independentes**:
    *   **Login-Server**: Monitora status, uptime, portas `2106`, `13001`, `6600` e Named Pipe.
    *   **Game-Server**: Monitora status, uptime, porta `7777` e tick rate de 20 TPS.
    *   **Chat-Server**: Monitora status, uptime e porta de canais `10241`.
*   **Métricas em Tempo Real**: Medidores dinâmicos de uso de **CPU (%)** e **Memória RAM (MB)** para cada processo individual.
*   **Controles Granulares**: Botões `LIGAR`, `PARAR` e `REINICIAR` para cada servidor separadamente, além dos botões mestres `LIGAR TODOS`, `PARAR TODOS` e `REINICIAR TODOS`.
*   **Central de Logs Colorida**:
    *   ⚪ **Login-Server**: Logs em **Branco / Prata**.
    *   🟢 **Game-Server**: Logs em **Verde Esmeralda**.
    *   🔵 **Chat-Server**: Logs em **Ciano / Azul Claro**.
    *   Filtros por servidor e por nível (`INFO`, `WARN`, `ERROR`, `DEBUG`), busca em tempo real e auto-scroll.
*   **Crash Detection & Auto-Restart**: Se qualquer servidor falhar inesperadamente, o supervisor detecta e reinicia apenas aquele serviço específico de forma transparente.

---

## ⚙️ Configuração (`config/launcher.json`)

Toda a configuração dos servidores e do inicializador está centralizada em `config/launcher.json`:

```json
{
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
      "max_attempts_per_minute": 15,
      "temp_ban_minutes": 15
    },
    "database": {
      "path": "aion.db"
    }
  },

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

  "launcher": {
    "autoStartLoginServer": true,
    "autoStartGameServer": true,
    "autoStartChatServer": true,
    "restartOnCrash": true,
    "crashRestartDelayMs": 2000,
    "gui": {
      "theme": "dark",
      "window_width": 1150,
      "window_height": 760,
      "http_port": 18080
    }
  },

  "logging": {
    "retentionDays": 10,
    "loginServerPath": "logs/login-server",
    "gameServerPath": "logs/game-server",
    "chatServerPath": "logs/chat-server"
  }
}
```

### Principais Opções:
1. **`announce_game_server_ip`**: IP de rede local (LAN) anunciado para o client (ex: `192.168.3.184`). **Nunca usar `127.0.0.1`**, pois o client Aion Classic rejeita endereços de loopback na lista de mundos.
2. **`auto_create_accounts`**: Quando `true`, cria qualquer conta automaticamente ao digitar usuário e senha na tela de login.
3. **`retentionDays`**: Rotação diária com retenção automática máxima de 10 dias de logs.

---

## 🎮 Como Conectar o Cliente de Jogo

Para abrir o jogo, execute:

```text
Cliente\GFAion\aionclassic\Start_Client_Classic_EU.bat
```

O script inicia o executável `bin64\Aion.bin` com os parâmetros corretos (`-usehqserver -hqip:127.0.0.1 -hqport:13001 -np:127.0.0.1 -dwsm -loginex ...`), comunicando diretamente com o `login-server.exe` através do Named Pipe interno.

---

## 📁 Estrutura de Pastas

```text
Produto Final/
├── Auto-Start EmuRust.exe   # Gerenciador gráfico e supervisor
├── login-server.exe         # Servidor de autenticação e STS
├── game-server.exe          # Servidor de mundo e gameplay
├── chat-server.exe          # Servidor dedicado de canais e chat
├── aion.db                  # Banco de dados SQLite compartilhado (WAL mode)
├── config/
│   └── launcher.json        # Configuração centralizada
├── data/
│   ├── client/              # Templates de NPCs, Itens e Skills
│   ├── itens_iniciais.csv   # Kits iniciais das classes
│   └── spawns.csv           # 1.254 Spawns de NPCs no mundo
└── logs/
    ├── login-server/        # Logs diários do Login-Server
    ├── game-server/         # Logs diários do Game-Server
    └── chat-server/         # Logs diários do Chat-Server
```
