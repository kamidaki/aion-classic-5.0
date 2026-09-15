# Spawn Parser (Refatorado & Otimizado)

Este pacote contém o **código-fonte completo em C#** e o **executável pronto para uso** do aplicativo **Spawn Parser**, utilizado para ler e extrair pontos de spawn de NPCs, Monstros e Recursos de Coleta (*Gather*) a partir dos arquivos de dados XML de servidores de jogos (como Aion / Lineage 2 / CryEngine).

---

## 📁 Estrutura deste Pacote

```text
SpawnParser_Entrega/
├── Executavel/
│   ├── spawn_parser_upd.exe      # Executável compilado (.NET 8 Windows Desktop)
│   └── app.ico                   # Ícone da aplicação
│
├── CodigoFonte/
│   ├── spawn_parser.csproj       # Arquivo de projeto C# (.NET SDK moderno)
│   ├── app.ico                   # Ícone embutido do projeto
│   ├── Program.cs                # Ponto de entrada (Main)
│   ├── FormMain.cs               # Interface gráfica (WinForms, logs fluidos e controles)
│   ├── Parser.cs                 # Motor de alta performance de leitura e exportação
│   ├── helper.cs                 # Conversão matemática segura de rotação/heading (h)
│   ├── save.cs                   # Utilitário de persistência atômica em UTF-8
│   ├── general.cs                # Estrutura de estados e parâmetros globais
│   └── Properties/
│       └── AssemblyInfo.cs       # Metadados do assembly
│
├── README.md                     # Esta documentação técnica
└── COMO_USAR.txt                 # Guia rápido de utilização
```

---

## 🔍 Diagnóstico: Por que a versão original travava e crashava?

A versão original do aplicativo apresentava graves problemas arquiteturais e de algoritmo que causavam encerramento fatal (*crash*) e congelamento da máquina:

1. **Complexidade Algorítmica Cúbica $O(N \times M \times N)$**:
   - Para cada objeto no arquivo da missão (`mission_mission0.xml`), o sistema varria todos os registros de `client_npcs.xml` (81 MB) e, a cada encontro, varria novamente todo o arquivo da missão.
   - Em bases com mais de 20.000 NPCs e 10.000 objetos, isso exigia **centenas de bilhões de iterações**, consumindo 100% de CPU indefinidamente.
2. **Crashes por Falta de Tratamento de Nulos (`NullReferenceException`)**:
   - Elementos `<Object>` sem atributo `Type` ou sem atributo `npc` executavam chamadas diretas como `.Equals("SP")` ou `text.Contains(null)`, derrubando o processo instantaneamente.
3. **Vazamento de Memória na LOH (*Large Object Heap*)**:
   - Para evitar duplicatas, o código original utilizava uma única string acumulando nomes (`text += text4;`), alocando gigabytes de memória e gerando falso-positivos em verificações de substring.
4. **Gargalo Extremo de I/O em Disco**:
   - O aplicativo abria, gravava e fechava o arquivo em disco para **cada linha individual do XML** (`using StreamWriter(..., append: true)`), realizando dezenas de milhares de operações de abertura por minuto.
5. **Congelamento da Interface e Limite GDI**:
   - Cada NPC encontrado chamava `Invoke` síncrono no `ListBox`, saturando a fila de mensagens do Windows e travando a janela ("Não Respondendo").
6. **Descarte de Coordenadas Flutuantes**:
   - Rotações com decimais (ex: `Angles="0,0,-45.5"`) falhavam em `Convert.ToInt32`, fazendo com que inúmeros pontos de spawn fossem silenciosamente descartados.

---

## ⚡ Soluções e Otimizações Implementadas

- **Indexação $O(N)$ em Memória**:
  - `client_npcs.xml` e `gather_src.xml` são carregados uma única vez em estruturas `Dictionary<string, NpcInfo>` com buscas em $O(1)$.
  - Os objetos de spawn são lidos e agrupados em uma única passada.
  - **Tempo de processamento reduzido de horas/travamento para ~4 segundos em arquivos de 81 MB!**
- **Validação Segura de Dados**:
  - Todos os atributos e nós XML são validados contra nulos e valores vazios.
  - O cálculo de ângulo em `helper.cs` utiliza `double.TryParse` com suporte a números com ponto decimal e cultura invariante.
- **Interface Não-Bloqueante**:
  - Atualizações via `BeginInvoke` com controle de buffer circular no log, mantendo a janela ágil e responsiva.
- **Gravação em Buffer Contínuo**:
  - O arquivo é escrito de forma direta e sequencial em UTF-8 com buffer único.
- **Autodetecção de Arquivos**:
  - Ao abrir, o programa verifica se existe a pasta `Arquivos_teste` e preenche os campos automaticamente para facilitar o teste imediato.

---

## 🏷️ Nomenclatura e Separação de Arquivos de Saída

Conforme solicitado, a saída foi padronizada com os seguintes sufixos:

- **Categoria `Npc`**: Salva como `spawn_{worldID}_NPC.xml` *(ex: `spawn_800040000_NPC.xml`)*
- **Categoria `Monster`**: Salva como `spawn_{worldID}_Monster.xml` *(ex: `spawn_800040000_Monster.xml`)*
- **Categoria `Gather`**: Salva como `spawn_{worldID}_Gather.xml` *(ex: `spawn_800040000_Gather.xml`)*
- **Categoria `All`**: Processa tudo em **uma única execução** e salva **os 3 arquivos separados** automaticamente:
  - `spawn_{worldID}_NPC.xml`
  - `spawn_{worldID}_Monster.xml`
  - `spawn_{worldID}_Gather.xml`

---

## 🛠️ Como Executar ou Recompilar

### 1. Para Rodar o Executável:
Basta acessar a pasta `Executavel/` e abrir o arquivo `spawn_parser_upd.exe`.
- Requisitos: Windows 10/11 ou Windows 7 SP1+ (com .NET 8 Runtime instalado).

### 2. Para Recompilar pelo Terminal (.NET SDK):
Abra o prompt de comando na pasta `CodigoFonte/` e execute:
```bash
dotnet build -c Release
```
Para gerar um executável único autocontido:
```bash
dotnet publish -c Release -r win-x64 --self-contained false -p:PublishSingleFile=true -o ../Executavel/
```

### 3. Para Abrir em IDEs:
Abra a pasta `CodigoFonte/` ou o arquivo `spawn_parser.csproj` diretamente no **Visual Studio 2022**, **JetBrains Rider** ou **VS Code** (com extensão C# Dev Kit).
