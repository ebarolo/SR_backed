import {
  AnonymousSubject,
  CommonModule,
  FormsModule,
  IonButton,
  IonCol,
  IonContent,
  IonFooter,
  IonGrid,
  IonHeader,
  IonInput,
  IonItem,
  IonList,
  IonRow,
  IonText,
  IonTitle,
  IonToolbar,
  NgControlStatus,
  NgForOf,
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
  ɵɵelementEnd,
  ɵɵelementStart,
  ɵɵlistener,
  ɵɵproperty,
  ɵɵtemplate,
  ɵɵtext,
  ɵɵtextInterpolate,
  ɵɵtwoWayBindingSet,
  ɵɵtwoWayListener,
  ɵɵtwoWayProperty
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
function ChatBotPage_ion_item_11_Template(rf, ctx) {
  if (rf & 1) {
    \u0275\u0275elementStart(0, "ion-item")(1, "ion-text");
    \u0275\u0275text(2);
    \u0275\u0275elementEnd()();
  }
  if (rf & 2) {
    const message_r1 = ctx.$implicit;
    \u0275\u0275advance(2);
    \u0275\u0275textInterpolate(message_r1.content);
  }
}
var _ChatBotPage = class _ChatBotPage {
  constructor(webSocketService) {
    this.webSocketService = webSocketService;
    this.messaggio = "";
    this.messages = [];
    this.messageSubscription = new Subscription();
  }
  ngOnInit() {
    this.messageSubscription = this.webSocketService.getMessages().subscribe((message) => {
      console.log("response message ", message);
      if (message.type == "chat") {
        this.messages.push(message);
      }
    });
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
_ChatBotPage.\u0275cmp = /* @__PURE__ */ \u0275\u0275defineComponent({ type: _ChatBotPage, selectors: [["app-chat_bot"]], standalone: true, features: [\u0275\u0275StandaloneFeature], decls: 20, vars: 4, consts: [[3, "translucent"], [3, "fullscreen"], ["collapse", "condense"], ["size", "large"], ["id", "container"], [4, "ngFor", "ngForOf"], ["size", "10"], ["type", "text", "fill", "solid", "label", "messaggio", "labelPlacement", "floating", "errorText", "messaggio non valido", "name", "messaggio", "value", "", 3, "ngModelChange", "ngModel"], ["expand", "block", "size", "medium", 3, "click"]], template: function ChatBotPage_Template(rf, ctx) {
  if (rf & 1) {
    \u0275\u0275elementStart(0, "ion-header", 0)(1, "ion-toolbar")(2, "ion-title");
    \u0275\u0275text(3, "chat-bot");
    \u0275\u0275elementEnd()()();
    \u0275\u0275elementStart(4, "ion-content", 1)(5, "ion-header", 2)(6, "ion-toolbar")(7, "ion-title", 3);
    \u0275\u0275text(8, "chat-bot");
    \u0275\u0275elementEnd()()();
    \u0275\u0275elementStart(9, "div", 4)(10, "ion-list");
    \u0275\u0275template(11, ChatBotPage_ion_item_11_Template, 3, 1, "ion-item", 5);
    \u0275\u0275elementEnd()()();
    \u0275\u0275elementStart(12, "ion-footer")(13, "ion-grid")(14, "ion-row")(15, "ion-col", 6)(16, "ion-input", 7);
    \u0275\u0275twoWayListener("ngModelChange", function ChatBotPage_Template_ion_input_ngModelChange_16_listener($event) {
      \u0275\u0275twoWayBindingSet(ctx.messaggio, $event) || (ctx.messaggio = $event);
      return $event;
    });
    \u0275\u0275elementEnd()();
    \u0275\u0275elementStart(17, "ion-col")(18, "ion-button", 8);
    \u0275\u0275listener("click", function ChatBotPage_Template_ion_button_click_18_listener() {
      return ctx.sendMessage();
    });
    \u0275\u0275text(19, "Messaggio");
    \u0275\u0275elementEnd()()()()();
  }
  if (rf & 2) {
    \u0275\u0275property("translucent", true);
    \u0275\u0275advance(4);
    \u0275\u0275property("fullscreen", true);
    \u0275\u0275advance(7);
    \u0275\u0275property("ngForOf", ctx.messages);
    \u0275\u0275advance(5);
    \u0275\u0275twoWayProperty("ngModel", ctx.messaggio);
  }
}, dependencies: [IonText, IonFooter, IonList, IonButton, IonItem, IonCol, IonGrid, IonRow, IonContent, IonHeader, IonTitle, IonToolbar, CommonModule, NgForOf, FormsModule, NgControlStatus, NgModel, IonInput] });
var ChatBotPage = _ChatBotPage;
(() => {
  (typeof ngDevMode === "undefined" || ngDevMode) && \u0275setClassDebugInfo(ChatBotPage, { className: "ChatBotPage" });
})();
export {
  ChatBotPage
};
//# sourceMappingURL=chat_bot.page-RLMGH46K.js.map
