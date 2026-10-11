"use strict";
const $ = (s, r = document) => r.querySelector(s);
const esc = (v) => String(v ?? "").replace(/[&<>"]/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" })[c]);
const store = {
  get: (k, d) => { try { return localStorage.getItem(k) || d; } catch { return d; } },
  set: (k, v) => { try { localStorage.setItem(k, v); } catch { /* private window */ } },
};
const S = { mode: store.get("mode", "online"), tab: store.get("tab", "negotiate"), runs: [], runId: null, meta: null,
            events: [], cfg: {}, cases: null, error: "", supplier: null, filter: "all", timer: null, open: new Set(), drawn: "" };

// tabs that show the running negotiation redraw as it progresses; the others (team, suppliers, settings) must not:
// redrawing would refetch from the arena and wipe what is being typed
const LIVE = new Set(["negotiate", "raw", "formatted"]);

async function api(path, opts, method = "POST") {
  const r = await fetch(path, opts && { method, headers: { "Content-Type": "application/json" }, body: JSON.stringify(opts) });
  const body = await r.json().catch(() => ({}));
  if (!r.ok) throw new Error(body.detail || `HTTP ${r.status}`);
  return body;
}

// ---- small renderers -------------------------------------------------------------------------
const chip = (text, cls = "") => `<span class="chip ${esc(cls || text)}">${esc(text)}</span>`;
const eur = (v) => (typeof v === "number" ? v.toLocaleString("en", { maximumFractionDigits: 2 }) : v);
const when = (t) => new Date(t * 1000).toLocaleString([], { month: "short", day: "numeric", hour: "2-digit", minute: "2-digit" });
function hl(value) {
  return esc(JSON.stringify(value, null, 2)).replace(/(&quot;(?:\\.|[^&\\]|&(?!quot;))*&quot;)(\s*:)?|\b(true|false|null)\b|-?\d+\.?\d*(?:[eE][+-]?\d+)?/g,
    (m, str, colon, lit) => str ? `<span class="${colon ? "k" : "s"}">${str}</span>${colon || ""}` : lit ? `<span class="b">${m}</span>` : `<span class="n">${m}</span>`);
}
const json = (v) => `<pre>${hl(v)}</pre>`;
function sheet(s) {
  const t = s.terms || s;
  return `<div class="sheet">${s.term_sheet_id ? `<b>${esc(s.term_sheet_id)}</b>` : ""}${Object.entries(t).map(([k, v]) =>
    `<span><b>${esc(k)}</b> ${esc(typeof v === "object" ? JSON.stringify(v) : eur(v))}</span>`).join("")}</div>`;
}
function table(rows, { wrap = [] } = {}) {
  if (!rows || (Array.isArray(rows) && !rows.length)) return `<p class="muted">Nothing recorded.</p>`;
  rows = Array.isArray(rows) ? rows : [rows];
  const cols = [...new Set(rows.flatMap(Object.keys))];
  return `<div class="scroll" tabindex="0"><table><thead><tr>${cols.map((c) => `<th>${esc(c)}</th>`).join("")}</tr></thead><tbody>${
    rows.map((r) => `<tr>${cols.map((c) => `<td class="${wrap.includes(c) ? "wrap" : ""}">${esc(r[c] ?? "")}</td>`).join("")}</tr>`).join("")}</tbody></table></div>`;
}
const kv = (o) => `<div class="scroll" tabindex="0"><table><tbody>${Object.entries(o || {}).filter(([, v]) => v !== null && v !== "").map(([k, v]) =>
  `<tr><th>${esc(k)}</th><td>${esc(v)}</td></tr>`).join("")}</tbody></table></div>`;

// ---- shell -----------------------------------------------------------------------------------
function paintChrome() {
  document.querySelectorAll("#mode button").forEach((b) => b.setAttribute("aria-pressed", b.dataset.mode === S.mode));
  document.querySelectorAll("#tabs button").forEach((b) => b.setAttribute("aria-selected", b.dataset.tab === S.tab));
  $("#stale").hidden = !S.cfg?.stale_code;
  const sel = $("#runs");
  sel.innerHTML = S.runs.length ? S.runs.map((r) => `<option value="${esc(r.run_id)}" ${r.run_id === S.runId ? "selected" : ""}>${
    esc(`${when(r.started)} · ${r.mode} · ${r.case_id.replace("case:", "")} · ${r.status === "done" ? (r.deal ? `score ${(r.score ?? 0).toFixed(2)}` : "no deal") : r.status}`)}</option>`).join("")
    : `<option>No sessions yet</option>`;
}
function render() {
  paintChrome();
  if (S.tab !== "raw") delete $("#view").dataset.raw;
  ({ negotiate: viewNegotiate, raw: viewRaw, formatted: viewFormatted, suppliers: viewSuppliers, team: viewTeam, settings: viewSettings })[S.tab]();
}
const setTab = (t) => { S.tab = t; store.set("tab", t); render(); };

