"use strict";
const $ = (id) => document.getElementById(id);
const RUPEE = "₹";
const money = (n) => RUPEE + Number(n).toLocaleString("en-IN", { minimumFractionDigits: 2, maximumFractionDigits: 2 });
const esc = (s) => String(s).replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
const todayISO = () => new Date().toISOString().slice(0, 10);
const round2 = (n) => Math.round(n * 100) / 100;

const S = { token: null, role: null, name: "", userId: null, connections: [], customers: [], bills: [], alerts: [], page: null, billFilter: "ALL" };

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
  try { sessionStorage.setItem("aqua", JSON.stringify({ token, role, name, userId })); } catch (e) {}
  $("auth-screen").classList.add("hidden");
  $("app").classList.remove("hidden");
  $("who").textContent = name;
  $("role-label").textContent = role.toLowerCase();
  buildNav();
  go(S.role === "ADMIN" ? "customers" : "bills");
}

function endSession() {
  S.token = null; S.role = null;
  try { sessionStorage.removeItem("aqua"); } catch (e) {}
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
    ? [["customers", "Customers"], ["readings", "Readings"], ["bills", "Bills"], ["payments", "Payments"], ["complaints", "Complaints"]]
    : [["bills", "My bills"], ["payments", "Payments"], ["complaints", "Complaints"], ["estimator", "Estimate"]];
  $("nav").innerHTML = items.map(([id, label]) => `<button class="nav-item" id="nav-${id}" data-page="${id}" type="button">${label}</button>`).join("");
  $("nav").querySelectorAll(".nav-item").forEach((b) => (b.onclick = () => go(b.dataset.page)));
}

async function go(page) {
  S.page = page;
  document.querySelectorAll(".nav-item").forEach((b) => b.classList.toggle("active", b.dataset.page === page));
  try {
    await loadData();
    await ({ customers: renderCustomers, readings: renderReadings, bills: renderBills, estimator: renderEstimator,
             payments: renderPayments, complaints: renderComplaints, profile: renderProfile })[page]();
  } catch (err) { $("view").innerHTML = `<p>${esc(err.message)}</p>`; }
}

async function loadData() {
  const reqs = [api("/connections"), api("/bills"), api("/alerts")];
  if (S.role === "ADMIN") reqs.push(api("/customers"));
  const [conns, bills, alerts, customers] = await Promise.all(reqs);
  S.connections = conns; S.bills = bills; S.alerts = alerts; S.customers = customers || [];
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
      <td>#${b.id}</td>${admin ? `<td>${esc(connOwner(b.connection_id))}</td>` : ""}<td>${esc(connLabel(b.connection_id))}</td>
      <td>${b.bill_date}</td><td class="num">${b.units} kL</td>
      <td class="num">${money(b.status === "PAID" ? b.total + b.late_fee : b.total)}</td><td>${b.due_date}</td>
      <td class="st">${status(b.status)}</td>
      <td>${!admin && b.status !== "PAID" ? `<button class="btn small pay-btn" data-id="${b.id}" type="button">Pay</button>` : ""}</td></tr>`).join("");

  $("view").innerHTML = `<h2>${admin ? "Bills" : "My bills"}</h2>
    <p class="lead">${admin ? "All bills issued to customers." : "Your water bills. Pay within 15 days of the bill date to avoid a late fee."}</p>
    ${notice}<div class="summary">${summary}</div>
    <div class="toolbar"><label for="bill-filter" style="margin:0">Show</label>
      <select id="bill-filter">${["ALL", "UNPAID", "OVERDUE", "PAID"].map((s) => `<option value="${s}" ${S.billFilter === s ? "selected" : ""}>${s === "ALL" ? "All" : s[0] + s.slice(1).toLowerCase()}</option>`).join("")}</select></div>
    <div class="table-wrap"><table><thead><tr><th>Bill</th>${admin ? "<th>Customer</th>" : ""}<th>Meter</th><th>Date</th><th class="num">Usage</th><th class="num">Amount</th><th>Due</th><th>Status</th><th></th></tr></thead>
      <tbody id="bill-rows">${rows || emptyRow(admin ? 9 : 8, "No bills to show.")}</tbody></table></div>`;
  $("bill-filter").onchange = (e) => { S.billFilter = e.target.value; renderBills(); };
  document.querySelectorAll(".pay-btn").forEach((b) => (b.onclick = () => openPay(+b.dataset.id)));
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
    <p class="lead">Check what a month's usage would cost.</p>
    <div class="form-box">
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
function renderCustomers() {
  const rows = S.customers.map((c) => {
    const conns = S.connections.filter((k) => k.customer_id === c.id);
    return `<tr><td>${c.id}</td><td>${esc(c.full_name)}</td><td>${esc(c.username)}</td>
      <td>${conns.map((k) => esc(k.meter_no)).join(", ") || '<span class="muted">-</span>'}</td>
      <td>${conns.map((k) => k.type[0] + k.type.slice(1).toLowerCase()).join(", ") || ""}</td>
      <td>${conns.map((k) => esc(k.address)).join("; ")}</td></tr>`;
  }).join("");
  $("view").innerHTML = `<div class="page-head"><div><h2>Customers</h2>
    <p class="lead">Registered customers and their water connections.</p></div>
    <button id="new-conn-btn" class="btn primary" type="button">New connection</button></div>
    <div class="table-wrap"><table><thead><tr><th>ID</th><th>Name</th><th>Username</th><th>Meter</th><th>Type</th><th>Address</th></tr></thead>
      <tbody id="customer-rows">${rows || emptyRow(6, "No customers yet.")}</tbody></table></div>`;
  $("new-conn-btn").onclick = openConnDialog;
}

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
function renderReadings() {
  $("view").innerHTML = `<h2>Meter readings</h2>
    <p class="lead">Enter the latest reading, then generate the bill from the last two readings.</p>
    <div class="form-box">
      <label for="m-conn">Connection</label>
      <select id="m-conn"><option value="">Select connection</option>${S.connections.map((c) => `<option value="${c.id}">${esc(c.meter_no)} - ${esc(customerName(c.customer_id))}</option>`).join("")}</select>
      <div class="row2"><div><label for="m-read">Reading (kL)</label><input id="m-read" type="number" min="0" step="0.01" placeholder="e.g. 125"></div>
      <div><label for="m-date">Date</label><input id="m-date" type="date" max="${todayISO()}" value="${todayISO()}"></div></div>
      <div style="display:flex;gap:10px;margin-top:16px"><button id="read-btn" class="btn primary" type="button">Save reading</button>
      <button id="gen-btn" class="btn" type="button">Generate bill</button></div></div>`;
  const connId = () => { const v = $("m-conn").value; if (!v) throw new Error("Select a connection first"); return +v; };
  $("read-btn").onclick = async () => {
    try {
      await api("/readings", "POST", { connection_id: connId(), reading: parseFloat($("m-read").value), read_on: $("m-date").value || undefined });
      toast("Reading saved"); $("m-read").value = "";
    } catch (err) { toast(err.message, "err"); }
  };
  $("gen-btn").onclick = async () => {
    try {
      const d = await api("/bills/generate", "POST", { connection_id: connId() });
      toast(`Bill #${d.id} generated: ${money(d.total)} for ${d.units} kL`);
    } catch (err) { toast(err.message, "err"); }
  };
}

