"use strict";
const $ = (id) => document.getElementById(id);
const RUPEE = "₹";
const money = (n) => RUPEE + Number(n).toLocaleString("en-IN", { minimumFractionDigits: 2, maximumFractionDigits: 2 });
const esc = (s) => String(s).replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
const todayISO = () => new Date().toISOString().slice(0, 10);
const round2 = (n) => Math.round(n * 100) / 100;

const S = { token: null, role: null, name: "", userId: null, connections: [], customers: [], bills: [], alerts: [], page: null, billFilter: "ALL",
  custType: "ALL", custQ: "", viewCustomerId: null, detailTab: "bills" };

/* ---------------- helpers ---------------- */
async function api(path, method = "GET", body) {
  const headers = { "Content-Type": "application/json" };
  if (S.token) headers.Authorization = "Bearer " + S.token;
  const r = await fetch("/api" + path, { method, headers, body: body ? JSON.stringify(body) : undefined });
  const data = await r.json().catch(() => ({}));
  if (!r.ok) {
    if (r.status === 401 && S.token) endSession();
    const d = data.detail;
    throw new Error(typeof d === "string" ? d
      : Array.isArray(d) ? d.map((e) => (e.loc ? e.loc[e.loc.length - 1] + ": " : "") + e.msg).join("; ") : "Request failed");
  }
  return data;
}

function toast(msg, kind = "") {
  const t = document.createElement("div");
  t.className = "toast " + kind;
  t.textContent = msg;
  $("toast").appendChild(t);
  setTimeout(() => t.remove(), 4000);
}

const lateFee = (b, on = todayISO()) => (b.status !== "PAID" && on > b.due_date ? round2(25 + b.total * 0.02) : 0);
const amountDue = (b) => round2(b.total + lateFee(b));
const status = (s) => `<span class="status s-${s}">${s[0] + s.slice(1).toLowerCase()}</span>`;
const emptyRow = (cols, text) => `<tr><td class="empty" colspan="${cols}">${text}</td></tr>`;
const connLabel = (id) => { const c = S.connections.find((x) => x.id === id); return c ? c.meter_no : "#" + id; };
const customerName = (id) => { const c = S.customers.find((x) => x.id === id); return c ? c.full_name : "#" + id; };
const connOwner = (id) => { const c = S.connections.find((x) => x.id === id); return c ? customerName(c.customer_id) : "-"; };

/* ---------------- sign in / create account ---------------- */
function showForm(which) {
  const login = which === "login";
  $("login-form").classList.toggle("hidden", !login);
  $("register-form").classList.toggle("hidden", login);
  ["auth-msg", "reg-msg"].forEach((id) => { $(id).textContent = ""; $(id).className = "form-msg"; });
  (login ? $("l-user") : $("r-name")).focus();
}
function setMsg(id, text, ok) { const e = $(id); e.textContent = text; e.className = "form-msg " + (ok ? "ok" : "err"); }

$("tab-register").onclick = () => showForm("register");
$("tab-login").onclick = () => showForm("login");

$("login-form").onsubmit = async (e) => {
  e.preventDefault();
  try {
    const d = await api("/auth/login", "POST", { username: $("l-user").value.trim(), password: $("l-pass").value });
    startSession(d.token, d.role, d.full_name, d.user_id);
  } catch (err) { setMsg("auth-msg", err.message, false); }
};

$("register-form").onsubmit = async (e) => {
  e.preventDefault();
  try {
    const d = await api("/auth/register", "POST", { username: $("r-user").value.trim(), password: $("r-pass").value, full_name: $("r-name").value.trim() });
    setMsg("reg-msg", "Account created. Your customer id is: " + d.id + ". You can sign in now.", true);
    $("l-user").value = d.username;
  } catch (err) { setMsg("reg-msg", err.message, false); }
};

function startSession(token, role, name, userId) {
  S.token = token; S.role = role; S.name = name; S.userId = userId;
  try { sessionStorage.setItem("hydrocore", JSON.stringify({ token, role, name, userId })); } catch (e) {}
  $("auth-screen").classList.add("hidden");
  $("app").classList.remove("hidden");
  $("who").textContent = name;
  $("role-label").textContent = role.toLowerCase();
  buildNav();
  go("dashboard");
}

function endSession() {
  S.token = null; S.role = null;
  try { sessionStorage.removeItem("hydrocore"); } catch (e) {}
  $("app").classList.add("hidden");
  $("auth-screen").classList.remove("hidden");
  $("l-pass").value = "";
  showForm("login");
}

$("logout-btn").onclick = async () => {
  try { await api("/auth/logout", "POST"); } catch (e) {}
  endSession();
};

/* ---------------- navigation (only what the system needs) ---------------- */
function buildNav() {
  const items = S.role === "ADMIN"
    ? [["dashboard", "Dashboard"], ["customers", "Customers"], ["readings", "Readings"], ["bills", "Bills"], ["payments", "Payments"], ["complaints", "Complaints"]]
    : [["dashboard", "Dashboard"], ["bills", "My bills"], ["payments", "Payments"], ["complaints", "Complaints"], ["estimator", "Estimate"]];
  $("nav").innerHTML = items.map(([id, label]) => `<button class="nav-item" id="nav-${id}" data-page="${id}" type="button">${label}</button>`).join("");
  $("nav").querySelectorAll(".nav-item").forEach((b) => (b.onclick = () => go(b.dataset.page)));
}

async function go(page) {
  S.page = page;
  const navPage = page === "customer" ? "customers" : page;          // a customer's history belongs under Customers
  document.querySelectorAll(".nav-item").forEach((b) => b.classList.toggle("active", b.dataset.page === navPage));
  try {
    await loadData();
    await ({ dashboard: renderDashboard, customers: renderCustomers, customer: renderCustomerDetail, readings: renderReadings, bills: renderBills, estimator: renderEstimator,
             payments: renderPayments, complaints: renderComplaints, profile: renderProfile })[page]();
  } catch (err) { $("view").innerHTML = `<p>${esc(err.message)}</p>`; }
}

async function loadData() {
  const reqs = [api("/connections"), api("/bills"), api("/alerts")];
  if (S.role === "ADMIN") reqs.push(api("/customers"));
  const [conns, bills, alerts, customers] = await Promise.all(reqs);
  S.connections = conns; S.bills = bills; S.alerts = alerts; S.customers = customers || [];
}

/* ---------------- dashboard: only what needs a decision today ---------------- */
function greeting() { const h = new Date().getHours(); return h < 12 ? "Good morning" : h < 17 ? "Good afternoon" : "Good evening"; }
function firstName() {
  if (S.role === "ADMIN") return "Administrator";
  const parts = S.name.replace(/\(.*?\)/g, "").trim().split(/\s+/);
  return parts[0].length === 1 && parts[1] ? parts[1] : parts[0];
}
const hero = () => `<div class="hero"><div><div class="hero-title" id="hero-title">${greeting()}, ${esc(firstName())}</div>
  <div class="hero-date">${new Date().toLocaleDateString("en-IN", { weekday: "long", day: "numeric", month: "long", year: "numeric" })}</div></div>
  <svg class="hero-wave" viewBox="0 0 400 100" preserveAspectRatio="none" aria-hidden="true">
    <path d="M0,62 C80,22 140,92 220,56 C290,26 340,62 400,36 V100 H0Z" fill="#cfe5f8"/><path d="M0,82 C90,52 170,100 260,74 C320,54 360,80 400,68 V100 H0Z" fill="#b4d6f2"/></svg></div>`;

