# Guia de Suporte e Escopo — Aion Classic 5.0 (Lost Academy Group)

<p align="center">
  <a href="./SUPPORT.md"><img src="https://img.shields.io/badge/Idioma-Portugu%C3%AAs_(Padr%C3%A3o)-10b981?style=for-the-badge" alt="Português Padrão" /></a>
  <a href="./README.md"><img src="https://img.shields.io/badge/README-Principal-3b82f6?style=for-the-badge" alt="README" /></a>
  <a href="./CONTRIBUTING.md"><img src="https://img.shields.io/badge/Contribui%C3%A7%C3%A3o-CONTRIBUTING.md-0ea5e9?style=for-the-badge" alt="CONTRIBUTING" /></a>
</p>

> [!CAUTION]
> # AUSÊNCIA DE SUPORTE TÉCNICO INDIVIDUAL
> O projeto **Aion Classic 5.0 — Lost Academy Group** é distribuído estritamente **"COMO É" (*AS-IS*)** para fins educacionais, de estudo e preservação técnica (consulte [`LICENSE`](./LICENSE)).
> **Não oferecemos suporte técnico individual, consultoria de instalação, resolução de problemas de ambiente local ou atendimento privado.**

---

## 1. O Que NÃO Recebe Suporte

Não abra issues solicitando atendimento pessoal ou suporte sobre:

1. Instalação, configuração ou recuperação de acesso do MySQL / MariaDB;
2. Configuração de JDK 25 / Maven ou variáveis de ambiente no sistema operacional do usuário;
3. Fornecimento ou download de clientes comerciais do jogo (o projeto adota estritamente o modelo *Bring Your Own Client*);
4. Erros causados por antivírus de terceiros, redistribuíveis do Visual C++ ou bloqueios de firewall local;
5. Pedidos de customização para servidores privados comerciais ou suporte a servidores secundários fora do escopo do **GameServer 1 — GameForge GSID 1**.

---

## 2. Verificações Autônomas Básicas (Referência Técnica)

Para executar o emulador localmente em modo padrão (**GameServer 1 — GameForge GSID 1**):

1. **JDK 25 e Build:** verifique se `JAVA_HOME` aponta para JDK 25 e compile com `mvn clean package --file "Código Fonte - Emulador/pom.xml"`.
2. **Banco de Dados Local (Exemplo Padrão):** certifique-se de que os schemas `aionclassic_ls`, `aionclassic_cs` e `aionclassic_gs` estejam acessíveis conforme sua configuração em `127.0.0.1:3306` (usuário/senha de exemplo local: `LostAcademyGroup` / `LostAcademyGroup`).
3. **Ordem de Serviços:** `ChatServer` (10241) $\to$ `LoginServer` (2106) $\to$ `GameServer-GameForge` (7777 / GSID 1). Por padrão, módulos secundários permanecem desabilitados em `Emulador - Produto Final/Config/config.json`.
4. **Cliente e Proxy `version.dll`:** consulte [`Ferramentas e Documentos/Códigos bin64/Código Fonte - Version.dll/README.md`](./Ferramentas%20e%20Documentos/C%C3%B3digos%20bin64/C%C3%B3digo%20Fonte%20-%20Version.dll/README.md) e [`Ferramentas e Documentos/Patch final - Client 5.0/README.md`](./Ferramentas%20e%20Documentos/Patch%20final%20-%20Client%205.0/README.md) caso precise gerar a `version.dll` para a pasta do seu cliente local.

---

## 3. Abertura de Relatos de Bug Válidos

Issues públicas devem ser usadas exclusivamente para relatar bugs reproduzíveis relacionados ao objetivo oficial PvE (**GameForge GSID 1**), usando o formulário [`.github/ISSUE_TEMPLATE/bug_report.yml`](.github/ISSUE_TEMPLATE/bug_report.yml) com comparação objetiva frente ao comportamento oficial da Gameforge EU e registros de reprodução.