/* ---------------- payments & receipts ---------------- */
const METHODS = { UPI: "UPI", CARD: "Card", NETBANKING: "Net banking", CASH: "Cash" };
let PAYMENTS = [];

async function renderPayments() {
  const admin = S.role === "ADMIN";
  PAYMENTS = await api("/payments");
  const total = round2(PAYMENTS.reduce((s, p) => s + p.amount, 0));
  const fees = round2(PAYMENTS.reduce((s, p) => s + p.late_fee, 0));
  const rows = PAYMENTS.map((p) => `<tr>
      <td>${p.receipt_no}</td><td>${p.paid_on}</td><td>#${p.bill_id}</td>${admin ? `<td>${esc(p.customer_name)}</td>` : ""}
      <td>${esc(p.meter_no)}</td><td>${METHODS[p.method] || p.method}</td>
      <td class="num">${money(p.late_fee)}</td><td class="num">${money(p.amount)}</td>
      <td><button class="btn small receipt-btn" data-id="${p.id}" type="button">Receipt</button></td></tr>`).join("");
  $("view").innerHTML = `<h2>Payments</h2>
    <p class="lead">${admin ? "All payments received." : "Your payment history. Open a receipt to view or print it."}</p>
    <div class="summary"><div><span class="k">Payments</span><span class="v">${PAYMENTS.length}</span></div>
      <div><span class="k">${admin ? "Total collected" : "Total paid"}</span><span class="v">${money(total)}</span></div>
      <div><span class="k">Late fees</span><span class="v">${money(fees)}</span></div></div>
    <div class="table-wrap"><table><thead><tr><th>Receipt</th><th>Date</th><th>Bill</th>${admin ? "<th>Customer</th>" : ""}<th>Meter</th><th>Method</th><th class="num">Late fee</th><th class="num">Amount</th><th></th></tr></thead>
      <tbody id="pay-rows">${rows || emptyRow(admin ? 9 : 8, "No payments yet.")}</tbody></table></div>`;
  document.querySelectorAll(".receipt-btn").forEach((b) => (b.onclick = () => openReceipt(+b.dataset.id)));
}