// ---- runs ------------------------------------------------------------------------------------
async function loadRuns() {
  S.runs = await api("/api/runs");
  if (!S.runId && S.runs.length) await openRun(S.runs[0].run_id);
  else paintChrome();
}
async function openRun(id) {
  clearTimeout(S.timer);
  S.runId = id; S.events = []; S.meta = null;
  await pull();
  render();
}
async function pull() {
  if (!S.runId) return;
  const r = await api(`/api/runs/${S.runId}?after=${S.events.length}`);
  S.events.push(...r.events); S.meta = r.meta;
  const i = S.runs.findIndex((x) => x.run_id === S.runId);
  if (i >= 0) S.runs[i] = r.meta;
  clearTimeout(S.timer);
  if (["starting", "running"].includes(r.meta.status)) {
    S.timer = setTimeout(async () => { await pull().catch(() => {}); if (LIVE.has(S.tab)) render(); else paintChrome(); }, 1500);
  }
}

// ---- negotiate -------------------------------------------------------------------------------
async function viewNegotiate() {
  const v = $("#view");
  const m = S.meta;
  v.innerHTML = `<div id="live"></div><h2>Pick a case</h2><div id="cases"><p class="muted">Loading…</p></div>`;
  paintLive();
  if (!S.cfg.llm_configured) $("#cases").insertAdjacentHTML("beforebegin", `<p class="err">No model configured: set LLM_MODEL and LLM_API_KEY in .env and restart.</p>`);
  const key = S.mode;
  if (!S.cases || S.cases.mode !== key) {
    try { S.cases = { mode: key, ...(await api(`/api/cases?mode=${key}`)) }; S.error = ""; }
    catch (e) { S.cases = null; S.error = e.message; }
  }
  if (S.tab !== "negotiate" || S.mode !== key) return;
  const box = $("#cases");
  if (S.error) { box.innerHTML = `<p class="err">${esc(S.error)}</p>`; return; }
  const me = S.cases.me, busy = m && ["starting", "running"].includes(m.status);
  const best = me?.best || {};
  box.innerHTML = (me ? `<p class="muted">${esc(me.team_name)} · ${me.practice.left} of ${me.practice.limit} practice sessions left today. Each run uses one.</p>`
    : `<p class="muted">Built-in scripted supplier: no key, no quota, not the real suppliers.</p>`) +
    `<div class="grid">${S.cases.cases.map((c) => `<div class="card"><div><b>${esc(c.title)}</b></div>
      <div class="muted">${chip(c.type.replace("_", " "))} ${esc(c.case_id)} · up to ${c.round_limit} rounds</div>
      <div class="sups">${c.suppliers.map((s) => `<button class="btn ghost" data-sup="${esc(s.id)}" title="Inspect all data on this supplier">${esc(s.name)} ›</button>`).join("")}</div>
      ${best[c.case_id] !== undefined ? `<div class="muted">Best score so far ${best[c.case_id].toFixed(2)}</div>` : ""}
      <button class="btn" data-case="${esc(c.case_id)}" ${busy || !S.cfg.llm_configured ? "disabled" : ""}>Haggle</button></div>`).join("")}</div>`;
  box.querySelectorAll("[data-sup]").forEach((b) => b.onclick = () => { S.supplier = b.dataset.sup; setTab("suppliers"); });
  box.querySelectorAll("[data-case]").forEach((b) => b.onclick = async () => {
    b.disabled = true;
    try {
      const meta = await api("/api/runs", { mode: S.mode, case_id: b.dataset.case });
      S.runs.unshift(meta); S.cases = null;
      await openRun(meta.run_id);
    } catch (e) { S.error = e.message; render(); }
  });
}
function paintLive() {
  const m = S.meta, box = $("#live");
  if (!box) return;
  if (!m) { box.innerHTML = `<p class="muted">Choose a case below. The agent reads the supplier's file, then haggles for as many rounds as the case allows.</p>`; return; }
  const sent = S.events.filter((e) => e.kind === "http" && e.method === "POST" && /\/messages$/.test(e.path) && !e.request?.message?.action).length;
  const prices = S.events.filter((e) => e.kind === "decision" && e.action === "send").map((e) => e.message.term_sheets[0].terms.unit_price);
  const r = m.result;
  box.innerHTML = `<div class="card"><div>${chip(m.status)} <b>${esc(m.title || m.case_id)}</b></div>
    <div class="muted">${esc(m.mode)} · ${esc(m.model)} · ${(m.suppliers || []).map((s) => esc(s.name)).join(", ")} · ${sent} e-mails sent${m.round_limit ? ` (limit ${m.round_limit} per supplier)` : ""}</div>
    ${prices.length ? `<div class="path">Our asks: ${prices.map(eur).join(" → ")}</div>` : ""}
    ${m.error ? `<div class="err">${esc(m.error)}</div>` : ""}
    ${r ? `<div>${r.deal ? `Deal with ${esc(r.supplier_id)} at €${eur(r.terms?.unit_price)} · C €${eur(r.c_deal)} vs opening €${eur(r.c_open)} · score <b>${(r.score ?? 0).toFixed(2)}</b>` : `No deal (${esc(r.end_reason || "ended")})`}</div>` : ""}
    <div class="tools" style="margin:8px 0 0"><button class="btn ghost" data-go="formatted">Read the negotiation</button><button class="btn ghost" data-go="raw">Raw JSON</button></div></div>`;
  box.querySelectorAll("[data-go]").forEach((b) => b.onclick = () => setTab(b.dataset.go));
}

