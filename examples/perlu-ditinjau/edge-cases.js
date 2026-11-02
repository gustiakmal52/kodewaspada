// Hanya fixture statis; tidak dipanggil atau dijalankan oleh pengujian.
const { exec: run, execSync } = require("child_process");
const cp = require("node:child_process");

export function shellAliases(request, response) {
  const name = request.query.name;
  // ruleid: kw-request-shell
  run("printf '%s' " + name);
  // ruleid: kw-request-shell
  execSync("printf '%s' " + request.params.name);
  // ruleid: kw-request-shell
  cp.execSync("printf '%s' " + request.body.name);
  // Encoding URL bukan sanitizer shell.
  // ruleid: kw-request-shell
  cp.exec("printf '%s' " + encodeURIComponent(request.query.name));
}

export function unknownSanitizer(element) {
  const value = document.location.hash;
  // Nama fungsi sanitize bukan bukti bahwa implementasinya aman.
  // ruleid: kw-request-html
  element.innerHTML = sanitize(value);
  // Tanpa import yang cocok, DOMPurify tidak dianggap sanitizer.
  // ruleid: kw-request-html
  element.innerHTML = DOMPurify.sanitize(value);
}
