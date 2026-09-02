# Aion Classic 5.0 — Suite de Captura e Engenharia Reversa de Pacotes

Este diretório contém a infraestrutura organizada para captura, armazenamento modular e análise de pacotes de rede coletados diretamente do servidor oficial **Gameforge Aion Classic 5.0**.

---

## 1. A Regra Principal de Arquitetura

O desenvolvimento e a evolução do emulador são norteados pela cadeia causal estrita de eventos:

$$\mathbf{Captura\ (PCAP)} \longrightarrow \mathbf{Protocolo\ (Wire)} \longrightarrow \mathbf{Evento} \longrightarrow \mathbf{Estado\ (World/Entity)} \longrightarrow \mathbf{Sistema\ (Gameplay\ Service)} \longrightarrow \mathbf{Resposta\ (Broadcast)}$$

> [!IMPORTANT]
> **Diretrizes de Extração e Integração**:
> 1. **Evidência Real Baseada em PCAPs e Memória**: Não fazer suposições quando a informação puder ser extraída diretamente das capturas oficiais ou da memória do processo `Aion.bin` em tempo real.
> 2. **Não implementar pacotes isoladamente**: Cada pacote identificado deve alimentar um evento de domínio no emulador, atualizar o estado persistente/em memória e acionar o sistema correspondente (`services/`), que por sua vez gera as respostas e broadcasts necessários.
> 3. **Comparação e Encadeamento Limpo**: Comparar o comportamento identificado com o código Rust existente, implementar apenas o necessário dentro da arquitetura desacoplada e garantir que não existam handlers duplicados, lógica espalhada ou soluções temporárias.

---

## 2. Estrutura Modular de Pastas

As capturas de tráfego são particionadas em módulos dedicados para facilitar a comparação cirúrgica e o isolamento de cada fluxo de jogo:

```text
Docs-Refs/Wireshark - Oficial Classic 5.0/
├── 01_Login_World/
│   ├── Elyos/                  # Login, Seleção e Entrada no Mundo em Sanctum (Elyos)
│   └── Asmodians/              # Login, Seleção e Entrada no Mundo em Pandaemonium (Asmodians)
├── 02_Character_Creation/
│   ├── Elyos/                  # Criação de Personagem, Rosto, Voz e Customização
│   └── Asmodians/              # Criação de Personagem Asmodian
├── 03_Tutorial_Inicial/
│   ├── Elyos_Poeta/            # Missões de tutorial e monstros iniciais de Poeta
│   └── Asmodians_Ishalgen/     # Missões de tutorial e monstros iniciais de Ishalgen
├── 04_Combate_Skills/
│   ├── Nova_Classe/            # Nova classe 5.0 (Soul Reaper / Foice, Magias, Ataques e Efeitos)
│   └── Geral/                  # Combate e habilidades de outras classes
├── 05_Quests_Dialogos/         # Interações com NPCs, Diálogos e Janelas de Missões
├── 06_Sistemas_Novos_5.0/      # Novas Instâncias e Conteúdos Exclusivos 5.0
├── capture_5.0.bat             # Executável de 1 clique para iniciar a captura
├── capture_5.0.ps1             # Motor de captura automatizado via dumpcap/Wireshark
└── README.md                   # Este manual técnico de referência
```

---

## 2. Como Gravar uma Sessão de Captura

### Passo a Passo:
1. Abra o arquivo **`capture_5.0.bat`** (ou execute no terminal).
2. O menu interativo exibirá as opções de pastas disponíveis:
   - Digite o número correspondente ao teste que irá realizar (ex: `1` para `01_Login_World\Elyos`).
3. O gravador iniciará imediatamente na interface de rede com o filtro de captura ativado e divisão automática em arquivos de no máximo **100 MB** cada.
4. Abra o cliente do jogo oficial 5.0 e execute as ações no jogo.
5. Quando concluir a sessão no jogo, retorne à janela do terminal e pressione **`Ctrl + C`** para finalizar a gravação de forma segura e gravar o arquivo `.pcapng`.

---

## 3. Configurações Técnicas de Captura

* **Utilitário de Baixo Overhead**: Utiliza `dumpcap.exe` nativo do Wireshark (`E:\Programas instalados - Leves\Wireshark\dumpcap.exe`), sem abrir interface pesada durante o jogo para garantir 0 impacto no FPS.
* **Filtro de Captura (BPF)**:
  ```text
  tcp and (port 2106 or port 7777 or port 10241 or port 13001 or port 6600 or (port >= 7770 and port <= 7790))
  ```
  *(Captura exclusivamente os pacotes do Aion Classic, descartando ruídos de Discord, navegadores, downloads e atualizações).*
* **Particionamento de Arquivos**: `-b filesize:102400` (cada arquivo é limitado a 100 MB).

---

## 4. Análise e Decodificação de Opcodes e Protocolo

Para inspecionar, decodificar a cifra dinâmica e listar todos os opcodes capturados na sessão oficial:

### Censo de Opcodes:
```powershell
python "D:\AION CLASSIC 5.0 - EMULADOR\6 - Ferramentas\aion_pcap.py" "01_Login_World\Elyos\<arquivo>.pcapng" "D:\AION CLASSIC 5.0 - EMULADOR" --opcodes
```

### Correlação Pedido / Resposta (Lift):
```powershell
python "D:\AION CLASSIC 5.0 - EMULADOR\6 - Ferramentas\aion_pcap.py" "01_Login_World\Elyos\<arquivo>.pcapng" "D:\AION CLASSIC 5.0 - EMULADOR" --correlacao
```

---

## 5. Filtros Úteis no Wireshark GUI

Ao abrir qualquer arquivo `.pcapng` gerado no Wireshark:

| Finalidade | Filtro de Exibição (Display Filter) |
|---|---|
| **Login Server & Auth (NCSoft)** | `tcp.port == 2106` |
| **Game Server (Mundo, Spawns, Movimento)** | `tcp.port == 7777` |
| **Chat Server (Canais e Sussurros)** | `tcp.port == 10241` |
| **Handshake Gameforge HQ** | `tcp.port == 13001` |
| **Handshake STS** | `tcp.port == 6600` |
| **Pacotes de Dados com Payload (ignora ACKs puros)** | `tcp.len > 0` |