// ---- raw JSON --------------------------------------------------------------------------------
function summary(e) {
  if (e.kind === "http") return `<span>${esc(e.method)} ${esc(e.path)}</span> ${chip(e.status, e.status < 400 ? "ok" : "bad")} <span class="muted">${e.ms} ms</span>`;
  if (e.kind === "llm") return `${chip("model", "model")} <span>${esc(e.supplier)}</span> ${e.error ? chip("failed", "bad") : ""} <span class="muted">${e.ms} ms</span>`;
  if (e.kind === "decision") return `${chip("decision", "ok")} <span>${esc(e.supplier)} · round ${esc(e.round ?? "close")} · ${esc(e.action)}</span>`;
  return `${chip(e.kind, "bad")} <span class="err">${esc(e.error || "")}</span>`;
}
function viewRaw() {
  const v = $("#view");
  if (!S.meta) { v.innerHTML = `<p class="muted">Run a negotiation first.</p>`; return; }
  const stamp = `${S.runId}|${S.filter}|${S.events.length}`;
  if (v.dataset.raw === stamp) return;  // nothing new: leave the rows the reader has open alone
  v.dataset.raw = stamp;
  const shown = S.events.filter((e) => S.filter === "all" || (S.filter === "arena" ? e.kind === "http" : e.kind !== "http"));
  v.innerHTML = `<div class="tools"><div class="seg" id="filter">${["all", "arena", "agent"].map((f) => `<button data-f="${f}" aria-pressed="${S.filter === f}">${f === "arena" ? "Arena API" : f === "agent" ? "Model & decisions" : "All"}</button>`).join("")}</div>
    <button class="btn ghost" id="copy">Copy all</button><button class="btn ghost" id="dl">Download</button><span class="muted">${shown.length} of ${S.events.length} events. Keys and headers are never recorded.</span></div>
    ${shown.map((e) => `<details class="row" data-i="${e.i}" ${S.open.has(e.i) ? "open" : ""}><summary><span class="num">#${e.i}</span>${summary(e)}</summary><div class="body"></div></details>`).join("")}`;
  v.querySelectorAll("#filter button").forEach((b) => b.onclick = () => { S.filter = b.dataset.f; viewRaw(); });
  const draw = (d) => {
    if (d.dataset.done) return;
    d.dataset.done = 1;  // the payload is only drawn once it is opened: model requests are large
    const e = S.events[+d.dataset.i], { i, at, kind, ...rest } = e;
    const [req, res] = e.kind === "http" || e.kind === "llm" ? [e.request, e.response] : [null, null];
    const other = Object.fromEntries(Object.entries(rest).filter(([k]) => !["request", "response"].includes(k)));
    d.lastElementChild.innerHTML = (req !== null || res !== null ? `<h3>Request</h3>${json(req)}<h3>Response</h3>${json(res)}` : "") +
      (Object.keys(other).length && e.kind !== "http" ? `<h3>${req !== null ? "Details" : "Event"}</h3>${json(other)}` : "");
  };
  v.querySelectorAll("details.row").forEach((d) => {
    if (d.open) draw(d);
    d.addEventListener("toggle", () => { d.open ? S.open.add(+d.dataset.i) : S.open.delete(+d.dataset.i); if (d.open) draw(d); });
  });
  const all = () => JSON.stringify({ meta: S.meta, events: S.events }, null, 2);
  $("#copy").onclick = () => navigator.clipboard?.writeText(all());
  $("#dl").onclick = () => { const a = document.createElement("a"); a.href = URL.createObjectURL(new Blob([all()], { type: "application/json" })); a.download = `${S.runId}.json`; a.click(); };
}

