# Política de Segurança e Divulgação de Vulnerabilidades

A segurança do projeto **AION CLASSIC 5.0 EMULADOR** é prioridade absoluta, especialmente em relação ao isolamento do backend, sockets NIO, supervisão de processos locais e proteção de dados.

---

## 1. Versões e Componentes com Suporte Ativo

| Componente | Tecnologia | Status de Suporte |
| :--- | :--- | :---: |
| **Backend Multimodular (`commons`, `login-server`, `game-server`, `chat-server`)** | Java 25 LTS (jdk-25.0.2) | :white_check_mark: Suportado |
| **Supervisor Nativo e Database Studio** | Rust 1.80+ (MSVC x64) | :white_check_mark: Suportado |
| **Academy NoLag Network Engine** | .NET 9 / C# | :white_check_mark: Suportado |
| **Proxy Hook do Cliente (`version.dll`)** | C/C++ (MSVC v143) | :white_check_mark: Suportado |
| Versões legadas (Java 8 / 11 / 17 / 21) | — | :x: Descontinuado |

---

## 2. Reportando uma Vulnerabilidade

**NUNCA abra uma Issue pública para reportar vulnerabilidades de segurança exploráveis.**

Para reportar problemas de segurança:
1. Utilize o recurso oficial do GitHub: **[Report a Vulnerability](https://github.com/kamidaki/aion-classic-5.0/security/advisories/new)** (Security Advisories privados).
2. Forneça uma descrição detalhada do problema, passos para reproduzir e, se possível, uma prova de conceito (PoC) segura.
3. A equipe responderá em até 48 horas após a confirmação do relatório com uma análise preliminar e prazo para correção.

---

## 3. Diretrizes de Contribuição Segura

- **Sem Credenciais no Repositório**: Arquivos como `database.properties`, tokens, senhas e chaves privadas nunca devem ser comitados.
- **Isolamento de Interfaces**: O supervisor web administrativo deve sempre operar estritamente em `127.0.0.1` (*loopback*).
- **Validação de Rede NIO**: O subsistema `GeoIPFilterService` e deserializadores de pacotes devem manter verificação estrita de buffer para prevenção de buffer over-read / out-of-memory.
