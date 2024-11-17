import {
  PlyrPlayerComponent
} from "./chunk-W6RQMKWS.js";
import {
  CommonModule,
  IonBackButton2 as IonBackButton,
  IonButtons,
  IonCard,
  IonCardContent,
  IonChip,
  IonCol,
  IonContent,
  IonGrid,
  IonHeader,
  IonItem,
  IonLabel,
  IonList,
  IonListHeader,
  IonRow,
  IonText,
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
  ɵɵproperty,
  ɵɵtemplate,
  ɵɵtext,
  ɵɵtextInterpolate,
  ɵɵtextInterpolate1
} from "./chunk-ASZ7S43O.js";
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

// src/app/pages/ricetta/ricetta.page.ts
function RicettaPage_ion_item_21_Template(rf, ctx) {
  if (rf & 1) {
    \u0275\u0275elementStart(0, "ion-item")(1, "ion-label");
    \u0275\u0275text(2);
    \u0275\u0275elementEnd()();
  }
  if (rf & 2) {
    const ingrediente_r1 = ctx.$implicit;
    \u0275\u0275advance(2);
    \u0275\u0275textInterpolate(ingrediente_r1);
  }
}
function RicettaPage_ion_item_31_Template(rf, ctx) {
  if (rf & 1) {
    \u0275\u0275elementStart(0, "ion-item")(1, "ion-label");
    \u0275\u0275text(2);
    \u0275\u0275elementEnd()();
  }
  if (rf & 2) {
    const step_r2 = ctx.$implicit;
    \u0275\u0275advance(2);
    \u0275\u0275textInterpolate(step_r2);
  }
}
var _RicettaPage = class _RicettaPage {
  constructor(router) {
    this.router = router;
    this.recipe = { titolo: "" };
    this.videoUrl = "";
  }
  ngOnInit() {
  }
  ionViewWillEnter() {
    const currentState = this.router.lastSuccessfulNavigation;
    console.log("ionViewWillEnter ", currentState == null ? void 0 : currentState.extras);
    if (currentState == null ? void 0 : currentState.extras.state) {
      this.recipe = currentState.extras.state["data"];
      console.log(this.recipe);
      this.videoUrl = this.recipe.video;
    } else {
      console.error("Nessuna ricetta passata");
    }
  }
};
_RicettaPage.\u0275fac = function RicettaPage_Factory(__ngFactoryType__) {
  return new (__ngFactoryType__ || _RicettaPage)(\u0275\u0275directiveInject(Router));
};
_RicettaPage.\u0275cmp = /* @__PURE__ */ \u0275\u0275defineComponent({ type: _RicettaPage, selectors: [["app-ricetta"]], standalone: true, features: [\u0275\u0275StandaloneFeature], decls: 41, vars: 9, consts: [[3, "translucent"], ["slot", "start"], [3, "fullscreen"], ["collapse", "condense"], ["size", "large"], [4, "ngFor", "ngForOf"], [3, "videoSrc"]], template: function RicettaPage_Template(rf, ctx) {
  if (rf & 1) {
    \u0275\u0275elementStart(0, "ion-header", 0)(1, "ion-toolbar")(2, "ion-buttons", 1);
    \u0275\u0275element(3, "ion-back-button");
    \u0275\u0275elementEnd();
    \u0275\u0275elementStart(4, "ion-title");
    \u0275\u0275text(5);
    \u0275\u0275elementEnd()()();
    \u0275\u0275elementStart(6, "ion-content", 2)(7, "ion-header", 3)(8, "ion-toolbar")(9, "ion-title", 4);
    \u0275\u0275text(10, "ricetta");
    \u0275\u0275elementEnd()()();
    \u0275\u0275elementStart(11, "ion-grid")(12, "ion-row")(13, "ion-col")(14, "ion-card")(15, "ion-card-content")(16, "ion-list")(17, "ion-list-header")(18, "ion-label")(19, "h2");
    \u0275\u0275text(20, "Ingredienti");
    \u0275\u0275elementEnd()()();
    \u0275\u0275template(21, RicettaPage_ion_item_21_Template, 3, 1, "ion-item", 5);
    \u0275\u0275elementStart(22, "ion-list-header")(23, "ion-chip");
    \u0275\u0275text(24);
    \u0275\u0275elementEnd();
    \u0275\u0275elementStart(25, "ion-chip");
    \u0275\u0275text(26);
    \u0275\u0275elementEnd()();
    \u0275\u0275elementStart(27, "ion-list-header")(28, "ion-label")(29, "h2");
    \u0275\u0275text(30, "Preparazione");
    \u0275\u0275elementEnd()()();
    \u0275\u0275template(31, RicettaPage_ion_item_31_Template, 3, 1, "ion-item", 5);
    \u0275\u0275elementEnd()()()();
    \u0275\u0275elementStart(32, "ion-col");
    \u0275\u0275element(33, "app-plyr-player", 6);
    \u0275\u0275elementEnd()();
    \u0275\u0275elementStart(34, "ion-row")(35, "ion-col")(36, "ion-text")(37, "h2");
    \u0275\u0275text(38, "CONSIGLI DELLO CHEF");
    \u0275\u0275elementEnd()();
    \u0275\u0275elementStart(39, "ion-text");
    \u0275\u0275text(40);
    \u0275\u0275elementEnd()()()()();
  }
  if (rf & 2) {
    \u0275\u0275property("translucent", true);
    \u0275\u0275advance(5);
    \u0275\u0275textInterpolate(ctx.recipe.titolo);
    \u0275\u0275advance();
    \u0275\u0275property("fullscreen", true);
    \u0275\u0275advance(15);
    \u0275\u0275property("ngForOf", ctx.recipe.ingredienti);
    \u0275\u0275advance(3);
    \u0275\u0275textInterpolate1("preparazione: ", ctx.recipe.tempo_di_preparazione, "");
    \u0275\u0275advance(2);
    \u0275\u0275textInterpolate1("cottura: ", ctx.recipe.tempo_cottura, "");
    \u0275\u0275advance(5);
    \u0275\u0275property("ngForOf", ctx.recipe.preparazione);
    \u0275\u0275advance(2);
    \u0275\u0275property("videoSrc", ctx.videoUrl);
    \u0275\u0275advance(7);
    \u0275\u0275textInterpolate1(" ", ctx.recipe.consigli_dello_chef, " ");
  }
}, dependencies: [PlyrPlayerComponent, IonText, IonChip, IonItem, IonList, IonCard, IonCardContent, IonLabel, IonCol, IonRow, IonGrid, IonListHeader, IonButtons, IonBackButton, IonContent, IonHeader, IonTitle, IonToolbar, CommonModule, NgForOf] });
var RicettaPage = _RicettaPage;
(() => {
  (typeof ngDevMode === "undefined" || ngDevMode) && \u0275setClassDebugInfo(RicettaPage, { className: "RicettaPage" });
})();
export {
  RicettaPage
};
//# sourceMappingURL=ricetta.page-WSGEQIGW.js.map