// ---- formatted -------------------------------------------------------------------------------
function claimChips(results, ids) {
  return (results || []).map((c) => chip(`argument ${c.index + 1}: ${c.result}`, c.result)).join(" ");
}
function viewFormatted() {
  const v = $("#view");
  if (!S.meta) { v.innerHTML = `<p class="muted">Run a negotiation first.</p>`; return; }
  const m = S.meta, ev = S.events;
  const open = ev.find((e) => e.kind === "http" && e.method === "POST" && e.path === "/v1/sessions");
  const first = ev.find((e) => e.kind === "llm");
  const used = ev.find((e) => e.kind === "prompt");  // recorded at the start of the run (older runs: none)
  const sys = used?.text || (first && (first.request.system || first.request.messages?.find((x) => x.role === "system")?.content));
  const ctx = first && first.request.messages?.find((x) => x.role === "user")?.content;
  const bySup = {};
  const col = (s) => bySup[s] ??= { rounds: [], open: open?.response?.threads?.[s]?.[0] };
  const pending = {};
  ev.forEach((e) => {
    if (e.kind === "decision" && e.supplier) pending[e.supplier] = e;
    if (e.kind === "http" && e.method === "POST" && /\/threads\/[^/]+\/messages$/.test(e.path)) {
      const s = e.path.split("/threads/")[1].split("/")[0], msg = e.request?.message || {};
      col(s).rounds.push({ dec: pending[s], msg, res: e.response, status: e.status });
      delete pending[s];
    }
  });
  const last = ev.filter((e) => e.kind === "http" && e.method === "GET" && /^\/v1\/sessions\/[^/]+$/.test(e.path)).pop();
  const end = last?.response?.status === "ended" ? last.response : null;
  const names = Object.fromEntries((m.suppliers || []).map((s) => [s.id, s.name]));
  v.innerHTML = `<div class="card">${chip(m.status)} <b>${esc(m.title || m.case_id)}</b> <span class="muted">${esc(m.mode)} · ${esc(m.session_id || "")}</span>
    ${m.result ? `<div>${m.result.deal ? `Deal with <b>${esc(names[m.result.supplier_id] || m.result.supplier_id)}</b> · C €${eur(m.result.c_deal)} (opening €${eur(m.result.c_open)}, best possible €${eur(m.result.c_best)}) · score <b>${(m.result.score ?? 0).toFixed(2)}</b>` : `No deal (${esc(m.result.end_reason || "ended")})`}</div>` : ""}
    ${m.error ? `<div class="err">${esc(m.error)}</div>` : ""}</div>
    ${first || used ? `<details class="card"><summary><b>The agent</b> · system prompt and supplier context this run used</summary><h3>System prompt of this run</h3><p class="muted">${used ? `${esc(used.source)} · ${esc(used.sha)}${S.cfg?.prompt_sha ? (S.cfg?.prompt_sha === used.sha ? " · same as the current prompt in Settings" : " · differs from the current prompt in Settings") : ""}` : "taken from the run's first model call (recorded before prompt versions were kept)"}</p><pre>${esc(sys || "(sent as a separate system field)")}</pre><h3>Supplier context injected</h3><pre>${esc(ctx || "")}</pre></details>` : ""}
    ${Object.entries(bySup).map(([s, c]) => {
      const path = [c.open?.term_sheets?.[0]?.terms?.unit_price, ...c.rounds.map((r) => r.res?.term_sheets?.[0]?.terms?.unit_price)].filter((x) => x !== undefined);
      return `<h2>${esc(names[s] || s)} <span class="muted">${esc(s)}</span></h2>${path.length ? `<p class="path">Their standing price: ${path.map(eur).join(" → ")}</p>` : ""}
      ${c.open ? mail(c.open, "Opening quote", false) : ""}
      ${c.rounds.map((r, n) => buyer(r, n + 1) + (r.res && !r.res.result ? mail(r.res, `Reply ${n + 1}`, true) : "")).join("")}`;
    }).join("")}
    ${(ev.filter((e) => e.kind === "error").map((e) => `<p class="err">${esc(e.supplier || "")} ${esc(e.error)}</p>`)).join("")}
    ${end ? outcome(end, m) : ""}`;
}
function mail(msg, label, withClaims) {
  return `<div class="card them"><div>${chip(msg.status || "open")} <b>${esc(label)}</b> <span class="muted">${esc(msg.from || "")}${msg.signals ? ` · replies in ${msg.signals.reply_delay_days} d` : ""}</span></div>
    <div class="muted">${esc(msg.subject || "")}</div><div class="mail">${esc(msg.body || "")}</div>
    ${(msg.term_sheets || []).map(sheet).join("")}
    ${withClaims ? `<div>${claimChips(msg.claim_results)}</div>` : ""}
    ${(msg.attachments || []).map((a) => chip(`📎 ${a.name}`)).join(" ")}
    ${msg.missing_fields?.length ? `<div class="muted">Left out (closes on their standard terms): ${esc(msg.missing_fields.join(", "))}</div>` : ""}</div>`;
}
function buyer(r, n) {
  const d = r.dec, m = r.msg;
  if (m.action) return `<div class="card me"><b>We ${esc(m.action.type.replace("_", " "))}</b></div>`;
  return `<div class="card me"><div>${chip("us", "ok")} <b>Round ${n}</b> ${d?.fallback ? chip("fallback", "warn") : ""} ${d?.attempts > 1 ? chip(`${d.attempts} model attempts`, "warn") : ""}
    ${d?.claims?.length ? chip(`${d.claims.length} verified claim${d.claims.length > 1 ? "s" : ""}`, "ok") : ""}</div>
    <div class="muted">${esc(m.subject || "")}</div><div class="mail">${esc(m.body || "")}</div>
    ${(m.term_sheets || []).map((t, i) => sheet(t) + (d?.sheet_costs ? `<div class="muted" style="margin:-2px 0 4px">C €${eur(d.sheet_costs[i])}</div>` : "")).join("")}
    ${d?.rationale ? `<div class="why">Why: ${esc(d.rationale)}</div>` : ""}
    ${d?.fallback ? `<div class="err">Model problem: ${esc(d.fallback)}</div>` : ""}
    ${r.status >= 400 ? `<div class="err">The arena refused this message (HTTP ${r.status}).</div>` : ""}</div>`;
}
function outcome(end, m) {
  const res = end.result || {}, trace = end.trace || [];
  return `<h2>Result</h2><div class="card">${m.result?.deal ? kv({ supplier: res.supplier_id, ...res.terms, "C deal": res.c_deal, "C open": res.c_open, "C best": res.c_best, score: res.score }) : `<p>No deal (${esc(end.end_reason)}).</p>`}
    ${res.cost_breakdown ? `<h3>Where C comes from</h3>${kv(res.cost_breakdown)}` : ""}</div>
    ${trace.length ? `<h2>The supplier's reasons</h2>${trace.map((t) => `<div class="card them"><b>Round ${esc(t.round)}</b> <span class="muted">${esc(t.actor)}</span><ul>${(t.reasons || []).map((x) => `<li>${esc(x)}</li>`).join("")}</ul></div>`).join("")}` : ""}`;
}

