import {
  CommonModule,
  FormsModule,
  HttpClient,
  IonChip,
  IonCol,
  IonContent,
  IonGrid,
  IonHeader,
  IonItem,
  IonLabel,
  IonList,
  IonRow,
  IonSearchbar,
  IonTitle,
  IonToolbar,
  NgForOf,
  Router,
  ɵsetClassDebugInfo,
  ɵɵStandaloneFeature,
  ɵɵadvance,
  ɵɵdefineComponent,
  ɵɵdirectiveInject,
  ɵɵelement,
  ɵɵelementEnd,
  ɵɵelementStart,
  ɵɵgetCurrentView,
  ɵɵlistener,
  ɵɵnextContext,
  ɵɵproperty,
  ɵɵresetView,
  ɵɵrestoreView,
  ɵɵtemplate,
  ɵɵtext,
  ɵɵtextInterpolate
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
import {
  __async
} from "./chunk-FSIFXKME.js";

// src/app/pages/ricette/ricette.page.ts
function RicettePage_ion_chip_10_Template(rf, ctx) {
  if (rf & 1) {
    const _r1 = \u0275\u0275getCurrentView();
    \u0275\u0275elementStart(0, "ion-chip", 6);
    \u0275\u0275listener("click", function RicettePage_ion_chip_10_Template_ion_chip_click_0_listener() {
      const categoria_r2 = \u0275\u0275restoreView(_r1).$implicit;
      const ctx_r2 = \u0275\u0275nextContext();
      return \u0275\u0275resetView(ctx_r2.searchByCat(categoria_r2));
    });
    \u0275\u0275text(1);
    \u0275\u0275elementEnd();
  }
  if (rf & 2) {
    const categoria_r2 = ctx.$implicit;
    \u0275\u0275advance();
    \u0275\u0275textInterpolate(categoria_r2);
  }
}
function RicettePage_ion_item_12_Template(rf, ctx) {
  if (rf & 1) {
    const _r4 = \u0275\u0275getCurrentView();
    \u0275\u0275elementStart(0, "ion-item", 7);
    \u0275\u0275listener("click", function RicettePage_ion_item_12_Template_ion_item_click_0_listener() {
      const recipe_r5 = \u0275\u0275restoreView(_r4).$implicit;
      const ctx_r2 = \u0275\u0275nextContext();
      return \u0275\u0275resetView(ctx_r2.goToRecipe(recipe_r5));
    });
    \u0275\u0275elementStart(1, "ion-label");
    \u0275\u0275text(2);
    \u0275\u0275elementEnd()();
  }
  if (rf & 2) {
    const recipe_r5 = ctx.$implicit;
    \u0275\u0275property("button", true);
    \u0275\u0275advance(2);
    \u0275\u0275textInterpolate(recipe_r5.titolo);
  }
}
var _RicettePage = class _RicettePage {
  constructor(http, router) {
    this.http = http;
    this.router = router;
    this.responseJson = [];
    this.recipeFinded = [];
    this.categorie = [];
  }
  ngOnInit() {
  }
  ionViewWillEnter() {
    this.getRecipeList();
  }
  getRecipeList() {
    return __async(this, null, function* () {
      this.http.get("/getRecipeList").subscribe({
        next: (response) => __async(this, null, function* () {
          console.log("Risposta dal server:", response);
          this.responseJson = response;
          this.categorie = yield this.getCategorie();
          this.recipeFinded = this.responseJson;
        }),
        error: (error) => __async(this, null, function* () {
          console.error("Errore durante l'invio:", error);
        })
      });
    });
  }
  searchRecipe(toFind) {
    const query = toFind.target.value.toLowerCase();
    console.log("categoria da cercare ", query);
    this.recipeFinded = this.responseJson.filter((recipe) => recipe.titolo.toLowerCase().includes(query));
    console.log(this.recipeFinded);
  }
  getCategorie() {
    return __async(this, null, function* () {
      var categorie = [...new Set(this.responseJson.map((item) => item.categoria))];
      console.log("Categorie uniche:", this.categorie);
      categorie.unshift("tutti");
      return categorie;
    });
  }
  searchByCat(cat) {
    const query = cat.toLowerCase();
    console.log("categoria da cercare ", query);
    if (query == "tutti") {
      this.recipeFinded = this.responseJson;
    } else {
      this.recipeFinded = this.responseJson.filter((recipe) => recipe.categoria.toLowerCase().includes(query));
    }
    console.log(this.recipeFinded);
  }
  goToRecipe(recipe) {
    console.log("ricetta da caricare ", recipe);
    const navigationExtras = {
      state: {
        data: recipe
      }
    };
    this.router.navigate(["/tabs/ricetta"], navigationExtras);
  }
};
_RicettePage.\u0275fac = function RicettePage_Factory(__ngFactoryType__) {
  return new (__ngFactoryType__ || _RicettePage)(\u0275\u0275directiveInject(HttpClient), \u0275\u0275directiveInject(Router));
};
_RicettePage.\u0275cmp = /* @__PURE__ */ \u0275\u0275defineComponent({ type: _RicettePage, selectors: [["app-ricette"]], standalone: true, features: [\u0275\u0275StandaloneFeature], decls: 14, vars: 5, consts: [[3, "translucent"], [3, "fullscreen"], ["size", "10"], ["placeholder", "cerca ricetta", 3, "ionInput", "debounce"], [3, "click", 4, "ngFor", "ngForOf"], [3, "button", "click", 4, "ngFor", "ngForOf"], [3, "click"], [3, "click", "button"]], template: function RicettePage_Template(rf, ctx) {
  if (rf & 1) {
    \u0275\u0275elementStart(0, "ion-header", 0)(1, "ion-toolbar")(2, "ion-title");
    \u0275\u0275text(3, "ricette");
    \u0275\u0275elementEnd()()();
    \u0275\u0275elementStart(4, "ion-content", 1)(5, "ion-grid")(6, "ion-row");
    \u0275\u0275element(7, "ion-col");
    \u0275\u0275elementStart(8, "ion-col", 2)(9, "ion-searchbar", 3);
    \u0275\u0275listener("ionInput", function RicettePage_Template_ion_searchbar_ionInput_9_listener($event) {
      return ctx.searchRecipe($event);
    });
    \u0275\u0275elementEnd();
    \u0275\u0275template(10, RicettePage_ion_chip_10_Template, 2, 1, "ion-chip", 4);
    \u0275\u0275elementStart(11, "ion-list");
    \u0275\u0275template(12, RicettePage_ion_item_12_Template, 3, 2, "ion-item", 5);
    \u0275\u0275elementEnd()();
    \u0275\u0275element(13, "ion-col");
    \u0275\u0275elementEnd()()();
  }
  if (rf & 2) {
    \u0275\u0275property("translucent", true);
    \u0275\u0275advance(4);
    \u0275\u0275property("fullscreen", true);
    \u0275\u0275advance(5);
    \u0275\u0275property("debounce", 1e3);
    \u0275\u0275advance();
    \u0275\u0275property("ngForOf", ctx.categorie);
    \u0275\u0275advance(2);
    \u0275\u0275property("ngForOf", ctx.recipeFinded);
  }
}, dependencies: [IonGrid, IonRow, IonCol, IonItem, IonList, IonChip, IonLabel, IonSearchbar, IonContent, IonHeader, IonTitle, IonToolbar, CommonModule, NgForOf, FormsModule] });
var RicettePage = _RicettePage;
(() => {
  (typeof ngDevMode === "undefined" || ngDevMode) && \u0275setClassDebugInfo(RicettePage, { className: "RicettePage" });
})();
export {
  RicettePage
};
//# sourceMappingURL=ricette.page-O5DYYQKR.js.map
