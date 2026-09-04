# JAVA 8 → JAVA 25 COMPLETE MIGRATION — AION CLASSIC 5.0

You are performing a **critical, production-grade Java modernization and migration** of my Aion Classic 5.0 emulator.

## SOURCE PROJECT — MUST BE MODIFIED

The target emulator is located at:

`D:\AION CLASSIC 5.0 - EMULADOR\1 - Código Fonte [Emulador]`

This is a newly developed Aion Classic 5.0 emulator, released/reconstructed around August 2026. It is currently based on **Java 8** and must be migrated completely to **Java 25**.

## REFERENCE PROJECT — ARCHITECTURAL/TECHNICAL EXEMPLAR

A mature Aion 4.8 Retail emulator exists at:

`D:\AION CLASSIC 5.0 - EMULADOR\5 - Documentação e Referências\3 - JAVA EMU - 4.8 RETAIL`

This emulator is already:

* Fully modernized for Java 25
* Highly optimized
* Cleanly modularized
* Production-proven
* Extremely well structured
* Considered one of the best Aion emulators
* Contains many bug fixes and architectural improvements beyond the original official implementation
* Already demonstrates the Java 25 patterns, libraries, concurrency model, GC/JIT configuration, threading strategies, and modern Java APIs that we want

### CRITICAL RULE

**DO NOT blindly copy the 4.8 emulator's game logic into the 5.0 emulator.**

The 4.8 emulator is the **technical and architectural reference**, not the functional source of the Classic 5.0 implementation.

Preserve the Classic 5.0 emulator's:

* Protocol
* Opcodes
* Packet structures
* Game logic
* Data structures
* Maps
* IDs
* Services
* Quests
* Skills
* NPCs
* Items
* Client compatibility
* 5.0-specific behavior

Use the 4.8 emulator primarily to determine **HOW the same type of Java 8 implementation should be modernized for Java 25**.

When an equivalent implementation, class, method, utility, concurrency mechanism, library, abstraction, or architectural pattern exists in the 4.8 emulator, study it carefully and use the same proven modernization strategy where applicable.

---

# PRIMARY OBJECTIVE

Migrate the Classic 5.0 emulator from **Java 8 to Java 25 completely**.

This is NOT merely a POM update.

Do NOT consider the migration complete simply because:

```text
mvn clean package
```

works with JDK 25.

The objective is to actually modernize the source code.

### ZERO JAVA 8 LEGACY REQUIREMENT

After the migration, the project must contain **no unnecessary Java 8-era implementation patterns**.

Every Java 8-specific or obsolete implementation must be reviewed and modernized where Java 25 provides a superior equivalent.

Only retain APIs, syntax, patterns, or constructs that are genuinely universal and remain correct and appropriate in Java 25.

Do NOT perform pointless rewrites merely for cosmetic reasons.

The goal is:

> **Modern Java 25 code, not Java 8 code that happens to compile on Java 25.**

---

# MANDATORY MIGRATION PLAN

Before modifying the project:

1. Thoroughly inspect the entire Classic 5.0 source tree.
2. Thoroughly inspect the Java 25 4.8 reference emulator.
3. Compare their:

   * Maven configuration
   * JDK configuration
   * Dependencies
   * Module structure
   * Threading
   * Executors
   * Concurrency
   * Collections
   * I/O
   * Networking
   * Reflection
   * Serialization
   * Logging
   * Database access
   * Scheduling
   * Caching
   * Memory management
   * Utility classes
   * Service architecture
   * Lifecycle management
   * Exception handling
   * Synchronization
   * Thread pools
   * Performance-critical code

Then create a **complete enumerated migration plan in Markdown**.

Create the plan inside:

`D:\AION CLASSIC 5.0 - EMULADOR\5 - PLANOS`

Like as:

`1. Baseline and environment audit.md`
`2. Java 8 usage inventory.md`
`3. Reference emulator architecture audit.md`

