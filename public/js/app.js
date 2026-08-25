const API_BASE = (location.hostname === "localhost" || location.hostname === "127.0.0.1")
  ? "http://127.0.0.1:8000/api/v1"
  : "/api/v1";

function getToken() { return localStorage.getItem("token"); }
function setToken(token) { localStorage.setItem("token", token); }
function clearToken() { localStorage.removeItem("token"); }
function isLoggedIn() { return !!getToken(); }

function headers() {
  const h = { "Content-Type": "application/json" };
  const token = getToken();
  if (token) h["Authorization"] = `Bearer ${token}`;
  return h;
}

async function api(method, path, body = null) {
  const opts = { method, headers: headers() };
  if (body) opts.body = JSON.stringify(body);
  
  try {
    const res = await fetch(`${API_BASE}${path}`, opts);
    const data = await res.json();
    if (!res.ok) throw new Error(data.detail || "Request failed");
    return data;
  } catch (err) {
    if (err.message === "Failed to fetch") throw new Error("Server not reachable. Check backend is running.");
    throw err;
  }
}

function showMsg(id, msg, show = true) {
  const el = document.getElementById(id);
  if (!el) return;
  el.textContent = msg;
  el.className = show ? (id.includes("error") ? "error-msg show" : "success-msg show") : "";
}

function hideMsg(id) { showMsg(id, "", false); }

function showToast(msg) {
  const t = document.getElementById("toast");
  t.textContent = msg;
  t.classList.add("show");
  setTimeout(() => t.classList.remove("show"), 3000);
}

function formatMoney(n) { return "KSH " + Number(n).toLocaleString(); }

function showPage(id) {
  document.querySelectorAll(".page").forEach(p => p.classList.remove("active"));
  document.getElementById(id).classList.add("active");

  const navItems = document.querySelectorAll(".nav-item");
  navItems.forEach(n => n.classList.remove("active"));

  const navMap = {
    "page-home": "nav-home",
    "page-account": "nav-account",
    "page-packages": "nav-invest",
    "page-earnings": "nav-earnings",
    "page-team": "nav-team",
  };
  const navId = navMap[id];
  if (navId) document.getElementById(navId)?.classList.add("active");

  const authPages = ["page-login", "page-register", "page-otp"];
  const nav = document.querySelector(".bottom-nav");
  const topbar = document.querySelector(".topbar");
  if (authPages.includes(id)) {
    if (nav) nav.style.display = "none";
    if (topbar) topbar.style.display = "none";
  } else {
    if (nav) nav.style.display = "flex";
    if (topbar) topbar.style.display = "flex";
  }

  window.scrollTo(0, 0);
}

async function loadAccount() {
  try {
    const [daily, summary, profile, team] = await Promise.all([
      api("GET", "/earnings/daily"),
      api("GET", "/earnings/summary"),
      api("GET", "/auth/profile"),
      api("GET", "/referrals/my-team"),
    ]);

    document.getElementById("today-earning").textContent = formatMoney(daily.today_earning);

    const claimBtn = document.getElementById("claim-btn");
    if (daily.earning_claimed) {
      claimBtn.textContent = "Claimed Today";
      claimBtn.disabled = true;
    } else {
      claimBtn.textContent = "Claim Now";
      claimBtn.disabled = !daily.today_earning;
    }

    document.getElementById("total-earnings").textContent = formatMoney(summary.total_earned);
    document.getElementById("referral-count").textContent = team.total_invites;
    document.getElementById("user-phone").textContent = profile.user.phone;

    if (profile.user.phone === "0712345678" || profile.user.is_admin) {
      document.getElementById("admin-menu-link").style.display = "block";
    }

    const pkgContainer = document.getElementById("active-packages");
    pkgContainer.innerHTML = "";
    if (daily.active_packages.length === 0) {
      pkgContainer.innerHTML = '<div class="empty-state"><div class="icon">📦</div><p>No active packages</p></div>';
    } else {
      daily.active_packages.forEach(pkg => {
        const pct = pkg.days_total ? Math.round((pkg.days_completed / pkg.days_total) * 100) : 0;
        pkgContainer.innerHTML += `
          <div class="card" style="margin-bottom:8px;">
            <div style="display:flex;justify-content:space-between;margin-bottom:8px;">
              <strong>${pkg.package_name}</strong>
              <span class="badge badge-active">Day ${pkg.days_completed}/${pkg.days_total}</span>
            </div>
            <div class="progress-bar-container">
              <div class="progress-bar" style="width:${pct}%"></div>
            </div>
            <div style="display:flex;justify-content:space-between;margin-top:8px;font-size:13px;color:var(--text-light);">
              <span>Invested: ${formatMoney(pkg.invested)}</span>
              <span>Earned: ${formatMoney(pkg.earned_so_far)}</span>
            </div>
          </div>`;
      });
    }

    document.getElementById("referral-bonus-dash").textContent = formatMoney(
      profile.user.referral_bonus
    );
  } catch (err) {
    showToast(err.message);
  }
}

