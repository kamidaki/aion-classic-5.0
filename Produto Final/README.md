# Aion Classic EU — Pacote de Produção (Deploy)

Ambiente de produção e execução do **EmuRust**, o emulador em Rust de alta performance para o Aion Classic EU (cliente x64).

---

## Como Iniciar o Emulador

Basta executar com **2 cliques**:

```text
Auto-Start EmuRust.exe
```

Ao iniciar, o painel do gerenciador abrirá automaticamente na janela nativa embutida e registrará o ícone na bandeja do sistema (System Tray).

---

## Recursos do Dashboard (Gerenciador Central)

* **Telemetria Day-Trade em Tempo Real**:
  * Gráfico multicurva interativo com linhas individuais para **Login-Server**, **Game-Server**, **Chat-Server**, **Launcher** e **Consumo Total**.
  * Alternância entre **Modo CPU (%)** (com Níveis Fibonacci) e **Modo Memória RAM (MB)**.
  * Painel de estatísticas com valores de Mínimo, Máximo, Média e Amostragem instantânea (1s).
* **Header Compacto & Ergonômico**:
  * Altura slim de 48px que maximiza o espaço útil de tela.
  * Pílulas com minileds de status rápido e botões de ação em 1 clique (`INICIAR`, `PARAR`, `REINICIAR`, `TELA CHEIA`, `ENCERRAR`).
* **Gaveta Lateral Esquerda (Left Drawer)**:
  * Registradores de Sistema: Target TPS (20.0 fixo), Tamanho do Banco `aion.db`, Memória Total do SO e Uptime.
  * Mapeamento de Portas de Rede ativas (`2106`, `7777`, `10241`, `6600`, `13001`, `18080`).
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

## Configuração Central (`config/launcher.json`)

```json
{
  "login-server": {
    "enabled": true,
    "bind_address": "0.0.0.0",
    "client_port": 2106,
    "hq_port": 13001,
    "sts_port": 6600,
    "announce_game_server_ip": "127.0.0.1",
    "announce_game_server_port": 7777,
    "default_server_id": 1,
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
    "server_id": 1,
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

---

## Como Iniciar o Cliente do Jogo

1. Certifique-se de que os servidores estão com status `ONLINE` no **Auto-Start EmuRust**.
2. Execute:
   ```text
   Cliente\GFAion\aionclassic\Start_Client_Classic_EU.bat
   ```
3. Digite qualquer usuário e senha na tela de login e clique em **OK**.
4. O emulador autenticará a conta automaticamente e carregará a tela de seleção de mundos.
