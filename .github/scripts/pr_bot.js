// @ts-check
"use strict";

const { execFileSync } = require("child_process");
const fs = require("fs");
const path = require("path");

const STICKY_MARKER = "<!-- aion-pr-bot-review -->";
const DEFAULT_AI_MODEL = "openai/gpt-4o-mini";

/** @type {Record<string, { color: string, description: string }>} */
const LABEL_DEFINITIONS = {
  "documentation": { color: "0075ca", description: "Melhorias ou adições de documentação" },
  "docs-only": { color: "10b981", description: "Via rápida: alteração exclusiva de documentação" },
  "area/gameforge": { color: "3b82f6", description: "Núcleo GameServer 1 (GameForge GSID 1)" },
  "area/login-server": { color: "6366f1", description: "Servidor de autenticação (LoginServer)" },
  "area/chat-server": { color: "8b5cf6", description: "Servidor de chat (ChatServer)" },
  "area/commons": { color: "0284c7", description: "Núcleo compartilhado (commons)" },
  "area/version-dll": { color: "f97316", description: "Hook nativo do cliente (version.dll / C++)" },
  "area/blender-plugins": { color: "ea580c", description: "Plugins oficiais do Blender" },
  "area/geo-nav": { color: "14b8a6", description: "Gerador Geo and Nav Builder" },
  "area/tools": { color: "64748b", description: "Ferramentas, documentos auxiliares e cliente" },
  "area/ci": { color: "0f172a", description: "Workflows, templates e automação GitHub" },
  "kind/bug": { color: "d73a4a", description: "Correção de bug ou regressão" },
  "kind/feature": { color: "0ea5e9", description: "Nova funcionalidade ou melhoria PvE/l10n" },
  "kind/perf": { color: "22c55e", description: "Otimização de desempenho" },
  "kind/security": { color: "b91c1c", description: "Correção ou hardening de segurança" },
  "kind/refactor": { color: "a855f7", description: "Refatoração ou estilo de código" },
  "kind/deps": { color: "0369a1", description: "Atualização de dependências" },
  "size/XS": { color: "dcfce7", description: "Alteração muito pequena (<= 20 linhas)" },
  "size/S": { color: "bbf7d0", description: "Alteração pequena (<= 100 linhas)" },
  "size/M": { color: "fef08a", description: "Alteração média (<= 400 linhas)" },
  "size/L": { color: "fed7aa", description: "Alteração grande (<= 1000 linhas)" },
  "size/XL": { color: "fecaca", description: "Alteração muito grande (> 1000 linhas)" },
  "bot/approved": { color: "16a34a", description: "Validado e aprovado automaticamente pelo bot" },
  "bot/needs-attention": { color: "dc2626", description: "Requer ajustes apontados pelo bot de revisão" },
  "dependencies": { color: "0369a1", description: "Pull requests de dependências" },
  "backend-java": { color: "b45309", description: "Código Java Maven do emulador" },
  "ci/cd": { color: "475569", description: "Automação de CI/CD" },
};

const BOT_MANAGED_PREFIXES = ["area/", "kind/", "size/", "bot/"];
const BOT_MANAGED_EXACT = new Set(["docs-only", "documentation"]);

function isBotManagedLabel(name) {
  return BOT_MANAGED_EXACT.has(name) || BOT_MANAGED_PREFIXES.some((p) => name.startsWith(p));
}

async function resolveTargetPullRequest(github, owner, repo, workflowRun) {
  const headSha = workflowRun.head_sha;
  const listedHints = Array.isArray(workflowRun.pull_requests) ? workflowRun.pull_requests : [];
  for (const hint of listedHints) {
    if (!hint || !hint.number) continue;
    const { data: pr } = await github.rest.pulls.get({ owner, repo, pull_number: hint.number });
    if (pr && pr.state === "open" && pr.head.sha === headSha) {
      return pr;
    }
  }

  const prs = await github.paginate(github.rest.pulls.list, {
    owner,
    repo,
    state: "open",
    sort: "updated",
    direction: "desc",
    per_page: 50,
  });
  return prs.find((p) => p.head && p.head.sha === headSha) || null;
}

