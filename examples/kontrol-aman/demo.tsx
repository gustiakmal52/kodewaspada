// Kontrol negatif untuk tiga aturan. Bukan jaminan bahwa seluruh aplikasi aman.
import { exec, execFile } from "node:child_process";
import Purifier from "dompurify";

export function limitedRoute(req: any, res: any) {
  // ok: kw-request-shell
  exec("printf '%s' contoh");
  // ok: kw-request-shell
  execFile("printf", ["%s", String(req.query.name)], { shell: false });
  // ok: kw-request-eval
  eval("1 + 1");
  // ok: kw-request-html
  res.json({ name: req.query.name });
}

export function textPreview(element: HTMLElement) {
  const text = window.location.hash.slice(1);
  // ok: kw-request-html
  element.textContent = text;
  // ok: kw-request-html
  element.innerHTML = "<p>Contoh tetap</p>";
  // ok: kw-request-html
  element.innerHTML = Purifier.sanitize(text);
  // ok: kw-request-html
  return <section>{text}</section>;
}

export function localObject() {
  const req = { query: { name: "contoh lokal" } };
  // ok: kw-request-shell
  exec("printf '%s' " + req.query.name);
}

export function unrelatedFunction(req: any, exec: (value: unknown) => void) {
  // Parameter ini bukan exec dari import child_process.
  // ok: kw-request-shell
  exec(req.query.name);
}
