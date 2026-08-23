# 06 - MAPEAMENTO DE PACOTES REAIS DO CLIENT

## OBJETIVO
Mapear todos os pacotes reais capturados e validados entre o client 64-bit do Aion Classic EU e os servidores de Login, STS, Game e Chat, documentando seus opcodes, tamanhos e sequência de handshake.

## PROBLEMA
Presumir que os pacotes do Aion Classic seguem o formato antigo do Aion 2015 ou de emuladores desatualizados resulta em falhas silenciosas de decodificação e desconexões.

## CAUSA
O tráfego de rede capturado com Wireshark/tshark (`traffic_capture.pcapng` e `gf-login.pcapng`) demonstra que o cliente utiliza três protocolos paralelos distintos:
1. **Gameforge HQ Auth Protocol (Porta 13001)**: Framing sem cifra com cabeçalho `[u16 len][u8 opcode][3 bytes zero][payload]`.
2. **STS Federated Auth Protocol (Porta 6600)**: HTTP 1.0 customizado sobre TCP com envelopes XML.
3. **Aion Game Protocol (Porta 7777)**: Cifra simétrica proprietária de streaming com dynamic key tables.

## ANÁLISE
### 1. Sequência Completa de Handshake (Modo Gameforge HQ)
```text
Client                  Login-Server (13001)       STS-Server (6600)        Game-Server (7777)
                                                                                 
   1. TCP SYN/ACK                                                  
   2. 0x05 AUTH_GREETING  (92 bytes)                                      
                                                                                 
   3. TCP SYN/ACK                         
   4. POST /Sts/Connect                         
   5. POST /Auth/LoginStart                         
   6. STS/1.0 200 OK (<Reply> LoginName)                         
                                                                                  
   7. 0x01 CREDENTIALS  (Token / Plaintext)                             
   8. 0x01 LOGIN_OK  (14 bytes)                                      
   9. 0x02 SERVER_LIST  (201 bytes)                                     
   10. 0x02 SERVER_SELECT  (10 bytes, id 0x17)                             
   11. 0x04 SESSION_KEY  (22 bytes, err=0)                               
                                                                                 
   12. TCP SYN/ACK 
   13. SM_KEY 
   14. CM_ENTER_WORLD (SessionKey) 
   15. SM_CHARACTER_LIST 
```

### 2. Opcodes Mapeados do Login Server (Modo NCSoft Clássico - Porta 2106)
| Opcode | Direção | Nome | Tamanho | Descrição |
|---|---|---|---|---|
| `0x00` | S -> C | `SM_INIT` | 194 bytes | Envia RSA Modulus + Blowfish key + flag `0xFD` + versão `4.5` |
| `0x08` | C -> S | `CM_LOGIN` | 128 bytes | Credenciais cifradas com Blowfish |
| `0x03` | S -> C | `SM_LOGIN_OK` | 52 bytes | Retorna AccountId, SessionKey1, flags `0x3F` e assinatura `0xFF 0xFE` |
| `0x04` | S -> C | `SM_SERVER_LIST` | Var (21B/srv) | Lista de mundos disponíveis com Bracket e ServerBits `0x401` |
| `0x02` | C -> S | `CM_SERVER_SELECT`| 10 bytes | Seleção do servidor de destino |
| `0x06` | S -> C | `SM_PLAY_OK` | 22 bytes | Envia SessionKey2 para conexão no GameServer |

## SOLUÇÃO
Implementar serializadores e desserializadores estritos para ambos os protocolos dentro do crate `login-server`, garantindo compatibilidade total tanto com clientes que iniciam com `-usehqserver` quanto com conexões diretas.

## ARQUIVOS ENVOLVIDOS
* `docs/protocol/auth-server.md`
* `docs/protocol/game-server.md`
* `Emulador-Rust/login-server/src/net/protocol/`
* `Emulador-Rust/game-server/src/net/protocol/`

## IMPLEMENTAÇÃO
* Implementação dos parsers de pacotes usando `bytes::Buf` e `bytes::BufMut`.
* Validação de tamanho e limites de framing para evitar buffer overflow.

## TESTES
* Teste com pacotes reais capturados reproduzidos via script de replay.
* Validação de integridade de checksum e encriptação.

## VALIDAÇÃO
* Todos os pacotes decodificam perfeitamente sem erros de parsing ou bytes órfãos.

## RISCOS
* Pacotes corrompidos ou maliciosos enviados por clientes manipulados.
* Mitigação: Rejeição imediata de conexões com pacotes de framing inválido.

## DEPENDÊNCIAS
* `bytes`, `krypt`.

## TO-DO
- [x] Mapear o fluxo do protocolo HQ (13001).
- [x] Mapear o fluxo do protocolo STS (6600).
- [x] Mapear o fluxo do protocolo NCSoft (2106).
- [x] Documentar os tamanhos e layouts exatos.

## STATUS
[x] TESTADO
[x] VALIDADO
STATUS: CORRIGIDO E VALIDADO
