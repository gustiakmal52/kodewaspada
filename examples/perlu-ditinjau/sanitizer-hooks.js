// Fixture saja: konfigurasi dan hook harus ditinjau, bukan diasumsikan aman.
import Purifier from "dompurify";

export function configuredPreview(element) {
  Purifier.setConfig({ ALLOWED_TAGS: ["p"] });
  // ruleid: kw-request-html
  element.innerHTML = Purifier.sanitize(window.location.hash);
}