/* A small dependency-free bar chart (SVG). series = [{ name, color, values }] */
function barChart(labels, series, { compact = true, showValues = false } = {}) {
  const W = 900, H = 210, L = 46, B = 28, T = 14, R = 8;
  const max = Math.max(1, ...series.flatMap((s) => s.values));
  const pow = 10 ** Math.floor(Math.log10(max));
  const top = Math.ceil(max / pow) * pow;
  const fmt = (n) => (compact && n >= 1000 ? round2(n / 1000) + "k" : String(round2(n)));
  const plotW = W - L - R, plotH = H - T - B;
  const groupW = plotW / labels.length;
  const barW = Math.min(44, (groupW * 0.7) / series.length);
  let svg = `<svg viewBox="0 0 ${W} ${H}" role="img" aria-label="${esc(series.map((s) => s.name).join(" and "))} by period">`;
  for (let i = 0; i <= 2; i++) {
    const v = (top / 2) * i, y = T + plotH - (v / top) * plotH;
    svg += `<line class="ch-grid" x1="${L}" x2="${W - R}" y1="${y}" y2="${y}"/><text class="ch-axis" x="${L - 6}" y="${y + 4}" text-anchor="end">${fmt(v)}</text>`;
  }
  labels.forEach((lab, i) => {
    const gx = L + i * groupW + groupW / 2;
    series.forEach((s, k) => {
      const val = s.values[i], h = (val / top) * plotH;
      const x = gx - (barW * series.length) / 2 + k * barW + (k ? 2 : 0);
      svg += `<rect x="${x}" y="${T + plotH - h}" width="${barW - (series.length > 1 ? 4 : 0)}" height="${Math.max(h, val ? 2 : 0)}" rx="2" fill="${s.color}"><title>${esc(lab)}: ${esc(s.name)} ${fmt(val)}</title></rect>`;
      if (showValues && val) svg += `<text class="ch-val" x="${x + (barW - (series.length > 1 ? 4 : 0)) / 2}" y="${T + plotH - h - 5}" text-anchor="middle">${fmt(val)}</text>`;
    });
    svg += `<text class="ch-axis" x="${gx}" y="${H - 8}" text-anchor="middle">${esc(lab)}</text>`;
  });
  return svg + "</svg>";
}

function lastMonths(n) {                                   // [{ key: "2026-11", label: "Nov" }, ...] oldest first
  const out = [], d = new Date();
  d.setDate(1);
  for (let i = n - 1; i >= 0; i--) {
    const m = new Date(d.getFullYear(), d.getMonth() - i, 1);
    out.push({ key: `${m.getFullYear()}-${String(m.getMonth() + 1).padStart(2, "0")}`, label: m.toLocaleDateString("en-IN", { month: "short" }) });
  }
  return out;
}
const daysOver = (due) => Math.max(0, Math.round((new Date(todayISO()) - new Date(due)) / 86400000));
const goLink = (page, text, filter) => `<button class="link go-link" data-page="${page}" ${filter ? `data-filter="${filter}"` : ""} type="button">${text}</button>`;
function bindGoLinks() {
  document.querySelectorAll(".go-link").forEach((b) => (b.onclick = () => { if (b.dataset.filter) S.billFilter = b.dataset.filter; go(b.dataset.page); }));
}
const plural = (n, one, many) => (n === 1 ? one : many);
function recentAlerts() {                      // a dashboard should not nag about last quarter
  const d = new Date(); d.setDate(d.getDate() - 30);
  const cutoff = d.toISOString().slice(0, 10);
  return S.alerts.filter((a) => a.created_on >= cutoff);
}

function renderDashboard() { return S.role === "ADMIN" ? adminDashboard() : customerDashboard(); }

async function adminDashboard() {
  const [payments, complaints, readings] = await Promise.all([api("/payments"), api("/complaints"), api("/readings")]);
  const month = todayISO().slice(0, 7);
  const outstanding = round2(S.bills.filter((b) => b.status !== "PAID").reduce((s, b) => s + amountDue(b), 0));
  const collected = round2(payments.filter((p) => p.paid_on.startsWith(month)).reduce((s, p) => s + p.amount, 0));
  const billedKl = round2(S.bills.filter((b) => b.bill_date.startsWith(month)).reduce((s, b) => s + b.units, 0));
  const ready = S.connections.filter((k) => {
    const rs = readings.filter((r) => r.connection_id === k.id);
    return rs.length >= 2 && !S.bills.some((b) => b.reading_id === rs[rs.length - 1].id);
  }).length;
  const overdue = S.bills.filter((b) => b.status === "OVERDUE").length;
  const openComplaints = complaints.filter((c) => c.status !== "RESOLVED").length;
  const alerts = recentAlerts().length;
  const items = [
    [ready, plural(ready, "meter is ready to bill", "meters are ready to bill"), goLink("readings", "Open readings")],
    [overdue, plural(overdue, "bill is overdue", "bills are overdue"), goLink("bills", "View", "OVERDUE")],
    [openComplaints, plural(openComplaints, "complaint is open", "complaints are open"), goLink("complaints", "View")],
    [alerts, plural(alerts, "high-usage alert", "high-usage alerts"), goLink("bills", "View", "ALL")],
  ].filter(([n]) => n > 0);
  const recent = payments.slice().sort((a, b) => b.paid_on.localeCompare(a.paid_on) || b.id - a.id).slice(0, 5);

  const months = lastMonths(6);
  const billedSeries = months.map((m) => round2(S.bills.filter((b) => b.bill_date.startsWith(m.key)).reduce((s, b) => s + b.total, 0)));
  const collectedSeries = months.map((m) => round2(payments.filter((p) => p.paid_on.startsWith(m.key)).reduce((s, p) => s + p.amount, 0)));
  const unpaidCount = S.bills.filter((b) => b.status !== "PAID").length;
  $("view").innerHTML = `${hero()}
    <div class="statement">
      <div class="balance"><span class="k">Outstanding balance</span>
        <span class="figure" id="dash-outstanding">${money(outstanding)}</span>
        <span class="note">${unpaidCount} unpaid ${plural(unpaidCount, "bill", "bills")}${overdue ? `, ${overdue} overdue. ${goLink("bills", "Review overdue bills", "OVERDUE")}` : ""}</span></div>
      <dl class="facts">
        <div><dt>Collected this month</dt><dd>${money(collected)}</dd></div>
        <div><dt>Water billed this month</dt><dd>${billedKl} kL</dd></div>
      </dl></div>
    <div class="panel chart-panel"><h3>Billed and collected, last 6 months
        <span class="legend"><i style="background:#9ec9ee"></i>Billed<i style="background:#1558b0"></i>Collected</span></h3>
      <div class="chart" id="dash-chart">${barChart(months.map((m) => m.label), [{ name: "Billed", color: "#9ec9ee", values: billedSeries }, { name: "Collected", color: "#1558b0", values: collectedSeries }])}</div></div>
    <div class="dash-grid">
      <div class="panel"><h3>Needs attention</h3>${items.length
        ? `<ul class="attn" id="attention-list">${items.map(([n, text, link]) => `<li><span><strong>${n}</strong> ${text}</span>${link}</li>`).join("")}</ul>`
        : '<p class="muted" id="attention-list">Nothing needs attention right now.</p>'}</div>
      <div class="panel"><h3>Recent payments</h3>${recent.length ? `<table class="plain"><tbody id="recent-payments">${recent.map((p) => `<tr>
          <td>${custLink(p.customer_id, p.customer_name)}<div class="muted small">${p.receipt_no}, ${p.paid_on}</div></td><td class="num">${money(p.amount)}</td></tr>`).join("")}</tbody></table>
        <div style="margin-top:8px">${goLink("payments", "All payments")}</div>` : '<p class="muted">No payments yet.</p>'}</div>
    </div>`;
  bindGoLinks();
  bindCustLinks();
}

