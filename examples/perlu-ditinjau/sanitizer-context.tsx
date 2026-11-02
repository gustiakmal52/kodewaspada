// Fixture: import yang benar tidak membuat semua penggunaan sanitize aman.
import DOMPurify from "dompurify";

export function modifiedConfiguration(element: HTMLElement) {
  // Konfigurasi custom tetap perlu tinjauan manusia; tidak disembunyikan aturan.
  // ruleid: kw-request-html
  element.innerHTML = DOMPurify.sanitize(window.location.hash, { ALLOWED_TAGS: ["p"] });
}

export function appendedInput(element: HTMLElement) {
  const clean = DOMPurify.sanitize(window.location.hash);
  // ruleid: kw-request-html
  element.innerHTML = clean + window.location.search;
}

export function shadowedBinding(DOMPurify: any, element: HTMLElement) {
  // Parameter lokal ini bukan default import di atas.
  // ruleid: kw-request-html
  element.innerHTML = DOMPurify.sanitize(window.location.hash);
}
