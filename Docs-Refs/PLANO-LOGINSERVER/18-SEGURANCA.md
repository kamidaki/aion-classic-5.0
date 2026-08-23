# 18 - SISTEMA DE SEGURANÇA E AUTO-CREATE ACCOUNTS

## OBJETIVO
Implementar mecanismos robustos de segurança no `login-server`, incluindo prevenção contra ataques de força bruta, rate limiting por IP, expiração de sessões, sanitização de payloads e criação automática de contas quando habilitada.

## PROBLEMA
Emuladores abertos na internet podem sofrer com flood de conexões maliciosas, ataques de brute force de senhas ou estouro de buffer através de pacotes forjados.

## CAUSA
Falta de validação de taxa de requisições e ausência de sanitização de inputs de strings nos sockets de rede.

## ANÁLISE
Medidas de Segurança Obrigatórias:
1. **Auto-Create Account**:
   * Quando `auto_create_accounts = true`, se o usuário informado no login não existir no banco de dados, o servidor cria automaticamente a conta com a senha fornecida (com hash seguro SHA-256 ou BCrypt).
   * O nome do usuário é sanitizado para aceitar apenas caracteres alfanuméricos e sublinhados (`[a-zA-Z0-9_]`), rejeitando injeções SQL ou caracteres de controle (`\0`, `\r`, `\n`).
2. **Rate Limiting & Anti-Brute-Force**:
   * Mapeamento de tentativas de login por IP em janela deslizante (ex: máximo de 10 tentativas por minuto).
   * Se um IP exceder o limite, o `login-server` bloqueia temporariamente novas tentativas daquele IP por 15 minutos (`temp_ban_minutes`).
   * Logs de alerta em nível `WARN` com o IP bloqueado, sem expor senhas ou dados sensíveis.
3. **Session Expiration**:
   * Chaves e tokens de sessão possuem TTL (Time-To-Live) de 10 minutos para serem consumidos no GameServer.
   * Sessões não consumidas são invalidadas e limpas periodicamente.
4. **Packet Size Protection**:
   * O `login-server` limita o tamanho máximo de qualquer pacote recebido a 64 KB, descartando imediatamente pacotes com tamanhos anômalos no cabeçalho.

## SOLUÇÃO
Criar o módulo `security` dentro do crate `login-server` com structs thread-safe `RateLimiter`, `IpBlocker` e `InputSanitizer`.

## ARQUIVOS ENVOLVIDOS
* `Emulador-Rust/login-server/src/security/mod.rs`
* `Emulador-Rust/login-server/src/security/rate_limit.rs`
* `Emulador-Rust/login-server/src/security/sanitizer.rs`
* `Emulador-Rust/login-server/src/account/mod.rs`

## IMPLEMENTAÇÃO
* Implementação do `RateLimiter` usando `dashmap` ou `parking_lot::Mutex<HashMap<IpAddr, AttemptHistory>>`.
* Validação de regex/alfanuméricos no `InputSanitizer`.
* Integração no loop de aceitação de conexões.

## TESTES
* Teste unitário de sanitização de nomes de usuário (strings com aspas, barras e nulos).
* Teste de bloqueio de IP após 10 tentativas com falha simuladas em sequência.
* Teste de auto-criação de conta com senha válida.

## VALIDAÇÃO
* Ataques de força bruta simulados são bloqueados imediatamente com código de erro amigável sem derrubar o servidor.

## RISCOS
* Bloquear jogadores em NAT compartilhada (múltiplos jogadores sob o mesmo IP público).
* Mitigação: O bloqueio é por tentativas consecutivas inválidas, não por acessos legítimos.

## DEPENDÊNCIAS
* `parking_lot`, `sha2`, `chrono`.

## TO-DO
- [x] Implementar `RateLimiter` por IP.
- [x] Implementar sanitizador de usernames e senhas.
- [x] Implementar auto-criação de contas com hash seguro.
- [x] Validar expiração de sessões na tabela SQLite.

## STATUS
[x] TESTADO
[x] VALIDADO
STATUS: CORRIGIDO E VALIDADO