function loadHome() {
  if (isLoggedIn()) {
    const phone = localStorage.getItem("phone") || "";
    document.getElementById("user-phone").textContent = phone;
  } else {
    document.getElementById("user-phone").textContent = "";
  }
  setTimeout(checkVideo, 1000);
}

function checkVideo() {
  const video = document.getElementById("home-promo-video");
  if (!video) return;
  video.addEventListener("error", showVideoFallback);
  setTimeout(() => {
    if (video.readyState < 2) showVideoFallback();
  }, 3000);
}

function showVideoFallback() {
  const fallback = document.getElementById("video-fallback");
  const overlay = document.getElementById("video-play-overlay");
  if (fallback) fallback.classList.add("show");
  if (overlay) overlay.style.display = "none";
}

function hideVideoFallback() {
  const fallback = document.getElementById("video-fallback");
  const overlay = document.getElementById("video-play-overlay");
  if (fallback) fallback.classList.remove("show");
  if (overlay) overlay.style.display = "flex";
}

function tryPlayVideo() {
  const video = document.getElementById("home-promo-video");
  if (!video) return;
  video.play().then(() => {
    document.getElementById("video-play-overlay").style.display = "none";
  }).catch(() => {
    showVideoFallback();
  });
}

function logout() {
  clearToken();
  localStorage.removeItem("phone");
  showPage("page-home");
  document.querySelector(".bottom-nav").style.display = "flex";
  document.querySelector(".topbar").style.display = "flex";
}

async function claimEarning() {
  const btn = document.getElementById("claim-btn");
  btn.disabled = true;
  btn.textContent = "Claiming...";

  try {
    const daily = await api("GET", "/earnings/daily");
    const claimable = daily.active_packages.find(p => p.next_earning_due);
    if (!claimable) throw new Error("No earnings to claim");

    const result = await api("POST", "/earnings/claim", { deposit_id: claimable.deposit_id });
    showToast(result.message);
    loadAccount();
  } catch (err) {
    showToast(err.message);
    btn.disabled = false;
    btn.textContent = "Claim Now";
  }
}

async function loadPackages() {
  try {
    const data = await api("GET", "/packages/list");
    const container = document.getElementById("packages-list");
    container.innerHTML = "";

    data.packages.forEach(pkg => {
      const isVip = pkg.is_increasing;
      container.innerHTML += `
        <div class="package-card" onclick="selectPackage('${pkg.id}', '${pkg.name}', ${pkg.amount})">
          <div class="pkg-header">
            <span class="pkg-name">${pkg.name}</span>
            <span class="pkg-badge ${isVip ? 'vip' : ''}">${isVip ? 'VIP' : 'Standard'}</span>
          </div>
          <div class="pkg-details">
            <div class="pkg-detail">Invest: <span>${formatMoney(pkg.amount)}</span></div>
            <div class="pkg-detail">Return: <span>${pkg.total_return ? formatMoney(pkg.total_return) : 'Progressive'}</span></div>
            <div class="pkg-detail">Daily: <span>${pkg.daily_bonus ? formatMoney(pkg.daily_bonus) : 'Increasing'}</span></div>
            <div class="pkg-detail">Days: <span>${pkg.duration_days || 'Variable'}</span></div>
          </div>
        </div>`;
    });
  } catch (err) {
    showToast(err.message);
  }
}

let selectedPkg = null;

function selectPackage(id, name, amount) {
  selectedPkg = { id, name, amount: parseFloat(amount) };
  document.querySelectorAll(".package-card").forEach(c => c.classList.remove("selected"));
  event.currentTarget.classList.add("selected");
  document.getElementById("modal-amount").textContent = formatMoney(selectedPkg.amount);
  document.getElementById("deposit-amount-input").value = selectedPkg.amount;
  hideMsg("deposit-error");
  document.getElementById("invest-modal").classList.add("show");
}

function validateDepositAmount() {
  if (!selectedPkg) return;
  const depositAmount = parseFloat(document.getElementById("deposit-amount-input").value) || 0;
  const pkgAmount = selectedPkg.amount;
  const errEl = document.getElementById("deposit-error");

  if (depositAmount > 0 && depositAmount < pkgAmount) {
    showMsg("deposit-error", `Deposit must be at least ${formatMoney(pkgAmount)} for ${selectedPkg.name}`);
    return false;
  } else {
    hideMsg("deposit-error");
    return true;
  }
}

