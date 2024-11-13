import {
  EnvironmentInjector,
  IonLabel,
  IonTabBar,
  IonTabButton,
  IonTabs2 as IonTabs,
  inject,
  ɵsetClassDebugInfo,
  ɵɵStandaloneFeature,
  ɵɵdefineComponent,
  ɵɵelementEnd,
  ɵɵelementStart,
  ɵɵtext
} from "./chunk-XQKGXJYT.js";
import "./chunk-CHE7QSOJ.js";
import "./chunk-KQEJHESJ.js";
import "./chunk-PSJYXVUC.js";
import "./chunk-7AHLWAGB.js";
import "./chunk-NHTTLMSC.js";
import "./chunk-OQQEQ4WG.js";
import "./chunk-HKAYGSB5.js";
import "./chunk-OMBHTXSN.js";
import "./chunk-O6VJ33GT.js";
import "./chunk-LHYYZWFK.js";
import "./chunk-4WT7J3YM.js";
import "./chunk-6FFMTLXI.js";
import "./chunk-XIXT7DF6.js";
import "./chunk-CC56LK7W.js";
import "./chunk-K3HSXS64.js";
import "./chunk-FSIFXKME.js";

// node_modules/ionicons/dist/esm-es5/utils-2c56d1c8.js
var CACHED_MAP;
var getIconMap = function() {
  if (typeof window === "undefined") {
    return /* @__PURE__ */ new Map();
  } else {
    if (!CACHED_MAP) {
      var t = window;
      t.Ionicons = t.Ionicons || {};
      CACHED_MAP = t.Ionicons.map = t.Ionicons.map || /* @__PURE__ */ new Map();
    }
    return CACHED_MAP;
  }
};
var addIcons = function(t) {
  Object.keys(t).forEach(function(e) {
    addToIconMap(e, t[e]);
    var r = e.replace(/([a-z0-9]|(?=[A-Z]))([A-Z0-9])/g, "$1-$2").toLowerCase();
    if (e !== r) {
      addToIconMap(r, t[e]);
    }
  });
};
var addToIconMap = function(t, e) {
  var r = getIconMap();
  var n = r.get(t);
  if (n === void 0) {
    r.set(t, e);
  } else if (n !== e) {
    console.warn('[Ionicons Warning]: Multiple icons were mapped to name "'.concat(t, '". Ensure that multiple icons are not mapped to the same icon name.'));
  }
};

// node_modules/ionicons/icons/index.mjs
var ellipse = "data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' class='ionicon' viewBox='0 0 512 512'><path d='M256 464c-114.69 0-208-93.31-208-208S141.31 48 256 48s208 93.31 208 208-93.31 208-208 208z'/></svg>";
var square = "data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' class='ionicon' viewBox='0 0 512 512'><path d='M416 464H96a48.05 48.05 0 01-48-48V96a48.05 48.05 0 0148-48h320a48.05 48.05 0 0148 48v320a48.05 48.05 0 01-48 48z'/></svg>";
var triangle = "data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' class='ionicon' viewBox='0 0 512 512'><path d='M464 464H48a16 16 0 01-14.07-23.62l208-384a16 16 0 0128.14 0l208 384A16 16 0 01464 464z'/></svg>";

// src/app/pages/tabs/tabs.page.ts
var _TabsPage = class _TabsPage {
  constructor() {
    this.environmentInjector = inject(EnvironmentInjector);
    addIcons({ triangle, ellipse, square });
  }
};
_TabsPage.\u0275fac = function TabsPage_Factory(__ngFactoryType__) {
  return new (__ngFactoryType__ || _TabsPage)();
};
_TabsPage.\u0275cmp = /* @__PURE__ */ \u0275\u0275defineComponent({ type: _TabsPage, selectors: [["app-tabs"]], standalone: true, features: [\u0275\u0275StandaloneFeature], decls: 11, vars: 0, consts: [["slot", "bottom"], ["tab", "chat_bot", "href", "/tabs/chat_bot"], ["tab", "import_recipe", "href", "/tabs/import_recipe"], ["tab", "ricette", "href", "/tabs/ricette"]], template: function TabsPage_Template(rf, ctx) {
  if (rf & 1) {
    \u0275\u0275elementStart(0, "ion-tabs")(1, "ion-tab-bar", 0)(2, "ion-tab-button", 1)(3, "ion-label");
    \u0275\u0275text(4, "CHAT BOT");
    \u0275\u0275elementEnd()();
    \u0275\u0275elementStart(5, "ion-tab-button", 2)(6, "ion-label");
    \u0275\u0275text(7, "IMPORTA");
    \u0275\u0275elementEnd()();
    \u0275\u0275elementStart(8, "ion-tab-button", 3)(9, "ion-label");
    \u0275\u0275text(10, "RICETTE");
    \u0275\u0275elementEnd()()()();
  }
}, dependencies: [IonTabs, IonTabBar, IonTabButton, IonLabel] });
var TabsPage = _TabsPage;
(() => {
  (typeof ngDevMode === "undefined" || ngDevMode) && \u0275setClassDebugInfo(TabsPage, { className: "TabsPage" });
})();

// src/app/pages/tabs/tabs.routes.ts
var routes = [
  {
    path: "tabs",
    component: TabsPage,
    children: [
      {
        path: "chat_bot",
        loadComponent: () => import("./chat_bot.page-RLMGH46K.js").then((m) => m.ChatBotPage)
      },
      {
        path: "import_recipe",
        loadComponent: () => import("./import_recipe.page-Z56OZKR5.js").then((m) => m.ImportRecipePage)
      },
      {
        path: "ricette",
        loadComponent: () => import("./ricette.page-YJFSTM5C.js").then((m) => m.RicettePage)
      },
      {
        path: "ricetta",
        loadComponent: () => import("./ricetta.page-4TUUBDGU.js").then((m) => m.RicettaPage)
      },
      {
        path: "",
        redirectTo: "/tabs/chat_bot",
        pathMatch: "full"
      }
    ]
  },
  {
    path: "",
    redirectTo: "/tabs/import_recipe",
    pathMatch: "full"
  }
];
export {
  routes
};
//# sourceMappingURL=tabs.routes-N34EUWS4.js.map