async function loadAnalysisReport(github, owner, repo, workflowRun, core, reportPath) {
  if (reportPath && fs.existsSync(reportPath)) {
    return { report: JSON.parse(fs.readFileSync(reportPath, "utf8")), waitingForChecks: false };
  }

  const headSha = workflowRun.head_sha;
  let checksRun = null;
  if (workflowRun.name === "PR Automated Review & Checks") {
    checksRun = workflowRun;
  } else {
    const { data } = await github.rest.actions.listWorkflowRunsForRepo({
      owner,
      repo,
      head_sha: headSha,
      event: "pull_request",
      per_page: 25,
    });
    const matching = (data.workflow_runs || [])
      .filter((r) => r.name === "PR Automated Review & Checks")
      .sort((a, b) => (b.run_number || 0) - (a.run_number || 0));

    if (matching.length === 0) {
      return { report: null, waitingForChecks: true };
    }
    const latest = matching[0];
    if (latest.status !== "completed") {
      core.info(`Run "${latest.name}" ainda em andamento (${latest.status}) para ${headSha}.`);
      return { report: null, waitingForChecks: true };
    }
    checksRun = latest;
  }

  const { data: arts } = await github.rest.actions.listWorkflowRunArtifacts({
    owner,
    repo,
    run_id: checksRun.id,
  });
  const art = (arts.artifacts || []).find((a) => a.name === "pr-review-report" && !a.expired);
  if (!art) {
    core.warning(`Artefato pr-review-report não encontrado no run ${checksRun.id}.`);
    return { report: null, waitingForChecks: false };
  }

  const dl = await github.rest.actions.downloadArtifact({
    owner,
    repo,
    artifact_id: art.id,
    archive_format: "zip",
  });
  const tmpZip = path.join(process.env.RUNNER_TEMP || "/tmp", `pr-report-${checksRun.id}.zip`);
  fs.writeFileSync(tmpZip, Buffer.from(dl.data));
  const jsonText = execFileSync("unzip", ["-p", tmpZip, "pr-review-report.json"], {
    encoding: "utf8",
    maxBuffer: 10 * 1024 * 1024,
  });
  return { report: JSON.parse(jsonText), waitingForChecks: false };
}

async function ensureLabelsExist(github, owner, repo, labelNames, core) {
  const existing = await github.paginate(github.rest.issues.listLabelsForRepo, {
    owner,
    repo,
    per_page: 100,
  });
  const existingLower = new Set(existing.map((l) => l.name.toLowerCase()));

  for (const name of labelNames) {
    if (existingLower.has(name.toLowerCase())) continue;
    const def = LABEL_DEFINITIONS[name] || {
      color: "64748b",
      description: `Label automática (${name})`,
    };
    try {
      await github.rest.issues.createLabel({
        owner,
        repo,
        name,
        color: def.color,
        description: def.description,
      });
      existingLower.add(name.toLowerCase());
    } catch (err) {
      if (err && err.status === 422) {
        existingLower.add(name.toLowerCase());
      } else {
        core.info(`Não foi possível criar label "${name}": ${err.message}`);
      }
    }
  }
}

async function evaluateCheckRuns(github, owner, repo, headSha, report) {
  const { data } = await github.rest.checks.listForRef({
    owner,
    repo,
    ref: headSha,
    per_page: 100,
  });
  const runs = data.check_runs || [];

  const findLatest = (name) =>
    runs.filter((r) => r.name === name).sort((a, b) => (b.id || 0) - (a.id || 0))[0] || null;

  const commitLintRun = findLatest("Validar Titulo do PR / Commit");
  const javaCiRun = findLatest("Build e Pacote GameForge GSID 1 (Java 25 LTS)");
  const reviewChecksRun = findLatest("Revisão Automática e Qualidade do PR");

  const failing = [];
  const pending = [];

  for (const r of [reviewChecksRun, commitLintRun, javaCiRun]) {
    if (!r) continue;
    if (r.name === "Build e Pacote GameForge GSID 1 (Java 25 LTS)" && !report.needs_java_build) {
      if (r.status === "completed" && r.conclusion === "failure") {
        failing.push(r.name);
      }
      continue;
    }
    if (r.status !== "completed") {
      pending.push(r.name);
    } else if (!["success", "neutral", "skipped"].includes(r.conclusion)) {
      failing.push(`${r.name} (${r.conclusion})`);
    }
  }

  if (report.needs_java_build && !javaCiRun) {
    pending.push("Build e Pacote GameForge GSID 1 (Java 25 LTS)");
  }

  return { commitLintRun, javaCiRun, reviewChecksRun, failing, pending };
}