function closeModal(id) {
  document.getElementById(id).classList.remove("show");
}

async function confirmInvest() {
  if (!selectedPkg) return;

  const depositAmount = parseFloat(document.getElementById("deposit-amount-input").value) || 0;

  if (!depositAmount || depositAmount <= 0) {
    showMsg("deposit-error", "Enter your deposit amount");
    return;
  }

  if (depositAmount < selectedPkg.amount) {
    showMsg("deposit-error", `Deposit must be at least ${formatMoney(selectedPkg.amount)} for ${selectedPkg.name}. You entered ${formatMoney(depositAmount)}.`);
    return;
  }

  const btn = document.getElementById("confirm-invest-btn");
  btn.disabled = true;
  btn.innerHTML = '<div class="spinner"></div>';

  try {
    const result = await api("POST", "/deposits/create", {
      package_id: selectedPkg.id,
      amount: depositAmount,
      payment_method: "manual",
    });
    closeModal("invest-modal");
    showToast(result.message);
    loadAccount();
  } catch (err) {
    showToast(err.message);
  } finally {
    btn.disabled = false;
    btn.textContent = "Confirm & Invest";
  }
}

async function loadTeam() {
  try {
    const data = await api("GET", "/referrals/my-team");
    const container = document.getElementById("team-list");
    const codeData = await api("GET", "/referrals/code");

    document.getElementById("referral-code").textContent = codeData.referral_code;
    document.getElementById("referral-link").value = codeData.referral_link;
    document.getElementById("team-count").textContent = data.total_invites;

    container.innerHTML = "";
    if (data.team.length === 0) {
      container.innerHTML = '<div class="empty-state"><div class="icon">👥</div><p>No referrals yet. Share your code!</p></div>';
      return;
    }

    data.team.forEach(member => {
      const initial = member.phone.slice(-2);
      container.innerHTML += `
        <div class="referral-item">
          <div class="referral-avatar">${initial}</div>
          <div class="referral-info">
            <div class="name">${member.full_name || member.phone}</div>
            <div class="detail">${member.deposit_amount ? "Deposited " + formatMoney(member.deposit_amount) : "Pending"}</div>
          </div>
          <span class="badge ${member.status === 'active' ? 'badge-active' : 'badge-pending'}">${member.status}</span>
        </div>`;
    });
  } catch (err) {
    showToast(err.message);
  }
}

function copyReferral() {
  const link = document.getElementById("referral-link");
  link.select();
  navigator.clipboard.writeText(link.value);
  showToast("Referral link copied!");
}

async function loadEarnings() {
  try {
    const [history, summary] = await Promise.all([
      api("GET", "/earnings/history"),
      api("GET", "/earnings/summary"),
    ]);

    document.getElementById("earned-total").textContent = formatMoney(summary.total_earned);
    document.getElementById("earned-pending").textContent = formatMoney(summary.pending_amount);

    const container = document.getElementById("earnings-list");
    container.innerHTML = "";

    if (history.earnings.length === 0) {
      container.innerHTML = '<div class="empty-state"><div class="icon">💰</div><p>No earnings yet</p></div>';
      return;
    }

    history.earnings.slice(0, 30).forEach(e => {
      const date = new Date(e.due_date).toLocaleDateString();
      container.innerHTML += `
        <div class="deposit-history-item">
          <div>
            <div style="font-weight:600;">Day ${e.day_number}</div>
            <div style="font-size:12px;color:var(--text-light);">${date}</div>
          </div>
          <div style="text-align:right;">
            <div style="font-weight:600;color:var(--secondary);">+${formatMoney(e.amount)}</div>
            <span class="badge ${e.status === 'claimed' ? 'badge-active' : 'badge-pending'}">${e.status}</span>
          </div>
        </div>`;
    });
  } catch (err) {
    showToast(err.message);
  }
}

async function loadDeposits() {
  try {
    const data = await api("GET", "/deposits/history");
    const container = document.getElementById("deposits-list");
    container.innerHTML = "";

    if (data.deposits.length === 0) {
      container.innerHTML = '<div class="empty-state"><div class="icon">💳</div><p>No deposits yet</p></div>';
      return;
    }

    data.deposits.forEach(d => {
      container.innerHTML += `
        <div class="deposit-history-item">
          <div>
            <div style="font-weight:600;">${d.package_name}</div>
            <div style="font-size:12px;color:var(--text-light);">${d.reference}</div>
          </div>
          <div style="text-align:right;">
            <div style="font-weight:600;">${formatMoney(d.amount)}</div>
            <span class="badge badge-${d.status}">${d.status}</span>
          </div>
        </div>`;
    });
  } catch (err) {
    showToast(err.message);
  }
}