async function customerDashboard() {
  const complaints = await api("/complaints");
  const open = S.bills.filter((b) => b.status !== "PAID").sort((a, b) => (a.due_date < b.due_date ? -1 : 1));
  const due = round2(open.reduce((s, b) => s + amountDue(b), 0));
  const oldest = open[0];
  const last = S.bills[S.bills.length - 1];
  const before = last ? S.bills.filter((b) => b.connection_id === last.connection_id && b.id < last.id).pop() : null;
  const diff = last && before ? round2(last.units - before.units) : null;
  const openComplaints = complaints.filter((c) => c.status !== "RESOLVED").length;
  const alert = recentAlerts().pop();

  const usage = S.bills.slice(-6);
  $("view").innerHTML = `${hero()}
    ${alert ? `<div class="notice"><strong>High water usage detected.</strong> ${esc(alert.message)} on meter ${esc(connLabel(alert.connection_id))}. If you have not used that much, check for a leak and ${goLink("complaints", "report it")}.</div>` : ""}
    <div class="dash-grid">
      <div class="panel"><h3>Amount due</h3>
        <div class="big" id="dash-due">${money(due)}</div>
        ${oldest ? `<p class="muted">${oldest.status === "OVERDUE" ? `Overdue since ${oldest.due_date}` : `Due by ${oldest.due_date}`}${open.length > 1 ? `, ${open.length} bills pending` : ""}</p>
          <button id="dash-pay" class="btn primary" type="button">Pay now</button>` : '<p class="muted">You are all paid up.</p>'}</div>
      <div class="panel"><h3>Latest bill</h3>${last ? `
        <table class="plain"><tbody>
          <tr><td class="muted">Bill</td><td class="num">#${last.id} &middot; ${last.bill_date}</td></tr>
          <tr><td class="muted">Usage</td><td class="num">${last.units} kL</td></tr>
          <tr><td class="muted">Amount</td><td class="num">${money(last.status === "PAID" ? last.total + last.late_fee : last.total)}</td></tr>
          <tr><td class="muted">Status</td><td class="num">${status(last.status)}</td></tr></tbody></table>
        ${diff === null ? "" : `<p class="muted small" style="margin-bottom:0">${diff === 0 ? "Same usage as the previous bill." : `${Math.abs(diff)} kL ${diff > 0 ? "more" : "less"} than the previous bill.`}</p>`}
        <div style="margin-top:8px">${goLink("bills", "All bills")}</div>` : '<p class="muted">No bills yet.</p>'}</div>
    </div>
    <div class="panel chart-panel"><h3>Your water usage (kL), last ${usage.length || 6} bills</h3>
      <div class="chart" id="dash-chart">${usage.length ? barChart(usage.map((b) => new Date(b.bill_date + "T00:00:00").toLocaleDateString("en-IN", { month: "short", year: "2-digit" })),
        [{ name: "Usage (kL)", color: "#1558b0", values: usage.map((b) => b.units) }], { compact: false, showValues: true }) : '<p class="muted">Your usage will appear here after your first bill.</p>'}</div></div>
    ${openComplaints ? `<p class="muted" style="margin-top:4px">You have ${openComplaints} open ${plural(openComplaints, "complaint", "complaints")}. ${goLink("complaints", "View")}</p>` : ""}`;
  if (oldest) $("dash-pay").onclick = () => openPay(oldest.id);
  bindGoLinks();
}

/* ---------------- bills ---------------- */
function renderBills() {
  const admin = S.role === "ADMIN";
  const open = S.bills.filter((b) => b.status !== "PAID");
  const overdue = S.bills.filter((b) => b.status === "OVERDUE");
  const outstanding = round2(open.reduce((s, b) => s + amountDue(b), 0));
  const collected = round2(S.bills.filter((b) => b.status === "PAID").reduce((s, b) => s + b.total + b.late_fee, 0));
  const last = S.bills[S.bills.length - 1];

  const summary = admin
    ? `<div><span class="k">Bills issued</span><span class="v">${S.bills.length}</span></div>
       <div><span class="k">Collected</span><span class="v">${money(collected)}</span></div>
       <div><span class="k">Outstanding</span><span class="v">${money(outstanding)}</span></div>
       <div><span class="k">Overdue bills</span><span class="v">${overdue.length}</span></div>`
    : `<div><span class="k">Amount due</span><span class="v">${money(outstanding)}</span></div>
       <div><span class="k">Overdue bills</span><span class="v">${overdue.length}</span></div>
       <div><span class="k">Last usage</span><span class="v">${last ? last.units + " kL" : "-"}</span></div>`;

  const notice = S.alerts.length
    ? `<div class="notice"><strong>High water usage detected</strong><ul>${S.alerts.slice(-3).reverse().map((a) =>
        `<li>${esc(a.message)} on meter ${esc(connLabel(a.connection_id))} (${a.created_on})</li>`).join("")}</ul></div>` : "";

  const list = (S.billFilter === "ALL" ? S.bills : S.bills.filter((b) => b.status === S.billFilter)).slice().reverse();
  const rows = list.map((b) => `<tr>
      <td>#${b.id}</td>${admin ? `<td>${custLink(connOwnerId(b.connection_id), connOwner(b.connection_id))}</td>` : ""}<td>${esc(connLabel(b.connection_id))}</td>
      <td>${b.bill_date}</td><td class="num">${b.units} kL</td>
      <td class="num">${money(b.status === "PAID" ? b.total + b.late_fee : b.total)}</td><td>${b.due_date}</td>
      <td class="st">${status(b.status)}</td>
      <td>${!admin && b.status !== "PAID" ? `<button class="btn small pay-btn" data-id="${b.id}" type="button">Pay</button>` : ""}</td></tr>`).join("");

  $("view").innerHTML = `<h2>${admin ? "Bills" : "My bills"}</h2>
    ${notice}<div class="summary" style="margin-top:14px">${summary}</div>
    <div class="toolbar"><label for="bill-filter" style="margin:0">Show</label>
      <select id="bill-filter">${["ALL", "UNPAID", "OVERDUE", "PAID"].map((s) => `<option value="${s}" ${S.billFilter === s ? "selected" : ""}>${s === "ALL" ? "All" : s[0] + s.slice(1).toLowerCase()}</option>`).join("")}</select></div>
    <div class="table-wrap"><table><thead><tr><th>Bill</th>${admin ? "<th>Customer</th>" : ""}<th>Meter</th><th>Date</th><th class="num">Usage</th><th class="num">Amount</th><th>Due</th><th>Status</th><th></th></tr></thead>
      <tbody id="bill-rows">${rows || emptyRow(admin ? 9 : 8, "No bills to show.")}</tbody></table></div>`;
  $("bill-filter").onchange = (e) => { S.billFilter = e.target.value; renderBills(); };
  document.querySelectorAll(".pay-btn").forEach((b) => (b.onclick = () => openPay(+b.dataset.id)));
  bindCustLinks();
}

