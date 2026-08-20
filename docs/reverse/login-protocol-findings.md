# O login do Classic 4.5 não é o protocolo legado da NCSoft

## O que se acreditava

`docs/reverse/game-dll-x64-findings.md` (o `walkthrough.md` original) descreve o cliente 4.5
falando o protocolo de login clássico da NCSoft: `SM_INIT` com módulo RSA embaralhado e chave
Blowfish, `SM_LOGIN_OK` com flags de conta, `SM_SERVER_LIST` com entradas de 21 bytes. A Fase 1
do roadmap foi construída em cima disso.

**Isso não se sustentou no teste contra o cliente.**

## O que o teste mostrou

Servidor Java com os três pacotes portados, cliente 4.5 real (`-ip:127.0.0.1 -port:2106 -ls
-noauthgg -cc:2`):

```
Connection attemp from: 127.0.0.1
[cripto] slice.limit=177 passado para a cripto=177 saiu com=192   <- tamanho igual ao do POC em C#
pacote do cliente nao decripta: 32 bytes
  cifrado    : 68ab0b85c5610e3acc9d13cd6adb12124ba2e6a8727156ecbc285c4a6aed2062
  chave envia: 810a77a53da64dc76e32213dc08a3220 (SM_INIT+0x95)
  -> nenhuma janela da regiao da chave decripta
```

O `CryptDiagnostics` testa **todas** as janelas de 16 bytes da região da chave no `SM_INIT`, mais a
chave estática. Nenhuma decripta. O problema não é offset.

## Por que a premissa era falsa

O POC em C#, de onde os layouts vieram, **nunca decriptou um pacote do cliente**. Ele:

* respondia a pacotes de 168 bytes sem sequer tentar decriptar
  (`if (payload.Length == 168) { SendLoginOk(); }`)
* logava `"Checksum Blowfish divergente, tentando processar..."` e seguia adiante

Ou seja, o "handshake Blowfish funcionando" era o servidor respondendo às cegas. O cliente chegar
à tela de seleção de servidor nunca foi confirmado por decriptação nenhuma.

## A evidência no binário

Varredura no `Game.dll` do cliente 4.5 (`ProductVersion 4526.0820.0706.7137`):

| procurado | resultado |
|---|---|
| chave estática do AL/POC (`6b 60 cb 5b …`) | **ausente** — nem os 4 primeiros bytes |
| P-array do Blowfish (`24 3f 6a 88 …`, dígitos de pi) | **ausente** |
| S-box do Blowfish (`d1 31 0b a6 …`) | **ausente** |

Ressalva honesta: o `Game.dll` é empacotado (Themida), então constantes podem estar cifradas nas
seções protegidas. A ausência sozinha não prova. Mas some com o resto.

## O que o POC em Rust mostra

O `reference/rust-poc` é a única base no disco que comprovadamente entrou no mundo com um cliente
Classic — e **não tem Blowfish em lugar nenhum**. O `krypt` só traz `game.rs` e `sts.rs`. O auth
server dele é texto claro:

```
[u16 tamanho][u8 opcode][3 bytes][payload]

0x05  greeting  92 bytes: duas chaves UUID + nome de serviço "aiongfc"
0x01  login ok  14 bytes
0x02  lista de servidores, entradas de 63 bytes (não 21)
0x04  session key, com bytes[14..18] obrigatoriamente zero
```

## O teste cruzado

Rodando o próprio auth-server do Rust na 2106, com os nossos flags:

```
→ AUTH_GREETING (92 bytes)
← credentials (0 bytes)          <- o cliente fechou sem responder
```

Com o nosso `SM_INIT`, o cliente responde 32 bytes; com o greeting do Rust, não responde nada. Mas
os flags do POC em Rust são outros — `-usehqserver -hqip -hqport:13001 -np: -loginex` — e o fluxo
dele tem mais duas peças que não estavam no ar: o named pipe do launcher
(`\.\pipe\GameforgeClientJSONRPC`) e o STS na 6600. O teste na 2106 com flags legados não exercita
o caminho que o POC usava, então ele não refuta o Rust; só mostra que os dois meios-caminhos falham.

O cliente exibe `Everything is OK. (0)` — o diálogo genérico de desconexão, sem código de erro útil.

## Onde isso deixa a Fase 1

Os três pacotes portados (`SM_INIT`, `SM_LOGIN_OK`, `SM_SERVER_LIST`) estão corretos **em relação ao
que o walkthrough descrevia** — os offsets são verificados por `scripts/verify_login_packets.sh` —
mas provavelmente descrevem um caminho de código que este cliente não percorre.

O próximo passo não é mexer mais nesses três. É reproduzir a configuração que comprovadamente
funcionou (launcher + STS 6600 + auth 13001 + os flags do POC em Rust), confirmar até onde o cliente
chega, e só então portar **esse** protocolo para o Java.