let feedbackImageData = null;

function previewFeedbackImage(event) {
  const file = event.target.files[0];
  if (!file) return;
  feedbackImageData = file;
  const reader = new FileReader();
  reader.onload = function(e) {
    document.getElementById("feedback-preview-img").src = e.target.result;
    document.getElementById("feedback-preview").style.display = "block";
  };
  reader.readAsDataURL(file);
}

function clearFeedbackImage() {
  feedbackImageData = null;
  document.getElementById("feedback-image").value = "";
  document.getElementById("feedback-preview").style.display = "none";
}

async function submitFeedback() {
  const msg = document.getElementById("feedback-msg").value.trim();
  if (!msg && !feedbackImageData) return showToast("Write something or add a photo");

  try {
    const formData = new FormData();
    if (msg) formData.append("message", msg);
    if (feedbackImageData) formData.append("image", feedbackImageData);

    const res = await fetch(`${API_BASE}/feedback/create`, {
      method: "POST",
      headers: { "Authorization": `Bearer ${getToken()}` },
      body: formData,
    });
    const result = await res.json();
    if (!res.ok) throw new Error(result.detail || "Failed");

    document.getElementById("feedback-msg").value = "";
    clearFeedbackImage();
    showToast("Posted!");
    loadFeed();
  } catch (err) {
    showToast(err.message);
  }
}

async function loadFeed() {
  try {
    const data = await api("GET", "/feedback/feed");
    const container = document.getElementById("feed-list");
    container.innerHTML = "";

    if (data.feedbacks.length === 0) {
      container.innerHTML = '<div class="empty-state"><div class="icon">💬</div><p>No posts yet. Be the first!</p></div>';
      return;
    }

    data.feedbacks.forEach(f => {
      const timeAgo = getTimeAgo(f.created_at);
      const imageHtml = f.image_path
        ? `<img src="${f.image_path.startsWith('http') ? f.image_path : (location.hostname === 'localhost' || location.hostname === '127.0.0.1' ? 'http://127.0.0.1:8000' : '') + f.image_path}" style="width:100%;max-height:300px;object-fit:cover;border-radius:8px;margin-top:8px;" loading="lazy">`
        : "";

      container.innerHTML += `
        <div class="feed-card">
          <div class="feed-header">
            <div class="feed-avatar">${f.user_display.slice(-2)}</div>
            <div>
              <div class="feed-user">${f.user_display}</div>
              <div class="feed-time">${timeAgo}</div>
            </div>
          </div>
          ${f.message ? `<div class="feed-message">${escapeHtml(f.message)}</div>` : ""}
          ${imageHtml}
          <div class="feed-actions">
            <button class="love-btn ${f.has_loved ? 'loved' : ''}" onclick="toggleLove('${f.id}', this)">
              <span class="love-icon">${f.has_loved ? '❤️' : '🤍'}</span>
              <span class="love-count">${f.love_count || 0}</span>
            </button>
          </div>
        </div>`;
    });
  } catch (err) {
    showToast(err.message);
  }
}

async function toggleLove(feedbackId, btn) {
  try {
    const result = await api("POST", `/feedback/love/${feedbackId}`);
    const icon = btn.querySelector(".love-icon");
    const count = btn.querySelector(".love-count");

    if (result.loved) {
      btn.classList.add("loved");
      icon.textContent = "❤️";
    } else {
      btn.classList.remove("loved");
      icon.textContent = "🤍";
    }
    count.textContent = result.love_count;
  } catch (err) {
    showToast(err.message);
  }
}

function escapeHtml(text) {
  const div = document.createElement("div");
  div.textContent = text;
  return div.innerHTML;
}

function getTimeAgo(isoDate) {
  const seconds = Math.floor((new Date() - new Date(isoDate)) / 1000);
  if (seconds < 60) return "Just now";
  const mins = Math.floor(seconds / 60);
  if (mins < 60) return `${mins}m ago`;
  const hrs = Math.floor(mins / 60);
  if (hrs < 24) return `${hrs}h ago`;
  const days = Math.floor(hrs / 24);
  if (days < 7) return `${days}d ago`;
  return new Date(isoDate).toLocaleDateString();
}

