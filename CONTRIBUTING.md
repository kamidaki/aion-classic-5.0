# Guia de Contribuição e Diretrizes de Engenharia — Aion Classic 5.0 (Lost Academy Group)

<p align="center">
  <a href="./CONTRIBUTING.md"><img src="https://img.shields.io/badge/Idioma-Portugu%C3%AAs_(Padr%C3%A3o)-10b981?style=for-the-badge" alt="Português Padrão" /></a>
  <a href="./CONTEXT.md"><img src="https://img.shields.io/badge/Arquitetura-CONTEXT.md-3b82f6?style=for-the-badge" alt="CONTEXT.md" /></a>
  <a href="./SECURITY.md"><img src="https://img.shields.io/badge/Seguran%C3%A7a-SECURITY.md-ef4444?style=for-the-badge" alt="SECURITY.md" /></a>
</p>

> [!CAUTION]
> # LEITURA OBRIGATÓRIA ANTES DE SUBMETER QUALQUER CÓDIGO OU PULL REQUEST
> 1. **ESCOPO EXCLUSIVO GAMEFORGE GSID 1:** Todas as contribuições devem contribuir diretamente para a fidelidade **100% PvE ao Aion Retail Oficial EU (Gameforge)** tendo como única referência o **GameServer 1 — GameForge (`GSID 1`)**.
> 2. **REJEIÇÃO DE GSID 2 E GSID 3:** Pull Requests que mencionem, alterem ou introduzam referências a **GSID 2** ou **GSID 3**, ou que modifiquem servidores secundários, **NÃO serão aceitos**.
> 3. **IDIOMA PADRÃO PORTUGUÊS:** Não altere o idioma padrão do projeto para inglês. A única exceção relacionada a idioma é a implementação ou melhoria de **sistema multilínguas** que permita ao usuário escolher o idioma mantendo o padrão atual.
> 4. **EVIDÊNCIAS OBRIGATÓRIAS:** Submissões devem incluir testes reais e comprovação técnica contra o servidor oficial Gameforge EU (capturas/logs, dados estáticos, análise via Ghidra/Wireshark quando aplicável).

---

## 1. Escopo Aceito e Critérios de Aprovação

Somente serão aceitos Pull Requests que contribuam diretamente para o objetivo principal do **Aion Classic 5.0 — Lost Academy Group**:

### Contribuições Aceitas
- Correções e melhorias PvE no módulo `game-server-gameforge` (**GameServer 1 — GameForge GSID 1**): quests, NPCs, skills, drops, instâncias, eventos, combate, progressão e regras oficiais;
- Ajustes de compatibilidade de rede e protocolo em componentes compartilhados (`commons`, `login-server`, `chat-server`, `version.dll`) necessários ao funcionamento do **GameForge GSID 1**;
- Implementação ou aperfeiçoamento de sistema multilínguas permitindo seleção de idioma pelo usuário sem remover o idioma padrão (Português);
- Correções de segurança, build Maven (Java 25 LTS) e documentação técnica alinhadas ao projeto.

### Contribuições Recusadas Automaticamente
Pull Requests serão fechados sem merge caso:
1. Alterem o escopo para servidores secundários ou contenham referências ao **GSID 2** ou **GSID 3**;
2. Desviem do comportamento oficial Gameforge EU (exceto correção de bug comprovadamente existente no oficial);
3. Alterem o idioma padrão do projeto para inglês;
4. Removam código funcional sem comprovação ou substituam mecânicas específicas por implementações genéricas;
5. Misturem múltiplos sistemas não relacionados em um único PR ou adicionem código bypass em Java para ocultar falhas em templates XML;
6. Introduzam credenciais reais, IPs privados, tokens secretos ou caminhos fixos locais (`C:\`, `D:\`).

---

## 2. Padrão de Qualidade e Testes Obrigatórios

Antes de abrir um Pull Request, valide localmente:

1. **Compilação Limpa (Java 25 LTS):**
   ```bash
   mvn clean package --file "Código Fonte - Emulador/pom.xml"
   ```
2. **Execução de Testes Automatizados:** todos os testes do `commons` e `game-server-gameforge` devem passar sem regressões.
3. **Preservação de Heranças 4.8:** modificações em códigos herdados da Beyond Aion 4.8 devem ser analisadas e corrigidas item a item, preservando créditos originais e comportamentos já validados para Classic 5.0.
4. **Portabilidade e Higienização:** use exclusivamente configurações de exemplo locais (`127.0.0.1`, porta `3306`, usuário `LostAcademyGroup`, senha `LostAcademyGroup`) quando editar templates de configuração.

---

## 3. Padrão de Mensagens de Commit

Mantenha mensagens objetivas em Português, no estilo Conventional Commits:

```text
fix(gameforge): corrigir dialogo e recompensa de quest em pandaemonium
feat(l10n): adicionar selecao de idioma nas mensagens do servidor
fix(login-server): validar tamanho de payload no pacote de autenticacao
docs: atualizar documentacao tecnica do objetivo GameForge GSID 1
```

---

## 4. Formulário de Pull Request

Ao submeter um Pull Request, preencha completamente o template [`.github/pull_request_template.md`](.github/pull_request_template.md). PRs em branco, sem evidências técnicas ou fora do escopo GameForge GSID 1 serão recusados.
