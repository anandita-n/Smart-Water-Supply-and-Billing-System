"use strict";
const $ = (id) => document.getElementById(id);
const RUPEE = "₹";
const money = (n) => RUPEE + Number(n).toLocaleString("en-IN", { minimumFractionDigits: 2, maximumFractionDigits: 2 });
const esc = (s) => String(s).replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
const todayISO = () => new Date().toISOString().slice(0, 10);
const round2 = (n) => Math.round(n * 100) / 100;

const ICONS = {
  dashboard: '<svg viewBox="0 0 24 24"><rect x="3" y="3" width="7" height="9"/><rect x="14" y="3" width="7" height="5"/><rect x="14" y="12" width="7" height="9"/><rect x="3" y="16" width="7" height="5"/></svg>',
  bills: '<svg viewBox="0 0 24 24"><path d="M6 2h9l5 5v15H6z"/><path d="M14 2v6h6M9 13h8M9 17h8"/></svg>',
  alerts: '<svg viewBox="0 0 24 24"><path d="M18 8a6 6 0 0 0-12 0c0 7-3 9-3 9h18s-3-2-3-9M13.7 21a2 2 0 0 1-3.4 0"/></svg>',
  calc: '<svg viewBox="0 0 24 24"><rect x="4" y="2" width="16" height="20" rx="2"/><path d="M8 6h8M8 11h2M14 11h2M8 15h2M14 15h2M8 19h2M14 19h2"/></svg>',
  people: '<svg viewBox="0 0 24 24"><circle cx="9" cy="8" r="3.5"/><path d="M2 21a7 7 0 0 1 14 0M17 4.5a3.5 3.5 0 0 1 0 7M22 21a7 7 0 0 0-4-6.3"/></svg>',
  meter: '<svg viewBox="0 0 24 24"><circle cx="12" cy="12" r="9"/><path d="M12 12l4-4M12 5v2M5 12h2M17 12h2"/></svg>',
};

const S = { token: null, role: null, name: "", userId: null, connections: [], customers: [], bills: [], alerts: [], page: "dashboard", billFilter: "ALL" };

/* ---------------- helpers ---------------- */
async function api(path, method = "GET", body) {
  const headers = { "Content-Type": "application/json" };
  if (S.token) headers.Authorization = "Bearer " + S.token;
  const r = await fetch("/api" + path, { method, headers, body: body ? JSON.stringify(body) : undefined });
  const data = await r.json().catch(() => ({}));
  if (!r.ok) {
    if (r.status === 401 && S.token) { endSession(); }
    const d = data.detail;
    let msg = typeof d === "string" ? d : Array.isArray(d) ? d.map((e) => (e.loc ? e.loc[e.loc.length - 1] + ": " : "") + e.msg).join("; ") : "Request failed";
    throw new Error(msg);
  }
  return data;
}

function toast(msg, kind = "") {
  const t = document.createElement("div");
  t.className = "toast " + kind;
  t.textContent = msg;
  $("toast").appendChild(t);
  setTimeout(() => t.remove(), 4200);
}

function setAuthMsg(msg, ok) { const e = $("auth-msg"); e.textContent = msg; e.className = "form-msg " + (ok ? "ok" : "err"); }

function lateFee(bill, on = todayISO()) { return bill.status !== "PAID" && on > bill.due_date ? round2(25 + bill.total * 0.02) : 0; }
function amountDue(bill) { return round2(bill.total + lateFee(bill)); }
function badge(s) { return `<span class="badge ${s}">${s}</span>`; }
function emptyRow(cols, text) { return `<tr><td class="empty" colspan="${cols}">${text}</td></tr>`; }
function monthLabel(iso) { return new Date(iso + "T00:00:00").toLocaleDateString("en-IN", { month: "short", year: "2-digit" }); }
function connLabel(id) { const c = S.connections.find((x) => x.id === id); return c ? c.meter_no : "#" + id; }
function customerName(id) { const c = S.customers.find((x) => x.id === id); return c ? c.full_name : "#" + id; }
function connOwner(connId) { const c = S.connections.find((x) => x.id === connId); return c ? customerName(c.customer_id) : "-"; }

