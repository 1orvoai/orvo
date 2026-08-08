// ORVO auth page handlers

async function orvoHandleSignup(event) {
  event.preventDefault();
  const btn = event.target.querySelector("button[type=submit]");
  const full_name = document.getElementById("full_name").value.trim();
  const email = document.getElementById("email").value.trim();
  const password = document.getElementById("password").value;
  const confirm = document.getElementById("confirm_password").value;

  if (password !== confirm) {
    orvoShowToast("Passwords do not match.", "error");
    return;
  }

  btn.disabled = true;
  btn.textContent = "Creating account...";
  try {
    await ORVO_API.post("/api/auth/signup", { full_name, email, password });
    orvoShowToast("Account created! Logging you in...", "success");
    const tokenResp = await ORVO_API.post("/api/auth/login", { email, password });
    ORVO_API.setToken(tokenResp.access_token);
    window.location.href = "/dashboard.html";
  } catch (err) {
    orvoShowToast(err.message, "error");
    btn.disabled = false;
    btn.textContent = "Create Account";
  }
}

async function orvoHandleLogin(event) {
  event.preventDefault();
  const btn = event.target.querySelector("button[type=submit]");
  const email = document.getElementById("email").value.trim();
  const password = document.getElementById("password").value;

  btn.disabled = true;
  btn.textContent = "Logging in...";
  try {
    const resp = await ORVO_API.post("/api/auth/login", { email, password });
    ORVO_API.setToken(resp.access_token);
    window.location.href = "/dashboard.html";
  } catch (err) {
    orvoShowToast(err.message, "error");
    btn.disabled = false;
    btn.textContent = "Log In";
  }
}

async function orvoHandleForgotPassword(event) {
  event.preventDefault();
  const btn = event.target.querySelector("button[type=submit]");
  const email = document.getElementById("email").value.trim();

  btn.disabled = true;
  btn.textContent = "Sending...";
  try {
    const resp = await ORVO_API.post("/api/auth/forgot-password", { email });
    document.getElementById("forgot-form-wrap").classList.add("hidden");
    document.getElementById("forgot-success").classList.remove("hidden");
    document.getElementById("forgot-success-msg").textContent = resp.message;
  } catch (err) {
    orvoShowToast(err.message, "error");
    btn.disabled = false;
    btn.textContent = "Send Reset Link";
  }
}

async function orvoHandleResetPassword(event) {
  event.preventDefault();
  const btn = event.target.querySelector("button[type=submit]");
  const params = new URLSearchParams(window.location.search);
  const token = params.get("token");
  if (!token) {
    orvoShowToast("Missing or invalid reset link.", "error");
    return;
  }
  const new_password = document.getElementById("new_password").value;
  const confirm = document.getElementById("confirm_password").value;
  if (new_password !== confirm) {
    orvoShowToast("Passwords do not match.", "error");
    return;
  }

  btn.disabled = true;
  btn.textContent = "Resetting...";
  try {
    await ORVO_API.post("/api/auth/reset-password", { token, new_password });
    orvoShowToast("Password reset! Redirecting to login...", "success");
    setTimeout(() => (window.location.href = "/login.html"), 1500);
  } catch (err) {
    orvoShowToast(err.message, "error");
    btn.disabled = false;
    btn.textContent = "Reset Password";
  }
}

async function orvoHandleChangePassword(event) {
  event.preventDefault();
  const btn = event.target.querySelector("button[type=submit]");
  const current_password = document.getElementById("current_password").value;
  const new_password = document.getElementById("new_password").value;
  const confirm = document.getElementById("confirm_new_password").value;

  if (new_password !== confirm) {
    orvoShowToast("New passwords do not match.", "error");
    return;
  }

  btn.disabled = true;
  btn.textContent = "Updating...";
  try {
    await ORVO_API.post("/api/auth/change-password", { current_password, new_password });
    orvoShowToast("Password changed successfully.", "success");
    event.target.reset();
  } catch (err) {
    orvoShowToast(err.message, "error");
  } finally {
    btn.disabled = false;
    btn.textContent = "Change Password";
  }
}

async function orvoLogout() {
  try {
    await ORVO_API.post("/api/auth/logout", {});
  } catch (e) {
    // ignore — token may already be invalid
  }
  ORVO_API.clearToken();
  window.location.href = "/login.html";
}

// Guard: redirect to login if not authenticated (call on protected pages)
function orvoRequireAuth() {
  if (!ORVO_API.isAuthenticated()) {
    window.location.href = "/login.html";
  }
}
