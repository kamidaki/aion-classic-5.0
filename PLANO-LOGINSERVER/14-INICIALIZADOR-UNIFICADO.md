# 14 - INICIALIZADOR UNIFICADO (AUTO-START EMURUST)

## OBJETIVO
Implementar o executável central de gerenciamento `Auto-Start EmuRust.exe` (crate `auto-start`), permitindo ao usuário iniciar, parar, reiniciar e monitorar os três servidores a partir de um único ponto de entrada elegante e seguro.

## PROBLEMA
Antes, o usuário precisava lidar com múltiplos scripts `.bat` (`Ligar_Emulador_1Click.bat`, `PARAR_SERVIDOR.bat`, etc.) e múltiplos terminais CMD desorganizados, sem supervisão de falhas ou métricas em tempo real.

## CAUSA
Ausência de um processo supervisor/launcher nativo em Rust.

## ANÁLISE
O `Auto-Start EmuRust.exe` deve atuar como um supervisor de processos:
1. **Process Controller**:
   * Gerencia instâncias filhas dos processos `login-server.exe`, `game-server.exe` e `chat-server.exe`.
   * Capacidade de enviar sinais de parada limpa ou encerramento forçado (`taskkill` / Win32 `TerminateProcess`).
   * Capacidade de reiniciar qualquer servidor individualmente sem afetar os outros.
2. **Crash Detector & Auto-Restart**:
   * Monitora o status de saída (`exit code`) de cada processo.
   * Se um servidor cair inesperadamente e a opção `restartOnCrash` estiver habilitada no `launcher.json`, o supervisor reinicia automaticamente apenas aquele processo específico e gera um alerta no Log Center.
3. **Métricas de Performance**:
   * Coleta contínua de uso de CPU (%) e Memória RAM (MB e %) para cada um dos 3 processos usando a API nativa do Windows (`GetProcessTimes`, `GetProcessMemoryInfo` via `sysinfo`).
4. **Log Forwarder**:
   * Captura a saída padrão (stdout e stderr) de cada servidor em streams assíncronos e direciona tanto para o Log Center na interface quanto para os arquivos físicos diários em `logs/`.

## SOLUÇÃO
Criar o crate `Emulador-Rust/auto-start/` gerando o binário `Auto-Start EmuRust.exe`.

## ARQUIVOS ENVOLVIDOS
* `Emulador-Rust/auto-start/Cargo.toml`
* `Emulador-Rust/auto-start/src/main.rs`
* `Emulador-Rust/auto-start/src/supervisor.rs`
* `Emulador-Rust/auto-start/src/metrics.rs`
* `Emulador-Rust/auto-start/src/log_center.rs`

## IMPLEMENTAÇÃO
* Implementação do supervisor de processos com `tokio::process::Command`.
* Implementação da coleta de métricas com `sysinfo`.
* Implementação do roteador de logs assíncrono.

## TESTES
* Teste de inicialização dos 3 servidores pelo launcher.
* Teste de parada individual e reinício de cada servidor.
* Teste de simulação de crash (matar processo pelo Task Manager) e validação do auto-restart.

## VALIDAÇÃO
* O `Auto-Start EmuRust.exe` inicializa, gerencia os 3 servidores de forma robusta e monitora suas métricas sem consumir CPU excessiva (< 0.5% CPU do supervisor).

## RISCOS
* Processos zumbis deixados para trás caso o supervisor seja fechado de forma abrupta.
* Mitigação: Uso de Windows Job Objects (`CreateJobObject`) com a flag `JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE`, garantindo que se o launcher for finalizado, todos os servidores filhos sejam limpos automaticamente pelo sistema operacional.

## DEPENDÊNCIAS
* `tokio`, `sysinfo`, `serde`, `serde_json`, `windows-sys`.

## TO-DO
- [x] Criar crate `auto-start`.
- [x] Implementar controle de processos com Job Objects.
- [x] Implementar crash detection e auto-restart.
- [x] Testar inicialização e supervisão.

## STATUS
[x] TESTADO
[x] VALIDADO
STATUS: CORRIGIDO E VALIDADO
