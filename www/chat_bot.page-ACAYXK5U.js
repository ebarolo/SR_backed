import {
  PlyrPlayerComponent
} from "./chunk-DQZA7ITP.js";
import {
  addIcons,
  chevronUpCircle,
  document
} from "./chunk-RXKXPMNG.js";
import {
  AnonymousSubject,
  CommonModule,
  FormsModule,
  IonButton,
  IonCard,
  IonCardContent,
  IonCardHeader,
  IonCardTitle,
  IonChip,
  IonCol,
  IonContent,
  IonFab,
  IonFabButton,
  IonFabList,
  IonFooter,
  IonGrid,
  IonHeader,
  IonIcon,
  IonInput,
  IonItem,
  IonLabel,
  IonList,
  IonListHeader,
  IonRow,
  IonText,
  IonTitle,
  IonToolbar,
  NgControlStatus,
  NgForOf,
  NgIf,
  NgModel,
  Observable,
  ReplaySubject,
  Subject,
  Subscriber,
  Subscription,
  ɵsetClassDebugInfo,
  ɵɵStandaloneFeature,
  ɵɵadvance,
  ɵɵdefineComponent,
  ɵɵdefineInjectable,
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
  ɵɵtextInterpolate,
  ɵɵtextInterpolate1,
  ɵɵtwoWayBindingSet,
  ɵɵtwoWayListener,
  ɵɵtwoWayProperty
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

// src/app/components/ricetta/ricetta.component.ts
function RicettaComponent_ion_item_13_Template(rf, ctx) {
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
function RicettaComponent_ion_item_23_Template(rf, ctx) {
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
var _RicettaComponent = class _RicettaComponent {
  constructor() {
    this.videoUrl = "";
  }
  ngOnInit() {
  }
};
_RicettaComponent.\u0275fac = function RicettaComponent_Factory(__ngFactoryType__) {
  return new (__ngFactoryType__ || _RicettaComponent)();
};
_RicettaComponent.\u0275cmp = /* @__PURE__ */ \u0275\u0275defineComponent({ type: _RicettaComponent, selectors: [["app-ricetta"]], inputs: { recipe: "recipe" }, standalone: true, features: [\u0275\u0275StandaloneFeature], decls: 34, vars: 7, consts: [[4, "ngFor", "ngForOf"], [3, "videoSrc"]], template: function RicettaComponent_Template(rf, ctx) {
  if (rf & 1) {
    \u0275\u0275elementStart(0, "ion-grid")(1, "ion-row")(2, "ion-col")(3, "ion-card")(4, "ion-card-header")(5, "ion-card-title");
    \u0275\u0275text(6);
    \u0275\u0275elementEnd()();
    \u0275\u0275elementStart(7, "ion-card-content")(8, "ion-list")(9, "ion-list-header")(10, "ion-label")(11, "h2");
    \u0275\u0275text(12, "Ingredienti");
    \u0275\u0275elementEnd()()();
    \u0275\u0275template(13, RicettaComponent_ion_item_13_Template, 3, 1, "ion-item", 0);
    \u0275\u0275elementStart(14, "ion-list-header")(15, "ion-chip");
    \u0275\u0275text(16);
    \u0275\u0275elementEnd();
    \u0275\u0275elementStart(17, "ion-chip");
    \u0275\u0275text(18);
    \u0275\u0275elementEnd()();
    \u0275\u0275elementStart(19, "ion-list-header")(20, "ion-label")(21, "h2");
    \u0275\u0275text(22, "Preparazione");
    \u0275\u0275elementEnd()()();
    \u0275\u0275template(23, RicettaComponent_ion_item_23_Template, 3, 1, "ion-item", 0);
    \u0275\u0275elementEnd()()()()();
    \u0275\u0275elementStart(24, "ion-row")(25, "ion-col");
    \u0275\u0275element(26, "app-plyr-player", 1);
    \u0275\u0275elementEnd()();
    \u0275\u0275elementStart(27, "ion-row")(28, "ion-col")(29, "ion-text")(30, "h2");
    \u0275\u0275text(31, "CONSIGLI DELLO CHEF");
    \u0275\u0275elementEnd()();
    \u0275\u0275elementStart(32, "ion-text");
    \u0275\u0275text(33);
    \u0275\u0275elementEnd()()()();
  }
  if (rf & 2) {
    \u0275\u0275advance(6);
    \u0275\u0275textInterpolate(ctx.recipe.metadata.titolo);
    \u0275\u0275advance(7);
    \u0275\u0275property("ngForOf", ctx.recipe.metadata.ingredienti);
    \u0275\u0275advance(3);
    \u0275\u0275textInterpolate1("preparazione: ", ctx.recipe.metadata.tempo_di_preparazione, "");
    \u0275\u0275advance(2);
    \u0275\u0275textInterpolate1("cottura: ", ctx.recipe.tempo_cottura, "");
    \u0275\u0275advance(5);
    \u0275\u0275property("ngForOf", ctx.recipe.metadata.preparazione);
    \u0275\u0275advance(3);
    \u0275\u0275property("videoSrc", ctx.videoUrl);
    \u0275\u0275advance(7);
    \u0275\u0275textInterpolate1(" ", ctx.recipe.metadata.consigli_dello_chef, " ");
  }
}, dependencies: [PlyrPlayerComponent, IonCardTitle, IonText, IonChip, IonItem, IonList, IonCard, IonCardContent, IonCardHeader, IonLabel, IonCol, IonRow, IonGrid, IonListHeader, CommonModule, NgForOf] });
var RicettaComponent = _RicettaComponent;
(() => {
  (typeof ngDevMode === "undefined" || ngDevMode) && \u0275setClassDebugInfo(RicettaComponent, { className: "RicettaComponent" });
})();

// node_modules/rxjs/dist/esm/internal/observable/dom/WebSocketSubject.js
var DEFAULT_WEBSOCKET_CONFIG = {
  url: "",
  deserializer: (e) => JSON.parse(e.data),
  serializer: (value) => JSON.stringify(value)
};
var WEBSOCKETSUBJECT_INVALID_ERROR_OBJECT = "WebSocketSubject.error must be called with an object with an error code, and an optional reason: { code: number, reason: string }";
var WebSocketSubject = class _WebSocketSubject extends AnonymousSubject {
  constructor(urlConfigOrSource, destination) {
    super();
    this._socket = null;
    if (urlConfigOrSource instanceof Observable) {
      this.destination = destination;
      this.source = urlConfigOrSource;
    } else {
      const config = this._config = Object.assign({}, DEFAULT_WEBSOCKET_CONFIG);
      this._output = new Subject();
      if (typeof urlConfigOrSource === "string") {
        config.url = urlConfigOrSource;
      } else {
        for (const key in urlConfigOrSource) {
          if (urlConfigOrSource.hasOwnProperty(key)) {
            config[key] = urlConfigOrSource[key];
          }
        }
      }
      if (!config.WebSocketCtor && WebSocket) {
        config.WebSocketCtor = WebSocket;
      } else if (!config.WebSocketCtor) {
        throw new Error("no WebSocket constructor can be found");
      }
      this.destination = new ReplaySubject();
    }
  }
  lift(operator) {
    const sock = new _WebSocketSubject(this._config, this.destination);
    sock.operator = operator;
    sock.source = this;
    return sock;
  }
  _resetState() {
    this._socket = null;
    if (!this.source) {
      this.destination = new ReplaySubject();
    }
    this._output = new Subject();
  }
  multiplex(subMsg, unsubMsg, messageFilter) {
    const self = this;
    return new Observable((observer) => {
      try {
        self.next(subMsg());
      } catch (err) {
        observer.error(err);
      }
      const subscription = self.subscribe({
        next: (x) => {
          try {
            if (messageFilter(x)) {
              observer.next(x);
            }
          } catch (err) {
            observer.error(err);
          }
        },
        error: (err) => observer.error(err),
        complete: () => observer.complete()
      });
      return () => {
        try {
          self.next(unsubMsg());
        } catch (err) {
          observer.error(err);
        }
        subscription.unsubscribe();
      };
    });
  }
  _connectSocket() {
    const {
      WebSocketCtor,
      protocol,
      url,
      binaryType
    } = this._config;
    const observer = this._output;
    let socket = null;
    try {
      socket = protocol ? new WebSocketCtor(url, protocol) : new WebSocketCtor(url);
      this._socket = socket;
      if (binaryType) {
        this._socket.binaryType = binaryType;
      }
    } catch (e) {
      observer.error(e);
      return;
    }
    const subscription = new Subscription(() => {
      this._socket = null;
      if (socket && socket.readyState === 1) {
        socket.close();
      }
    });
    socket.onopen = (evt) => {
      const {
        _socket
      } = this;
      if (!_socket) {
        socket.close();
        this._resetState();
        return;
      }
      const {
        openObserver
      } = this._config;
      if (openObserver) {
        openObserver.next(evt);
      }
      const queue = this.destination;
      this.destination = Subscriber.create((x) => {
        if (socket.readyState === 1) {
          try {
            const {
              serializer
            } = this._config;
            socket.send(serializer(x));
          } catch (e) {
            this.destination.error(e);
          }
        }
      }, (err) => {
        const {
          closingObserver
        } = this._config;
        if (closingObserver) {
          closingObserver.next(void 0);
        }
        if (err && err.code) {
          socket.close(err.code, err.reason);
        } else {
          observer.error(new TypeError(WEBSOCKETSUBJECT_INVALID_ERROR_OBJECT));
        }
        this._resetState();
      }, () => {
        const {
          closingObserver
        } = this._config;
        if (closingObserver) {
          closingObserver.next(void 0);
        }
        socket.close();
        this._resetState();
      });
      if (queue && queue instanceof ReplaySubject) {
        subscription.add(queue.subscribe(this.destination));
      }
    };
    socket.onerror = (e) => {
      this._resetState();
      observer.error(e);
    };
    socket.onclose = (e) => {
      if (socket === this._socket) {
        this._resetState();
      }
      const {
        closeObserver
      } = this._config;
      if (closeObserver) {
        closeObserver.next(e);
      }
      if (e.wasClean) {
        observer.complete();
      } else {
        observer.error(e);
      }
    };
    socket.onmessage = (e) => {
      try {
        const {
          deserializer
        } = this._config;
        observer.next(deserializer(e));
      } catch (err) {
        observer.error(err);
      }
    };
  }
  _subscribe(subscriber) {
    const {
      source
    } = this;
    if (source) {
      return source.subscribe(subscriber);
    }
    if (!this._socket) {
      this._connectSocket();
    }
    this._output.subscribe(subscriber);
    subscriber.add(() => {
      const {
        _socket
      } = this;
      if (this._output.observers.length === 0) {
        if (_socket && (_socket.readyState === 1 || _socket.readyState === 0)) {
          _socket.close();
        }
        this._resetState();
      }
    });
    return subscriber;
  }
  unsubscribe() {
    const {
      _socket
    } = this;
    if (_socket && (_socket.readyState === 1 || _socket.readyState === 0)) {
      _socket.close();
    }
    this._resetState();
    super.unsubscribe();
  }
};

// node_modules/rxjs/dist/esm/internal/observable/dom/webSocket.js
function webSocket(urlConfigOrSource) {
  return new WebSocketSubject(urlConfigOrSource);
}

// src/app/services/web_socket.service.ts
var _WebSocketService = class _WebSocketService {
  constructor() {
    this.socket$ = webSocket("ws://localhost:1865/ws");
  }
  // Send a message to the server
  sendMessage(message) {
    this.socket$.next(message);
  }
  // Receive messages from the server
  getMessages() {
    return this.socket$.asObservable();
  }
  // Close the WebSocket connection
  closeConnection() {
    this.socket$.complete();
  }
};
_WebSocketService.\u0275fac = function WebSocketService_Factory(__ngFactoryType__) {
  return new (__ngFactoryType__ || _WebSocketService)();
};
_WebSocketService.\u0275prov = /* @__PURE__ */ \u0275\u0275defineInjectable({ token: _WebSocketService, factory: _WebSocketService.\u0275fac, providedIn: "root" });
var WebSocketService = _WebSocketService;

// src/app/pages/chat_bot/chat_bot.page.ts
function ChatBotPage_ion_item_9_Template(rf, ctx) {
  if (rf & 1) {
    const _r1 = \u0275\u0275getCurrentView();
    \u0275\u0275elementStart(0, "ion-item", 12);
    \u0275\u0275listener("click", function ChatBotPage_ion_item_9_Template_ion_item_click_0_listener() {
      const response_r2 = \u0275\u0275restoreView(_r1).$implicit;
      const ctx_r2 = \u0275\u0275nextContext();
      return \u0275\u0275resetView(ctx_r2.openRecipe(response_r2));
    });
    \u0275\u0275elementStart(1, "ion-text");
    \u0275\u0275text(2);
    \u0275\u0275elementEnd()();
  }
  if (rf & 2) {
    const response_r2 = ctx.$implicit;
    \u0275\u0275advance(2);
    \u0275\u0275textInterpolate(response_r2.response);
  }
}
function ChatBotPage_ion_col_10_Template(rf, ctx) {
  if (rf & 1) {
    \u0275\u0275elementStart(0, "ion-col");
    \u0275\u0275element(1, "app-ricetta", 13);
    \u0275\u0275elementEnd();
  }
  if (rf & 2) {
    const ctx_r2 = \u0275\u0275nextContext();
    \u0275\u0275advance();
    \u0275\u0275property("recipe", ctx_r2.objRecipe);
  }
}
var _ChatBotPage = class _ChatBotPage {
  constructor(webSocketService) {
    this.webSocketService = webSocketService;
    this.messaggio = "";
    this.responses = [];
    this.objRecipe = {};
    this.showRecipe = false;
    this.chatStatus = "";
    this.messageSubscription = new Subscription();
    addIcons({ chevronUpCircle, document });
  }
  ngOnInit() {
  }
  ionViewWillEnter() {
    this.messageSubscription = this.webSocketService.getMessages().subscribe((message) => {
      var _a;
      this.chatStatus = "";
      console.log(message);
      if (message.type == "chat") {
        console.log(message.content);
        if (((_a = message == null ? void 0 : message.why) == null ? void 0 : _a.memory) !== void 0) {
          message.response = message.content.split("**")[0];
          console.log("***memoria dichiarativa***");
          console.log(message.why.memory.declarative);
        } else {
          console.log("*** nessuna memoria solo llm ***");
          message.response = message.content;
        }
        this.responses.push(message);
      }
    }, (erorr) => {
      this.chatStatus = "NON DISPONIBILE";
      console.info("error web soket", erorr);
    });
  }
  openRecipe(recipe) {
    var _a;
    console.log("openRecipe", recipe.why.memory.declarative[0]);
    if ((_a = recipe.why.memory.declarative[0].metadata) == null ? void 0 : _a.titolo) {
      this.objRecipe = recipe.why.memory.declarative[0];
      this.showRecipe = true;
    }
  }
  sendMessage() {
    this.showRecipe = false;
    const message = { text: this.messaggio };
    console.log("sendMessage ", this.messaggio);
    this.webSocketService.sendMessage(message);
    this.chatStatus = "PENDING";
  }
  ionViewWillLeave() {
    this.messageSubscription.unsubscribe();
    this.webSocketService.closeConnection();
    this.chatStatus = "CLOSE";
  }
};
_ChatBotPage.\u0275fac = function ChatBotPage_Factory(__ngFactoryType__) {
  return new (__ngFactoryType__ || _ChatBotPage)(\u0275\u0275directiveInject(WebSocketService));
};
_ChatBotPage.\u0275cmp = /* @__PURE__ */ \u0275\u0275defineComponent({ type: _ChatBotPage, selectors: [["app-chat_bot"]], standalone: true, features: [\u0275\u0275StandaloneFeature], decls: 26, vars: 7, consts: [[3, "translucent"], [3, "fullscreen"], [3, "click", 4, "ngFor", "ngForOf"], [4, "ngIf"], ["size", "1"], ["vertical", "bottom", "horizontal", "start"], ["name", "chevron-up-circle"], ["side", "top"], ["name", "document"], ["size", "8"], ["type", "text", "fill", "solid", "label", "messaggio", "labelPlacement", "floating", "errorText", "messaggio non valido", "name", "messaggio", "value", "", 3, "ngModelChange", "ngModel"], ["expand", "block", "size", "medium", 3, "click", "disabled"], [3, "click"], [3, "recipe"]], template: function ChatBotPage_Template(rf, ctx) {
  if (rf & 1) {
    \u0275\u0275elementStart(0, "ion-header", 0)(1, "ion-toolbar")(2, "ion-title");
    \u0275\u0275text(3);
    \u0275\u0275elementEnd()()();
    \u0275\u0275elementStart(4, "ion-content", 1)(5, "ion-grid")(6, "ion-row")(7, "ion-col")(8, "ion-list");
    \u0275\u0275template(9, ChatBotPage_ion_item_9_Template, 3, 1, "ion-item", 2);
    \u0275\u0275elementEnd()();
    \u0275\u0275template(10, ChatBotPage_ion_col_10_Template, 2, 1, "ion-col", 3);
    \u0275\u0275elementEnd()()();
    \u0275\u0275elementStart(11, "ion-footer")(12, "ion-grid")(13, "ion-row")(14, "ion-col", 4)(15, "ion-fab", 5)(16, "ion-fab-button");
    \u0275\u0275element(17, "ion-icon", 6);
    \u0275\u0275elementEnd();
    \u0275\u0275elementStart(18, "ion-fab-list", 7)(19, "ion-fab-button");
    \u0275\u0275element(20, "ion-icon", 8);
    \u0275\u0275elementEnd()()()();
    \u0275\u0275elementStart(21, "ion-col", 9)(22, "ion-input", 10);
    \u0275\u0275twoWayListener("ngModelChange", function ChatBotPage_Template_ion_input_ngModelChange_22_listener($event) {
      \u0275\u0275twoWayBindingSet(ctx.messaggio, $event) || (ctx.messaggio = $event);
      return $event;
    });
    \u0275\u0275elementEnd()();
    \u0275\u0275elementStart(23, "ion-col")(24, "ion-button", 11);
    \u0275\u0275listener("click", function ChatBotPage_Template_ion_button_click_24_listener() {
      return ctx.sendMessage();
    });
    \u0275\u0275text(25, "Messaggio");
    \u0275\u0275elementEnd()()()()();
  }
  if (rf & 2) {
    \u0275\u0275property("translucent", true);
    \u0275\u0275advance(3);
    \u0275\u0275textInterpolate1("chat-bot ", ctx.chatStatus, "");
    \u0275\u0275advance();
    \u0275\u0275property("fullscreen", true);
    \u0275\u0275advance(5);
    \u0275\u0275property("ngForOf", ctx.responses);
    \u0275\u0275advance();
    \u0275\u0275property("ngIf", ctx.showRecipe);
    \u0275\u0275advance(12);
    \u0275\u0275twoWayProperty("ngModel", ctx.messaggio);
    \u0275\u0275advance(2);
    \u0275\u0275property("disabled", ctx.chatStatus !== "");
  }
}, dependencies: [IonIcon, IonFabList, IonFab, IonFabButton, RicettaComponent, IonText, IonFooter, IonList, IonButton, IonItem, IonCol, IonGrid, IonRow, IonContent, IonHeader, IonTitle, IonToolbar, CommonModule, NgForOf, NgIf, FormsModule, NgControlStatus, NgModel, IonInput] });
var ChatBotPage = _ChatBotPage;
(() => {
  (typeof ngDevMode === "undefined" || ngDevMode) && \u0275setClassDebugInfo(ChatBotPage, { className: "ChatBotPage" });
})();
export {
  ChatBotPage
};
//# sourceMappingURL=chat_bot.page-ACAYXK5U.js.map
