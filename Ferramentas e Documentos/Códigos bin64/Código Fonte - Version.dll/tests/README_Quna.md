# Quna: saldo exibido no cliente

No cliente Classic 5.0 x64, todo campo de Quna (inventário, "Funds owned" da Quna Market,
compra na Auction House, expansão do Wardrobe) mostra a soma de dois globais de 64 bits do
`Game.dll`: Quna e Quna grátis (RVA `0x15E3A40` e `0x15E3A48` neste build). Os dois nascem em
`-1` e o campo aparece como "-". Só o parser da resposta XML do STS da NCSoft (porta 6600)
grava neles, e o cliente do emulador não abre o STS (`-noweb -nowebshop`).

O emulador manda o saldo da conta no S 0x11B `[H código][Q saldo]`, no login e a cada mudança.
O hook de `version.dll` entra na função que recebe cada pacote do servidor já decifrado
(`[H opcode cru][C][H checksum][payload]`) e, quando o opcode cru é `0x10B` (S 0x11B) com
checksum válido, grava o saldo no global de Quna e 0 no de Quna grátis. O pacote segue sem
alteração para o cliente.

A instalação procura duas assinaturas únicas em seções executáveis: a chamada da entrega do
pacote no laço de recepção e a função que escreve o saldo no cabeçalho da Quna Market (de onde
saem os endereços dos globais). Clientes diferentes não recebem a alteração. Só existe no
**bin64**. O `Game.dll` original não é alterado.

Testes nativos:

```powershell
msbuild tests/quna_fix_checks.vcxproj /p:Configuration=Release /p:Platform=x64
& ./src/x64/QunaChecks/quna_fix_checks.exe
```

Cobrem o 0x11B oficial (saldo 438), o do login do emulador, outros opcodes, checksum errado,
corpo curto, saldo negativo e cliente sem os globais.
