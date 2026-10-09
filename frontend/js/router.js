const routes = [];

export function route(pattern, handler) {
  const keys = [];
  const regexStr = pattern
    .split("/")
    .map((seg) => {
      if (seg.startsWith(":")) {
        keys.push(seg.slice(1));
        return "([^/]+)";
      }
      return seg.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
    })
    .join("/");
  routes.push({ regex: new RegExp(`^${regexStr}$`), keys, handler });
}

export function currentPath() {
  return (location.hash.slice(1) || "/").split("?")[0];
}

export async function resolve() {
  const path = currentPath();
  for (const r of routes) {
    const m = path.match(r.regex);
    if (m) {
      const params = {};
      r.keys.forEach((k, i) => (params[k] = decodeURIComponent(m[i + 1])));
      await r.handler(params);
      return;
    }
  }
  navigate("/");
}

export function navigate(path) {
  if (location.hash.slice(1) === path) {
    resolve();
  } else {
    location.hash = path;
  }
}

window.addEventListener("hashchange", resolve);