async function loadAdmin() {
  try {
    const [users, deposits, reports] = await Promise.all([
      api("GET", "/admin/users"),
      api("GET", "/admin/deposits?status=pending"),
      api("GET", "/admin/reports"),
    ]);

    const r = reports.reports;
    document.getElementById("admin-total-users").textContent = r.total_users;
    document.getElementById("admin-total-deposits").textContent = r.total_deposits_approved;
    document.getElementById("admin-pending").textContent = r.pending_deposits;
    document.getElementById("admin-total-earnings").textContent = r.total_earnings_claimed;

    const pendingContainer = document.getElementById("admin-pending-list");
    pendingContainer.innerHTML = "";

    if (deposits.deposits.length === 0) {
      pendingContainer.innerHTML = '<div class="empty-state"><p>No pending deposits</p></div>';
    } else {
      deposits.deposits.forEach(d => {
        pendingContainer.innerHTML += `
          <div class="card" style="margin-bottom:8px;">
            <div style="display:flex;justify-content:space-between;margin-bottom:8px;">
              <strong>${d.package_name}</strong>
              <span>${formatMoney(d.amount)}</span>
            </div>
            <div style="font-size:13px;color:var(--text-light);margin-bottom:8px;">
              User: ${d.user_phone}<br>Ref: ${d.reference}
            </div>
            <div style="display:flex;gap:8px;">
              <button class="btn btn-success" style="flex:1;padding:10px;" onclick="adminAction('${d.id}', 'approve')">Approve</button>
              <button class="btn btn-danger" style="flex:1;padding:10px;" onclick="adminAction('${d.id}', 'reject')">Reject</button>
            </div>
          </div>`;
      });
    }

    loadAdminDepositRequests();
    loadPaymentSettings();
    loadAdminWithdrawals();
  } catch (err) {
    showToast(err.message);
  }
}

async function loadPaymentSettings() {
  try {
    const info = await api("GET", "/deposit-requests/payment-info");
    document.getElementById("admin-payment-number").value = info.payment_number;
    document.getElementById("admin-payment-name").value = info.payment_name;
  } catch (err) {
    showToast(err.message);
  }
}

async function adminUpdatePayment() {
  const number = document.getElementById("admin-payment-number").value.trim();
  const name = document.getElementById("admin-payment-name").value.trim();
  hideMsg("admin-payment-msg");

  if (!number) return showToast("Enter a payment number");

  try {
    await api("PUT", "/deposit-requests/admin/update-payment-number", {
      payment_number: number,
      payment_name: name || undefined,
    });
    showMsg("admin-payment-msg", "Payment number updated successfully!");
  } catch (err) {
    showToast(err.message);
  }
}

async function adminAction(depositId, action) {
  try {
    if (action === "approve") {
      await api("PUT", `/deposits/approve/${depositId}`);
      showToast("Deposit approved!");
    } else {
      await api("PUT", `/deposits/reject/${depositId}`, { action: "reject", reason: "Rejected by admin" });
      showToast("Deposit rejected");
    }
    loadAdmin();
  } catch (err) {
    showToast(err.message);
  }
}

async function doResendOTP() {
  const phone = document.getElementById("otp-phone").value.trim();
  if (!phone) return showToast("Enter phone number first");

  try {
    const result = await api("POST", "/auth/resend-otp", { phone });
    document.getElementById("otp-hint").style.display = "block";
    document.getElementById("otp-display").style.display = "block";
    document.getElementById("otp-display-code").textContent = result.otp;
    showToast("OTP sent! Check the code below.");
  } catch (err) {
    showToast(err.message);
  }
}

async function redeemGift() {
  const code = document.getElementById("gift-code-input").value.trim().toUpperCase();
  hideMsg("gift-error");
  hideMsg("gift-success");
  if (!code) return showMsg("gift-error", "Enter a gift code");

  try {
    const result = await api("POST", "/gifts/redeem", { code });
    showMsg("gift-success", result.message);
    document.getElementById("gift-code-input").value = "";
    loadGifts();
  } catch (err) {
    showMsg("gift-error", err.message);
  }
}

async function loadGifts() {
  try {
    const data = await api("GET", "/gifts/my-received");
    const container = document.getElementById("my-gifts-list");
    container.innerHTML = "";

    if (data.gifts.length === 0) {
      container.innerHTML = '<div class="empty-state"><div class="icon">🎁</div><p>No gifts received yet</p></div>';
      return;
    }

    container.innerHTML = `<div style="text-align:center;font-size:14px;margin-bottom:12px;color:var(--secondary);font-weight:600;">Total received: ${formatMoney(data.total_received)}</div>`;
    data.gifts.forEach(g => {
      container.innerHTML += `
        <div class="deposit-history-item">
          <div>
            <div style="font-weight:600;">${g.code}</div>
            <div style="font-size:12px;color:var(--text-light);">${g.description || "Gift"}</div>
          </div>
          <div style="text-align:right;">
            <div style="font-weight:600;color:var(--secondary);">+${formatMoney(g.amount)}</div>
            <div style="font-size:11px;color:var(--text-light);">${g.received_at ? new Date(g.received_at).toLocaleDateString() : ""}</div>
          </div>
        </div>`;
    });
  } catch (err) {
    showToast(err.message);
  }
}

