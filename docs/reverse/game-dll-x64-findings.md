# Relatório Completo de Engenharia Reversa e Desenvolvimento
## Emulador Aion Classic EU (Moderno x64)

---

### 1. Visão Geral da Sessão
Durante esta sessão, desenvolvemos a infraestrutura completa do emulador **Aion Classic (.NET 9 C#)** voltado para o cliente moderno de 64 bits do **Aion Classic EU (Gameforge)** e realizamos engenharia reversa profunda no executável e bibliotecas do cliente (`Game.dll x64`) para desvendar e implementar todo o handshake de autenticação de baixo nível.

---

### 2. Arquitetura do Emulador Criada
A solução foi estruturada em módulos de alta performance em C# / .NET 9:
- **`AionClassic.LoginServer`**: Servidor de autenticação assíncrono escutando em `0.0.0.0:2106`.
- **`AionClassic.GameServer`**: Servidor de mundo e templates estáticos escutando em `0.0.0.0:7777`.
- **`AionClassic.Network`**: Motores de criptografia (Blowfish e RSA 1024-bit com Scramble de NCSoft) e leitura/escrita de pacotes em memória.
- **`AionClassic.Data` & `AionClassic.Common`**: Modelos de conta, personagens e templates.
- **`Start_Client_Classic_EU.bat`**: Script de inicialização calibrado com flags do Gameforge EU (`-cc:2 -lang:eng`).

---

### 3. Descobertas de Engenharia Reversa no `Game.dll x64`

| Endereço / Rotina | Descrição Técnica | Impacto / Correção Aplicada |
|---|---|---|
| **`0x15A0E0` (`UI Login Submit`)** | O manipulador do clique no botão de login verificava se a autenticação web do Gameforge estava ativa (`authState == 3`). | **Patch no `Game.dll`**: Instrução em `0x15A125` substituída por 6 NOPs (`90 90 90 90 90 90`), liberando o clique direto. |
| **`0x842301` (`SM_INIT Parser`)** | O cliente executa `movzx ecx, byte ptr [rdx+0xA8]; lea eax, [rcx-0xFD]; cmp al, 1`. | **Flag `0xFD`**: O byte no offset `0xA8` do `SM_INIT` obrigatoriamente deve ser `0xFD`, seguido das versões do Classic `4.5` (`0x04 0x05 0x00 0x00`) para ativar o RSA e a chave Blowfish. |
| **`0x717BE2` (`SM_LOGIN_OK TOS`)** | O cliente testa o bit `0x10` (16) das flags da conta (`test bl, 0x10`). Se zerado, bloqueia na tela de Termos de Serviço. | **Flags `0x3F`**: Configurado `0x0000003F` nos campos de flags da conta e `TOS = 1` no offset `0x30`. |
| **`0x717B40` (`Account Signature`)** | O cliente exige que os offsets `0x20` e `0x21` contenham `0xFF` e `0xFE` (`cmp [rbp+67h], 0xFF` e `cmp [rbp+68h], 0xFE`). | **Assinatura `0xFF 0xFE`**: Adicionados os bytes de validação para permitir a chamada `cmp eax, 0x102` que invoca `UI_ServerSelect`. |
| **`0x84284D` (`SM_SERVER_LIST`)** | Cada entrada de servidor possui **21 bytes** (em vez dos 20 bytes do Aion 2015). O 21º byte é o `Bracket / CountryCode` comparado com o `-cc:2` (`0x842B1B: cmp eax, ecx`). | **Estrutura de 21 bytes**: Adicionado o 21º byte com valor `2` e criadas entradas universais para Brackets 0, 1 e 2. |
| **`0x842B20` (`Classic Server Bits`)** | O cliente executa `bt r15d, 10; jae 0x842DD8` (testa o Bit 10 = `0x400` do campo `ServerBits`). | **ServerBits `0x401`**: Configurado `0x00000401` (Bit 10 ativo = Servidor Classic). |
| **`0x843077` (`Character Counts`)** | O cliente lê `short(totalServers)` seguido diretamente por 1 byte por servidor para a quantidade de personagens criados. | **Seção de Contagem**: Removido byte extra intercalado, alinhando com a estrutura esperada. |

---

### 4. Layout Exato dos Pacotes Implementados

#### `SM_INIT` (194 bytes totais)
- `offset 0x00` (1 byte): `0x00` (Opcode)
- `offset 0x01..0x04` (4 bytes): `SessionId`
- `offset 0x05..0x08` (4 bytes): `0x0000C621` (Revision)
- `offset 0x09..0x88` (128 bytes): RSA Modulus embaralhado
- `offset 0x89..0x94` (12 bytes): `0` (Padding)
- `offset 0x95..0xA4` (16 bytes): Chave Blowfish da sessão
- `offset 0xA5..0xA7` (3 bytes): `0`
- `offset 0xA8` (1 byte): **`0xFD`** (Chave de ativação do RSA x64)
- `offset 0xA9..0xAC` (4 bytes): `0x04, 0x05, 0x00, 0x00` (Versão 4.5 Classic)

#### `SM_LOGIN_OK` (Opcode `0x03`)
- `offset 0x00..0x03`: `AccountId`
- `offset 0x04..0x07`: `SessionKey1`
- `offset 0x08..0x0F`: `0`
- `offset 0x10..0x1F`: `0x0000003F` (Termos Aceitos / Adulto / Ativo)
- `offset 0x20`: `0xFF` (Assinatura Classic)
- `offset 0x21`: `0xFE` (Assinatura Classic)
- `offset 0x22..0x2F`: `0`
- `offset 0x30..0x33`: `0x00000001` (TOS Flag)
- `offset 0x34..0x4C`: `0` (25 bytes padding)

#### `SM_SERVER_LIST` (Opcode `0x04`)
- `offset 0x00`: `serverCount`
- `offset 0x01`: `lastServerId`
- **Por servidor (21 bytes)**:
  - `ID` (1 byte)
  - `IP` (4 bytes)
  - `Porta` (4 bytes: 7777)
  - `AgeLimit` (1 byte: 0)
  - `PvP` (1 byte: 1)
  - `PlayersOnline` (2 bytes: 0)
  - `MaxPlayers` (2 bytes: 1000)
  - `Status` (1 byte: 1)
  - `ServerBits` (4 bytes: `0x00000401`)
  - `Bracket` (1 byte: `2` / `1` / `0`)
- **Seção de Contagem**: `short(serverCount)` + `byte[serverCount]` (contagem de chars).

---

### 5. Estado Atual do Sistema
- Ambos os serviços (`LoginServer` na `2106` e `GameServer` na `7777`) estão compilados, funcionais e rodando de forma estável em .NET 9.
- O cliente x64 conecta, estabelece o handshake de criptografia Blowfish, valida os Termos de Serviço e recebe a lista de servidores sem gerar falhas de rede.
- Backup intacto de segurança de todos os binários preservado em `Game.dll.bak`.

---

### 6. Próximos Passos (Para a Próxima Sessão)
1. **Inspecionar a função de chamada `sub_747451`** (a rotina de instanciação do XML da interface `UI_ServerSelect`) para verificar se ela espera algum arquivo XML específico descompactado na pasta `data/ui/` do Gameforge.
2. **Testar o bypass de transição direta**: Fazer o cliente transicionar do login direto para o GameServer ignorando a renderização visual da lista, ou mapear o ID de string exato do servidor no `Strings.pak`.