async function fetchAdvisoryAiSummary(github, owner, repo, prNumber, report, core) {
  const token = process.env.GITHUB_TOKEN;
  if (!token || report.is_bot) return "";
  if ((report.stats?.total_changes || 0) > 1500) return "";

  try {
    const { data: diffText } = await github.rest.pulls.get({
      owner,
      repo,
      pull_number: prNumber,
      mediaType: { format: "diff" },
    });
    const rawDiff = typeof diffText === "string" ? diffText : String(diffText || "");
    if (!rawDiff.trim()) return "";
    const truncated = rawDiff.slice(0, 18000);

    const controller = new AbortController();
    const timer = setTimeout(() => controller.abort(), 20000);
    try {
      const resp = await fetch("https://models.github.ai/inference/chat/completions", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        signal: controller.signal,
        body: JSON.stringify({
          model: DEFAULT_AI_MODEL,
          temperature: 0.2,
          max_tokens: 450,
          messages: [
            {
              role: "system",
              content:
                "Você é o revisor técnico do emulador Aion Classic 5.0 (Lost Academy Group). " +
                "Responda em Português (PT-BR) em até 4 bullets objetivos, analisando apenas o diff fornecido: " +
                "1) resumo da mudança, 2) possíveis bugs/riscos (se houver), 3) clareza/qualidade. Nunca invente erros.",
            },
            {
              role: "user",
              content: `Título: ${report.title}\nModo: ${report.is_docs_only ? "Docs-Only" : "Código/Geral"}\n\nDiff:\n${truncated}`,
            },
          ],
        }),
      });
      if (!resp.ok) {
        core.info(`GitHub Models indisponível (${resp.status}) — seguindo com revisão determinística.`);
        return "";
      }
      const payload = await resp.json();
      return (payload?.choices?.[0]?.message?.content || "").trim();
    } finally {
      clearTimeout(timer);
    }
  } catch (err) {
    core.info(`Revisão IA opcional ignorada: ${err.message}`);
    return "";
  }
}