async function adminCreateGifts() {
  const amount = parseFloat(document.getElementById("admin-gift-amount").value);
  const desc = document.getElementById("admin-gift-desc").value.trim();
  const qty = parseInt(document.getElementById("admin-gift-qty").value) || 1;

  if (!amount || amount <= 0) return showToast("Enter a valid amount");

  try {
    const result = await api("POST", "/gifts/admin/create", {
      amount,
      description: desc || undefined,
      quantity: qty,
    });

    document.getElementById("admin-gift-result").style.display = "block";
    document.getElementById("admin-gift-codes").innerHTML =
      result.codes.map(c => `<div style="padding:4px 0;border-bottom:1px solid #ccc;">${c}</div>`).join("");
    showToast(result.message);
    loadAdminGifts();
  } catch (err) {
    showToast(err.message);
  }
}

async function loadAdminGifts() {
  try {
    const data = await api("GET", "/gifts/admin/list");
    const container = document.getElementById("admin-gifts-list");
    if (!container) return;
    container.innerHTML = "";

    if (data.gifts.length === 0) {
      container.innerHTML = '<div class="empty-state"><p>No gift codes created</p></div>';
      return;
    }

    data.gifts.forEach(g => {
      container.innerHTML += `
        <div style="display:flex;justify-content:space-between;align-items:center;padding:12px 0;border-bottom:1px solid var(--border);">
          <div style="flex:1;">
            <div style="font-family:monospace;font-weight:700;font-size:14px;">${g.code}</div>
            <div style="font-size:12px;color:var(--text-light);">
              ${formatMoney(g.amount)} ${g.used_by ? "→ " + g.used_by : "— unused"}
              ${g.description ? " | " + g.description : ""}
            </div>
          </div>
          <button class="btn ${g.is_active ? 'btn-success' : 'btn-danger'}"
                  style="width:auto;padding:6px 12px;font-size:12px;"
                  onclick="adminToggleGift('${g.id}')">
            ${g.is_active ? 'Active' : 'Voided'}
          </button>
        </div>`;
    });
  } catch (err) {
    showToast(err.message);
  }
}

async function adminToggleGift(giftId) {
  try {
    await api("PUT", `/gifts/admin/toggle/${giftId}`);
    loadAdminGifts();
  } catch (err) {
    showToast(err.message);
  }
}

async function loadDepositPage() {
  try {
    const info = await api("GET", "/deposit-requests/payment-info");
    document.getElementById("deposit-payment-number").textContent = info.payment_number;
    document.getElementById("deposit-payment-name").textContent = info.payment_name;

    document.getElementById("deposit-payment-number").onclick = function() {
      navigator.clipboard.writeText(info.payment_number);
      showToast("Payment number copied!");
    };

    loadMyDepositRequests();
  } catch (err) {
    showToast(err.message);
  }
}

async function submitDepositRequest() {
  const amount = parseFloat(document.getElementById("deposit-req-amount").value);
  const message = document.getElementById("deposit-req-message").value.trim();

  hideMsg("deposit-req-error");
  hideMsg("deposit-req-success");

  if (!amount || amount <= 0) return showMsg("deposit-req-error", "Enter the amount you sent");
  if (!message) return showMsg("deposit-req-error", "Paste the M-PESA confirmation message");
  if (message.length < 10) return showMsg("deposit-req-error", "Message too short. Paste the full confirmation.");

  try {
    const result = await api("POST", "/deposit-requests/create", {
      amount,
      mpesa_message: message,
    });
    showMsg("deposit-req-success", result.message);
    document.getElementById("deposit-req-amount").value = "";
    document.getElementById("deposit-req-message").value = "";
    loadMyDepositRequests();
  } catch (err) {
    showMsg("deposit-req-error", err.message);
  }
}

