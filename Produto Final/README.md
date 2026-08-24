# Aion Classic EU — Pacote de Produção (Deploy)

Ambiente de produção e execução do **EmuRust**, o emulador de alta performance em Rust para o **Aion Classic EU 4.5** (cliente 64-bit).

---

## 1. Regras Obrigatórias de Login e Execução

O **EmuRust** segue a arquitetura oficial e dos emuladores consagrados (Java 4.8 Retail / Java 2.4 Classic Gameforge):

* **Autenticação Pura**: O acesso ocorre **unicamente via Login e Senha**. Métodos adicionais (Launcher proprietário, 2FA, OAuth, SMS/códigos de telefone) são dispensados e ignorados.
* **Porta de Conexão**: O cliente conecta-se sempre na porta de login padrão **`2106`**.
* **Inicialização via Script `.bat`** (`Cliente\GFAion\aionclassic\Start_Client_Classic_EU.bat`):
  * **Sem parâmetros de credenciais**: Abre a tela tradicional de login in-game. O jogador digita usuário e senha na interface do jogo.
  * **Com parâmetros de credenciais** (`-account:user -password:pass`): Pula a tela de login in-game e avança imediatamente para os Termos de Serviço / Seleção de Servidores.

---

## 2. Como Iniciar o Emulador

Basta executar com **2 cliques**:

```text
Auto-Start EmuRust.exe
```

Ao iniciar, o painel do gerenciador abrirá automaticamente na janela nativa embutida e registrará o ícone na bandeja do sistema (System Tray).

---

## 3. Mapeamento de Portas e Serviços

| Porta | Protocolo | Serviço | Descrição |
|---|---|---|---|
| **`2106`** | TCP | Login Server (NCSoft) | Porta principal de autenticação e handshake do cliente com RSA/Blowfish. |
| **`13001`** | TCP | Login Server (HQ Auth) | Protocolo de autenticação secundária Gameforge HQ. |
| **`6600`** | TCP | Login Server (STS) | Handshake STS para compatibilidade com o cliente oficial. |
| **`9014`** | TCP | Login Server (Internal GS) | Porta interna de controle e autenticação GS <> LS (senha `Sabrewolf100!`). |
| **`7777`** | TCP | Game Server | Conexão do mundo de jogo, combate, inventário, movimentação e spawns (20.0 TPS). |
| **`9021`** | TCP | Chat Server (Internal GS) | Porta interna de controle e canais GS <> CS (senha `Sabrewolf100!`). |
| **`10241`** | TCP | Chat Server | Canais regionais, sussurros, anúncios de legião e anti-flood. |
| **`18080`** | HTTP | Painel Mobile LAN | Interface web responsiva para monitoramento e controle via celular/tablet. |

---

## 4. Recursos do Dashboard (Gerenciador Central)

* **Telemetria Day-Trade em Tempo Real**:
  * Gráfico multicurva interativo com linhas individuais para **Login-Server**, **Game-Server**, **Chat-Server**, **Launcher** e **Consumo Total**.
  * Alternância entre **Modo CPU (%)** (com Níveis Fibonacci) e **Modo Memória RAM (MB)**.
  * Painel de estatísticas com valores de Mínimo, Máximo, Média e Amostragem instantânea (1s).
* **Header Compacto & Ergonômico**:
  * Altura slim de 48px que maximiza o espaço útil de tela.
  * Pílulas com minileds de status rápido e botões de ação em 1 clique (`INICIAR`, `PARAR`, `REINICIAR`, `TELA CHEIA`, `ENCERRAR`).
* **Gaveta Lateral Esquerda (Left Drawer)**:
  * Registradores de Sistema: Target TPS (20.0 fixo), Tamanho dos Bancos (`login.db` / `game.db` / `chat.db`), Memória Total do SO e Uptime.
  * Mapeamento de Portas de Rede ativas (`2106`, `7777`, `10241`, `6600`, `9014`, `9021`, `13001`, `18080`).
  * Conexão Mobile LAN com link direto e botão de cópia.
* **Experiência Mobile iOS-Like**:
  * Acesso remoto via navegador pelo celular no mesmo Wi-Fi (`http://<LAN-IP>:18080`).
  * Barra de navegação inferior estilo vidro fosco (`Status`, `Gráfico`, `Logs`, `Menu`) e Botão de Ação Flutuante (FAB).
* **Central de Logs Unificada**:
  * Monitoramento consolidado de todos os servidores + logs internos do supervisor.
  * Filtros por serviço, busca em tempo real, auto-scroll e limpeza de console.
* **Crash Detection & Auto-Restart**:
  * Se qualquer servidor encerrar de forma inesperada, o supervisor detecta e reinicia apenas aquele serviço específico de forma silenciosa.

---

## 5. Configuração Central (`config/launcher.json`)

```json
{
  "login-server": {
    "enabled": true,
    "bind_address": "127.0.0.1",
    "client_port": 2106,
    "hq_port": 13001,
    "sts_port": 6600,
    "gameserver_port": 9014,
    "gameserver_password": "Sabrewolf100!",
    "announce_game_server_ip": "127.0.0.1",
    "announce_game_server_port": 7777,
    "default_server_id": 1,
    "auto_create_accounts": true,
    "development_mode": false,
    "default_dev_username": "fly",
    "database": {
      "path": "data/Banco de Dados/login.db"
    }
  },

  "game-server": {
    "enabled": true,
    "bind_address": "127.0.0.1",
    "port": 7777,
    "server_id": 1,
    "server_name": "Brasil em Chamas (São Paulo)",
    "login_server_address": "127.0.0.1:9014",
    "gameserver_password": "Sabrewolf100!",
    "chat_server_address": "127.0.0.1:9021",
    "chat_password": "Sabrewolf100!",
    "tick_rate_tps": 20,
    "max_players": 1000,
    "data_path": "data/client",
    "database": {
      "path": "data/Banco de Dados/game.db"
    }
  },

  "chat-server": {
    "enabled": true,
    "bind_address": "127.0.0.1",
    "port": 10241,
    "internal_port": 9021,
    "chat_password": "Sabrewolf100!",
    "max_channels": 500,
    "anti_flood_messages_per_sec": 5,
    "database": {
      "path": "data/Banco de Dados/chat.db"
    }
  }
}
```

---

## 6. Banco de Dados SQLite Isolado (`data/Banco de Dados/`)

Os bancos operam em modo **WAL (Write-Ahead Logging)** com migrações automáticas:
* **`login.db`**: `accounts`, `account_data`, `account_time`, `banned_ip`, `banned_mac`, `gameservers`, `sessions`.
* **`game.db`**: `characters`, `players`, `character_items`, `inventory`, `character_skills`, `player_skills`, `player_quests`, `character_mail`, `guilds`, `guild_members`, `character_buddies`, `broker_listings`, `broker_history`, `abyss_rank`, `player_titles`, `player_effects`, `player_bind_point`.
* **`chat.db`**: `chat_channels`, `chat_bans`.
