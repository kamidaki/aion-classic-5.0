# ⚠️ AVISO - BACKUP HISTÓRICO DE REFERÊNCIA (EmuRustDurak)

Este diretório contém o **backup da versão inicial/protótipo** do emulador Rust (`EmuRustDurak`), utilizado para análise comparativa e engenharia reversa.

---

### ⚠️ DIRETRIZ IMPORTANTE: NÃO UTILIZAR DIRETAMENTE EM PRODUÇÃO
* O código contido nesta pasta é estritamente para **consulta técnica e referência histórica**.
* O emulador oficial ativo em desenvolvimento e produção está localizado em:
  * **Código-Fonte:** [`Emulador-Rust/`](../../Emulador-Rust/)
  * **Binários e Configurações de Produção:** [`Produto Final/`](../../Produto%20Final/)

---

### 🔍 O que este protótipo fazia:
1. **Named Pipe Win32:** Criava o canal `\\.\pipe\GameforgeClientJSONRPC` para simular o cliente GameForge Launcher.
2. **Autenticação HQ / STS:** Iniciava `aion.bin` com `-usehqserver` e trocava pacotes proprietários nas portas 13001 (HQ) e 6600 (STS).
3. **Mapeamento de Servidores:** Servia o servidor ID 23 ("Atreia") com layout específico de 63 bytes por entrada.