The plan must contain numbered files separed by phases and substeps.

Example structure (dont copy, its ONLY AN EXAMPLE):

```text
1. Baseline and environment audit
2. Java 8 usage inventory
3. Reference emulator architecture audit
4. Maven/build modernization
5. Dependency modernization
6. Language/API modernization
7. Collections and streams modernization
8. Concurrency modernization
9. Executor/thread-pool modernization
10. Virtual threads analysis and migration
11. Synchronization/locking modernization
12. I/O and networking modernization
13. Database layer modernization
14. Logging and diagnostics modernization
15. Reflection/runtime modernization
16. GC/JIT/runtime optimization
17. Performance-sensitive services migration
18. Static analysis and Java 8 legacy scan
19. Full compilation and test validation
20. Runtime/regression validation
21. Final audit
22. Final Java 25 certification
other files....
```

Do not simply create this plan and stop.

**Execute it sequentially from step 1 to the final step.**

Mark every completed step in the Markdown plan.

If a step fails, investigate and fix the problem before proceeding.

---

# MANDATORY BACKUP / SAFETY STRATEGY

This is a critical migration.

Before modifying substantial portions of the project:

* Verify Git status.
* Create a safe rollback point.
* Preserve the original Java 8 state.
* Never destroy working code without a recoverable version.
* Prefer small, logically isolated commits/checkpoints whenever possible.

Never perform a massive uncontrolled rewrite of the entire repository in one operation.

The emulator currently works.

Therefore:

> **The working behavior of the Classic 5.0 emulator is the highest priority.**

Modernization must improve the implementation without changing its intended game behavior.

---

# USE PYTHON AGGRESSIVELY FOR MASS MIGRATION

Python MUST be used whenever it can safely automate repetitive transformations.

Create temporary migration/audit scripts when necessary.

Python may be used for:

* Recursive source scanning
* Java 8 pattern detection
* Import analysis
* Package analysis
* Deprecated API detection
* Automated import replacement
* Repetitive syntax transformations
* Safe bulk replacements
* Dependency inventory
* Maven file analysis
* Duplicate-pattern detection
* Java source statistics
* Migration progress reports
* Post-migration validation
* Java 8 legacy scans
* Detecting inconsistent modernization
* Comparing patterns against the Java 25 reference project

However:

### NEVER perform blind regex rewriting of complex Java code.

For potentially dangerous transformations:

1. Detect candidates with Python.
2. Analyze the context.
3. Transform only when the transformation is demonstrably safe.
4. Compile immediately.
5. Review compilation errors.
6. Run validation.
7. Continue.

For complex AST-level transformations, prefer proper parsing/refactoring techniques instead of dangerous regex replacements.

---

# JAVA 25 MODERNIZATION

Inspect the 4.8 Java 25 emulator and identify exactly how it modernizes the following areas.

## 1. Language Features

Audit opportunities for:

* `var`
* enhanced switch expressions
* pattern matching
* records
* sealed classes/interfaces
* improved `instanceof`
* text blocks
* modern `String` APIs
* improved collection APIs
* improved exception handling
* modern constructors/factories
* modern interface patterns

Only use features where they improve maintainability and are appropriate for the project.

Do NOT introduce modern syntax merely for novelty.

---

# CONCURRENCY AND THREADING

This is one of the most important parts of the migration.

Analyze every:

* `Thread`
* `Runnable`
* `Callable`
* `Executor`
* `ExecutorService`
* `ScheduledExecutorService`
* thread pool
* synchronization block
* lock
* concurrent collection
* queue
* future
* asynchronous task
* scheduler
* worker
* networking thread
* packet-processing thread

Compare them against the proven Java 25 implementation used by the 4.8 emulator.

Determine where Java 25 provides a better implementation.

## Virtual Threads

Evaluate Java 25 virtual threads carefully.

Do NOT mechanically replace every platform thread with a virtual thread.