/* ---------------- auth ---------------- */
function showTab(which) {
  const login = which === "login";
  $("login-form").classList.toggle("hidden", !login);
  $("register-form").classList.toggle("hidden", login);
  $("tab-login").classList.toggle("active", login);
  $("tab-register").classList.toggle("active", !login);
  setAuthMsg("", true);
}
$("tab-login").onclick = () => showTab("login");
$("tab-register").onclick = () => showTab("register");

$("login-form").onsubmit = async (e) => {
  e.preventDefault();
  try {
    const d = await api("/auth/login", "POST", { username: $("l-user").value.trim(), password: $("l-pass").value });
    startSession(d.token, d.role, d.full_name, d.user_id);
  } catch (err) { setAuthMsg(err.message, false); }
};

$("register-form").onsubmit = async (e) => {
  e.preventDefault();
  try {
    const d = await api("/auth/register", "POST", { username: $("r-user").value.trim(), password: $("r-pass").value, full_name: $("r-name").value.trim() });
    setAuthMsg("Account created. Your customer id is: " + d.id + ". You can sign in now.", true);
    $("l-user").value = d.username;
  } catch (err) { setAuthMsg(err.message, false); }
};

function startSession(token, role, name, userId) {
  S.token = token; S.role = role; S.name = name; S.userId = userId;
  try { sessionStorage.setItem("aqua", JSON.stringify({ token, role, name, userId })); } catch (e) {}
  $("auth-screen").classList.add("hidden");
  $("app").classList.remove("hidden");
  $("who").textContent = name;
  $("avatar").textContent = (name.trim()[0] || "?").toUpperCase();
  $("role-label").textContent = role.toLowerCase();
  $("today").textContent = new Date().toLocaleDateString("en-IN", { weekday: "long", day: "numeric", month: "long", year: "numeric" });
  buildNav();
  go("dashboard");
}

function endSession() {
  S.token = null; S.role = null;
  try { sessionStorage.removeItem("aqua"); } catch (e) {}
  $("app").classList.add("hidden");
  $("auth-screen").classList.remove("hidden");
  $("l-pass").value = "";
  showTab("login");
}

$("logout-btn").onclick = async () => {
  try { await api("/auth/logout", "POST"); } catch (e) {}
  endSession();
};

/* ---------------- navigation ---------------- */
function buildNav() {
  const items = S.role === "ADMIN"
    ? [["dashboard", "Overview", "dashboard"], ["customers", "Customers", "people"], ["readings", "Meter readings", "meter"], ["bills", "Bills", "bills"], ["alerts", "Alerts", "alerts"], ["estimator", "Bill estimator", "calc"]]
    : [["dashboard", "Dashboard", "dashboard"], ["bills", "My bills", "bills"], ["alerts", "Alerts", "alerts"], ["estimator", "Bill estimator", "calc"]];
  $("nav").innerHTML = items.map(([id, label, icon]) => `<button class="nav-item" id="nav-${id}" data-page="${id}" type="button">${ICONS[icon]}<span>${label}</span></button>`).join("");
  $("nav").querySelectorAll(".nav-item").forEach((b) => (b.onclick = () => go(b.dataset.page)));
}

const TITLES = { dashboard: null, customers: "Customers & connections", readings: "Meter readings", bills: null, alerts: "Alerts", estimator: "Bill estimator" };

