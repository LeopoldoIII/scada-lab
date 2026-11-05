/**
 * SCADA Web HMI Client Application.
 * Handles telemetry polling, SVG SLD rendering, and supervisory control actions.
 */

const STATE = {
  token: localStorage.getItem("scada_token") || null,
  user: JSON.parse(localStorage.getItem("scada_user") || "null"),
  pollIntervalMs: 1500,
  pollTimer: null,
};

// --- Initialization ---
document.addEventListener("DOMContentLoaded", () => {
  updateUserSessionUI();
  startTelemetryPolling();
});

// --- Authentication Logic ---
function toggleAuthModal() {
  const modal = document.getElementById("authModalBackdrop");
  const errEl = document.getElementById("authErrorMsg");
  errEl.style.display = "none";
  errEl.innerText = "";

  if (STATE.token) {
    // Logout action
    logout();
  } else {
    modal.classList.toggle("open");
  }
}

async function handleLogin() {
  const username = document.getElementById("usernameInput").value.trim();
  const password = document.getElementById("passwordInput").value.trim();
  const errEl = document.getElementById("authErrorMsg");

  try {
    const resp = await fetch("/api/v1/auth/login", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ username, password }),
    });

    if (!resp.ok) {
      const err = await resp.json();
      throw new Error(err.detail || "Authentication failed");
    }

    const data = await resp.json();
    STATE.token = data.access_token;
    STATE.user = { username: data.username, role: data.role };

    localStorage.setItem("scada_token", STATE.token);
    localStorage.setItem("scada_user", JSON.stringify(STATE.user));

    document.getElementById("authModalBackdrop").classList.remove("open");
    updateUserSessionUI();
  } catch (err) {
    errEl.style.display = "block";
    errEl.innerText = err.message;
  }
}

function logout() {
  STATE.token = null;
  STATE.user = null;
  localStorage.removeItem("scada_token");
  localStorage.removeItem("scada_user");
  updateUserSessionUI();
}

function updateUserSessionUI() {
  const badge = document.getElementById("operatorBadge");
  const btn = document.getElementById("authBtn");
  const controlBadge = document.getElementById("controlAuthBadge");

  if (STATE.token && STATE.user) {
    badge.innerText = `OPERATOR: ${STATE.user.username} (${STATE.user.role})`;
    btn.innerText = "LOGOUT";
    btn.className = "btn btn-danger btn-sm";
    controlBadge.innerText = `CLEARANCE: ${STATE.user.role}`;
    controlBadge.className = STATE.user.role === "OPERATOR" ? "badge btn-success btn-sm" : "badge btn-secondary btn-sm";
  } else {
    badge.innerText = "OPERATOR: Guest (Unauthenticated)";
    btn.innerText = "LOGIN";
    btn.className = "btn btn-secondary btn-sm";
    controlBadge.innerText = "CLEARANCE: NONE";
    controlBadge.className = "badge btn-secondary btn-sm";
  }
}

// --- Telemetry & Alarm Polling ---
function startTelemetryPolling() {
  fetchTelemetry();
  fetchAlarms();
  STATE.pollTimer = setInterval(() => {
    fetchTelemetry();
    fetchAlarms();
  }, STATE.pollIntervalMs);
}

async function fetchTelemetry() {
  const commDot = document.getElementById("commStatusDot");
  const commText = document.getElementById("commStatusText");

  try {
    const resp = await fetch("/api/v1/telemetry");
    if (!resp.ok) throw new Error("HTTP error");
    const data = await resp.json();

    commDot.className = "pulse-dot active";
    commText.innerText = "FIELD COMMS: HEALTHY";

    renderTelemetry(data);
  } catch (err) {
    commDot.className = "pulse-dot";
    commText.innerText = "FIELD COMMS: DEGRADED / RETRYING";
  }
}

function renderTelemetry(data) {
  // Numeric Readouts
  document.getElementById("valGridVoltage").innerText = data.grid_voltage_kv.toFixed(2);
  document.getElementById("valBusFrequency").innerText = data.bus_frequency_hz.toFixed(2);
  document.getElementById("valBatterySoc").innerText = data.battery_soc_percent.toFixed(1);
  document.getElementById("valPowerFlow").innerText = (data.power_flow_mw >= 0 ? "+" : "") + data.power_flow_mw.toFixed(2);
  document.getElementById("valBatteryTemp").innerText = data.battery_temp_c.toFixed(1);
  document.getElementById("valBatterySoh").innerText = data.battery_soh_percent.toFixed(1);

  // Mode Tag
  const modeTag = document.getElementById("firewallModeTag");
  modeTag.innerText = `MODE: ${data.firewall_status}`;
  if (data.firewall_status === "ISLANDED") {
    modeTag.className = "mode-tag islanded";
  } else {
    modeTag.className = "mode-tag";
  }

  // SVG Elements
  document.getElementById("sldGridVoltage").textContent = `${data.grid_voltage_kv.toFixed(2)} kV`;
  document.getElementById("sldGridFreq").textContent = `${data.bus_frequency_hz.toFixed(2)} Hz`;
  document.getElementById("sldBatterySoc").textContent = `BESS SoC: ${data.battery_soc_percent.toFixed(1)}%`;
  document.getElementById("sldPowerFlow").textContent = `FLOW: ${(data.power_flow_mw >= 0 ? "+" : "") + data.power_flow_mw.toFixed(2)} MW`;

  const isTripped = data.breaker_status === "TRIPPED";
  const breakerEl = document.getElementById("breakerCb101");
  const breakerText = document.getElementById("breakerStateText");
  const busLine1 = document.getElementById("busLine1");
  const gridBox = document.getElementById("sldGridBox");
  const firewallStatusText = document.getElementById("sldFirewallStatus");

  if (isTripped) {
    breakerEl.classList.add("tripped");
    breakerText.textContent = "TRIPPED";
    busLine1.classList.add("tripped");
    gridBox.classList.add("tripped");
    firewallStatusText.textContent = "STATUS: ISLANDED (BACKUP)";
  } else {
    breakerEl.classList.remove("tripped");
    breakerText.textContent = "CLOSED";
    busLine1.classList.remove("tripped");
    gridBox.classList.remove("tripped");
    firewallStatusText.textContent = "STATUS: NORMAL (GRID-TIED)";
  }
}