function buildStickyBody({
  pr,
  report,
  decision,
  appliedLabels,
  checkState,
  titleRenamedTo,
  aiSummary,
  approvePermissionNote,
}) {
  const modeText = report.is_docs_only
    ? "Fast-Track Documentação (`.md` / docs)"
    : report.needs_java_build
    ? "Validação Completa (Backend Java 25 + Qualidade)"
    : "Validação Proporcional (Ferramentas / Scripts / Plugins)";

  let badge = "⏳ **Aguardando verificações**";
  if (decision === "APPROVE") badge = "✅ **PR Validado e Aprovado pelo Bot**";
  else if (decision === "CHANGES_REQUESTED") badge = "⚠️ **Ajustes Necessários Antes do Merge**";
  else if (decision === "DRAFT") badge = "📝 **Rascunho (Draft) — Aguardando Ready for Review**";

  const statusEmoji = (run, skipReason) => {
    if (skipReason) return `⏭️ Dispensado (${skipReason})`;
    if (!run) return "⏳ Pendente";
    if (run.status !== "completed") return `⏳ Em andamento (${run.status})`;
    if (run.conclusion === "success") return "✅ Passou";
    if (run.conclusion === "skipped" || run.conclusion === "neutral") return `⏭️ ${run.conclusion}`;
    return `❌ ${run.conclusion}`;
  };

  const lines = [
    STICKY_MARKER,
    `### 🤖 Bot Revisor — Aion Classic 5.0`,
    "",
    `${badge}`,
    "",
    `- **Modo:** ${modeText}`,
    `- **Arquivos / Linhas:** \`${report.stats.files_changed}\` arquivo(s) (\`+${report.stats.additions}\` / \`-${report.stats.deletions}\`)`,
    `- **Labels aplicadas:** ${appliedLabels.map((l) => `\`${l}\``).join(", ")}`,
  ];

  if (titleRenamedTo) {
    lines.push(`- **Título padronizado automaticamente:** \`${titleRenamedTo}\``);
  }

  lines.push(
    "",
    "| Verificação | Status |",
    "| :--- | :--- |",
    `| Revisão Automática (Sintaxe, Segredos e Escopo) | ${report.passed ? "✅ Passou" : "❌ Falhou"} |`,
    `| Título Semantico / Fast-Track | ${statusEmoji(checkState.commitLintRun)} |`,
    `| Build & Testes Backend Java 25 | ${statusEmoji(checkState.javaCiRun, report.needs_java_build ? "" : "sem alterações em Java")} |`
  );

  if (report.blocking_issues && report.blocking_issues.length > 0) {
    lines.push("", "#### ❌ Pontos Bloqueantes Encontrados");
    for (const issue of report.blocking_issues) {
      lines.push(`- \`${issue.file}:${issue.line || 1}\` (\`${issue.rule}\`): ${issue.message}`);
    }
  }

  if (checkState.failing && checkState.failing.length > 0) {
    lines.push("", "#### ❌ Workflows / Checks com Falha");
    for (const f of checkState.failing) {
      lines.push(`- ${f}`);
    }
  }

  if (report.warnings && report.warnings.length > 0) {
    lines.push("", "#### 💡 Avisos Não-Bloqueantes");
    for (const w of report.warnings.slice(0, 10)) {
      lines.push(`- \`${w.file}:${w.line || 1}\`: ${w.message}`);
    }
  }

  if (report.autofix_candidates && report.autofix_candidates.length > 0) {
    lines.push("", "#### 🛠️ Auto-Correção Disponível (`/autofix`)");
    if (pr.head?.repo?.fork) {
      lines.push(
        `Detectamos pequenos ajustes de formatação/EOF em ${report.autofix_candidates.map((f) => `\`${f}\``).join(", ")} ` +
          "(em PRs de fork externo o bot não tem permissão para gravar no seu branch; opcional e não bloqueante)."
      );
    } else {
      lines.push(
        `Comente \`/autofix\` neste PR para corrigir automaticamente espaços/EOF/CRLF em: ${report.autofix_candidates.map((f) => `\`${f}\``).join(", ")}.`
      );
    }
  }

  if (aiSummary) {
    lines.push("", "#### 🧠 Análise Consultiva (IA)", "", aiSummary);
  }

  if (approvePermissionNote) {
    lines.push("", `> [!NOTE]\n> ${approvePermissionNote}`);
  }

  lines.push("", `<sub>Commit analisado: \`${pr.head.sha.slice(0, 8)}\`</sub>`);
  return lines.join("\n");
}

async function upsertStickyComment(github, owner, repo, prNumber, body) {
  const comments = await github.paginate(github.rest.issues.listComments, {
    owner,
    repo,
    issue_number: prNumber,
    per_page: 100,
  });
  const existing = comments.find((c) => typeof c.body === "string" && c.body.includes(STICKY_MARKER));
  if (existing) {
    await github.rest.issues.updateComment({
      owner,
      repo,
      comment_id: existing.id,
      body,
    });
  } else {
    await github.rest.issues.createComment({
      owner,
      repo,
      issue_number: prNumber,
      body,
    });
  }
}