async function go(page) {
  S.page = page;
  document.querySelectorAll(".nav-item").forEach((b) => b.classList.toggle("active", b.dataset.page === page));
  $("page-title").textContent = TITLES[page] || (page === "bills" ? (S.role === "ADMIN" ? "All bills" : "My bills") : S.role === "ADMIN" ? "Overview" : "Dashboard");
  $("view").innerHTML = '<p class="muted">Loading...</p>';
  try {
    await loadData();
    ({ dashboard: renderDashboard, customers: renderCustomers, readings: renderReadings, bills: renderBills, alerts: renderAlerts, estimator: renderEstimator })[page]();
  } catch (err) { $("view").innerHTML = `<div class="card">${esc(err.message)}</div>`; }
}

async function loadData() {
  const reqs = [api("/connections"), api("/bills"), api("/alerts")];
  if (S.role === "ADMIN") reqs.push(api("/customers"));
  const [conns, bills, alerts, customers] = await Promise.all(reqs);
  S.connections = conns; S.bills = bills; S.alerts = alerts; S.customers = customers || [];
}

/* ---------------- dashboard ---------------- */
function usageChart(bills) {
  const last = bills.slice(-6);
  if (!last.length) return '<div class="empty">No bills yet. Usage will appear here after your first bill.</div>';
  const max = Math.max(...last.map((b) => b.units), 1);
  return `<div class="chart">${last.map((b) => `<div class="bar-col"><div class="bar-val">${b.units}</div>
    <div class="bar" style="height:${Math.max((b.units / max) * 130, 3)}px"></div><div class="bar-lbl">${monthLabel(b.bill_date)}</div></div>`).join("")}</div>`;
}

function billsTable(bills, { admin = false, actions = true } = {}) {
  const head = `<tr><th>Bill</th>${admin ? "<th>Customer</th>" : ""}<th>Meter</th><th>Bill date</th><th class="num">Usage</th><th class="num">Amount</th><th>Due</th><th>Status</th>${actions ? "<th></th>" : ""}</tr>`;
  const rows = bills.map((b) => `<tr>
    <td>#${b.id}</td>${admin ? `<td>${esc(connOwner(b.connection_id))}</td>` : ""}<td>${esc(connLabel(b.connection_id))}</td><td>${b.bill_date}</td>
    <td class="num">${b.units} kL</td><td class="num">${money(b.status === "PAID" ? b.total + b.late_fee : b.total)}</td><td>${b.due_date}</td>
    <td class="status">${badge(b.status)}</td>
    ${actions ? `<td>${b.status !== "PAID" ? `<button class="btn btn-primary btn-small pay-btn" data-id="${b.id}" type="button">Pay</button>` : ""}</td>` : ""}</tr>`).join("");
  return `<div class="table-wrap"><table><thead>${head}</thead><tbody id="bill-rows">${rows || emptyRow(9, "No bills to show.")}</tbody></table></div>`;
}

function bindPayButtons() { document.querySelectorAll(".pay-btn").forEach((b) => (b.onclick = () => openPay(+b.dataset.id))); }