async function loadMyDepositRequests() {
  try {
    const data = await api("GET", "/deposit-requests/my-requests");
    const container = document.getElementById("my-deposit-reqs-list");
    if (!container) return;
    container.innerHTML = "";

    if (data.requests.length === 0) {
      container.innerHTML = '<div class="empty-state"><p>No deposit requests yet</p></div>';
      return;
    }

    data.requests.forEach(r => {
      const date = new Date(r.created_at).toLocaleDateString();
      container.innerHTML += `
        <div class="deposit-history-item" style="flex-direction:column;align-items:flex-start;gap:6px;">
          <div style="display:flex;justify-content:space-between;width:100%;">
            <div style="font-weight:600;">${formatMoney(r.amount)}</div>
            <span class="deposit-status-badge deposit-status-${r.status}">${r.status.toUpperCase()}</span>
          </div>
          <div style="font-size:12px;color:var(--text-light);word-break:break-all;">${escapeHtml(r.mpesa_message.substring(0, 80))}${r.mpesa_message.length > 80 ? '...' : ''}</div>
          <div style="font-size:11px;color:var(--text-light);">${date}</div>
        </div>`;
    });
  } catch (err) {
    showToast(err.message);
  }
}

async function loadAdminDepositRequests() {
  try {
    const data = await api("GET", "/deposit-requests/admin/list");
    const container = document.getElementById("admin-deposit-reqs-list");
    if (!container) return;
    container.innerHTML = "";

    const pending = data.requests.filter(r => r.status === "pending");
    const processed = data.requests.filter(r => r.status !== "pending");

    if (data.requests.length === 0) {
      container.innerHTML = '<div class="empty-state"><p>No deposit requests</p></div>';
      return;
    }

    if (pending.length > 0) {
      pending.forEach(r => {
        const date = new Date(r.created_at).toLocaleDateString();
        container.innerHTML += `
          <div class="card" style="margin-bottom:8px;">
            <div style="display:flex;justify-content:space-between;margin-bottom:8px;">
              <strong>${r.user_phone}</strong>
              <span style="font-weight:700;color:var(--primary);">${formatMoney(r.amount)}</span>
            </div>
            <div style="background:var(--bg);padding:10px;border-radius:8px;margin-bottom:8px;font-size:12px;color:var(--text);word-break:break-all;line-height:1.4;">
              ${escapeHtml(r.mpesa_message)}
            </div>
            <div style="font-size:11px;color:var(--text-light);margin-bottom:8px;">${date}</div>
            <div style="display:flex;gap:8px;">
              <button class="btn btn-success" style="flex:1;padding:10px;" onclick="adminApproveDepositReq('${r.id}')">Approve</button>
              <button class="btn btn-danger" style="flex:1;padding:10px;" onclick="adminRejectDepositReq('${r.id}')">Reject</button>
            </div>
          </div>`;
      });
    }

    if (processed.length > 0) {
      container.innerHTML += '<div style="font-size:13px;color:var(--text-light);margin:12px 0 8px;font-weight:600;">Processed</div>';
      processed.slice(0, 10).forEach(r => {
        const date = new Date(r.created_at).toLocaleDateString();
        container.innerHTML += `
          <div style="display:flex;justify-content:space-between;align-items:center;padding:10px 0;border-bottom:1px solid var(--border);">
            <div>
              <div style="font-weight:600;font-size:13px;">${r.user_phone}</div>
              <div style="font-size:11px;color:var(--text-light);">${formatMoney(r.amount)} · ${date}</div>
            </div>
            <span class="deposit-status-badge deposit-status-${r.status}">${r.status.toUpperCase()}</span>
          </div>`;
      });
    }
  } catch (err) {
    showToast(err.message);
  }
}

async function adminApproveDepositReq(requestId) {
  try {
    await api("PUT", `/deposit-requests/admin/approve/${requestId}`);
    showToast("Deposit approved!");
    loadAdminDepositRequests();
  } catch (err) {
    showToast(err.message);
  }
}

async function adminRejectDepositReq(requestId) {
  try {
    await api("PUT", `/deposit-requests/admin/reject/${requestId}`);
    showToast("Deposit rejected");
    loadAdminDepositRequests();
  } catch (err) {
    showToast(err.message);
  }
}

async function loadWithdrawPage() {
  try {
    const [balanceData, requestsData] = await Promise.all([
      api("GET", "/withdrawals/balance"),
      api("GET", "/withdrawals/my-requests"),
    ]);

    document.getElementById("withdraw-balance").textContent = formatMoney(balanceData.balance);

    const container = document.getElementById("withdraw-reqs-list");
    if (!container) return;
    container.innerHTML = "";

    if (requestsData.requests.length === 0) {
      container.innerHTML = '<div class="empty-state"><p>No withdrawal requests yet</p></div>';
      return;
    }

    requestsData.requests.forEach(r => {
      const date = new Date(r.created_at).toLocaleDateString();
      container.innerHTML += `
        <div class="deposit-history-item" style="flex-direction:column;align-items:flex-start;gap:6px;">
          <div style="display:flex;justify-content:space-between;width:100%;">
            <div style="font-weight:600;">${formatMoney(r.amount)}</div>
            <span class="deposit-status-badge deposit-status-${r.status}">${r.status.toUpperCase()}</span>
          </div>
          <div style="font-size:12px;color:var(--text-light);">📱 ${r.phone}</div>
          ${r.status === 'rejected' && r.reason ? `<div style="font-size:12px;color:var(--danger);">Reason: ${escapeHtml(r.reason)}</div>` : ''}
          <div style="font-size:11px;color:var(--text-light);">${date}</div>
        </div>`;
    });
  } catch (err) {
    showToast(err.message);
  }
}

