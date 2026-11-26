let appState = null;

const escapeHtml = (value) =>
  String(value ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#39;");

const formatSum = (amount) =>
  Number(amount) === 0
    ? "Bepul"
    : `${Number(amount).toLocaleString("ru-RU").replaceAll(",", " ")} so'm`;

async function api(url, options = {}) {
  const res = await fetch(url, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  const data = await res.json();
  if (!res.ok) {
    throw new Error(data.error || "Xatolik yuz berdi");
  }
  return data;
}

function renderProfileAndServices(state) {
  const { profile, services } = state;
  document.getElementById("bizNicheLabel").textContent = profile.niche_label || "";
  document.getElementById("bizName").textContent = profile.name || "";
  document.getElementById("bizTagline").textContent = profile.tagline || "";
  document.getElementById("bizHours").textContent = `Ish vaqti: ${profile.hours || ""}`;
  document.getElementById("bizAddress").textContent = `Manzil: ${profile.address || ""}`;
  document.getElementById("bizPhone").textContent = `Tel: ${profile.phone || ""}`;

  document.querySelectorAll(".niche-btn").forEach((btn) => {
    btn.classList.toggle("active", btn.dataset.niche === profile.niche);
  });

  const grid = document.getElementById("servicesGrid");
  grid.innerHTML = services
    .map(
      (s) => `
      <div class="service-item">
        <div>
          <strong>${escapeHtml(s.name)}</strong>
          <p>${escapeHtml(s.description)} (${s.duration_min} daq.)</p>
        </div>
        <div class="service-price">
          <strong>${formatSum(s.price_uzs)}</strong>
          <button type="button" class="btn btn-sm btn-primary select-svc-btn" data-id="${s.id}">Tanlash</button>
        </div>
      </div>`
    )
    .join("");

  const select = document.getElementById("serviceSelect");
  select.innerHTML = services
    .map((s) => `<option value="${s.id}">${escapeHtml(s.name)} (${formatSum(s.price_uzs)})</option>`)
    .join("");
}

function renderAdmin(state) {
  const { stats, orders } = state;
  document.getElementById("pendingBadge").textContent = stats.pending_orders;
  document.getElementById("kpiTotal").textContent = stats.total_orders;
  document.getElementById("kpiPending").textContent = stats.pending_orders;
  document.getElementById("kpiRevenue").textContent = formatSum(stats.confirmed_revenue_uzs);
  document.getElementById("kpiSubRevenue").textContent = formatSum(stats.subscription_revenue_uzs);

  const body = document.getElementById("ordersBody");
  if (!orders.length) {
    body.innerHTML = `<tr><td colspan="6" class="muted">Hozircha buyurtmalar yo'q.</td></tr>`;
    return;
  }

  body.innerHTML = orders
    .map(
      (o) => `
      <tr>
        <td>
          <strong>${escapeHtml(o.customer_name)}</strong><br/>
          <small class="muted">${escapeHtml(o.customer_phone)}</small>
        </td>
        <td>
          ${escapeHtml(o.service_name)}
          ${o.notes ? `<br/><small class="muted">${escapeHtml(o.notes)}</small>` : ""}
        </td>
        <td>${escapeHtml(o.preferred_time)}</td>
        <td>${formatSum(o.price_uzs)}</td>
        <td><span class="badge badge-${escapeHtml(o.status)}">${escapeHtml(o.status)}</span></td>
        <td>
          <div style="display:flex;gap:6px;flex-wrap:wrap;">
            <button class="btn btn-sm btn-primary status-btn" data-id="${o.id}" data-status="tasdiqlandi">Tasdiqlash</button>
            <button class="btn btn-sm btn-green status-btn" data-id="${o.id}" data-status="bajarildi">Bajarildi</button>
            <button class="btn btn-sm btn-red status-btn" data-id="${o.id}" data-status="bekor">Bekor</button>
          </div>
        </td>
      </tr>`
    )
    .join("");
}

function renderPricingAndPayments(state) {
  const plansGrid = document.getElementById("plansGrid");
  plansGrid.innerHTML = state.plans
    .map(
      (p) => `
      <div class="plan-card ${p.popular ? "popular" : ""}">
        <div>
          <h3>${escapeHtml(p.name)}</h3>
          <div class="plan-price">${formatSum(p.price_uzs)} <small class="muted">/ ${escapeHtml(p.period)}</small></div>
          <ul>${p.features.map((f) => `<li>${escapeHtml(f)}</li>`).join("")}</ul>
        </div>
        <button class="btn btn-primary checkout-btn" data-plan="${escapeHtml(p.id)}">To'lov havolasi yaratish</button>
      </div>`
    )
    .join("");

  const paymentsBody = document.getElementById("paymentsBody");
  if (!state.payments.length) {
    paymentsBody.innerHTML = `<tr><td colspan="7" class="muted">Hali obuna to'lovlari yaratilmagan.</td></tr>`;
    return;
  }

  paymentsBody.innerHTML = state.payments
    .map(
      (p) => `
      <tr>
        <td><code>${escapeHtml(p.invoice_code)}</code></td>
        <td>${escapeHtml(p.business_name)}</td>
        <td>${escapeHtml(p.plan_name)}</td>
        <td>${escapeHtml(p.provider.toUpperCase())}</td>
        <td>${formatSum(p.amount_uzs)}</td>
        <td><span class="badge badge-${escapeHtml(p.status)}">${escapeHtml(p.status)}</span></td>
        <td>
          ${
            p.status === "kutilmoqda"
              ? `<button class="btn btn-sm btn-green confirm-pay-btn" data-id="${p.id}">To'landi (Demo)</button>`
              : `<span class="muted">Faol</span>`
          }
        </td>
      </tr>`
    )
    .join("");
}

function renderAll(state) {
  appState = state;
  renderProfileAndServices(state);
  renderAdmin(state);
  renderPricingAndPayments(state);
}

function appendChat(role, text) {
  const box = document.getElementById("chatMessages");
  const div = document.createElement("div");
  div.className = `msg ${role}`;
  div.textContent = text;
  box.appendChild(div);
  box.scrollTop = box.scrollHeight;
}

async function sendChatMessage(message) {
  appendChat("user", message);
  try {
    const res = await api("/api/chat", {
      method: "POST",
      body: JSON.stringify({ message }),
    });
    document.getElementById("aiModeLabel").textContent =
      res.mode === "gemini" ? "Gemini AI ulangan" : "Tezkor lokal AI rejimi";
    appendChat("bot", res.reply);
  } catch (err) {
    appendChat("bot", `Xatolik: ${err.message}`);
  }
}

document.addEventListener("DOMContentLoaded", async () => {
  try {
    const state = await api("/api/state");
    renderAll(state);
    appendChat(
      "bot",
      `Assalomu alaykum! Men ${state.profile.name} AI maslahatchisiman. Xizmatlar, narxlar yoki vaqt haqida istalgan savolni bering.`
    );
  } catch (err) {
    alert(`Yuklashda xatolik: ${err.message}`);
  }

  // Tab navigation
  document.querySelectorAll(".tab-btn").forEach((btn) => {
    btn.addEventListener("click", () => {
      document.querySelectorAll(".tab-btn").forEach((b) => b.classList.remove("active"));
      document.querySelectorAll(".tab-panel").forEach((p) => p.classList.remove("active"));
      btn.classList.add("active");
      document.getElementById(`tab-${btn.dataset.tab}`).classList.add("active");
    });
  });

  // Switch demo niche
  document.querySelectorAll(".niche-btn").forEach((btn) => {
    btn.addEventListener("click", async () => {
      const state = await api("/api/niche", {
        method: "POST",
        body: JSON.stringify({ niche: btn.dataset.niche }),
      });
      renderAll(state);
      appendChat("bot", `Shablon yangilandi: ${state.profile.name} (${state.profile.niche_label}).`);
    });
  });

  // Select service shortcut
  document.getElementById("servicesGrid").addEventListener("click", (e) => {
    const btn = e.target.closest(".select-svc-btn");
    if (!btn) return;
    document.getElementById("serviceSelect").value = btn.dataset.id;
    document.getElementById("bookingBox").scrollIntoView({ behavior: "smooth" });
  });

  // Booking form
  document.getElementById("orderForm").addEventListener("submit", async (e) => {
    e.preventDefault();
    const form = e.target;
    const payload = Object.fromEntries(new FormData(form).entries());
    const msgEl = document.getElementById("orderStatusMsg");
    try {
      const res = await api("/api/orders", {
        method: "POST",
        body: JSON.stringify(payload),
      });
      renderAll(res.state);
      form.reset();
      msgEl.textContent = "Buyurtma qabul qilindi! Admin CRM da ko'rishingiz mumkin.";
    } catch (err) {
      msgEl.textContent = err.message;
    }
  });

  // AI chat form & quick prompts
  document.getElementById("chatForm").addEventListener("submit", async (e) => {
    e.preventDefault();
    const input = document.getElementById("chatInput");
    const msg = input.value.trim();
    if (!msg) return;
    input.value = "";
    await sendChatMessage(msg);
  });

  document.querySelectorAll(".chip").forEach((chip) => {
    chip.addEventListener("click", () => sendChatMessage(chip.dataset.prompt));
  });

  // Admin: update order status
  document.getElementById("ordersBody").addEventListener("click", async (e) => {
    const btn = e.target.closest(".status-btn");
    if (!btn) return;
    const res = await api(`/api/orders/${btn.dataset.id}`, {
      method: "PATCH",
      body: JSON.stringify({ status: btn.dataset.status }),
    });
    renderAll(res.state);
  });

  // Admin: add new service
  document.getElementById("serviceForm").addEventListener("submit", async (e) => {
    e.preventDefault();
    const form = e.target;
    const payload = Object.fromEntries(new FormData(form).entries());
    const msgEl = document.getElementById("serviceStatusMsg");
    try {
      const res = await api("/api/services", {
        method: "POST",
        body: JSON.stringify(payload),
      });
      renderAll(res.state);
      form.reset();
      msgEl.textContent = "Yangi xizmat qo'shildi!";
    } catch (err) {
      msgEl.textContent = err.message;
    }
  });

  // Pricing: create Click/Payme invoice
  document.getElementById("plansGrid").addEventListener("click", async (e) => {
    const btn = e.target.closest(".checkout-btn");
    if (!btn) return;
    const provider = document.querySelector("input[name='provider']:checked").value;
    const businessName = document.getElementById("checkoutBizName").value.trim() || appState.profile.name;
    const res = await api("/api/payments/checkout", {
      method: "POST",
      body: JSON.stringify({
        plan_id: btn.dataset.plan,
        provider,
        business_name: businessName,
      }),
    });
    renderAll(res.state);
    const box = document.getElementById("checkoutResult");
    box.classList.remove("hidden");
    box.innerHTML = `
      <strong>Invoice yaratildi: ${escapeHtml(res.payment.invoice_code)} (${escapeHtml(res.payment.provider.toUpperCase())})</strong><br/>
      <small>Rejim: ${escapeHtml(res.mode)}. Haqiqiy kassa ulanganda mijoz quyidagi havolaga yo'naltiriladi:</small><br/>
      <a href="${escapeHtml(res.checkout_url)}" target="_blank" rel="noopener noreferrer" style="color:#8ce9b5;word-break:break-all;">
        ${escapeHtml(res.checkout_url)}
      </a>
    `;
  });

  // Pricing: confirm demo payment
  document.getElementById("paymentsBody").addEventListener("click", async (e) => {
    const btn = e.target.closest(".confirm-pay-btn");
    if (!btn) return;
    const res = await api("/api/payments/confirm", {
      method: "POST",
      body: JSON.stringify({ payment_id: Number(btn.dataset.id) }),
    });
    renderAll(res.state);
  });
});