async function openReceipt(id) {
  try {
    const r = await api("/payments/" + id);
    $("receipt-body").innerHTML = `<div class="receipt-head"><strong>AquaBill - Water Supply &amp; Billing</strong>
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
      <td>#${c.id}</td><td style="white-space:nowrap">${c.created_on}</td>${admin ? `<td>${esc(c.customer_name)}</td>` : ""}
      <td style="white-space:nowrap">${CATEGORY[c.category]}</td><td style="white-space:nowrap">${c.meter_no ? esc(c.meter_no) : '<span class="muted">-</span>'}</td>
      <td class="cell-text">${esc(c.description)}</td><td class="cst">${cstatus(c.status)}</td>
      <td class="cell-text">${c.resolution ? esc(c.resolution) : '<span class="muted">-</span>'}</td>
      ${admin ? `<td>${NEXT[c.status].length ? `<button class="btn small cu-btn" data-id="${c.id}" type="button">Update</button>` : ""}</td>` : ""}</tr>`).join("");
  $("view").innerHTML = `<div class="page-head"><div><h2>Complaints</h2>
      <p class="lead">${admin ? "Complaints raised by customers." : "Report a leak, a billing problem or a supply issue."}</p></div>
      ${admin ? "" : '<button id="new-complaint-btn" class="btn primary" type="button">New complaint</button>'}</div>
    <div class="summary"><div><span class="k">Total</span><span class="v">${COMPLAINTS.length}</span></div>
      <div><span class="k">Open or in progress</span><span class="v">${open}</span></div>
      <div><span class="k">Resolved</span><span class="v">${COMPLAINTS.length - open}</span></div></div>
    <div class="table-wrap"><table><thead><tr><th>ID</th><th>Date</th>${admin ? "<th>Customer</th>" : ""}<th>Type</th><th>Meter</th><th>Description</th><th>Status</th><th>Resolution</th>${admin ? "<th></th>" : ""}</tr></thead>
      <tbody id="complaint-rows">${rows || emptyRow(admin ? 9 : 8, "No complaints.")}</tbody></table></div>`;
  if (admin) document.querySelectorAll(".cu-btn").forEach((b) => (b.onclick = () => openUpdateComplaint(+b.dataset.id)));
  else $("new-complaint-btn").onclick = openNewComplaint;
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
    <label for="cu-status">Move to</label><select id="cu-status">${NEXT[c.status].map((s) => `<option value="${s}">${CSTATUS[s]}</option>`).join("")}</select>
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

/* ---------------- profile & password ---------------- */
$("who").onclick = () => go("profile");

async function renderProfile() {
  document.querySelectorAll(".nav-item").forEach((b) => b.classList.remove("active"));
  const me = await api("/me");
  $("view").innerHTML = `<h2>My profile</h2><p class="lead">Your account details and password.</p>
    <table class="kv"><tr><td>Username</td><td id="p-username">${esc(me.username)}</td></tr>
      <tr><td>Role</td><td>${me.role[0] + me.role.slice(1).toLowerCase()}</td></tr></table>
    <div class="section"><h3>Name</h3>
      <label for="p-name">Full name</label><input id="p-name" value="${esc(me.full_name)}" maxlength="80">
      <button id="p-name-btn" class="btn primary" style="margin-top:14px" type="button">Save name</button>
      <div id="p-msg" class="form-msg" role="status"></div></div>
    <div class="section"><h3>Change password</h3>
      <label for="p-cur">Current password</label><input id="p-cur" type="password" autocomplete="current-password">
      <label for="p-new">New password (at least 6 characters)</label><input id="p-new" type="password" autocomplete="new-password">
      <label for="p-new2">Confirm new password</label><input id="p-new2" type="password" autocomplete="new-password">
      <button id="p-pass-btn" class="btn primary" style="margin-top:14px" type="button">Change password</button>
      <div id="p-pass-msg" class="form-msg" role="status"></div></div>`;
  $("p-name-btn").onclick = async () => {
    try {
      const d = await api("/me", "PUT", { full_name: $("p-name").value });
      S.name = d.full_name; $("who").textContent = d.full_name;
      try { sessionStorage.setItem("aqua", JSON.stringify({ token: S.token, role: S.role, name: S.name, userId: S.userId })); } catch (e) {}
      setMsg("p-msg", "Name updated.", true);
    } catch (err) { setMsg("p-msg", err.message, false); }
  };
  $("p-pass-btn").onclick = async () => {
    if ($("p-new").value !== $("p-new2").value) return setMsg("p-pass-msg", "The new passwords do not match.", false);
    try {
      await api("/me/password", "POST", { current_password: $("p-cur").value, new_password: $("p-new").value });
      ["p-cur", "p-new", "p-new2"].forEach((id) => ($(id).value = ""));
      setMsg("p-pass-msg", "Password changed. Other devices have been signed out.", true);
    } catch (err) { setMsg("p-pass-msg", err.message, false); }
  };
}

/* ---------------- boot: restore session ---------------- */
(async function boot() {
  try {
    const saved = JSON.parse(sessionStorage.getItem("aqua") || "null");
    if (saved && saved.token) {
      S.token = saved.token;
      await api("/me");
      startSession(saved.token, saved.role, saved.name, saved.userId);
    }
  } catch (e) { endSession(); }
})();