function renderDashboard() {
  const v = $("view");
  const unpaid = S.bills.filter((b) => b.status !== "PAID");
  const overdue = S.bills.filter((b) => b.status === "OVERDUE");
  const outstanding = round2(unpaid.reduce((s, b) => s + amountDue(b), 0));
  const alertBanner = S.alerts.length ? `<div class="banner bad">Heads up: ${S.alerts.length} high-usage alert${S.alerts.length > 1 ? "s" : ""}. Check for leaks.</div>` : "";

  if (S.role === "ADMIN") {
    const billed = round2(S.bills.reduce((s, b) => s + b.total, 0));
    const collected = round2(S.bills.filter((b) => b.status === "PAID").reduce((s, b) => s + b.total + b.late_fee, 0));
    v.innerHTML = `${alertBanner}
      <div class="grid-stats">
        <div class="stat"><div class="label">Customers</div><div class="value">${S.customers.length}</div><div class="sub">${S.connections.length} connections</div></div>
        <div class="stat"><div class="label">Total billed</div><div class="value">${money(billed)}</div><div class="sub">${S.bills.length} bills</div></div>
        <div class="stat good"><div class="label">Collected</div><div class="value">${money(collected)}</div><div class="sub">${S.bills.filter((b) => b.status === "PAID").length} paid</div></div>
        <div class="stat warn"><div class="label">Outstanding</div><div class="value">${money(outstanding)}</div><div class="sub">${unpaid.length} unpaid, ${overdue.length} overdue</div></div>
      </div>
      <div class="card"><h3>Recent bills</h3>${billsTable(S.bills.slice(-6).reverse(), { admin: true, actions: false })}</div>`;
    return;
  }
  const last = S.bills[S.bills.length - 1];
  v.innerHTML = `${alertBanner}
    <div class="grid-stats">
      <div class="stat ${outstanding ? "warn" : "good"}"><div class="label">Amount due</div><div class="value">${money(outstanding)}</div><div class="sub">${unpaid.length ? unpaid.length + " bill(s) pending" : "All paid, thank you!"}</div></div>
      <div class="stat ${overdue.length ? "bad" : ""}"><div class="label">Overdue bills</div><div class="value">${overdue.length}</div><div class="sub">Late fee applies after due date</div></div>
      <div class="stat"><div class="label">Last usage</div><div class="value">${last ? last.units + " kL" : "-"}</div><div class="sub">${last ? "Billed " + last.bill_date : "No bills yet"}</div></div>
      <div class="stat"><div class="label">Connections</div><div class="value">${S.connections.length}</div><div class="sub">${S.connections.map((c) => esc(c.meter_no)).join(", ") || "None yet"}</div></div>
    </div>
    <div class="two-col">
      <div class="card"><h3>Water usage (last 6 bills, kL)</h3>${usageChart(S.bills)}</div>
      <div class="card"><h3>Pending bills</h3>${unpaid.length ? unpaid.map((b) => `<div style="display:flex;justify-content:space-between;align-items:center;padding:10px 0;border-bottom:1px solid var(--line)">
          <div><strong>Bill #${b.id}</strong> ${badge(b.status)}<br><small class="muted">Due ${b.due_date}</small></div>
          <div style="text-align:right"><strong>${money(amountDue(b))}</strong><br><button class="btn btn-primary btn-small pay-btn" data-id="${b.id}" type="button">Pay</button></div></div>`).join("") : '<div class="empty">Nothing to pay right now.</div>'}</div>
    </div>`;
  bindPayButtons();
}

/* ---------------- bills ---------------- */
function renderBills() {
  const list = S.billFilter === "ALL" ? S.bills : S.bills.filter((b) => b.status === S.billFilter);
  $("view").innerHTML = `<div class="card">
    <div class="toolbar"><label for="bill-filter" style="margin:0">Show</label>
      <select id="bill-filter">${["ALL", "UNPAID", "OVERDUE", "PAID"].map((s) => `<option value="${s}" ${S.billFilter === s ? "selected" : ""}>${s === "ALL" ? "All bills" : s[0] + s.slice(1).toLowerCase()}</option>`).join("")}</select>
      <button id="refresh-btn" class="btn btn-ghost btn-small" type="button">Refresh</button></div>
    ${billsTable(list.slice().reverse(), { admin: S.role === "ADMIN" })}</div>`;
  $("bill-filter").onchange = (e) => { S.billFilter = e.target.value; renderBills(); };
  $("refresh-btn").onclick = () => go("bills");
  bindPayButtons();
}

