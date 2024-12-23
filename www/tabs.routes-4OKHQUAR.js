import {
  addIcons,
  ellipse,
  square,
  triangle
} from "./chunk-RXKXPMNG.js";
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
} from "./chunk-CVZKNICT.js";
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
        loadComponent: () => import("./chat_bot.page-ACAYXK5U.js").then((m) => m.ChatBotPage)
      },
      {
        path: "import_recipe",
        loadComponent: () => import("./import_recipe.page-KOER25YQ.js").then((m) => m.ImportRecipePage)
      },
      {
        path: "ricette",
        loadComponent: () => import("./ricette.page-O5DYYQKR.js").then((m) => m.RicettePage)
      },
      {
        path: "ricetta",
        loadComponent: () => import("./ricetta.page-ZBWQZBV3.js").then((m) => m.RicettaPage)
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
//# sourceMappingURL=tabs.routes-4OKHQUAR.js.map
