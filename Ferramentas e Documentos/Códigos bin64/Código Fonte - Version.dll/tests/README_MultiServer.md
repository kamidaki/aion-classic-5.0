# Multi-GameServer Routing Fix & Validation Test Suite (`multiserver_fix_checks`)

## 1. Visão Geral
Este documento descreve o módulo `multiserver_fix.h` incorporado à `version.dll` (x64) e a suíte de testes unitários automatizados `multiserver_fix_checks.cpp`.

## 2. Diagnóstico de Engenharia Reversa (Game.dll x64)
Durante a inicialização e exibição da lista de servidores (`SM_SERVER_LIST`):
1. **Loop de Criação de Mapa de IP (`0x18088dc10` - `0x18088dd5e`):**
   * O cliente insere as entradas em um `std::map<std::string, ServerEntry*>` indexado pelo IP (`127.0.0.1`).
   * Quando dois servidores possuem o mesmo IP (ex: GS ID 2 e GS ID 3), a instrução `jle` em `0x18088dcb4` descarta a segunda entrada, mantendo apenas a entrada com menor `serverId` (GS ID 2).
2. **Loop de Agrupamento e Sobrescrita (`0x18088ddb0` - `0x18088de19`):**
   * O cliente itera sobre os servidores e consulta o IP no mapa (`0x18088ddd4`).
   * A instrução `0x18088de12: mov eax, [rax + 4]` obtém o ID mapeado (2).
   * A instrução `0x18088de15: mov [r15 + 8], eax` sobrescreve o campo `+8` de todos os servidores do mesmo IP com o ID 2.
3. **Seleção de Servidor na UI (`0x180647470`):**
   * Ao clicar em um servidor, o manipulador de clique executa em `0x1806474a7`:
     `mov eax, dword ptr [rdx + 8]`
     `mov dword ptr [0x1815dc4a0], eax`
   * Em vez de ler o campo legítimo `+4` (que continha o ID 3 recebido do pacote de rede), ele lia o campo `+8`, forçando o envio de `CM_PLAY` com servidor 2.

## 3. Correção por Patches Binários em Tempo de Execução (`multiserver_fix.h`)
Para garantir compatibilidade universal sem alterar os binários originais no disco, a `version.dll` injeta dois micro-patches diretamente no espaço de endereçamento da `Game.dll` após a descriptografia do WinLicense:
1. **Patch 1 (Leitura da Seleção de UI):**
   * Endereço virtual relativo da instrução de leitura: offset +2 da assinatura `selectSig`.
   * Substituição do byte `0x08` por `0x04` (`mov eax, [rdx + 8]` -> `mov eax, [rdx + 4]`).
2. **Patch 2 (Desativação da Sobrescrita do Mapa de IP):**
   * Desvio incondicional no loop de agregação: substituição de `74 0C` (`je +0x0C`) por `EB 0C` (`jmp +0x0C`).
   * Desvia da instrução `mov [r15 + 8], eax`.

## 4. Suíte de Testes Automatizados (`multiserver_fix_checks.cpp`)
A suíte realiza **222 verificações automatizadas**, incluindo:
* Busca e casamento estrito de assinaturas binárias com máscaras (`QunaFindPattern`).
* Validação de escrita segura com `VirtualProtect` e `FlushInstructionCache`.
* Validação de integridade de buffers contra corrupções laterais.
* Garantia de idempotência (múltiplas chamadas não corrompem o estado).
* Validação defensiva contra chamadas com ponteiro nulo (`nullptr`).

### Como Executar os Testes
Para compilar e rodar a suíte no Visual Studio / MSVC x64:
```cmd
cd "Ferramentas e Documentos\Códigos bin64\Código Fonte - Version.dll\tests"
msbuild multiserver_fix_checks.vcxproj /p:Configuration=Release /p:Platform=x64
x64\Release\multiserver_fix_checks.exe
```
Resultado: **222 assertions passed with 0 errors.**