// ---- suppliers -------------------------------------------------------------------------------
async function viewSuppliers() {
  const v = $("#view");
  const list = await api("/api/suppliers");
  const known = new Map(list.map((x) => [x.id, x]));
  for (const c of S.cases?.cases || []) for (const sp of c.suppliers) if (!known.has(sp.id)) known.set(sp.id, { ...sp, runs: [] });
  if (S.supplier && !known.has(S.supplier)) known.set(S.supplier, { id: S.supplier, name: S.supplier, runs: [] });
  const all = [...known.values()];
  if (!all.length) { v.innerHTML = `<p class="muted">Pick a case on the Negotiate tab to see its suppliers.</p>`; return; }
  const cur = S.meta?.suppliers?.map((s) => s.id) || [];
  const rank = (x) => (cur.includes(x.id) ? 2 : x.runs.length ? 1 : 0);
  all.sort((a, b) => rank(b) - rank(a) || a.name.localeCompare(b.name));
  S.supplier = known.has(S.supplier) ? S.supplier : all[0].id;
  const s = known.get(S.supplier);
  v.innerHTML = `<div class="tools"><label class="muted">Supplier <select id="sup">${all.map((x) => `<option value="${esc(x.id)}" ${x.id === S.supplier ? "selected" : ""}>${esc(x.name)}${cur.includes(x.id) ? " (current)" : ""}</option>`).join("")}</select></label></div>
    <h2 style="margin-top:0">Sessions</h2>${s.runs.length ? "" : `<p class="muted">No session with this supplier yet.</p>`}${s.runs.length ? table(s.runs.map((r) => ({ when: when(r.started), arena: r.mode, case: r.case_id, outcome: r.status === "done" ? (r.deal ? `deal, score ${(r.score ?? 0).toFixed(2)}` : "no deal") : r.status }))) : ""}
    <div id="dos"><p class="muted">Loading the supplier file…</p></div>`;
  $("#sup").onchange = (e) => { S.supplier = e.target.value; viewSuppliers(); };
  try { paintDossier(await api(`/api/suppliers/${encodeURIComponent(S.supplier)}`)); }
  catch (e) { $("#dos").innerHTML = `<p class="err">${esc(e.message)}</p>`; }
}
function paintDossier(d) {
  const sec = (title, body) => `<details class="card" open><summary><b>${title}</b></summary>${body}</details>`;
  const m = d.master || {}, i = d.intel || {};
  $("#dos").innerHTML = `<h2>${esc(m.name)}</h2><p class="muted">${esc([m.country, m.category, m.incoterm, m.payment_days && `${m.payment_days} days net`, m.abc_class && `class ${m.abc_class}`].filter(Boolean).join(" · "))}</p>` +
    sec("Company", kv({ owner: i.owner_type, parent: i.group_parent, founded: i.founded, staff: i.staff, turnover: i.turnover_band, "equity ratio %": i.equity_ratio_pct, "credit index": `${i.credit_index} (12 months ago ${i.credit_index_12m_ago})`, "VDA 6.3": i.vda63_grade, certifications: i.certifications })) +
    sec("Delivery and quality by quarter", table(d.scorecards)) + sec("Quality notifications", table(d.quality)) +
    sec("News", table(d.news, { wrap: ["body"] })) + sec("Past negotiations", table(d.history, { wrap: ["note"] })) +
    sec("Prices we paid", table(d.prices)) + sec("Quotes", table(d.quotes, { wrap: ["remarks"] })) + sec("Our should-cost estimate", table(d.should_cost)) +
    sec("Part and cost drivers", table(d.parts) + table(d.cost_drivers)) +
    sec("Contracts", table(d.contracts) + table(d.clauses, { wrap: ["text"] })) +
    sec("Sourcing and spend", table(d.sourcing) + table(d.spend) + kv(d.orders)) +
    sec("Letters, e-mails and notes", table(d.documents.map(({ file, ...r }) => r), { wrap: ["subject"] }) +
      d.documents.filter((x) => x.file).map((x) => `<details data-path="${esc(x.file)}"><summary>${esc(x.date)} · ${esc(x.kind)} · ${esc(x.subject)}</summary><pre>…</pre></details>`).join(""));
  document.querySelectorAll("#dos details[data-path]").forEach((det) => det.addEventListener("toggle", async () => {
    if (!det.open || det.dataset.done) return;
    det.dataset.done = 1;
    try { det.querySelector("pre").textContent = (await api(`/api/document?path=${encodeURIComponent(det.dataset.path)}`)).text; }
    catch (e) { det.querySelector("pre").textContent = e.message; }
  }));
}

