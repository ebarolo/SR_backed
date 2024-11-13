import {
  findClosestIonContent,
  scrollToTop
} from "./chunk-TI7RV26D.js";
import "./chunk-52T2EOVQ.js";
import {
  componentOnReady
} from "./chunk-X6PYF5VD.js";
import {
  readTask,
  writeTask
} from "./chunk-D2XNQ3S7.js";
import {
  __async
} from "./chunk-FSIFXKME.js";

// node_modules/@ionic/core/dist/esm/status-tap-f472b09f.js
var startStatusTap = () => {
  const win = window;
  win.addEventListener("statusTap", () => {
    readTask(() => {
      const width = win.innerWidth;
      const height = win.innerHeight;
      const el = document.elementFromPoint(width / 2, height / 2);
      if (!el) {
        return;
      }
      const contentEl = findClosestIonContent(el);
      if (contentEl) {
        new Promise((resolve) => componentOnReady(contentEl, resolve)).then(() => {
          writeTask(() => __async(void 0, null, function* () {
            contentEl.style.setProperty("--overflow", "hidden");
            yield scrollToTop(contentEl, 300);
            contentEl.style.removeProperty("--overflow");
          }));
        });
      }
    });
  });
};
export {
  startStatusTap
};
/*! Bundled license information:

@ionic/core/dist/esm/status-tap-f472b09f.js:
  (*!
   * (C) Ionic http://ionicframework.com - MIT License
   *)
*/
//# sourceMappingURL=status-tap-f472b09f-JWSJF4KX.js.map