/* ---------------- payment dialog ---------------- */
let payingId = null;
function openPay(id) {
  const b = S.bills.find((x) => x.id === id);
  if (!b) return;
  payingId = id;
  const fee = lateFee(b);
  $("pay-body").innerHTML = `<p class="muted" style="margin:0">Bill #${b.id}, meter ${esc(connLabel(b.connection_id))}, ${b.units} kL</p>
    <table class="breakdown">
      <tr><td>Water charge</td><td>${money(b.water_charge)}</td></tr>
      <tr><td>Fixed charge</td><td>${money(b.fixed_charge)}</td></tr>
      <tr><td>Late fee${fee ? " (due " + b.due_date + ")" : ""}</td><td>${money(fee)}</td></tr>
      <tr class="total"><td>Total</td><td id="pay-total">${money(amountDue(b))}</td></tr></table>
    <label for="pay-method">Payment method</label>
    <select id="pay-method"><option value="UPI">UPI</option><option value="CARD">Debit / credit card</option><option value="NETBANKING">Net banking</option></select>`;
  $("pay-modal").classList.remove("hidden");
}
function closePay() { $("pay-modal").classList.add("hidden"); payingId = null; }
$("confirm-cancel").onclick = closePay;
$("pay-modal").onclick = (e) => { if (e.target.id === "pay-modal") closePay(); };
$("confirm-ok").onclick = async () => {
  const b = S.bills.find((x) => x.id === payingId);
  if (!b) return;
  try {
    await api(`/bills/${b.id}/pay`, "POST", { amount: amountDue(b), method: $("pay-method").value });
    toast("Payment received for bill #" + b.id + ". Receipt available under Payments.");
    closePay();
    go(S.page);
  } catch (err) { toast(err.message, "err"); }
};

/* ---------------- estimator (customer) ---------------- */
function renderEstimator() {
  $("view").innerHTML = `<h2>Estimate a bill</h2>
    <div class="form-box" style="margin-top:14px">
      <div class="row2"><div><label for="c-units">Water used (kL)</label><input id="c-units" type="number" min="0" step="0.01" placeholder="e.g. 25"></div>
      <div><label for="c-type">Connection type</label><select id="c-type"><option>DOMESTIC</option><option>COMMERCIAL</option></select></div></div>
      <button id="calc-btn" class="btn primary" style="margin-top:16px" type="button">Calculate</button>
      <div id="calc-out" class="calc-result" role="status"></div></div>
    <h3>Tariff</h3>
    <div class="table-wrap" style="max-width:560px"><table><thead><tr><th>Monthly usage</th><th class="num">Rate per kL</th></tr></thead><tbody>
      <tr><td>First 10 kL</td><td class="num">${money(5)}</td></tr><tr><td>10 - 20 kL</td><td class="num">${money(8)}</td></tr>
      <tr><td>20 - 30 kL</td><td class="num">${money(12)}</td></tr><tr><td>Above 30 kL</td><td class="num">${money(20)}</td></tr></tbody></table></div>
    <p class="muted" style="max-width:560px">Commercial water charge is 1.5 times the domestic charge. Fixed monthly charge: ${money(50)} domestic, ${money(150)} commercial. Paying after the due date adds ${money(25)} plus 2% of the bill.</p>`;
  $("calc-btn").onclick = async () => {
    const out = $("calc-out");
    try {
      const d = await api(`/tariff/calculate?units=${encodeURIComponent($("c-units").value)}&type=${$("c-type").value}`);
      out.className = "calc-result";
      out.innerHTML = `Water charge ${money(d.water_charge)} + fixed charge ${money(d.fixed_charge)}<br><strong style="font-size:18px">Total: ${money(d.total)}</strong>`;
    } catch (err) { out.className = "calc-result err"; out.textContent = err.message; }
  };
}

/* ---------------- admin: customers ---------------- */
function customerRows() {
  const q = S.custQ.trim().toLowerCase();
  const list = S.customers.filter((c) => {
    const conns = S.connections.filter((k) => k.customer_id === c.id);
    if (S.custType !== "ALL" && !conns.some((k) => k.type === S.custType)) return false;
    if (!q) return true;
    return [c.full_name, c.username, ...conns.map((k) => k.meter_no)].some((s) => s.toLowerCase().includes(q));
  });
  const rows = list.map((c) => {
    const conns = S.connections.filter((k) => k.customer_id === c.id && (S.custType === "ALL" || k.type === S.custType));
    return `<tr><td>${c.id}</td><td>${custLink(c.id, c.full_name)}</td><td>${esc(c.username)}</td>
      <td>${conns.map((k) => esc(k.meter_no)).join(", ") || '<span class="muted">-</span>'}</td>
      <td>${conns.map((k) => k.type[0] + k.type.slice(1).toLowerCase()).join(", ")}</td>
      <td>${conns.map((k) => esc(k.address)).join("; ")}</td></tr>`;
  }).join("");
  return rows || emptyRow(6, "No customers match.");
}

function renderCustomers() {
  $("view").innerHTML = `<div class="page-head"><h2>Customers</h2>
    <button id="new-conn-btn" class="btn primary" type="button">New connection</button></div>
    <div class="toolbar" style="margin-top:14px"><label for="type-filter" style="margin:0">Type</label>
      <select id="type-filter"><option value="ALL">All types</option><option value="DOMESTIC">Domestic</option><option value="COMMERCIAL">Commercial</option></select>
      <input id="cust-search" type="search" placeholder="Search name, username or meter" style="max-width:260px;padding:6px 10px" value="${esc(S.custQ)}"></div>
    <div class="table-wrap"><table><thead><tr><th>ID</th><th>Name</th><th>Username</th><th>Meter</th><th>Type</th><th>Address</th></tr></thead>
      <tbody id="customer-rows">${customerRows()}</tbody></table></div>`;
  $("type-filter").value = S.custType;
  const refresh = () => { $("customer-rows").innerHTML = customerRows(); bindCustLinks(); };
  $("type-filter").onchange = (e) => { S.custType = e.target.value; refresh(); };
  $("cust-search").oninput = (e) => { S.custQ = e.target.value; refresh(); };
  $("new-conn-btn").onclick = openConnDialog;
  bindCustLinks();
}

