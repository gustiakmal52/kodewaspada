// Fixture untuk analisis statis. Jangan dijalankan sebagai aplikasi/server.
import { exec as runShell, execSync } from "node:child_process";
import * as child from "child_process";

export function shellRoute(req, res) {
  const name = req.query.name;
  const command = "printf '%s' " + name;
  // ruleid: kw-request-shell
  runShell(command);
  // ruleid: kw-request-shell
  execSync("printf '%s' " + req.body.name);
  // ruleid: kw-request-shell
  child.exec("printf '%s' " + req.params.name);
  res.json({ status: "contoh statis" });
}

export const codeRoute = (request, response) => {
  const expression = request.body.expression;
  const copiedExpression = expression;
  // ruleid: kw-request-eval
  eval(copiedExpression);
  // ruleid: kw-request-eval
  new Function("return " + request.query.expression);
  // ruleid: kw-request-html
  response.send("<p>" + request.query.name + "</p>");
};

export function browserExample(element) {
  const fragment = decodeURIComponent(window.location.hash.slice(1));
  // ruleid: kw-request-html
  element.innerHTML = fragment;
  // ruleid: kw-request-eval
  Function("return " + location.search.slice(1));
}
