// Fixture TypeScript/JSX untuk scanner; tidak dijalankan.
export function Preview() {
  const text: string = window.location.hash.slice(1);
  // ruleid: kw-request-html
  return <section dangerouslySetInnerHTML={{ __html: text }} />;
}

export function requestPreview(request: any, response: any) {
  const expression: string = request.body.expression;
  // ruleid: kw-request-eval
  eval(expression);
}