Determine which workloads are suitable for:

* virtual threads
* platform threads
* bounded executor pools
* scheduled executors
* event-driven processing

Pay special attention to:

* blocking I/O
* database operations
* network operations
* packet processing
* task scheduling
* long-running game loops
* CPU-bound AI
* pathfinding
* world updates
* persistence
* timers

Virtual threads must be introduced only where they provide a real architectural/performance advantage and do not violate game-server timing or concurrency guarantees.

---

# SYNCHRONIZATION

Audit all:

```java
synchronized
wait()
notify()
notifyAll()
```

and all explicit locking.

Evaluate whether Java 25 alternatives provide safer or more scalable implementations:

* `ReentrantLock`
* `ReadWriteLock`
* `StampedLock`
* atomic classes
* concurrent collections
* structured concurrency where appropriate
* immutable state
* lock-free approaches where appropriate

Do not remove synchronization simply because it looks old.

First determine the invariant it protects.

**Never introduce race conditions while modernizing concurrency.**

---

# COLLECTIONS AND DATA STRUCTURES

Audit:

* `Vector`
* `Hashtable`
* legacy synchronized collections
* unnecessary `CopyOnWriteArrayList`
* unnecessary concurrent collections
* repeated defensive copies
* inefficient iteration
* unnecessary boxing
* excessive allocations
* inefficient maps/sets/lists

Use the 4.8 Java 25 emulator as a reference for proven collection patterns.

Do not change collection semantics without verifying behavior.

---

# STREAMS / LAMBDAS

Review old Java 8 Stream/Lambda usage.

Do not assume every Stream should remain a Stream.

For performance-critical game-server code, compare:

* loops
* streams
* parallel streams
* collectors
* direct collection operations

Avoid `parallelStream()` unless it is demonstrably appropriate.

The objective is **predictable server performance**, not fashionable syntax.

---

# I/O AND NETWORKING

Audit all Java I/O and networking code.

Look for Java 8-era implementations that can be improved using modern Java APIs.

Review:

* NIO
* buffers
* channels
* sockets
* file operations
* serialization
* resource management
* blocking operations
* asynchronous operations

Preserve packet timing and protocol behavior.

---

# DATABASE

Audit the complete database layer.

Review:

* JDBC usage
* connection management
* prepared statements
* result sets
* transactions
* connection pools
* resource closing
* synchronization
* blocking operations
* thread usage
* database executors

Modernize where appropriate without changing SQL semantics or game behavior.

---

# DEPENDENCIES AND LIBRARIES

Compare the Classic 5.0 Maven dependencies against the 4.8 Java 25 emulator.

For each dependency:

1. Determine whether it is still necessary.
2. Determine whether it supports Java 25.
3. Determine whether a newer compatible version exists.
4. Determine whether the 4.8 emulator already uses a better alternative.
5. Check API compatibility.
6. Check behavioral differences.
7. Upgrade only when safe.

Do not blindly copy every 4.8 dependency because the 5.0 emulator may have different requirements.

---

# MAVEN

Modernize the Maven configuration properly.

The final build must explicitly target Java 25.

However:

**DO NOT consider changing the Maven compiler configuration sufficient.**

The source code itself must be modernized.

Verify:

* Maven compiler configuration
* plugins
* dependency versions
* annotation processors
* test configuration
* packaging
* profiles
* runtime configuration
* JVM arguments
* module/build structure

Use the 4.8 emulator as the primary reference for its proven Java 25 Maven configuration.

---

# GC / JIT / JVM PERFORMANCE

Analyze the Java 25 runtime configuration of the 4.8 emulator.

Identify:

* GC strategy
* heap configuration
* JVM flags
* JIT-related configuration
* startup configuration
* memory settings
* diagnostics
* monitoring
* garbage-generation hotspots

Apply only settings appropriate to the Classic 5.0 workload.