async function fetchAlarms() {
  try {
    const resp = await fetch("/api/v1/alarms");
    if (!resp.ok) return;
    const alarms = await resp.json();
    renderAlarms(alarms);
  } catch (err) {
    // Silent polling retry
  }
}

function renderAlarms(alarms) {
  const container = document.getElementById("alarmsList");
  const badge = document.getElementById("alarmCountBadge");

  badge.innerText = `${alarms.length} ACTIVE`;
  if (alarms.length > 0) {
    badge.className = "alarm-count-badge has-alarms";
    container.innerHTML = "";

    alarms.forEach((alarm) => {
      const card = document.createElement("div");
      card.className = `alarm-card ${alarm.acknowledged ? "acknowledged" : ""}`;
      card.innerHTML = `
        <div class="alarm-title-row">
          <span class="alarm-code">[${alarm.severity}] ${alarm.code}</span>
          <span class="alarm-status">${alarm.acknowledged ? "ACK'D" : "UNACK'D"}</span>
        </div>
        <div class="alarm-desc">${alarm.message}</div>
        <div class="alarm-actions">
          <span class="alarm-time">${alarm.triggered_at.split("T")[1].replace("Z", "")}</span>
          ${
            !alarm.acknowledged
              ? `<button class="btn btn-warning btn-sm" onclick="handleAcknowledgeAlarm('${alarm.code}')">ACK</button>`
              : `<small style="color: #64748b;">Ack by: ${alarm.acknowledged_by || "Operator"}</small>`
          }
        </div>
      `;
      container.appendChild(card);
    });
  } else {
    badge.className = "alarm-count-badge";
    container.innerHTML = '<div class="no-alarms-msg">All systems operating within nominal limits.</div>';
  }
}

// --- Supervisory Control Actions ---
async function handleDispatchSetpoint() {
  const setpoint = parseFloat(document.getElementById("setpointInput").value);
  const feedback = document.getElementById("dispatchFeedbackText");
  const btn = document.getElementById("dispatchBtn");

  if (!STATE.token) {
    alert("Authentication Required: Please sign in as OPERATOR to dispatch setpoints.");
    toggleAuthModal();
    return;
  }

  // Industrial latency simulation state
  btn.disabled = true;
  feedback.innerText = "STATE: DISPATCHING TO CONTROLLER...";
  feedback.style.color = "#f59e0b";

  try {
    const resp = await fetch("/api/v1/controls/dispatch", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${STATE.token}`,
      },
      body: JSON.stringify({ power_mw: setpoint }),
    });

    if (!resp.ok) {
      const err = await resp.json();
      throw new Error(err.detail || "Dispatch rejected");
    }

    // Realistic RTU confirmation delay
    setTimeout(() => {
      feedback.innerText = `STATE: CONFIRMED (${setpoint.toFixed(1)} MW)`;
      feedback.style.color = "#10b981";
      btn.disabled = false;
    }, 1200);
  } catch (err) {
    feedback.innerText = `ERROR: ${err.message}`;
    feedback.style.color = "#ef4444";
    btn.disabled = false;
  }
}

async function handleTripGrid() {
  if (!STATE.token) {
    alert("Authentication Required: Please sign in as OPERATOR to trigger simulation.");
    toggleAuthModal();
    return;
  }

  try {
    const resp = await fetch("/api/v1/sim/trip-grid", {
      method: "POST",
      headers: { Authorization: `Bearer ${STATE.token}` },
    });
    if (!resp.ok) {
      const err = await resp.json();
      alert(`Action failed: ${err.detail}`);
    } else {
      fetchTelemetry();
      fetchAlarms();
    }
  } catch (err) {
    alert(`Network failure: ${err.message}`);
  }
}

async function handleRestoreGrid() {
  if (!STATE.token) {
    alert("Authentication Required: Please sign in as OPERATOR.");
    toggleAuthModal();
    return;
  }

  try {
    const resp = await fetch("/api/v1/sim/restore-grid", {
      method: "POST",
      headers: { Authorization: `Bearer ${STATE.token}` },
    });
    if (!resp.ok) {
      const err = await resp.json();
      alert(`Action failed: ${err.detail}`);
    } else {
      fetchTelemetry();
      fetchAlarms();
    }
  } catch (err) {
    alert(`Network failure: ${err.message}`);
  }
}

async function handleAcknowledgeAlarm(alarmCode) {
  if (!STATE.token) {
    alert("Authentication Required: Please sign in as OPERATOR to acknowledge alarms.");
    toggleAuthModal();
    return;
  }

  try {
    const resp = await fetch(`/api/v1/alarms/${alarmCode}/ack`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${STATE.token}`,
      },
      body: JSON.stringify({ operator_note: "Acknowledged via HMI" }),
    });

    if (!resp.ok) {
      const err = await resp.json();
      alert(`Acknowledge failed: ${err.detail}`);
    } else {
      fetchAlarms();
    }
  } catch (err) {
    alert(`Error: ${err.message}`);
  }
}