/* ---------------- admin: one customer's history ---------------- */
function custLink(id, name) {
  return S.role === "ADMIN" ? `<a href="#" class="cust-link" data-cid="${id}">${esc(name)}</a>` : esc(name);
}
function bindCustLinks() {
  document.querySelectorAll(".cust-link").forEach((a) => (a.onclick = (e) => { e.preventDefault(); S.viewCustomerId = +a.dataset.cid; S.detailTab = "bills"; go("customer"); }));
}
const connOwnerId = (connId) => { const c = S.connections.find((x) => x.id === connId); return c ? c.customer_id : null; };

async function renderCustomerDetail() {
  const id = S.viewCustomerId;
  const cust = S.customers.find((c) => c.id === id);
  if (!cust) return go("customers");
  const [payments, complaints, readings] = await Promise.all([api("/payments"), api("/complaints"), api("/readings")]);
  const conns = S.connections.filter((k) => k.customer_id === id);
  const ids = new Set(conns.map((k) => k.id));
  const bills = S.bills.filter((b) => ids.has(b.connection_id));
  const pays = payments.filter((p) => p.customer_id === id);
  const comps = complaints.filter((c) => c.customer_id === id);
  const reads = readings.filter((r) => ids.has(r.connection_id));
  PAYMENTS = pays;

  const open = bills.filter((b) => b.status !== "PAID");
  const outstanding = round2(open.reduce((s, b) => s + amountDue(b), 0));
  const paidTotal = round2(pays.reduce((s, p) => s + p.amount, 0));

  const panes = {
    bills: `<div class="table-wrap"><table><thead><tr><th>Bill</th><th>Meter</th><th>Date</th><th class="num">Usage</th><th class="num">Amount</th><th>Due</th><th>Status</th></tr></thead><tbody id="bill-rows">${
      bills.slice().reverse().map((b) => `<tr><td>#${b.id}</td><td>${esc(connLabel(b.connection_id))}</td><td>${b.bill_date}</td><td class="num">${b.units} kL</td>
        <td class="num">${money(b.status === "PAID" ? b.total + b.late_fee : b.total)}</td><td>${b.due_date}</td><td>${status(b.status)}</td></tr>`).join("") || emptyRow(7, "No bills yet.")}</tbody></table></div>`,
    payments: `<div class="table-wrap"><table><thead><tr><th>Receipt</th><th>Date</th><th>Bill</th><th>Method</th><th class="num">Late fee</th><th class="num">Amount</th><th></th></tr></thead><tbody>${
      pays.map((p) => `<tr><td>${p.receipt_no}</td><td>${p.paid_on}</td><td>#${p.bill_id}</td><td>${METHODS[p.method] || p.method}</td><td class="num">${money(p.late_fee)}</td><td class="num">${money(p.amount)}</td>
        <td><button class="btn small receipt-btn" data-id="${p.id}" type="button">Receipt</button></td></tr>`).join("") || emptyRow(7, "No payments yet.")}</tbody></table></div>`,
    complaints: `<div class="table-wrap"><table><thead><tr><th>ID</th><th>Date</th><th>Type</th><th>Description</th><th>Status</th><th>Resolution</th></tr></thead><tbody>${
      comps.map((c) => `<tr><td>#${c.id}</td><td style="white-space:nowrap">${c.created_on}</td><td>${CATEGORY[c.category]}</td><td class="cell-text">${esc(c.description)}</td><td>${cstatus(c.status)}</td>
        <td class="cell-text">${c.resolution ? esc(c.resolution) : '<span class="muted">-</span>'}</td></tr>`).join("") || emptyRow(6, "No complaints.")}</tbody></table></div>`,
    readings: `<div class="table-wrap"><table><thead><tr><th>Date</th><th>Meter</th><th class="num">Reading (kL)</th><th class="num">Used since previous</th></tr></thead><tbody>${
      reads.map((r, i) => {
        const prev = reads.slice(0, i).reverse().find((x) => x.connection_id === r.connection_id);
        return `<tr><td>${r.read_on}</td><td>${esc(r.meter_no)}</td><td class="num">${r.reading}</td><td class="num">${prev ? round2(r.reading - prev.reading) + " kL" : '<span class="muted">first reading</span>'}</td></tr>`;
      }).reverse().join("") || emptyRow(4, "No readings yet.")}</tbody></table></div>`,
  };
  const tabs = [["bills", "Bills", bills.length], ["payments", "Payments", pays.length], ["complaints", "Complaints", comps.length], ["readings", "Meter readings", reads.length]];

  $("view").innerHTML = `<a href="#" id="back-customers" class="back-link">&lsaquo; Customers</a>
    <div class="id-head"><div class="avatar-sq">${esc(initials(cust.full_name))}</div>
      <div><h2 id="detail-name">${esc(cust.full_name)}</h2><div class="meta">@${esc(cust.username)} &middot; Customer ID ${cust.id}</div></div></div>
    <div class="summary"><div><span class="k">Amount due</span><span class="v">${money(outstanding)}</span></div>
      <div><span class="k">Total paid</span><span class="v">${money(paidTotal)}</span></div>
      <div><span class="k">Overdue bills</span><span class="v">${bills.filter((b) => b.status === "OVERDUE").length}</span></div>
      <div><span class="k">Open complaints</span><span class="v">${comps.filter((c) => c.status !== "RESOLVED").length}</span></div></div>
    <div class="info-card"><h3>Connections</h3>${conns.length ? `<div class="table-wrap" style="border:0"><table><thead><tr><th>Meter</th><th>Type</th><th>Address</th></tr></thead><tbody>${
      conns.map((k) => `<tr><td>${esc(k.meter_no)}</td><td>${k.type[0] + k.type.slice(1).toLowerCase()}</td><td>${esc(k.address)}</td></tr>`).join("")}</tbody></table></div>` : '<span class="muted">No connection yet.</span>'}</div>
    <div class="tabs" id="detail-tabs">${tabs.map(([k, label, n]) => `<button class="tab-btn ${S.detailTab === k ? "active" : ""}" data-tab="${k}" id="dtab-${k}" type="button">${label}<span class="count">${n}</span></button>`).join("")}</div>
    <div id="detail-pane">${panes[S.detailTab]}</div>`;
  $("back-customers").onclick = (e) => { e.preventDefault(); go("customers"); };
  document.querySelectorAll(".tab-btn").forEach((b) => (b.onclick = () => { S.detailTab = b.dataset.tab; renderCustomerDetail(); }));
  document.querySelectorAll(".receipt-btn").forEach((b) => (b.onclick = () => openReceipt(+b.dataset.id)));
}
const initials = (name) => name.replace(/\(.*?\)/g, "").trim().split(/\s+/).map((w) => w[0]).slice(0, 2).join("").toUpperCase();

