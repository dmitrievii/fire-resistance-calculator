(() => {
  const PAGE_HOST = "dmitrievii.github.io";
  const DEFAULT_PUBLIC_API = "https://dmitrievii-fire-resistance-calculator-api.onrender.com";
  const storageKey = "fire_ui_api_base_url";

  const params = new URLSearchParams(window.location.search);
  const queryOverride = params.get("api");
  if (queryOverride) {
    window.localStorage.setItem(storageKey, queryOverride.replace(/\/$/, ""));
  }

  const stored = window.localStorage.getItem(storageKey);
  const apiBase = (queryOverride || stored || (window.location.hostname === PAGE_HOST ? DEFAULT_PUBLIC_API : ""))
    .replace(/\/$/, "");

  window.FIRE_API_BASE_URL = apiBase;

  if (!apiBase) return;

  const nativeFetch = window.fetch.bind(window);
  window.fetch = (input, init) => {
    if (typeof input === "string" && input.startsWith("/api/")) {
      return nativeFetch(`${apiBase}${input}`, init);
    }
    return nativeFetch(input, init);
  };
})();
