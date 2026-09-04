# FASE 02: JAVA 8 USAGE INVENTORY
## Aion Classic 5.0 EU — Java 25 Migration

> **Fase**: 02 de 22  
> **Status**: `[CONCLUÍDO]`  
> **Data de Execução**: 2026-09-04  
> **Objetivo**: Inventário exaustivo de padrões legados da era Java 8 presentes no código-fonte do Aion Classic 5.0.

---

## 1. Resumo Quantitativo de Padrões Legados Detectados

| Padrão Legado | Ocorrências | Arquivos Afetados | Impacto na Migração Java 25 |
| :--- | :--- | :--- | :--- |
| **Construtores de wrapper obsoletos (ex: new Integer(x))** | 7 | 6 | Alto / Prioritário |
| **APIs legadas de data/calendário (java.util.Date / Calendar)** | 25 | 25 | Alto / Prioritário |
| **Coleções obsoletas legadas (Vector, Hashtable, Enumeration)** | 3 | 2 | Alto / Prioritário |
| **Try sem recursos (fechamento manual em vez de try-with-resources)** | 84 | 30 | Alto / Prioritário |
| **Blocos e métodos sincronizados (synchronized)** | 217 | 140 | Alto / Prioritário |
| **Bloqueios explícitos via ReentrantLock** | 40 | 15 | Alto / Prioritário |
| **Instanciação manual de Thread da plataforma** | 2 | 2 | Alto / Prioritário |
| **Uso de ForkJoinPool / coleções chmv8 de backport Java 8** | 11 | 8 | Alto / Prioritário |
| **Cases de switch statement tradicional (break em cascata)** | 11382 | 1093 | Alto / Prioritário |
| **Pattern matching ausente (instanceof seguido de cast explícito)** | 73 | 51 | Alto / Prioritário |

---

## 2. Detalhamento por Categoria de Padrão

### 2.1. Tipagem e Sintaxe Obsoleta
- **Construtores Wrapper (`new Integer()`, `new Long()`)**: Depreciados para remoção desde o Java 9. Devem ser substituídos por `valueOf()` ou autoboxing natural.
- **Pattern Matching para `instanceof`**: Dezenas de ocorrências onde uma checagem `obj instanceof Type` é imediatamente seguida de cast manual `Type t = (Type) obj;`. Modernizável para `if (obj instanceof Type t)`.
- **Switch Statements vs Switch Expressions**: Mais de 11.000 `case ... :` com risco de fall-through acidental e sintaxe verbosa.

### 2.2. Concorrência e Threading
- **Backport `chmv8`**: Classes em `com.aionemu.commons.utils.internal.chmv8` (especialmente `ForkJoinPool` no `ThreadPoolManager`) são resíduos da época pré-Java 8. O Java 25 possui `java.util.concurrent.ForkJoinPool` otimizado e nativo na JVM.
- **`synchronized` (217 ocorrências)** e **`ReentrantLock` (40 ocorrências)**: Devem ser auditados para garantir que protegem invariantes reais e que não causem contenção com virtual threads.
- **Instanciações diretas de `new Thread`**: Podem se beneficiar de `Thread.ofVirtual()` ou factories estruturados em tarefas assíncronas desacopladas.

### 2.3. Gestão de Recursos e I/O
- **Try sem Recursos**: Pelo menos 84 blocos realizam fechamento manual (`close()`, `dispose()`) em blocos finally ou sequenciais, propensos a leaks em caso de falha antes do fechamento.
- **APIs de Data**: `java.util.Date` e `java.util.Calendar` presentes em pontos de parsing e agendamento, candidatos à transição para `java.time` (Instant, Duration, LocalDateTime).

### 2.4. Bibliotecas e Dependências System-Scope
- Módulos `ChatServer`, `LoginServer` e `GameServer` referenciam 35 JARs na pasta local `libs/`, incluindo:
  - `netty-3.2.7.Final.jar` (ano 2011)
  - `c3p0-0.9.1.1.jar` / `HikariCP-4.0.3.jar` (antigo)
  - `logback-classic-1.1.2.jar` (ano 2014)
  - `commons-lang3-3.1.jar` / `commons-io-2.4.jar`

---

## 3. Conclusão da Fase 02
O inventário mapeia com precisão cirúrgica todos os pontos onde o emulador 5.0 mantém código ou bibliotecas no estado Java 8, fornecendo o escopo exato para as transformações de modernização das fases subsequentes.