async function run({ github, context, core, reportPath = "" }) {
  const owner = context.repo.owner;
  const repo = context.repo.repo;
  const workflowRun = context.payload.workflow_run;
  if (!workflowRun) {
    core.info("Payload sem workflow_run; encerrando sem ação.");
    return;
  }
  if (workflowRun.event !== "pull_request") {
    core.info(`Evento "${workflowRun.event}" não é pull_request; ignorando.`);
    return;
  }

  const pr = await resolveTargetPullRequest(github, owner, repo, workflowRun);
  if (!pr) {
    core.info(`Nenhum PR aberto encontrado com head_sha=${workflowRun.head_sha}; encerrando.`);
    return;
  }

  const { report, waitingForChecks } = await loadAnalysisReport(github, owner, repo, workflowRun, core, reportPath);
  if (!report) {
    if (waitingForChecks) {
      core.info("Aguardando conclusão de PR Automated Review & Checks antes de comentar.");
    }
    return;
  }

  // Padroniza título de PR docs-only quando vier direto da UI web do GitHub (ex.: "Update README.md")
  let titleRenamedTo = "";
  if (report.is_docs_only && report.suggested_title && pr.title !== report.suggested_title) {
    try {
      await github.rest.pulls.update({
        owner,
        repo,
        pull_number: pr.number,
        title: report.suggested_title,
      });
      titleRenamedTo = report.suggested_title;
      report.title = report.suggested_title;
    } catch (err) {
      core.info(`Não foi possível atualizar título do PR #${pr.number}: ${err.message}`);
    }
  }

  const checkState = await evaluateCheckRuns(github, owner, repo, pr.head.sha, report);

  let decision = "APPROVE";
  if (!report.passed || checkState.failing.length > 0) {
    decision = "CHANGES_REQUESTED";
  } else if (checkState.pending.length > 0) {
    decision = "PENDING";
  } else if (pr.draft) {
    decision = "DRAFT";
  }

  const desiredManagedLabels = new Set(report.labels || []);
  if (decision === "APPROVE") {
    desiredManagedLabels.add("bot/approved");
  } else if (decision === "CHANGES_REQUESTED") {
    desiredManagedLabels.add("bot/needs-attention");
  }

  const currentLabels = (pr.labels || []).map((l) => l.name);
  const manualLabels = currentLabels.filter((name) => !isBotManagedLabel(name));
  const finalLabels = Array.from(new Set([...manualLabels, ...desiredManagedLabels]));

  await ensureLabelsExist(github, owner, repo, Array.from(desiredManagedLabels), core);
  const sameLabels =
    finalLabels.length === currentLabels.length && finalLabels.every((l) => currentLabels.includes(l));
  if (!sameLabels) {
    await github.rest.issues.setLabels({
      owner,
      repo,
      issue_number: pr.number,
      labels: finalLabels,
    });
  }

  let aiSummary = "";
  if (decision === "APPROVE" || decision === "CHANGES_REQUESTED") {
    aiSummary = await fetchAdvisoryAiSummary(github, owner, repo, pr.number, report, core);
  }

  let approvePermissionNote = "";
  if (decision === "APPROVE" || decision === "CHANGES_REQUESTED") {
    const desiredReviewState = decision === "APPROVE" ? "APPROVED" : "CHANGES_REQUESTED";
    const { data: reviews } = await github.rest.pulls.listReviews({
      owner,
      repo,
      pull_number: pr.number,
      per_page: 100,
    });
    const ownForCommit = reviews.filter(
      (r) =>
        r.commit_id === pr.head.sha &&
        r.user &&
        (r.user.login === "github-actions[bot]" || r.user.type === "Bot") &&
        typeof r.body === "string" &&
        r.body.includes(STICKY_MARKER)
    );
    const latestOwn = ownForCommit[ownForCommit.length - 1];
    const alreadySubmitted = latestOwn && latestOwn.state === desiredReviewState;

    if (!alreadySubmitted) {
      const reviewBody =
        decision === "APPROVE"
          ? `${STICKY_MARKER}\nAprovado automaticamente: todas as verificações proporcionais passaram para o commit \`${pr.head.sha.slice(0, 8)}\`.`
          : `${STICKY_MARKER}\nRevisão automática solicitou ajustes antes do merge (ver detalhes no comentário do bot).`;
      try {
        await github.rest.pulls.createReview({
          owner,
          repo,
          pull_number: pr.number,
          commit_id: pr.head.sha,
          event: decision,
          body: reviewBody,
        });
      } catch (err) {
        if (err && err.status === 403) {
          approvePermissionNote =
            "Aprovação automática por Actions não está habilitada neste repositório. " +
            "Ative **Settings → Actions → General → Allow GitHub Actions to create and approve pull requests** para permitir o APPROVE oficial.";
          core.info(approvePermissionNote);
        } else {
          core.warning(`Falha ao enviar review automático (${err.status || "erro"}): ${err.message}`);
        }
      }
    }
  }

  const stickyBody = buildStickyBody({
    pr,
    report,
    decision,
    appliedLabels: finalLabels,
    checkState,
    titleRenamedTo,
    aiSummary,
    approvePermissionNote,
  });
  await upsertStickyComment(github, owner, repo, pr.number, stickyBody);
}

module.exports = { run, buildStickyBody, isBotManagedLabel };