/* ---------------- payment dialog ---------------- */
let payingId = null;
function openPay(id) {
  const b = S.bills.find((x) => x.id === id);
  if (!b) return;
  payingId = id;
  const fee = lateFee(b);
  $("pay-body").innerHTML = `<p class="muted" style="margin:0">Bill #${b.id} for meter ${esc(connLabel(b.connection_id))}, ${b.units} kL used.</p>
    <table class="breakdown">
      <tr><td>Water charge</td><td>${money(b.water_charge)}</td></tr>
      <tr><td>Fixed charge</td><td>${money(b.fixed_charge)}</td></tr>
      <tr><td>Late fee ${fee ? "(paid after " + b.due_date + ")" : ""}</td><td>${money(fee)}</td></tr>
      <tr class="total"><td>Total payable</td><td id="pay-total">${money(amountDue(b))}</td></tr></table>`;
  $("pay-modal").classList.remove("hidden");
}
function closePay() { $("pay-modal").classList.add("hidden"); payingId = null; }
$("confirm-cancel").onclick = closePay;
$("pay-modal").onclick = (e) => { if (e.target.id === "pay-modal") closePay(); };
$("confirm-ok").onclick = async () => {
  const b = S.bills.find((x) => x.id === payingId);
  if (!b) return;
  try {
    await api(`/bills/${b.id}/pay`, "POST", { amount: amountDue(b) });
    toast("Payment successful for bill #" + b.id, "ok");
    closePay();
    go(S.page);
  } catch (err) { toast(err.message, "err"); }
};

/* ---------------- alerts ---------------- */
function renderAlerts() {
  $("view").innerHTML = `<div class="card">${S.alerts.length ? S.alerts.slice().reverse().map((a) => `<div class="alert-item"><div>&#9888;</div>
    <div><strong>${esc(a.message)}</strong><small>Meter ${esc(connLabel(a.connection_id))} &middot; ${a.created_on}</small></div></div>`).join("")
    : '<div class="empty">No alerts. Your usage looks normal.</div>'}</div>`;
}

/* ---------------- estimator ---------------- */
function renderEstimator() {
  $("view").innerHTML = `<div class="two-col">
    <div class="card"><h3>Estimate a monthly bill</h3>
      <div class="form-grid"><div><label for="c-units">Water used (kL)</label><input id="c-units" type="number" min="0" step="0.01" placeholder="e.g. 25"></div>
      <div><label for="c-type">Connection type</label><select id="c-type"><option>DOMESTIC</option><option>COMMERCIAL</option></select></div></div>
      <button id="calc-btn" class="btn btn-primary" style="margin-top:16px" type="button">Calculate</button>
      <div id="calc-out" class="form-msg" role="status"></div></div>
    <div class="card"><h3>Tariff slabs (per month)</h3>
      <table class="slab-table"><thead><tr><th>Usage</th><th class="num">Rate / kL</th></tr></thead>
      <tbody><tr><td>0 - 10 kL</td><td class="num">${money(5)}</td></tr><tr><td>10 - 20 kL</td><td class="num">${money(8)}</td></tr>
      <tr><td>20 - 30 kL</td><td class="num">${money(12)}</td></tr><tr><td>Above 30 kL</td><td class="num">${money(20)}</td></tr></tbody></table>
      <p class="muted" style="font-size:13px">Commercial water charge is 1.5x. Fixed charge: ${money(50)} domestic, ${money(150)} commercial. Pay within 15 days to avoid a late fee of ${money(25)} + 2%.</p></div></div>`;
  $("calc-btn").onclick = async () => {
    const out = $("calc-out");
    try {
      const d = await api(`/tariff/calculate?units=${encodeURIComponent($("c-units").value)}&type=${$("c-type").value}`);
      out.className = "form-msg ok";
      out.innerHTML = `Water charge: ${money(d.water_charge)} &nbsp;|&nbsp; Fixed: ${money(d.fixed_charge)} &nbsp;|&nbsp; <span style="font-size:18px">Total: ${money(d.total)}</span>`;
      out.dataset.total = d.total;
    } catch (err) { out.className = "form-msg err"; out.textContent = err.message; }
  };
}