// ---- team ------------------------------------------------------------------------------------
const ago = (t) => new Date(t * 1000).toLocaleString([], { month: "short", day: "numeric", hour: "2-digit", minute: "2-digit" });
// Best score per case, the session that set it and its rounds (what the board's "rounds" adds up), plus the
// hosted cases not played yet, which count 0.
function bestRows(best, sessions, board) {
  const rows = Object.entries(best).map(([k, x]) => {
    const s = (Array.isArray(sessions) ? sessions : []).find((r) => r.case_id === k && Math.abs((r.score ?? -1) - x) < 1e-9);
    return { case: k.replace("case:", ""), best: x.toFixed(2), "rounds (all threads)": s?.rounds ?? "", session: s?.session_id ?? "" };
  });
  const total = rows.reduce((n, r) => n + (Number(r["rounds (all threads)"]) || 0), 0);
  const missing = (S.cases?.cases || []).map((c) => c.case_id).filter((id) => !(id in best));
  return [...rows, ...missing.map((id) => ({ case: id.replace("case:", ""), best: "not played (counts 0)", "rounds (all threads)": "", session: "" })),
    { case: "total", best: "", "rounds (all threads)": total, session: "" }];
}
async function viewTeam() {
  const v = $("#view");
  v.innerHTML = `<p class="muted">Asking the arena…</p>`;
  let t;
  try { t = await api(`/api/team?mode=${S.mode}`); } catch (e) { v.innerHTML = `<p class="err">${esc(e.message)}</p>`; return; }
  if (S.tab !== "team") return;
  const part = (title, x, ok) => `<h2>${title}</h2>${x?.error ? `<p class="err">${esc(x.error)}</p>` : ok(x)}`;
  const me = t.me?.error ? null : t.me;
  const rec = t.recorded || {};
  const sessions = (rows) => (rows?.length ? table(rows.map((r) => ({ when: ago(r.created_at), case: r.case_id, status: r.status,
    "end reason": r.end_reason, deal: r.deal ? "yes" : "no", score: r.score == null ? "" : r.score.toFixed(2), rounds: r.rounds,
    session: r.session_id, "recorded here": rec[r.session_id] ? "yes" : "" }))) : `<p class="muted">None yet.</p>`);
  v.innerHTML = `<p class="muted">What the ${esc(S.mode)} arena's API says about us, read now. Scores here are the arena's own.</p>
    ${part("Team and quota", t.me, (m) => `<div class="card">${kv({ team: m.team_name, status: m.status,
      "practice sessions used": `${m.practice?.used} of ${m.practice?.limit} (${m.practice?.left} left)`, "next one frees up": m.practice?.resets_at })}
      <h3>Best score per case</h3>${m.best && Object.keys(m.best).length ? table(bestRows(m.best, t.sessions, t.leaderboard)) : `<p class="muted">No scored session yet.</p>`}
      <p class="muted">The board counts every hosted case: a case we have not played scores 0 in the mean. Its "rounds" column adds up the messages of our best session per case, across all supplier threads (an RFQ with three suppliers counts the messages to each), so it can be far above the number of rounds of any one negotiation. Rounds only break exact ties.</p></div>`)}
    <h2>Per case vs. the other teams</h2><div id="compare"><p class="muted">Asking the arena for every team's cases…</p></div>
    ${part("Practice leaderboard", t.leaderboard, (b) => table((b.teams || b.rows || []).map((r) => ({ rank: r.rank, team: r.team_name,
      total: r.total, played: r.played, deals: r.deals, rounds: r.rounds, "": r.team_name === me?.team_name ? "← us" : "" }))))}
    ${part("Our practice sessions", t.sessions, sessions)}${part("Our sandbox sessions", t.sandbox_sessions, sessions)}
    ${part("Data downloads", t.downloads, (d) => kv(Object.fromEntries(Object.entries(d).map(([k, x]) => [k, JSON.stringify(x)]))))}
    ${part("Arena health", t.health, (h) => kv(h))}`;
  viewCompare(me?.team_name);
}
// Every team's score per final case, one row per case: who won it, where we stand and how far behind the best we are.
// The arena only publishes per-team case results for the final (/v1/results), so before the first wave this is empty.
async function viewCompare(us) {
  let c;
  try { c = await api(`/api/compare?mode=${S.mode}`); } catch (e) { c = { error: e.message }; }
  const box = $("#compare");
  if (S.tab !== "team" || !box) return;
  if (c.error) { box.innerHTML = `<p class="err">${esc(c.error)}</p>`; return; }
  us = c.me || us;
  if (!c.cases.length) { box.innerHTML = `<p class="muted">No case results yet: the arena publishes every team's result per case only for the final, once its first wave has started.</p>`; return; }
  const teams = [...c.teams].sort((a, b) => (a.rank ?? 1e9) - (b.rank ?? 1e9));
  const pts = (x) => (typeof x?.score === "number" ? x.score * 100 : null);
  const cell = (x, best, mine) => {
    if (!x) return `<td class="muted">–</td>`;
    const p = pts(x);
    const label = p == null ? x.status || "" : p.toFixed(1);
    const title = [x.status, x.end_reason, x.rounds != null ? `${x.rounds} rounds` : "", x.saved_eur != null ? `€${eur(x.saved_eur)} saved` : ""].filter(Boolean).join(" · ");
    return `<td class="${p != null && p === best ? "top" : ""} ${mine ? "us" : ""}" title="${esc(title)}">${esc(label)}</td>`;
  };
  const rows = c.cases.map((r) => {
    const scores = teams.map((t) => pts(r.teams[t.team_name])).filter((p) => p != null);
    const best = scores.length ? Math.max(...scores) : null;
    const ours = pts(r.teams[us]);
    const rank = ours == null ? "" : 1 + scores.filter((p) => p > ours).length;
    return `<tr><th title="${esc(r.title || "")}">${esc(r.case_id.replace("case:", ""))}<br><small class="muted">W${esc(r.wave)} · ${esc(r.type || "")}</small></th>
      <td>${rank ? `${rank} / ${scores.length}` : "–"}</td><td>${ours == null || best == null ? "–" : (ours - best).toFixed(1)}</td>
      ${teams.map((t) => cell(r.teams[t.team_name], best, t.team_name === us)).join("")}</tr>`;
  }).join("");
  box.innerHTML = `<p class="muted">Final cases, score × 100 per team (hover a cell for status, rounds and € saved). Bold green: best on that case; highlighted column: us.</p>
    <div class="scroll" tabindex="0"><table class="compare"><thead><tr><th>case</th><th>our rank</th><th>vs. best</th>${
      teams.map((t) => `<th class="${t.team_name === us ? "us" : ""}">${esc(t.team_name)}<br><small class="muted">#${esc(t.rank ?? "")} · ${esc(t.total ?? "")}</small></th>`).join("")}</tr></thead><tbody>${rows}</tbody></table></div>`;
}

