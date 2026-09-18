# Siel Hammer: aviso local de cancelamento no sucesso

No cliente Classic 5.0 x64, o resultado `SM_SIEL_HAMMER_RESULT` (opcode interno
`0x1A2`, status zero) abre `DlgItemCrushResult` e fecha `DlgItemCrush`.
O fechamento envia automaticamente `CM_SIEL_HAMMER_CANCEL` (`0x152`) e chama
`ResetProgress`, que emite `STR_MSG_DECOMPOSE_ITEM_CRUSH_STOP` (1404452) quando
o byte de progresso do diálogo, offset `0x524`, ainda está ativo.
A mensagem nasce no cliente; não é um `SM_SYSTEM_MESSAGE` enviado pelo emulador.

O hook de `version.dll` marca o escopo da apresentação do resultado bem-sucedido
e limpa esse byte somente quando `ResetProgress` é chamado dentro desse escopo.
O envio automático do cancelamento é preservado. O botão Stop continua emitindo
a mensagem, e o estado é restaurado inclusive se ocorrer uma exceção no diálogo.
O escopo é local à thread.

A instalação exige assinaturas únicas em seções executáveis e confirmação RTTI
de `DlgItemCrushResult`. Clientes diferentes não recebem essa alteração.
Esta correção é exclusiva do patch **bin64**; não há hook equivalente no bin32.
O `Game.dll` original não é alterado. O cliente precisa ser fechado e reaberto
depois de substituir `bin64/version.dll` pelo arquivo da distribuição do patch.

Compile o projeto principal em Release/x64 com MSBuild e a dependência Detours
4.0.1 restaurada. Para os testes nativos:

```powershell
msbuild tests/siel_hammer_fix_checks.vcxproj /p:Configuration=Release /p:Platform=x64
& ./src/x64/HammerChecks/siel_hammer_fix_checks.exe
```

Os testes exercitam sucesso, Stop, resultado aninhado, isolamento entre threads,
exceção na UI e reset repetido. A conferência visual no jogo deve incluir uma
desmontagem concluída e o botão Stop durante os dois segundos de progresso.

A ordenação de inventário implementada no servidor permanece alinhada à PCAP
oficial, mas essa ordenação, sozinha, não remove o aviso local do cliente.