async function submitWithdrawal() {
  const amount = parseFloat(document.getElementById("withdraw-amount").value);
  const phone = document.getElementById("withdraw-phone").value.trim();

  hideMsg("withdraw-error");
  hideMsg("withdraw-success");

  if (!amount || amount <= 0) return showMsg("withdraw-error", "Enter a valid amount");
  if (!phone || phone.length < 10) return showMsg("withdraw-error", "Enter a valid phone number");

  try {
    const result = await api("POST", "/withdrawals/create", { amount, phone });
    showMsg("withdraw-success", result.message);
    document.getElementById("withdraw-amount").value = "";
    loadWithdrawPage();
  } catch (err) {
    showMsg("withdraw-error", err.message);
  }
}

async function loadAdminWithdrawals() {
  try {
    const data = await api("GET", "/withdrawals/admin/list");
    const container = document.getElementById("admin-withdrawals-list");
    if (!container) return;
    container.innerHTML = "";

    const pending = data.requests.filter(r => r.status === "pending");
    const processed = data.requests.filter(r => r.status !== "pending");

    if (data.requests.length === 0) {
      container.innerHTML = '<div class="empty-state"><p>No withdrawal requests</p></div>';
      return;
    }

    if (pending.length > 0) {
      pending.forEach(r => {
        const date = new Date(r.created_at).toLocaleDateString();
        container.innerHTML += `
          <div class="card" style="margin-bottom:8px;">
            <div style="display:flex;justify-content:space-between;margin-bottom:8px;">
              <strong>${r.user_phone}</strong>
              <span style="font-weight:700;color:var(--primary);">${formatMoney(r.amount)}</span>
            </div>
            <div style="font-size:13px;color:var(--text-light);margin-bottom:8px;">
              Send to: <strong>${r.phone}</strong><br>Date: ${date}
            </div>
            <div style="display:flex;gap:8px;">
              <button class="btn btn-success" style="flex:1;padding:10px;" onclick="adminApproveWithdrawal('${r.id}')">Approve</button>
              <button class="btn btn-danger" style="flex:1;padding:10px;" onclick="adminRejectWithdrawal('${r.id}')">Reject</button>
            </div>
          </div>`;
      });
    }

    if (processed.length > 0) {
      container.innerHTML += '<div style="font-size:13px;color:var(--text-light);margin:12px 0 8px;font-weight:600;">Processed</div>';
      processed.slice(0, 10).forEach(r => {
        const date = new Date(r.created_at).toLocaleDateString();
        container.innerHTML += `
          <div style="display:flex;justify-content:space-between;align-items:center;padding:10px 0;border-bottom:1px solid var(--border);">
            <div>
              <div style="font-weight:600;font-size:13px;">${r.user_phone} → ${r.phone}</div>
              <div style="font-size:11px;color:var(--text-light);">${formatMoney(r.amount)} · ${date}</div>
            </div>
            <span class="deposit-status-badge deposit-status-${r.status}">${r.status.toUpperCase()}</span>
          </div>`;
      });
    }
  } catch (err) {
    showToast(err.message);
  }
}

async function adminApproveWithdrawal(requestId) {
  try {
    await api("PUT", `/withdrawals/admin/approve/${requestId}`);
    showToast("Withdrawal approved!");
    loadAdminWithdrawals();
  } catch (err) {
    showToast(err.message);
  }
}

async function adminRejectWithdrawal(requestId) {
  try {
    await api("PUT", `/withdrawals/admin/reject/${requestId}`, { reason: "Rejected by admin" });
    showToast("Withdrawal rejected");
    loadAdminWithdrawals();
  } catch (err) {
    showToast(err.message);
  }
}

function requireAuth(action) {
  if (!isLoggedIn()) {
    showToast("Please login or register to continue");
    showPage("page-login");
    return false;
  }
  return true;
}

function init() {
  showPage("page-home");
  document.querySelector(".bottom-nav").style.display = "flex";
  document.querySelector(".topbar").style.display = "flex";
  if (isLoggedIn()) {
    loadHome();
  }
}

document.addEventListener("DOMContentLoaded", init);