/* "New connection" popup */
function openConnDialog() {
  $("conn-body").innerHTML = `
    <label for="a-cust">Customer</label><select id="a-cust"><option value="">Select customer</option>${S.customers.map((c) => `<option value="${c.id}">${esc(c.full_name)} (${esc(c.username)})</option>`).join("")}</select>
    <div class="row2"><div><label for="a-meter">Meter number</label><input id="a-meter" placeholder="e.g. MTR-1007"></div>
    <div><label for="a-type">Type</label><select id="a-type"><option>DOMESTIC</option><option>COMMERCIAL</option></select></div></div>
    <label for="a-addr">Address</label><input id="a-addr" placeholder="Service address">
    <div id="conn-msg" class="form-msg" role="alert" style="margin-top:10px"></div>`;
  $("conn-modal").classList.remove("hidden");
  $("a-cust").focus();
}
function closeConnDialog() { $("conn-modal").classList.add("hidden"); }
$("conn-cancel").onclick = closeConnDialog;
$("conn-modal").onclick = (e) => { if (e.target.id === "conn-modal") closeConnDialog(); };
$("conn-btn").onclick = async () => {
  try {
    await api("/connections", "POST", { customer_id: +$("a-cust").value, meter_no: $("a-meter").value.trim(), type: $("a-type").value, address: $("a-addr").value.trim() });
    closeConnDialog();
    toast("Connection added");
    go("customers");
  } catch (err) { setMsg("conn-msg", err.message, false); }
};

/* ---------------- admin: readings ---------------- */
let READINGS = [];
let readingConnId = null;

/* One row per connection: shows where it stands, and what the admin can do next. */
async function renderReadings() {
  READINGS = await api("/readings");
  const rows = S.connections.map((k) => {
    const rs = READINGS.filter((r) => r.connection_id === k.id);
    const last = rs[rs.length - 1], prev = rs[rs.length - 2];
    const billed = last && S.bills.some((b) => b.reading_id === last.id);
    const ready = rs.length >= 2 && !billed;
    const state = !last ? "No readings yet" : rs.length === 1 ? "Starting reading saved" : billed ? "Billed, waiting for next reading" : "Ready to bill";
    const whyDisabled = !last ? "Add the starting reading first" : rs.length === 1 ? "Add a second reading to get usage" : "Already billed. Add a new reading first";
    return `<tr>
      <td>${esc(k.meter_no)}</td><td>${custLink(k.customer_id, customerName(k.customer_id))}</td>
      <td class="num">${last ? last.reading + " kL" : "-"}</td><td>${last ? last.read_on : "-"}</td>
      <td class="num">${prev ? round2(last.reading - prev.reading) + " kL" : "-"}</td>
      <td class="rstate">${state}</td>
      <td style="white-space:nowrap"><button class="btn small add-reading-btn" data-id="${k.id}" data-meter="${esc(k.meter_no)}" type="button">Add reading</button>
        <button class="btn small gen-btn" data-id="${k.id}" data-meter="${esc(k.meter_no)}" type="button" ${ready ? "" : `disabled title="${whyDisabled}"`}>Generate bill</button></td></tr>`;
  }).join("");
  $("view").innerHTML = `<h2>Meter readings</h2>
    <div class="table-wrap" style="margin-top:14px"><table><thead><tr><th>Meter</th><th>Customer</th><th class="num">Last reading</th><th>Read on</th><th class="num">Used last period</th><th>Status</th><th></th></tr></thead>
      <tbody id="reading-rows">${rows || emptyRow(7, "No connections yet. Add one from the Customers page.")}</tbody></table></div>`;
  bindCustLinks();
  document.querySelectorAll(".add-reading-btn").forEach((b) => (b.onclick = () => openReadingDialog(+b.dataset.id)));
  document.querySelectorAll(".gen-btn").forEach((b) => (b.onclick = async () => {
    try {
      const d = await api("/bills/generate", "POST", { connection_id: +b.dataset.id });
      toast(`Bill #${d.id} generated: ${money(d.total)} for ${d.units} kL`);
      go("readings");
    } catch (err) { toast(err.message, "err"); }
  }));
}

function openReadingDialog(connId) {
  readingConnId = connId;
  const k = S.connections.find((x) => x.id === connId);
  const rs = READINGS.filter((r) => r.connection_id === connId);
  const last = rs[rs.length - 1];
  $("rd-body").innerHTML = `<p style="margin:0"><strong>${esc(k.meter_no)}</strong> &middot; ${esc(customerName(k.customer_id))}</p>
    <p class="muted hint">${last ? `Previous reading: ${last.reading} kL on ${last.read_on}.` : "No readings yet. This first reading is the starting point; the bill is generated from the next one."}
      Enter the number now shown on the meter. Usage = this reading minus the previous one.</p>
    <div class="row2"><div><label for="m-read">Meter shows (kL)</label><input id="m-read" type="number" min="${last ? last.reading : 0}" step="0.01" placeholder="e.g. 125"></div>
    <div><label for="m-date">Date read</label><input id="m-date" type="date" max="${todayISO()}" ${last ? `min="${last.read_on}"` : ""} value="${todayISO()}"></div></div>
    <div id="rd-msg" class="form-msg" role="alert" style="margin-top:10px"></div>`;
  $("read-bill-btn").classList.toggle("hidden", !last);        // a bill needs a previous reading to compare with
  $("rd-modal").classList.remove("hidden");
  $("m-read").focus();
}
$("rd-cancel").onclick = () => $("rd-modal").classList.add("hidden");
$("rd-modal").onclick = (e) => { if (e.target.id === "rd-modal") $("rd-modal").classList.add("hidden"); };
async function saveReading(andBill) {
  try {
    const value = parseFloat($("m-read").value);
    if (Number.isNaN(value)) throw new Error("Enter the meter reading");
    await api("/readings", "POST", { connection_id: readingConnId, reading: value, read_on: $("m-date").value || undefined });
    let message = "Reading saved";
    if (andBill) {
      try {
        const d = await api("/bills/generate", "POST", { connection_id: readingConnId });
        message = `Reading saved. Bill #${d.id} generated: ${money(d.total)} for ${d.units} kL`;
      } catch (err) {
        $("rd-modal").classList.add("hidden");
        toast(`Reading saved, but the bill could not be generated: ${err.message}`, "err");
        return go("readings");
      }
    }
    $("rd-modal").classList.add("hidden");
    toast(message);
    go("readings");
  } catch (err) { setMsg("rd-msg", err.message, false); }
}
$("read-btn").onclick = () => saveReading(false);
$("read-bill-btn").onclick = () => saveReading(true);

/* ---------------- payments & receipts ---------------- */
const METHODS = { UPI: "UPI", CARD: "Card", NETBANKING: "Net banking", CASH: "Cash" };
let PAYMENTS = [];

