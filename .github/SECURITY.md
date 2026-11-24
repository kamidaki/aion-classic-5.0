# Política de Segurança e Divulgação de Vulnerabilidades — Aion Classic 5.0 (Lost Academy Group)

A segurança do ecossistema **Aion Classic 5.0 — Lost Academy Group** baseia-se na arquitetura autoritativa no servidor (**Zero-Trust Client Architecture**) e na higienização estrita de configurações versionadas.

---

## 1. Versões e Componentes com Suporte Ativo

| Componente | Tecnologia | Status de Suporte |
| :--- | :--- | :---: |
| **Backend Java 25 (`commons`, `login-server`, `chat-server`)** | Java 25 LTS (jdk-25.0.2) | Suportado |
| **GameServer GameForge (`game-server-gameforge` - GSID 1)** | Java 25 LTS / DB `aionclassic_gs` | Suportado (Padrão) |
| **Proxy Hook Standalone (`version.dll`)** | C/C++ (MSVC v143 x64/x86) | Suportado |
| **Versões legadas Java (8 / 11 / 17 / 21) ou dependências Javolution** | — | Descontinuado |

---

## 2. Como Reportar Vulnerabilidades

**NUNCA abra uma Issue pública para relatar vulnerabilidades de segurança exploráveis.**

Para reportar problemas de segurança:
1. Utilize o canal oficial privado do GitHub: **[Report a Vulnerability (GitHub Security Advisories)](https://github.com/kamidaki/aion-classic-5.0/security/advisories/new)**.
2. Forneça uma descrição detalhada do problema, passos exatos para reproduzir e impacto observado.
3. Evite publicar credenciais, dumps de memória sensíveis ou payloads de ataque em comentários públicos.

---

## 3. Diretrizes de Segurança do Repositório

* **Sem Credenciais Reais no Repositório:** `database.properties`, `network.properties` e `config.json` utilizam exclusivamente valores locais de exemplo (`127.0.0.1:3306`, usuário/senha `LostAcademyGroup`). Credenciais reais, tokens e chaves privadas nunca devem ser submetidos.
* **Isolamento de Rede Local:** Painel de controle e endpoints administrativos locais devem permanecer restritos ao loopback (`127.0.0.1`).
* **Validação de Rede NIO e GeoIP:** `GeoIPFilterService` e deserializadores de pacotes mantêm verificação estrita de limites de buffer.
* **Registro de Vulnerabilidades Mitigadas:** Consulte [`Ferramentas e Documentos/docs/AUDITORIA_VULNERABILIDADES.md`](../Ferramentas%20e%20Documentos/docs/AUDITORIA_VULNERABILIDADES.md).
