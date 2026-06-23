const state = {
  plans: [],
  activePlan: null,
  filter: "",
};

const els = {
  list: document.querySelector("#plan-list"),
  search: document.querySelector("#plan-search"),
  sourceMeta: document.querySelector("#source-meta"),
  title: document.querySelector("#active-title"),
  refresh: document.querySelector("#refresh-button"),
  copyLink: document.querySelector("#copy-link-button"),
  status: document.querySelector("#document-status"),
  document: document.querySelector("#document"),
  outline: document.querySelector("#outline-list"),
  headingCount: document.querySelector("#heading-count"),
  codeCount: document.querySelector("#code-count"),
};

function escapeHtml(value) {
  return value
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

function inlineMarkup(value) {
  const escaped = escapeHtml(value);
  return escaped
    .replace(/`([^`]+)`/g, "<code>$1</code>")
    .replace(/\*\*([^*]+)\*\*/g, "<strong>$1</strong>")
    .replace(/\*([^*]+)\*/g, "<em>$1</em>")
    .replace(
      /\[([^\]]+)\]\(([^)]+)\)/g,
      '<a href="$2" target="_blank" rel="noreferrer">$1</a>',
    );
}

function slugify(value) {
  return value
    .toLowerCase()
    .replace(/[^a-z0-9\s-]/g, "")
    .trim()
    .replace(/\s+/g, "-")
    .slice(0, 80);
}

function formatSize(bytes) {
  if (bytes < 1024) return `${bytes} B`;
  return `${(bytes / 1024).toFixed(1)} KB`;
}

function showStatus(message, kind = "neutral") {
  els.status.textContent = message;
  els.status.classList.remove("is-hidden");
  els.status.dataset.kind = kind;
}

function hideStatus() {
  els.status.classList.add("is-hidden");
}

async function fetchJson(url) {
  const response = await fetch(url, { cache: "no-store" });
  if (!response.ok) {
    throw new Error(`${response.status} ${response.statusText}`);
  }
  return response.json();
}

async function loadPlans() {
  showStatus("Loading local plan files.");
  const payload = await fetchJson("/api/plans");
  state.plans = payload.plans;
  els.sourceMeta.textContent = payload.plans_dir;
  renderPlanList();
  if (state.plans.length === 0) {
    els.title.textContent = "No plans found";
    els.document.innerHTML = "";
    els.outline.innerHTML = "";
    showStatus("No .md or .mdx files were found in the served plan directory.", "empty");
    return;
  }
  const urlPlan = new URLSearchParams(window.location.search).get("plan");
  const initial =
    state.plans.find((plan) => plan.name === urlPlan) ?? state.plans[0];
  await selectPlan(initial.name, false);
}

function renderPlanList() {
  const filtered = state.plans.filter((plan) =>
    plan.name.toLowerCase().includes(state.filter.toLowerCase()),
  );
  els.list.innerHTML = "";
  for (const plan of filtered) {
    const button = document.createElement("button");
    button.type = "button";
    button.className = "plan-button";
    if (state.activePlan?.name === plan.name) button.classList.add("is-active");
    button.innerHTML = `<strong>${escapeHtml(plan.name)}</strong><span>${formatSize(
      plan.size,
    )}</span>`;
    button.addEventListener("click", () => selectPlan(plan.name));
    els.list.append(button);
  }
}

async function selectPlan(name, updateUrl = true) {
  const payload = await fetchJson(`/api/plans/${encodeURIComponent(name)}`);
  state.activePlan = payload;
  els.title.textContent = payload.name;
  if (updateUrl) {
    const url = new URL(window.location.href);
    url.searchParams.set("plan", payload.name);
    window.history.replaceState({}, "", url);
  }
  renderPlanList();
  renderDocument(payload.content);
}

function renderDocument(markdown) {
  const blocks = tokenize(markdown);
  const outline = [];
  let codeCount = 0;
  const html = blocks
    .map((block) => {
      if (block.type === "heading") {
        const id = slugify(block.text);
        outline.push({ id, level: block.level, text: block.text });
        return `<h${block.level} id="${id}">${inlineMarkup(block.text)}</h${block.level}>`;
      }
      if (block.type === "paragraph") {
        return `<p>${inlineMarkup(block.text)}</p>`;
      }
      if (block.type === "list") {
        const tag = block.ordered ? "ol" : "ul";
        const items = block.items
          .map((item) => `<li>${inlineMarkup(item)}</li>`)
          .join("");
        return `<${tag}>${items}</${tag}>`;
      }
      if (block.type === "table") {
        return renderTable(block.rows);
      }
      if (block.type === "code") {
        codeCount += 1;
        return `<pre><code>${escapeHtml(block.text)}</code></pre>`;
      }
      if (block.type === "quote") {
        return `<blockquote>${inlineMarkup(block.text)}</blockquote>`;
      }
      return "";
    })
    .join("\n");

  els.document.innerHTML = html;
  els.headingCount.textContent = String(outline.length);
  els.codeCount.textContent = String(codeCount);
  renderOutline(outline);
  hideStatus();
}

function tokenize(markdown) {
  const lines = markdown.replace(/\r\n/g, "\n").split("\n");
  const blocks = [];
  let i = 0;
  while (i < lines.length) {
    const line = lines[i];
    if (!line.trim()) {
      i += 1;
      continue;
    }
    if (line.startsWith("```")) {
      const code = [];
      i += 1;
      while (i < lines.length && !lines[i].startsWith("```")) {
        code.push(lines[i]);
        i += 1;
      }
      i += 1;
      blocks.push({ type: "code", text: code.join("\n") });
      continue;
    }
    const heading = line.match(/^(#{1,4})\s+(.+)$/);
    if (heading) {
      blocks.push({
        type: "heading",
        level: heading[1].length,
        text: heading[2].trim(),
      });
      i += 1;
      continue;
    }
    if (line.startsWith(">")) {
      const quote = [];
      while (i < lines.length && lines[i].startsWith(">")) {
        quote.push(lines[i].replace(/^>\s?/, ""));
        i += 1;
      }
      blocks.push({ type: "quote", text: quote.join(" ") });
      continue;
    }
    if (isTableStart(lines, i)) {
      const rows = [];
      while (i < lines.length && /^\|.*\|$/.test(lines[i].trim())) {
        rows.push(lines[i]);
        i += 1;
      }
      blocks.push({ type: "table", rows });
      continue;
    }
    const listMatch = line.match(/^(\s*)([-*]|\d+\.)\s+(.+)$/);
    if (listMatch) {
      const ordered = /\d+\./.test(listMatch[2]);
      const items = [];
      while (i < lines.length) {
        const item = lines[i].match(/^(\s*)([-*]|\d+\.)\s+(.+)$/);
        if (!item) break;
        items.push(item[3].trim());
        i += 1;
      }
      blocks.push({ type: "list", ordered, items });
      continue;
    }
    const paragraph = [line.trim()];
    i += 1;
    while (
      i < lines.length &&
      lines[i].trim() &&
      !lines[i].startsWith("```") &&
      !lines[i].match(/^(#{1,4})\s+(.+)$/) &&
      !lines[i].match(/^(\s*)([-*]|\d+\.)\s+(.+)$/) &&
      !isTableStart(lines, i)
    ) {
      paragraph.push(lines[i].trim());
      i += 1;
    }
    blocks.push({ type: "paragraph", text: paragraph.join(" ") });
  }
  return blocks;
}

function isTableStart(lines, index) {
  return (
    index + 1 < lines.length &&
    /^\|.*\|$/.test(lines[index].trim()) &&
    /^\|[\s:-|]+\|$/.test(lines[index + 1].trim())
  );
}

function renderTable(rows) {
  const parsed = rows
    .filter((row, index) => index !== 1)
    .map((row) =>
      row
        .trim()
        .slice(1, -1)
        .split("|")
        .map((cell) => cell.trim()),
    );
  const [head = [], ...body] = parsed;
  const header = head.map((cell) => `<th>${inlineMarkup(cell)}</th>`).join("");
  const bodyRows = body
    .map(
      (row) =>
        `<tr>${row.map((cell) => `<td>${inlineMarkup(cell)}</td>`).join("")}</tr>`,
    )
    .join("");
  return `<table><thead><tr>${header}</tr></thead><tbody>${bodyRows}</tbody></table>`;
}

function renderOutline(outline) {
  els.outline.innerHTML = "";
  if (outline.length === 0) {
    const item = document.createElement("li");
    item.textContent = "No headings in this plan.";
    els.outline.append(item);
    return;
  }
  for (const heading of outline) {
    const item = document.createElement("li");
    const link = document.createElement("a");
    link.href = `#${heading.id}`;
    link.className = `depth-${heading.level}`;
    link.textContent = heading.text;
    item.append(link);
    els.outline.append(item);
  }
}

els.search.addEventListener("input", (event) => {
  state.filter = event.target.value;
  renderPlanList();
});

els.refresh.addEventListener("click", () => {
  loadPlans().catch((error) => showStatus(`Unable to refresh plans: ${error.message}`, "error"));
});

els.copyLink.addEventListener("click", async () => {
  await navigator.clipboard.writeText(window.location.href);
  els.copyLink.textContent = "Copied";
  window.setTimeout(() => {
    els.copyLink.textContent = "Copy Link";
  }, 1400);
});

loadPlans().catch((error) => {
  els.title.textContent = "Plan viewer error";
  showStatus(`Unable to load plans: ${error.message}`, "error");
});
