# Guia de Suporte e Escopo — Aion Classic 5.0 (Lost Academy Group)

> [!CAUTION]
> **O projeto é fornecido "COMO É" (*AS-IS*) e NÃO oferece suporte técnico individual**, ajuda para instalação de MySQL/JDK, fornecimento de arquivos protegidos do cliente ou assistência para configurações personalizadas.

---

## 1. Diagnóstico Básico para Ambiente Local (GameForge GSID 1)

* **Compilação:** requer **JDK 25 LTS** e **Maven 3.9+**.
* **Banco de Dados:** utilize as configurações de exemplo locais (`127.0.0.1`, porta `3306`, usuário `LostAcademyGroup`, senha `LostAcademyGroup`) nos arquivos `database.properties` ou ajuste para sua instância local (schemas `aionclassic_ls`, `aionclassic_cs`, `aionclassic_gs`).
* **Serviços Padrão Ativos:** `ChatServer` (`10241`), `LoginServer` (`2106`) e `GameServer-GameForge` (`7777` — GSID 1).
* **Cliente Local e `version.dll`:** compile conforme [`Código Fonte - Version.dll/README.md`](../Ferramentas%20e%20Documentos/C%C3%B3digos%20bin64/C%C3%B3digo%20Fonte%20-%20Version.dll/README.md) e consulte [`Patch final - Client 5.0/README.md`](../Ferramentas%20e%20Documentos/Patch%20final%20-%20Client%205.0/README.md).

---

## 2. Escopo de Issues Públicas

Relatos públicos devem tratar exclusivamente de falhas técnicas reproduzíveis ou propostas de melhoria compatíveis com a fidelidade oficial **PvE do Aion Retail EU (Gameforge)** no **GameServer 1 — GameForge GSID 1**. Consulte [`CONTRIBUTING.md`](../CONTRIBUTING.md).
