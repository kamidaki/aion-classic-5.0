# 07 - MAPEAMENTO DE OFFSETS E ESTRUTURAS BINÁRIAS

## OBJETIVO
Documentar detalhadamente cada offset de memória, campos de estruturas, tipos primitivos, padding e flags binárias exigidas pelo client x64 do Aion Classic EU.

## PROBLEMA
Qualquer desalinhamento de 1 único byte em estruturas de rede faz com que o cliente x64 interprete campos incorretamente (como ler o IP como porta ou a contagem de personagens como status), resultando em crashes ou telas pretas.

## CAUSA
O compilador de 64 bits do client organiza os campos com alinhamentos estritos e espera tamanhos específicos verificados por instruções `movzx`, `cmp` e `test`.

## ANÁLISE
### 1. `SM_INIT` (Tamanho Total: 194 bytes)
```
Offset (Hex) | Tipo     | Conteúdo / Descrição
-------------+----------+-------------------------------------------------------
0x00         | u8       | Opcode: 0x00
0x01..0x04   | u32 (LE) | SessionId
0x05..0x08   | u32 (LE) | Revision / Protocol Version: 0x0000C621
0x09..0x88   | 128 B    | RSA 1024-bit Scrambled Public Modulus
0x89..0x94   | 12 B     | Zero Padding
0x95..0xA4   | 16 B     | Dynamic Blowfish Key
0xA5..0xA7   | 3 B      | Zero Padding
0xA8         | u8       | 0xFD (Flag de ativação obrigatória do x64)
0xA9..0xAC   | 4 B      | 0x04, 0x05, 0x00, 0x00 (Aion Classic Version 4.5)
0xAD..0xC1   | 21 B     | Zero Trailing Padding
```

### 2. `SM_LOGIN_OK` (Tamanho Total: 52 bytes)
```
Offset (Hex) | Tipo     | Conteúdo / Descrição
-------------+----------+-------------------------------------------------------
0x00..0x03   | u32 (LE) | AccountId
0x04..0x07   | u32 (LE) | SessionKey1
0x08..0x0F   | 8 B      | Zero Padding
0x10..0x1F   | 16 B     | Account Flags (0x0000003F - Ativo / Adulto / TOS OK)
0x20         | u8       | 0xFF (Assinatura de validação da conta Classic)
0x21         | u8       | 0xFE (Assinatura de validação da conta Classic)
0x22..0x2F   | 14 B     | Zero Padding
0x30..0x33   | u32 (LE) | 0x00000001 (TOS Accepted Flag)
0x34..0x4C   | 25 B     | Zero Padding
```

### 3. `SM_SERVER_LIST` Entry (Tamanho: 21 bytes por servidor)
```
Offset (Hex) | Tipo     | Conteúdo / Descrição
-------------+----------+-------------------------------------------------------
0x00         | u8       | Server ID (ex: 23 para Atreia)
0x01..0x04   | 4 B      | Server IP (IPv4 bytes binários ou mapeados)
0x05..0x08   | u32 (LE) | Server Port (7777)
0x09         | u8       | Age Limit (0 = Livre)
0x0A         | u8       | PvP Server (1 = Habilitado)
0x0B..0x0C   | u16 (LE) | Players Online
0x0D..0x0E   | u16 (LE) | Max Players (ex: 1000)
0x0F         | u8       | Server Status (1 = Online, 0 = Offline)
0x10..0x13   | u32 (LE) | ServerBits (0x00000401 -> Bit 10 = Classic Server)
0x14         | u8       | Bracket / Country Code (2 para Classic EU)
```

### 4. Gameforge HQ Server Entry (Tamanho: 63 bytes por servidor)
```
Offset (Hex) | Tipo     | Conteúdo / Descrição
-------------+----------+-------------------------------------------------------
0x00         | u8       | Constante 0x01
0x01         | u8       | Server Type (4 = Mundo, 5 = Instância)
0x04         | u8       | Online Flag (1 = Online)
0x05         | u8       | Server ID (0x17 = 23)
0x09         | u8       | Characters Count na conta
0x0D..0x20   | ASCII    | Server IP em string ASCII terminada em nulo
0x35..0x36   | u16 (LE) | Server Port (7777)
0x37         | u8       | Flag 0x01 se online e tipo 4
```

## SOLUÇÃO
Implementar testes unitários com asserções byte-a-byte (`assert_eq!`) para garantir que nenhuma estrutura sofra desvios durante refatorações.

## ARQUIVOS ENVOLVIDOS
* `Emulador-Rust/login-server/src/net/protocol/packets/`
* `Emulador-Rust/login-server/src/net/protocol/hq/`

## IMPLEMENTAÇÃO
* Código Rust com estruturas `#[repr(C, packed)]` ou construtores manuais seguros usando slices.

## TESTES
* `test_sm_init_offsets`
* `test_sm_login_ok_offsets`
* `test_sm_server_list_offsets`

## VALIDAÇÃO
* Asserções executadas via `cargo test` com 100% de sucesso.

## RISCOS
* Problemas de alinhamento em diferentes arquiteturas (x86_64 vs aarch64).
* Mitigação: Uso explícito de `to_le_bytes()` e offsets absolutos.

## DEPENDÊNCIAS
* `bytes`.

## TO-DO
- [x] Mapear offsets de `SM_INIT` (194 bytes).
- [x] Mapear offsets de `SM_LOGIN_OK` (52 bytes).
- [x] Mapear estrutura de 21 bytes do `SM_SERVER_LIST`.
- [x] Mapear estrutura de 63 bytes do HQ Server List.

## STATUS
[x] TESTADO
[x] VALIDADO
STATUS: CORRIGIDO E VALIDADO