// ---- settings --------------------------------------------------------------------------------
async function viewSettings() {
  const v = $("#view");
  let c;
  try { c = await api("/api/settings"); } catch (e) { v.innerHTML = `<p class="err">${esc(e.message)}</p>`; return; }
  if (S.tab !== "settings") return;
  const f = (id, label, val, type = "text", hint = "") => `<label class="field"><span>${label}</span><input id="${id}" type="${type}" value="${esc(val)}" ${type === "password" ? 'autocomplete="off"' : ""}><small class="muted">${hint}</small></label>`;
  v.innerHTML = `<h2 style="margin-top:0">Model</h2><div class="card form">
      <label class="field"><span>Provider</span><select id="provider"><option value="openai" ${c.provider === "openai" ? "selected" : ""}>OpenAI-compatible</option><option value="anthropic" ${c.provider === "anthropic" ? "selected" : ""}>Anthropic</option></select><small class="muted">Any OpenAI-compatible endpoint, or Anthropic.</small></label>
      ${f("model", "Model", c.model)}${f("base_url", "Base URL", c.base_url, "text", "OpenAI-compatible only")}${f("endpoint", "Endpoint", c.endpoint, "text", "appended to the base URL")}
      ${f("timeout", "Timeout (s) per call", c.timeout, "number", "The arena allows 60 s per reply: slower answers become a plain fallback counter.")}
      ${f("api_key", "API key", "", "password", c.has_key ? "A key is set. Leave empty to keep it; it is never shown again." : "No key set yet. Stored only in haggle_settings.json (git-ignored).")}
      <div class="tools"><button class="btn" id="save">Save</button><button class="btn ghost" id="test">Test the model</button><span id="msg" class="muted"></span></div></div>
    <h2>System prompt</h2><div class="card form">
      ${c.stale_code ? `<p class="stale">This server started before the code on disk changed: the prompt below may not be the one a fresh server runs. Restart <code>arena-haggle</code>.</p>` : ""}
      <p class="muted">The prompt a new run uses. Source: <b>${esc(c.prompt_source)}</b> · ${esc(c.prompt_sha)}${c.prompt_is_default ? " · the built-in default" : ""}. It must keep the JSON answer format with <code>"offers"</code> and the [[cN]] claim markers or the agent cannot act on it (a prompt without them is not saved). Every run records the prompt hash and the full text.</p>
      ${f("prompt_file", "Prompt file", c.prompt_file, "text", "Saved here (tracked in git, so versions are shared). Delete or reset to use the built-in prompt.")}
      <textarea id="prompt" rows="22" spellcheck="false" aria-label="Running system prompt">${esc(c.prompt)}</textarea>
      ${c.ignored_prompt ? `<details class="stale"><summary>${esc(c.prompt_file)} is ignored: it lacks the "offers" answer format (the model no longer sets prices)</summary><pre>${esc(c.ignored_prompt)}</pre></details>` : ""}
      <div class="tools"><button class="btn" id="saveprompt">Save prompt</button><button class="btn ghost" id="reset">Reset to built-in</button></div></div>`;
  const val = (id) => $("#" + id).value;
  const note = (t) => { $("#msg").textContent = t; };
  const model = () => ({ provider: val("provider"), model: val("model"), base_url: val("base_url"), endpoint: val("endpoint"), timeout: val("timeout"), api_key: val("api_key"), prompt_file: val("prompt_file") });
  const run = async (body, done) => { try { await api("/api/settings", body, "PUT"); note(done); S.cfg = await api("/api/config"); await viewSettings(); $("#msg").textContent = done; } catch (e) { note(e.message); $("#msg").scrollIntoView({ block: "center" }); } };
  $("#save").onclick = () => run(model(), "Saved.");
  $("#saveprompt").onclick = () => run({ ...model(), prompt: val("prompt") }, "Prompt saved.");
  $("#reset").onclick = () => run({ ...model(), reset_prompt: true }, "Back to the built-in prompt.");
  $("#test").onclick = async () => { note("Calling the model…"); try { const r = await api("/api/settings/test", {}); note(r.ok ? `Works: "${r.detail}"` : `Failed: ${r.detail}`); } catch (e) { note(e.message); } };
}

// ---- boot ------------------------------------------------------------------------------------
document.querySelectorAll("#mode button").forEach((b) => b.onclick = () => { S.mode = b.dataset.mode; store.set("mode", S.mode); S.cases = null; S.error = ""; render(); });
document.querySelectorAll("#tabs button").forEach((b) => b.onclick = () => setTab(b.dataset.tab));
$("#runs").onchange = (e) => openRun(e.target.value);
(async () => {
  try { S.cfg = await api("/api/config"); await loadRuns(); } catch (e) { S.error = e.message; }
  render();
})();