async function renderPayments() {
  const admin = S.role === "ADMIN";
  PAYMENTS = await api("/payments");
  const total = round2(PAYMENTS.reduce((s, p) => s + p.amount, 0));
  const fees = round2(PAYMENTS.reduce((s, p) => s + p.late_fee, 0));
  const rows = PAYMENTS.map((p) => `<tr>
      <td>${p.receipt_no}</td><td>${p.paid_on}</td><td>#${p.bill_id}</td>${admin ? `<td>${custLink(p.customer_id, p.customer_name)}</td>` : ""}
      <td>${esc(p.meter_no)}</td><td>${METHODS[p.method] || p.method}</td>
      <td class="num">${money(p.late_fee)}</td><td class="num">${money(p.amount)}</td>
      <td><button class="btn small receipt-btn" data-id="${p.id}" type="button">Receipt</button></td></tr>`).join("");
  $("view").innerHTML = `<h2>Payments</h2>
    <div class="summary" style="margin-top:14px"><div><span class="k">Payments</span><span class="v">${PAYMENTS.length}</span></div>
      <div><span class="k">${admin ? "Total collected" : "Total paid"}</span><span class="v">${money(total)}</span></div>
      <div><span class="k">Late fees</span><span class="v">${money(fees)}</span></div></div>
    <div class="table-wrap"><table><thead><tr><th>Receipt</th><th>Date</th><th>Bill</th>${admin ? "<th>Customer</th>" : ""}<th>Meter</th><th>Method</th><th class="num">Late fee</th><th class="num">Amount</th><th></th></tr></thead>
      <tbody id="pay-rows">${rows || emptyRow(admin ? 9 : 8, "No payments yet.")}</tbody></table></div>`;
  document.querySelectorAll(".receipt-btn").forEach((b) => (b.onclick = () => openReceipt(+b.dataset.id)));
  bindCustLinks();
}

async function openReceipt(id) {
  try {
    const r = await api("/payments/" + id);
    $("receipt-body").innerHTML = `<div class="receipt-head"><strong>HydroCore - Water Supply &amp; Billing</strong>
      <span class="receipt-no">Receipt ${r.receipt_no} &middot; ${r.paid_on}</span></div>
      <table class="kv"><tr><td>Customer</td><td>${esc(r.customer_name)}</td></tr>
        <tr><td>Meter</td><td>${esc(r.meter_no)} (${r.connection_type[0] + r.connection_type.slice(1).toLowerCase()})</td></tr>
        <tr><td>Address</td><td>${esc(r.address)}</td></tr>
        <tr><td>Bill</td><td>#${r.bill_id}, ${r.bill_date}, ${r.units} kL</td></tr>
        <tr><td>Payment method</td><td>${METHODS[r.method] || r.method}</td></tr></table>
      <table class="breakdown"><tr><td>Water charge</td><td>${money(r.water_charge)}</td></tr>
        <tr><td>Fixed charge</td><td>${money(r.fixed_charge)}</td></tr>
        <tr><td>Late fee</td><td>${money(r.late_fee)}</td></tr>
        <tr class="total"><td>Amount paid</td><td id="receipt-total">${money(r.amount)}</td></tr></table>`;
    $("receipt-modal").classList.remove("hidden");
  } catch (err) { toast(err.message, "err"); }
}
$("receipt-close").onclick = () => $("receipt-modal").classList.add("hidden");
$("receipt-print").onclick = () => window.print();
$("receipt-modal").onclick = (e) => { if (e.target.id === "receipt-modal") $("receipt-modal").classList.add("hidden"); };

/* ---------------- complaints ---------------- */
const CATEGORY = { LEAK: "Leak", BILLING: "Billing", NO_SUPPLY: "No supply", OTHER: "Other" };
const CSTATUS = { OPEN: "Open", IN_PROGRESS: "In progress", RESOLVED: "Resolved" };
const NEXT = { OPEN: ["IN_PROGRESS"], IN_PROGRESS: ["RESOLVED"], RESOLVED: [] };
const cstatus = (s) => `<span class="status s-${s}">${CSTATUS[s]}</span>`;
let COMPLAINTS = [];

async function renderComplaints() {
  const admin = S.role === "ADMIN";
  COMPLAINTS = await api("/complaints");
  const open = COMPLAINTS.filter((c) => c.status !== "RESOLVED").length;
  const rows = COMPLAINTS.map((c) => `<tr>
      <td>#${c.id}</td><td style="white-space:nowrap">${c.created_on}</td>${admin ? `<td>${custLink(c.customer_id, c.customer_name)}</td>` : ""}
      <td style="white-space:nowrap">${CATEGORY[c.category]}</td><td style="white-space:nowrap">${c.meter_no ? esc(c.meter_no) : '<span class="muted">-</span>'}</td>
      <td class="cell-text">${esc(c.description)}</td><td class="cst">${cstatus(c.status)}</td>
      <td class="cell-text">${c.resolution ? esc(c.resolution) : '<span class="muted">-</span>'}</td>
      ${admin ? `<td>${NEXT[c.status].length ? `<button class="btn small cu-btn" data-id="${c.id}" type="button">Update</button>` : ""}</td>` : ""}</tr>`).join("");
  $("view").innerHTML = `<div class="page-head"><h2>Complaints</h2>
      ${admin ? "" : '<button id="new-complaint-btn" class="btn primary" type="button">New complaint</button>'}</div>
    <div class="summary" style="margin-top:14px"><div><span class="k">Total</span><span class="v">${COMPLAINTS.length}</span></div>
      <div><span class="k">Open or in progress</span><span class="v">${open}</span></div>
      <div><span class="k">Resolved</span><span class="v">${COMPLAINTS.length - open}</span></div></div>
    <div class="table-wrap"><table><thead><tr><th>ID</th><th>Date</th>${admin ? "<th>Customer</th>" : ""}<th>Type</th><th>Meter</th><th>Description</th><th>Status</th><th>Resolution</th>${admin ? "<th></th>" : ""}</tr></thead>
      <tbody id="complaint-rows">${rows || emptyRow(admin ? 9 : 8, "No complaints.")}</tbody></table></div>`;
  if (admin) document.querySelectorAll(".cu-btn").forEach((b) => (b.onclick = () => openUpdateComplaint(+b.dataset.id)));
  else $("new-complaint-btn").onclick = openNewComplaint;
  bindCustLinks();
}

function openNewComplaint() {
  $("cp-body").innerHTML = `
    <div class="row2"><div><label for="cp-cat">Type</label><select id="cp-cat">${Object.entries(CATEGORY).map(([k, v]) => `<option value="${k}">${v}</option>`).join("")}</select></div>
    <div><label for="cp-conn">Connection</label><select id="cp-conn"><option value="">Not about a specific meter</option>${S.connections.map((c) => `<option value="${c.id}">${esc(c.meter_no)}</option>`).join("")}</select></div></div>
    <label for="cp-desc">Describe the problem (10 to 500 characters)</label><textarea id="cp-desc" maxlength="500" placeholder="What is happening, and since when?"></textarea>
    <div id="cp-msg" class="form-msg" role="alert"></div>`;
  $("cp-modal").classList.remove("hidden");
  $("cp-desc").focus();
}
$("cp-cancel").onclick = () => $("cp-modal").classList.add("hidden");
$("cp-modal").onclick = (e) => { if (e.target.id === "cp-modal") $("cp-modal").classList.add("hidden"); };
$("cp-save").onclick = async () => {
  try {
    const body = { category: $("cp-cat").value, description: $("cp-desc").value.trim() };
    if ($("cp-conn").value) body.connection_id = +$("cp-conn").value;
    await api("/complaints", "POST", body);
    $("cp-modal").classList.add("hidden");
    toast("Complaint submitted");
    go("complaints");
  } catch (err) { setMsg("cp-msg", err.message, false); }
};

