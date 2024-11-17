import {
  PlyrPlayerComponent
} from "./chunk-W6RQMKWS.js";
import {
  AnonymousSubject,
  CommonModule,
  FormsModule,
  IonButton,
  IonCard,
  IonCardContent,
  IonChip,
  IonCol,
  IonContent,
  IonFooter,
  IonGrid,
  IonHeader,
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
  Router,
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

// src/app/components/ricetta/ricetta.component.ts
function RicettaComponent_ion_item_10_Template(rf, ctx) {
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
function RicettaComponent_ion_item_20_Template(rf, ctx) {
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
  constructor(router) {
    this.router = router;
    this.videoUrl = "";
  }
  ngOnInit() {
  }
};
_RicettaComponent.\u0275fac = function RicettaComponent_Factory(__ngFactoryType__) {
  return new (__ngFactoryType__ || _RicettaComponent)(\u0275\u0275directiveInject(Router));
};
_RicettaComponent.\u0275cmp = /* @__PURE__ */ \u0275\u0275defineComponent({ type: _RicettaComponent, selectors: [["app-ricetta"]], inputs: { recipe: "recipe" }, standalone: true, features: [\u0275\u0275StandaloneFeature], decls: 30, vars: 6, consts: [[4, "ngFor", "ngForOf"], [3, "videoSrc"]], template: function RicettaComponent_Template(rf, ctx) {
  if (rf & 1) {
    \u0275\u0275elementStart(0, "ion-grid")(1, "ion-row")(2, "ion-col")(3, "ion-card")(4, "ion-card-content")(5, "ion-list")(6, "ion-list-header")(7, "ion-label")(8, "h2");
    \u0275\u0275text(9, "Ingredienti");
    \u0275\u0275elementEnd()()();
    \u0275\u0275template(10, RicettaComponent_ion_item_10_Template, 3, 1, "ion-item", 0);
    \u0275\u0275elementStart(11, "ion-list-header")(12, "ion-chip");
    \u0275\u0275text(13);
    \u0275\u0275elementEnd();
    \u0275\u0275elementStart(14, "ion-chip");
    \u0275\u0275text(15);
    \u0275\u0275elementEnd()();
    \u0275\u0275elementStart(16, "ion-list-header")(17, "ion-label")(18, "h2");
    \u0275\u0275text(19, "Preparazione");
    \u0275\u0275elementEnd()()();
    \u0275\u0275template(20, RicettaComponent_ion_item_20_Template, 3, 1, "ion-item", 0);
    \u0275\u0275elementEnd()()()();
    \u0275\u0275elementStart(21, "ion-col");
    \u0275\u0275element(22, "app-plyr-player", 1);
    \u0275\u0275elementEnd()();
    \u0275\u0275elementStart(23, "ion-row")(24, "ion-col")(25, "ion-text")(26, "h2");
    \u0275\u0275text(27, "CONSIGLI DELLO CHEF");
    \u0275\u0275elementEnd()();
    \u0275\u0275elementStart(28, "ion-text");
    \u0275\u0275text(29);
    \u0275\u0275elementEnd()()()();
  }
  if (rf & 2) {
    \u0275\u0275advance(10);
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
}, dependencies: [PlyrPlayerComponent, IonText, IonChip, IonItem, IonList, IonCard, IonCardContent, IonLabel, IonCol, IonRow, IonGrid, IonListHeader, CommonModule, NgForOf] });
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
function ChatBotPage_ion_item_14_Template(rf, ctx) {
  if (rf & 1) {
    const _r1 = \u0275\u0275getCurrentView();
    \u0275\u0275elementStart(0, "ion-item", 10);
    \u0275\u0275listener("click", function ChatBotPage_ion_item_14_Template_ion_item_click_0_listener() {
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
function ChatBotPage_ion_col_15_Template(rf, ctx) {
  if (rf & 1) {
    \u0275\u0275elementStart(0, "ion-col");
    \u0275\u0275element(1, "app-ricetta", 11);
    \u0275\u0275elementEnd();
  }
  if (rf & 2) {
    const ctx_r2 = \u0275\u0275nextContext();
    \u0275\u0275advance();
    \u0275\u0275property("recipe", ctx_r2.recipe);
  }
}
var _ChatBotPage = class _ChatBotPage {
  constructor(webSocketService) {
    this.webSocketService = webSocketService;
    this.messaggio = "";
    this.responses = [];
    this.recipe = {};
    this.showRecipe = false;
    this.messageSubscription = new Subscription();
  }
  ngOnInit() {
    this.messageSubscription = this.webSocketService.getMessages().subscribe((message) => {
      var _a;
      console.log(message);
      if (message.type == "chat") {
        console.log(message.content);
        if (((_a = message == null ? void 0 : message.why) == null ? void 0 : _a.memory) !== void 0) {
          message.response = message.content.split("**")[0] + message.content.split("**")[1];
          console.log(message.why.memory.declarative);
        } else {
          message.response = message.content;
        }
        this.responses.push(message);
      }
    });
  }
  openRecipe(recipe) {
    console.log(recipe.why.memory.declarative[0]);
    this.showRecipe = true;
    this.recipe = recipe.why.declarative[0];
  }
  sendMessage() {
    const message = { text: this.messaggio };
    console.log("sendMessage ", this.messaggio);
    this.webSocketService.sendMessage(message);
  }
  ngOnDestroy() {
    this.messageSubscription.unsubscribe();
    this.webSocketService.closeConnection();
  }
};
_ChatBotPage.\u0275fac = function ChatBotPage_Factory(__ngFactoryType__) {
  return new (__ngFactoryType__ || _ChatBotPage)(\u0275\u0275directiveInject(WebSocketService));
};
_ChatBotPage.\u0275cmp = /* @__PURE__ */ \u0275\u0275defineComponent({ type: _ChatBotPage, selectors: [["app-chat_bot"]], standalone: true, features: [\u0275\u0275StandaloneFeature], decls: 24, vars: 5, consts: [[3, "translucent"], [3, "fullscreen"], ["collapse", "condense"], ["size", "large"], ["id", "container"], [3, "click", 4, "ngFor", "ngForOf"], [4, "ngIf"], ["size", "10"], ["type", "text", "fill", "solid", "label", "messaggio", "labelPlacement", "floating", "errorText", "messaggio non valido", "name", "messaggio", "value", "", 3, "ngModelChange", "ngModel"], ["expand", "block", "size", "medium", 3, "click"], [3, "click"], [3, "recipe"]], template: function ChatBotPage_Template(rf, ctx) {
  if (rf & 1) {
    \u0275\u0275elementStart(0, "ion-header", 0)(1, "ion-toolbar")(2, "ion-title");
    \u0275\u0275text(3, "chat-bot");
    \u0275\u0275elementEnd()()();
    \u0275\u0275elementStart(4, "ion-content", 1)(5, "ion-header", 2)(6, "ion-toolbar")(7, "ion-title", 3);
    \u0275\u0275text(8, "chat-bot");
    \u0275\u0275elementEnd()()();
    \u0275\u0275elementStart(9, "div", 4)(10, "ion-grid")(11, "ion-row")(12, "ion-col")(13, "ion-list");
    \u0275\u0275template(14, ChatBotPage_ion_item_14_Template, 3, 1, "ion-item", 5);
    \u0275\u0275elementEnd()();
    \u0275\u0275template(15, ChatBotPage_ion_col_15_Template, 2, 1, "ion-col", 6);
    \u0275\u0275elementEnd()()()();
    \u0275\u0275elementStart(16, "ion-footer")(17, "ion-grid")(18, "ion-row")(19, "ion-col", 7)(20, "ion-input", 8);
    \u0275\u0275twoWayListener("ngModelChange", function ChatBotPage_Template_ion_input_ngModelChange_20_listener($event) {
      \u0275\u0275twoWayBindingSet(ctx.messaggio, $event) || (ctx.messaggio = $event);
      return $event;
    });
    \u0275\u0275elementEnd()();
    \u0275\u0275elementStart(21, "ion-col")(22, "ion-button", 9);
    \u0275\u0275listener("click", function ChatBotPage_Template_ion_button_click_22_listener() {
      return ctx.sendMessage();
    });
    \u0275\u0275text(23, "Messaggio");
    \u0275\u0275elementEnd()()()()();
  }
  if (rf & 2) {
    \u0275\u0275property("translucent", true);
    \u0275\u0275advance(4);
    \u0275\u0275property("fullscreen", true);
    \u0275\u0275advance(10);
    \u0275\u0275property("ngForOf", ctx.responses);
    \u0275\u0275advance();
    \u0275\u0275property("ngIf", ctx.showRecipe);
    \u0275\u0275advance(5);
    \u0275\u0275twoWayProperty("ngModel", ctx.messaggio);
  }
}, dependencies: [RicettaComponent, IonText, IonFooter, IonList, IonButton, IonItem, IonCol, IonGrid, IonRow, IonContent, IonHeader, IonTitle, IonToolbar, CommonModule, NgForOf, NgIf, FormsModule, NgControlStatus, NgModel, IonInput] });
var ChatBotPage = _ChatBotPage;
(() => {
  (typeof ngDevMode === "undefined" || ngDevMode) && \u0275setClassDebugInfo(ChatBotPage, { className: "ChatBotPage" });
})();
export {
  ChatBotPage
};
//# sourceMappingURL=chat_bot.page-BK3YBR3D.js.map