Do not blindly copy JVM flags.

Java 25's modern JVM should be allowed to optimize naturally wherever explicit tuning is unnecessary.

---

# PERFORMANCE AUDIT

During migration, identify:

* excessive object allocation
* unnecessary synchronization
* thread contention
* lock contention
* excessive context switching
* inefficient collections
* repeated database calls
* unnecessary packet allocations
* unnecessary copying
* expensive logging
* blocking operations on inappropriate threads
* memory leaks
* excessive GC pressure
* inefficient scheduling
* CPU hotspots

The final Java 25 implementation should be **better than the original Java 8 implementation**, not merely equivalent.

---

# CRITICAL RULE: PRESERVE GAME BEHAVIOR

Do NOT change:

* packet protocols
* opcodes
* packet layouts
* network semantics
* game mechanics
* quest behavior
* skill behavior
* combat calculations
* player state transitions
* NPC behavior
* map behavior
* persistence semantics
* client compatibility

unless a change is explicitly required by the Java 25 migration or fixes a confirmed technical bug.

If a modernization could alter behavior, stop and analyze it before proceeding.

---

# COMPILATION REQUIREMENT

After EVERY significant migration phase:

```bash
mvn clean compile
```

or the appropriate project Maven build command.

For major milestones:

```bash
mvn clean package
```

The build MUST pass before proceeding.

Never accumulate dozens of unverified transformations.

If compilation fails:

1. Stop.
2. Diagnose the root cause.
3. Fix it.
4. Recompile.
5. Continue only after success.

---

# VALIDATION REQUIREMENTS

Do not rely exclusively on compilation.

After the migration, perform:

### Static validation

Search for remaining Java 8-era patterns and obsolete APIs.

Use tools such as:

* `jdeprscan`
* compiler warnings
* Maven dependency analysis
* static analysis
* Python scanners
* IDE/compiler diagnostics
* source-code searches

Create a final report identifying every remaining legacy construct and explaining why it was intentionally retained.

### Runtime validation

Verify that the emulator can:

* start correctly
* initialize all modules
* connect to the database
* start networking
* accept client connections
* authenticate
* enter the game
* load the world
* create/load players
* move players
* execute core services
* process packets
* execute scheduled tasks
* execute combat/game logic
* persist data
* shut down cleanly

The Java 25 migration must not introduce regressions.

---

# REFERENCE-DRIVEN MODERNIZATION

For every major Java 8 pattern discovered in the Classic 5.0 emulator:

1. Locate the equivalent concept in the Java 25 4.8 emulator.
2. Understand why the 4.8 implementation was designed that way.
3. Determine whether the same modernization applies to Classic 5.0.
4. Adapt it to the 5.0 architecture.
5. Preserve 5.0-specific behavior.
6. Compile.
7. Validate.
8. Document the migration.

Do not simply copy code.

**Understand → adapt → validate.**

---

# DO NOT TAKE SHORTCUTS

The following are explicitly prohibited:

* Updating only `pom.xml`
* Changing only `source/target`
* Replacing `java.version` and declaring success
* Blind global search-and-replace
* Blind regex rewriting of Java
* Replacing all threads with virtual threads
* Replacing all collections without analysis
* Introducing parallel streams indiscriminately
* Removing synchronization without proving safety
* Copying 4.8 game logic into 5.0
* Breaking existing 5.0 behavior
* Ignoring compiler warnings
* Ignoring deprecated APIs
* Leaving obvious Java 8 legacy simply because Java 25 can compile it
* Performing a huge unvalidated rewrite

---

# FINAL ZERO-LEGACY AUDIT

At the end, perform a complete repository-wide audit.

Search for:

* Java 8-only APIs
* obsolete APIs
* deprecated APIs
* legacy thread patterns
* obsolete synchronization patterns
* unnecessary legacy collections
* unnecessary manual resource handling
* obsolete utility implementations
* redundant compatibility code
* old dependency versions
* Java 8-specific workarounds
* unnecessary compatibility layers
* Java 8 compiler assumptions
* obsolete Maven configuration
* old JVM flags
* unnecessary custom implementations replaced by modern JDK functionality

Classify every finding:

```text
[MIGRATED]
[INTENTIONALLY RETAINED]
[NOT APPLICABLE]
[REQUIRES FUTURE WORK]
```

There must be a technical reason for every intentionally retained legacy construct.

---

# FINAL DELIVERABLES

When everything is complete, produce:

## 1. Migration Plan

Update:

`D:\AION CLASSIC 5.0 - EMULADOR\5 - PLANOS\JAVA25_MIGRATION_AION_CLASSIC_5.0.md`

Mark every step as completed.

## 2. Migration Report

Create a detailed Markdown report containing:

* Initial Java 8 state
* Final Java 25 state
* Number of classes modified
* Number of files modified
* Dependencies upgraded
* APIs modernized
* Concurrency changes
* Virtual-thread decisions
* GC/JIT changes
* Maven changes
* Performance improvements
* Deprecated APIs removed
* Legacy Java 8 patterns removed
* Intentionally retained patterns
* Compilation results
* Runtime validation results
* Any remaining limitations

## 3. Final Java 25 Certification

The final report must explicitly answer:

```text
Is the entire emulator actually migrated to Java 25?
YES / NO

Is the source code still fundamentally written using Java 8-era patterns?
YES / NO

Does Maven build successfully using JDK 25?
YES / NO

Was the emulator behavior preserved?
YES / NO

Were concurrency changes validated?
YES / NO

Were virtual threads introduced only where appropriate?
YES / NO

Was the Java 25 reference emulator used as the modernization benchmark?
YES / NO

Are there remaining Java 8 legacy constructs?
YES / NO
```

If any answer is `NO`, explain exactly why.

---

# FINAL SUCCESS CRITERIA

The migration is considered complete ONLY when:

1. The entire Classic 5.0 emulator runs on JDK 25.
2. Maven builds successfully with JDK 25.
3. The source code has been genuinely modernized.
4. Java 8-era implementations have been systematically reviewed.
5. Java 25 APIs/features are used where technically beneficial.
6. Concurrency has been modernized safely.
7. Virtual threads are used where appropriate, not indiscriminately.
8. GC/JIT/runtime configuration has been reviewed.
9. Dependencies are Java 25-compatible and modernized where appropriate.
10. No unnecessary Java 8 compatibility layer remains.
11. The Classic 5.0 protocol and game behavior remain intact.
12. The emulator remains operational.
13. Every migration phase has been compiled and validated.
14. The complete migration plan is documented in `.md`.
15. The final repository passes a comprehensive Java 8 legacy audit.
16. The resulting architecture should approach the **quality, cleanliness, modularity, performance, and Java 25 engineering standards demonstrated by the 4.8 reference emulator**, while remaining functionally correct for Classic 5.0.

## EXECUTION ORDER

Start now.

**Do not ask for confirmation for every step.**

First inspect both projects, create the complete Markdown migration plan, establish the rollback/checkpoint strategy, and then execute the plan sequentially.

Work methodically.

Use Python for intelligent bulk analysis and safe repetitive transformations.

Compile continuously.

Validate continuously.

Fix problems immediately.

Do not declare completion until the entire migration has been audited and validated.

ONLY COMMIT AND PUSH AFTER MIGRATE 100% IS COMPLETED (no warns, no errors during chat-server, login-server and game-server inicialization, need init the emulador to confirm, not only compile with maven)

**The goal is not "Java 8 code that compiles on Java 25."**

The goal is:

> **A genuinely modern, production-grade, fully Java 25 Aion Classic 5.0 emulator, using the proven Java 25 4.8 emulator as its technical benchmark without compromising Classic 5.0 functionality.**