/* ---------------- admin: customers ---------------- */
function renderCustomers() {
  const rows = S.customers.map((c) => {
    const conns = S.connections.filter((k) => k.customer_id === c.id);
    return `<tr><td>${c.id}</td><td>${esc(c.full_name)}</td><td>${esc(c.username)}</td><td>${conns.map((k) => esc(k.meter_no) + " (" + k.type.toLowerCase() + ")").join(", ") || '<span class="muted">none</span>'}</td></tr>`;
  }).join("");
  $("view").innerHTML = `<div class="two-col">
    <div class="card"><h3>Customers</h3><div class="table-wrap"><table><thead><tr><th>ID</th><th>Name</th><th>Username</th><th>Connections</th></tr></thead>
      <tbody id="customer-rows">${rows || emptyRow(4, "No customers have registered yet.")}</tbody></table></div></div>
    <div class="card"><h3>New connection</h3>
      <label for="a-cust">Customer</label><select id="a-cust"><option value="">Select customer...</option>${S.customers.map((c) => `<option value="${c.id}">${esc(c.full_name)} (${esc(c.username)})</option>`).join("")}</select>
      <label for="a-meter">Meter number</label><input id="a-meter" placeholder="e.g. MTR-1001">
      <label for="a-type">Type</label><select id="a-type"><option>DOMESTIC</option><option>COMMERCIAL</option></select>
      <label for="a-addr">Address</label><input id="a-addr" placeholder="Service address">
      <button id="conn-btn" class="btn btn-primary btn-block" type="button">Create connection</button></div></div>`;
  $("conn-btn").onclick = async () => {
    try {
      await api("/connections", "POST", { customer_id: +$("a-cust").value, meter_no: $("a-meter").value.trim(), type: $("a-type").value, address: $("a-addr").value.trim() });
      toast("Connection created", "ok");
      go("customers");
    } catch (err) { toast(err.message, "err"); }
  };
}

/* ---------------- admin: readings ---------------- */
function renderReadings() {
  $("view").innerHTML = `<div class="card" style="max-width:620px"><h3>Record a meter reading</h3>
    <p class="muted" style="margin-top:-6px">Add the reading, then generate the bill from the last two readings.</p>
    <label for="m-conn">Connection</label>
    <select id="m-conn"><option value="">Select connection...</option>${S.connections.map((c) => `<option value="${c.id}">${esc(c.meter_no)} - ${esc(customerName(c.customer_id))} (${c.type.toLowerCase()})</option>`).join("")}</select>
    <div class="form-grid"><div><label for="m-read">Meter reading (kL)</label><input id="m-read" type="number" min="0" step="0.01" placeholder="e.g. 125"></div>
    <div><label for="m-date">Reading date</label><input id="m-date" type="date" max="${todayISO()}" value="${todayISO()}"></div></div>
    <div style="display:flex;gap:10px;margin-top:18px"><button id="read-btn" class="btn btn-primary" type="button">Save reading</button>
    <button id="gen-btn" class="btn btn-ghost" type="button">Generate bill</button></div></div>`;
  const connId = () => { const v = $("m-conn").value; if (!v) throw new Error("Select a connection first"); return +v; };
  $("read-btn").onclick = async () => {
    try {
      await api("/readings", "POST", { connection_id: connId(), reading: parseFloat($("m-read").value), read_on: $("m-date").value || undefined });
      toast("Reading saved", "ok"); $("m-read").value = "";
    } catch (err) { toast(err.message, "err"); }
  };
  $("gen-btn").onclick = async () => {
    try {
      const d = await api("/bills/generate", "POST", { connection_id: connId() });
      toast(`Bill #${d.id} generated: ${money(d.total)} for ${d.units} kL`, "ok");
    } catch (err) { toast(err.message, "err"); }
  };
}

/* ---------------- boot: restore session ---------------- */
(async function boot() {
  $("today").textContent = "";
  try {
    const saved = JSON.parse(sessionStorage.getItem("aqua") || "null");
    if (saved && saved.token) {
      S.token = saved.token;
      await api("/me");
      startSession(saved.token, saved.role, saved.name, saved.userId);
    }
  } catch (e) { endSession(); }
})();
