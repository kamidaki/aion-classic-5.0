# Política de Segurança e Divulgação de Vulnerabilidades — AION CLASSIC 5.0 EMULADOR

A segurança do ecossistema **AION CLASSIC 5.0 EMULADOR** é tratada com rigor inegociável, baseada na arquitetura de **Confiança Zero no Cliente** e isolamento absoluto de processos, redes e bancos de dados.

---

## 1. Versões e Componentes com Suporte Ativo

| Componente | Tecnologia | Status de Suporte |
| :--- | :--- | :---: |
| **Backend Java 25 (`commons`, `login-server`, `chat-server`)** | Java 25 LTS (jdk-25.0.2) | Suportado |
| **GameServer GameForge (`game-server-gameforge` - GSID 1)** | Java 25 LTS / DB `aionclassic_gs` | Suportado |
| **GameServer Remake (`game-server-remake` - GSID 2)** | Java 25 LTS / DB `aionclassic_gs2` | Suportado |
| **GameServer BattleRoyale (`game-server-battleroyale` - GSID 3)** | Java 25 LTS / DB `aionclassic_gs3` | Suportado |
| **Supervisor Nativo e DB Studio (`Aion Classic - EMULADOR.exe`)** | Rust 1.80+ (MSVC x64) | Suportado |
| **Proxy Hook Standalone (`version.dll`)** | C/C++ (MSVC v143 x64/x86) | Suportado |
| **Otimizador de Latência (`Academy NoLag`)** | .NET 9.0 / C# | Suportado |
| **Versões legadas Java (8 / 11 / 17 / 21) ou dependências Javolution** | — | Descontinuado / Proibido |

---

## 2. Como Reportar Vulnerabilidades

**NUNCA abra uma Issue pública para relatar vulnerabilidades de segurança exploráveis.**

Para reportar problemas de segurança:
1. Utilize o canal oficial privado do GitHub: **[Report a Vulnerability (GitHub Security Advisories)](https://github.com/kamidaki/aion-classic-5.0/security/advisories/new)**.
2. Forneça uma descrição detalhada do problema, passos exatos para reproduzir e, se aplicável, provas de conceito (PoC) seguras.
3. Os mantenedores confirmarão o recebimento em até **48 horas** com análise preliminar e prazo para publicação de correção.

---

## 3. Diretrizes de Segurança Inegociáveis

* **Isolamento de GameServers**: Cada GameServer é um processo e banco estritamente separado. Nenhuma falha em um servidor pode comprometer a estabilidade dos demais.
* **Sem Credenciais no Repositório**: Arquivos como `database.properties`, tokens, senhas e chaves privadas nunca devem ser versionados.
* **Isolamento de Painel Administrativo**: O supervisor web embutido em Rust deve sempre operar estritamente em `127.0.0.1:18080` (loopback exclusivo).
* **Validação de Rede NIO e GeoIP**: O subsistema `GeoIPFilterService` e deserializadores de pacotes devem manter verificação estrita de buffer para prevenção de buffer over-read e esgotamento de memória.