let updatingId = null;
function openUpdateComplaint(id) {
  const c = COMPLAINTS.find((x) => x.id === id);
  if (!c) return;
  updatingId = id;
  $("cu-body").innerHTML = `<p class="muted" style="margin:0">#${c.id} from ${esc(c.customer_name)}: ${esc(c.description)}</p>
    <label for="cu-status">Status</label>
    <select id="cu-status">${Object.keys(CSTATUS).map((s) => {
      const allowed = NEXT[c.status].includes(s);
      return `<option value="${s}" ${allowed ? "" : "disabled"} ${s === NEXT[c.status][0] ? "selected" : ""}>${CSTATUS[s]}${s === c.status ? " (current)" : ""}</option>`;
    }).join("")}</select>
    <p class="muted hint">A complaint moves one step at a time: Open, then In progress, then Resolved.</p>
    <label for="cu-res">Resolution note (required when resolving)</label><textarea id="cu-res" maxlength="500" placeholder="What was done?"></textarea>
    <div id="cu-msg" class="form-msg" role="alert"></div>`;
  $("cu-modal").classList.remove("hidden");
}
$("cu-cancel").onclick = () => $("cu-modal").classList.add("hidden");
$("cu-modal").onclick = (e) => { if (e.target.id === "cu-modal") $("cu-modal").classList.add("hidden"); };
$("cu-save").onclick = async () => {
  try {
    await api("/complaints/" + updatingId, "PATCH", { status: $("cu-status").value, resolution: $("cu-res").value.trim() || undefined });
    $("cu-modal").classList.add("hidden");
    toast("Complaint updated");
    go("complaints");
  } catch (err) { setMsg("cu-msg", err.message, false); }
};

/* ---------------- profile (centered, edit through the three-dots menu) ---------------- */
$("who").onclick = () => go("profile");

async function renderProfile() {
  document.querySelectorAll(".nav-item").forEach((b) => b.classList.remove("active"));
  const me = await api("/me");
  const mine = S.connections.filter((k) => k.customer_id === me.id);
  $("view").innerHTML = `<div class="profile">
    <div class="profile-head">
      <div class="avatar-sq">${esc(initials(me.full_name))}</div>
      <div><h2 id="profile-name">${esc(me.full_name)}</h2><div class="muted">@${esc(me.username)}</div>
        <div style="margin-top:8px"><span class="role">${me.role.toLowerCase()}</span></div></div>
      <button id="p-menu-btn" class="kebab" type="button" aria-label="Edit profile" aria-haspopup="true">&#8942;</button>
      <div id="p-menu" class="menu hidden">
        <button id="menu-name" type="button">Edit name</button>
        <button id="menu-password" type="button">Change password</button>
      </div>
    </div>
    <div class="info-card"><h3>Account information</h3>
      <div class="info-grid">
        <div><span class="k">Full name</span><span class="v">${esc(me.full_name)}</span></div>
        <div><span class="k">Username</span><span class="v" id="p-username">${esc(me.username)}</span></div>
        <div><span class="k">Role</span><span class="v">${me.role[0] + me.role.slice(1).toLowerCase()}</span></div>
        <div><span class="k">${me.role === "ADMIN" ? "Staff ID" : "Customer ID"}</span><span class="v">${me.id}</span></div>
      </div></div>
    ${me.role === "CUSTOMER" ? `<div class="info-card"><h3>My connections</h3>${mine.length ? `<div class="table-wrap" style="border:0"><table><thead><tr><th>Meter</th><th>Type</th><th>Address</th></tr></thead><tbody>${
      mine.map((k) => `<tr><td>${esc(k.meter_no)}</td><td>${k.type[0] + k.type.slice(1).toLowerCase()}</td><td>${esc(k.address)}</td></tr>`).join("")}</tbody></table></div>` : '<span class="muted">No connection has been set up for you yet.</span>'}</div>` : ""}
  </div>`;
  const menu = $("p-menu");
  $("p-menu-btn").onclick = (e) => { e.stopPropagation(); menu.classList.toggle("hidden"); };
  document.addEventListener("click", () => menu.classList.add("hidden"), { once: true });
  $("menu-name").onclick = () => openNameDialog(me);
  $("menu-password").onclick = openPasswordDialog;
}

function openNameDialog(me) {
  $("pn-body").innerHTML = `<label for="p-name">Full name</label><input id="p-name" value="${esc(me.full_name)}" maxlength="80">
    <div id="p-msg" class="form-msg" role="alert" style="margin-top:10px"></div>`;
  $("pn-modal").classList.remove("hidden");
  $("p-name").focus();
}
$("pn-cancel").onclick = () => $("pn-modal").classList.add("hidden");
$("pn-modal").onclick = (e) => { if (e.target.id === "pn-modal") $("pn-modal").classList.add("hidden"); };
$("p-name-btn").onclick = async () => {
  try {
    const d = await api("/me", "PUT", { full_name: $("p-name").value });
    S.name = d.full_name; $("who").textContent = d.full_name;
    try { sessionStorage.setItem("hydrocore", JSON.stringify({ token: S.token, role: S.role, name: S.name, userId: S.userId })); } catch (e) {}
    $("pn-modal").classList.add("hidden");
    toast("Name updated");
    go("profile");
  } catch (err) { setMsg("p-msg", err.message, false); }
};

function openPasswordDialog() {
  $("pw-body").innerHTML = `
    <label for="p-cur">Current password</label><input id="p-cur" type="password" autocomplete="current-password">
    <label for="p-new">New password (at least 6 characters)</label><input id="p-new" type="password" autocomplete="new-password">
    <label for="p-new2">Confirm new password</label><input id="p-new2" type="password" autocomplete="new-password">
    <div id="p-pass-msg" class="form-msg" role="alert" style="margin-top:10px"></div>`;
  $("pw-modal").classList.remove("hidden");
  $("p-cur").focus();
}
$("pw-cancel").onclick = () => $("pw-modal").classList.add("hidden");
$("pw-modal").onclick = (e) => { if (e.target.id === "pw-modal") $("pw-modal").classList.add("hidden"); };
$("p-pass-btn").onclick = async () => {
  if ($("p-new").value !== $("p-new2").value) return setMsg("p-pass-msg", "The new passwords do not match.", false);
  try {
    await api("/me/password", "POST", { current_password: $("p-cur").value, new_password: $("p-new").value });
    $("pw-modal").classList.add("hidden");
    toast("Password changed. Other devices have been signed out.");
  } catch (err) { setMsg("p-pass-msg", err.message, false); }
};

/* ---------------- boot: restore session ---------------- */
(async function boot() {
  try {
    const saved = JSON.parse(sessionStorage.getItem("hydrocore") || "null");
    if (saved && saved.token) {
      S.token = saved.token;
      await api("/me");
      startSession(saved.token, saved.role, saved.name, saved.userId);
    }
  } catch (e) { endSession(); }
})();
