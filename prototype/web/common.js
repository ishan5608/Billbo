const $ = (s, el = document) => el.querySelector(s);
const esc = s => String(s ?? "").replace(/[&<>"']/g, c => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
const inr = n => "₹" + Math.round(Number(n) || 0).toLocaleString("en-IN");
async function api(path, body) {
  const r = await fetch(path, body ? { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body) } : {});
  const j = await r.json();
  if (!r.ok) throw new Error(j.error || "request failed");
  return j;
}
function topbar(active) {
  const links = [["/", "Home"], ["/chat", "Owner chat"], ["/dashboard", "Accountant dashboard"], ["/portal", "Mock GST portal"]];
  document.body.insertAdjacentHTML("afterbegin", `<header class="top"><a class="brand" href="/">Billbo</a><nav>${links.map(([h, t]) =>
    `<a href="${h}" class="${h === active ? "on" : ""}">${t}</a>`).join("")}</nav><span class="tag">Prototype · synthetic data · filing is simulated</span></header>`);
}
function qs(name) { return new URLSearchParams(location.search).get(name); }
