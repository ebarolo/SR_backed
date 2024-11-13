import {
  APP_INITIALIZER,
  ApplicationRef,
  Injectable,
  InjectionToken,
  Injector,
  IonApp,
  IonRouterOutlet2 as IonRouterOutlet,
  IonicRouteStrategy,
  NEVER,
  NgModule,
  NgZone,
  PLATFORM_ID,
  PreloadAllModules,
  RouteReuseStrategy,
  Subject,
  bootstrapApplication,
  concat,
  defer,
  delay,
  filter,
  from,
  fromEvent,
  isDevMode,
  isPlatformBrowser,
  makeEnvironmentProviders,
  map,
  merge,
  of,
  provideHttpClient,
  provideIonicAngular,
  provideRouter,
  publish,
  setClassMetadata,
  switchMap,
  take,
  tap,
  throwError,
  withPreloading,
  ɵsetClassDebugInfo,
  ɵɵStandaloneFeature,
  ɵɵdefineComponent,
  ɵɵdefineInjectable,
  ɵɵdefineInjector,
  ɵɵdefineNgModule,
  ɵɵelement,
  ɵɵelementEnd,
  ɵɵelementStart,
  ɵɵinject
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
import {
  __spreadValues
} from "./chunk-FSIFXKME.js";

// src/app/app.routes.ts
var routes = [
  {
    path: "",
    loadChildren: () => import("./tabs.routes-N34EUWS4.js").then((m) => m.routes)
  }
];

// src/app/app.component.ts
var _AppComponent = class _AppComponent {
  constructor() {
  }
};
_AppComponent.\u0275fac = function AppComponent_Factory(__ngFactoryType__) {
  return new (__ngFactoryType__ || _AppComponent)();
};
_AppComponent.\u0275cmp = /* @__PURE__ */ \u0275\u0275defineComponent({ type: _AppComponent, selectors: [["app-root"]], standalone: true, features: [\u0275\u0275StandaloneFeature], decls: 2, vars: 0, template: function AppComponent_Template(rf, ctx) {
  if (rf & 1) {
    \u0275\u0275elementStart(0, "ion-app");
    \u0275\u0275element(1, "ion-router-outlet");
    \u0275\u0275elementEnd();
  }
}, dependencies: [IonApp, IonRouterOutlet], encapsulation: 2 });
var AppComponent = _AppComponent;
(() => {
  (typeof ngDevMode === "undefined" || ngDevMode) && \u0275setClassDebugInfo(AppComponent, { className: "AppComponent" });
})();

// node_modules/@angular/service-worker/fesm2022/service-worker.mjs
var ERR_SW_NOT_SUPPORTED = "Service workers are disabled or not supported by this browser";
function errorObservable(message) {
  return defer(() => throwError(new Error(message)));
}
var NgswCommChannel = class {
  constructor(serviceWorker) {
    this.serviceWorker = serviceWorker;
    if (!serviceWorker) {
      this.worker = this.events = this.registration = errorObservable(ERR_SW_NOT_SUPPORTED);
    } else {
      const controllerChangeEvents = fromEvent(serviceWorker, "controllerchange");
      const controllerChanges = controllerChangeEvents.pipe(map(() => serviceWorker.controller));
      const currentController = defer(() => of(serviceWorker.controller));
      const controllerWithChanges = concat(currentController, controllerChanges);
      this.worker = controllerWithChanges.pipe(filter((c) => !!c));
      this.registration = this.worker.pipe(switchMap(() => serviceWorker.getRegistration()));
      const rawEvents = fromEvent(serviceWorker, "message");
      const rawEventPayload = rawEvents.pipe(map((event) => event.data));
      const eventsUnconnected = rawEventPayload.pipe(filter((event) => event && event.type));
      const events = eventsUnconnected.pipe(publish());
      events.connect();
      this.events = events;
    }
  }
  postMessage(action, payload) {
    return this.worker.pipe(take(1), tap((sw) => {
      sw.postMessage(__spreadValues({
        action
      }, payload));
    })).toPromise().then(() => void 0);
  }
  postMessageWithOperation(type, payload, operationNonce) {
    const waitForOperationCompleted = this.waitForOperationCompleted(operationNonce);
    const postMessage = this.postMessage(type, payload);
    return Promise.all([postMessage, waitForOperationCompleted]).then(([, result]) => result);
  }
  generateNonce() {
    return Math.round(Math.random() * 1e7);
  }
  eventsOfType(type) {
    let filterFn;
    if (typeof type === "string") {
      filterFn = (event) => event.type === type;
    } else {
      filterFn = (event) => type.includes(event.type);
    }
    return this.events.pipe(filter(filterFn));
  }
  nextEventOfType(type) {
    return this.eventsOfType(type).pipe(take(1));
  }
  waitForOperationCompleted(nonce) {
    return this.eventsOfType("OPERATION_COMPLETED").pipe(filter((event) => event.nonce === nonce), take(1), map((event) => {
      if (event.result !== void 0) {
        return event.result;
      }
      throw new Error(event.error);
    })).toPromise();
  }
  get isEnabled() {
    return !!this.serviceWorker;
  }
};
var _SwPush = class _SwPush {
  /**
   * True if the Service Worker is enabled (supported by the browser and enabled via
   * `ServiceWorkerModule`).
   */
  get isEnabled() {
    return this.sw.isEnabled;
  }
  constructor(sw) {
    this.sw = sw;
    this.pushManager = null;
    this.subscriptionChanges = new Subject();
    if (!sw.isEnabled) {
      this.messages = NEVER;
      this.notificationClicks = NEVER;
      this.subscription = NEVER;
      return;
    }
    this.messages = this.sw.eventsOfType("PUSH").pipe(map((message) => message.data));
    this.notificationClicks = this.sw.eventsOfType("NOTIFICATION_CLICK").pipe(map((message) => message.data));
    this.pushManager = this.sw.registration.pipe(map((registration) => registration.pushManager));
    const workerDrivenSubscriptions = this.pushManager.pipe(switchMap((pm) => pm.getSubscription()));
    this.subscription = merge(workerDrivenSubscriptions, this.subscriptionChanges);
  }
  /**
   * Subscribes to Web Push Notifications,
   * after requesting and receiving user permission.
   *
   * @param options An object containing the `serverPublicKey` string.
   * @returns A Promise that resolves to the new subscription object.
   */
  requestSubscription(options) {
    if (!this.sw.isEnabled || this.pushManager === null) {
      return Promise.reject(new Error(ERR_SW_NOT_SUPPORTED));
    }
    const pushOptions = {
      userVisibleOnly: true
    };
    let key = this.decodeBase64(options.serverPublicKey.replace(/_/g, "/").replace(/-/g, "+"));
    let applicationServerKey = new Uint8Array(new ArrayBuffer(key.length));
    for (let i = 0; i < key.length; i++) {
      applicationServerKey[i] = key.charCodeAt(i);
    }
    pushOptions.applicationServerKey = applicationServerKey;
    return this.pushManager.pipe(switchMap((pm) => pm.subscribe(pushOptions)), take(1)).toPromise().then((sub) => {
      this.subscriptionChanges.next(sub);
      return sub;
    });
  }
  /**
   * Unsubscribes from Service Worker push notifications.
   *
   * @returns A Promise that is resolved when the operation succeeds, or is rejected if there is no
   *          active subscription or the unsubscribe operation fails.
   */
  unsubscribe() {
    if (!this.sw.isEnabled) {
      return Promise.reject(new Error(ERR_SW_NOT_SUPPORTED));
    }
    const doUnsubscribe = (sub) => {
      if (sub === null) {
        throw new Error("Not subscribed to push notifications.");
      }
      return sub.unsubscribe().then((success) => {
        if (!success) {
          throw new Error("Unsubscribe failed!");
        }
        this.subscriptionChanges.next(null);
      });
    };
    return this.subscription.pipe(take(1), switchMap(doUnsubscribe)).toPromise();
  }
  decodeBase64(input) {
    return atob(input);
  }
};
_SwPush.\u0275fac = function SwPush_Factory(__ngFactoryType__) {
  return new (__ngFactoryType__ || _SwPush)(\u0275\u0275inject(NgswCommChannel));
};
_SwPush.\u0275prov = /* @__PURE__ */ \u0275\u0275defineInjectable({
  token: _SwPush,
  factory: _SwPush.\u0275fac
});
var SwPush = _SwPush;
(() => {
  (typeof ngDevMode === "undefined" || ngDevMode) && setClassMetadata(SwPush, [{
    type: Injectable
  }], () => [{
    type: NgswCommChannel
  }], null);
})();
var _SwUpdate = class _SwUpdate {
  /**
   * True if the Service Worker is enabled (supported by the browser and enabled via
   * `ServiceWorkerModule`).
   */
  get isEnabled() {
    return this.sw.isEnabled;
  }
  constructor(sw) {
    this.sw = sw;
    if (!sw.isEnabled) {
      this.versionUpdates = NEVER;
      this.unrecoverable = NEVER;
      return;
    }
    this.versionUpdates = this.sw.eventsOfType(["VERSION_DETECTED", "VERSION_INSTALLATION_FAILED", "VERSION_READY", "NO_NEW_VERSION_DETECTED"]);
    this.unrecoverable = this.sw.eventsOfType("UNRECOVERABLE_STATE");
  }
  /**
   * Checks for an update and waits until the new version is downloaded from the server and ready
   * for activation.
   *
   * @returns a promise that
   * - resolves to `true` if a new version was found and is ready to be activated.
   * - resolves to `false` if no new version was found
   * - rejects if any error occurs
   */
  checkForUpdate() {
    if (!this.sw.isEnabled) {
      return Promise.reject(new Error(ERR_SW_NOT_SUPPORTED));
    }
    const nonce = this.sw.generateNonce();
    return this.sw.postMessageWithOperation("CHECK_FOR_UPDATES", {
      nonce
    }, nonce);
  }
  /**
   * Updates the current client (i.e. browser tab) to the latest version that is ready for
   * activation.
   *
   * In most cases, you should not use this method and instead should update a client by reloading
   * the page.
   *
   * <div class="alert is-important">
   *
   * Updating a client without reloading can easily result in a broken application due to a version
   * mismatch between the application shell and other page resources,
   * such as lazy-loaded chunks, whose filenames may change between
   * versions.
   *
   * Only use this method, if you are certain it is safe for your specific use case.
   *
   * </div>
   *
   * @returns a promise that
   *  - resolves to `true` if an update was activated successfully
   *  - resolves to `false` if no update was available (for example, the client was already on the
   *    latest version).
   *  - rejects if any error occurs
   */
  activateUpdate() {
    if (!this.sw.isEnabled) {
      return Promise.reject(new Error(ERR_SW_NOT_SUPPORTED));
    }
    const nonce = this.sw.generateNonce();
    return this.sw.postMessageWithOperation("ACTIVATE_UPDATE", {
      nonce
    }, nonce);
  }
};
_SwUpdate.\u0275fac = function SwUpdate_Factory(__ngFactoryType__) {
  return new (__ngFactoryType__ || _SwUpdate)(\u0275\u0275inject(NgswCommChannel));
};
_SwUpdate.\u0275prov = /* @__PURE__ */ \u0275\u0275defineInjectable({
  token: _SwUpdate,
  factory: _SwUpdate.\u0275fac
});
var SwUpdate = _SwUpdate;
(() => {
  (typeof ngDevMode === "undefined" || ngDevMode) && setClassMetadata(SwUpdate, [{
    type: Injectable
  }], () => [{
    type: NgswCommChannel
  }], null);
})();
var SCRIPT = new InjectionToken(ngDevMode ? "NGSW_REGISTER_SCRIPT" : "");
function ngswAppInitializer(injector, script, options, platformId) {
  return () => {
    if (!(isPlatformBrowser(platformId) && "serviceWorker" in navigator && options.enabled !== false)) {
      return;
    }
    const ngZone = injector.get(NgZone);
    const appRef = injector.get(ApplicationRef);
    ngZone.runOutsideAngular(() => {
      const sw = navigator.serviceWorker;
      const onControllerChange = () => {
        var _a;
        return (_a = sw.controller) == null ? void 0 : _a.postMessage({
          action: "INITIALIZE"
        });
      };
      sw.addEventListener("controllerchange", onControllerChange);
      appRef.onDestroy(() => {
        sw.removeEventListener("controllerchange", onControllerChange);
      });
    });
    let readyToRegister$;
    if (typeof options.registrationStrategy === "function") {
      readyToRegister$ = options.registrationStrategy();
    } else {
      const [strategy, ...args] = (options.registrationStrategy || "registerWhenStable:30000").split(":");
      switch (strategy) {
        case "registerImmediately":
          readyToRegister$ = of(null);
          break;
        case "registerWithDelay":
          readyToRegister$ = delayWithTimeout(+args[0] || 0);
          break;
        case "registerWhenStable":
          const whenStable$ = from(injector.get(ApplicationRef).whenStable());
          readyToRegister$ = !args[0] ? whenStable$ : merge(whenStable$, delayWithTimeout(+args[0]));
          break;
        default:
          throw new Error(`Unknown ServiceWorker registration strategy: ${options.registrationStrategy}`);
      }
    }
    ngZone.runOutsideAngular(() => readyToRegister$.pipe(take(1)).subscribe(() => navigator.serviceWorker.register(script, {
      scope: options.scope
    }).catch((err) => console.error("Service worker registration failed with:", err))));
  };
}
function delayWithTimeout(timeout) {
  return of(null).pipe(delay(timeout));
}
function ngswCommChannelFactory(opts, platformId) {
  return new NgswCommChannel(isPlatformBrowser(platformId) && opts.enabled !== false ? navigator.serviceWorker : void 0);
}
var SwRegistrationOptions = class {
};
function provideServiceWorker(script, options = {}) {
  return makeEnvironmentProviders([SwPush, SwUpdate, {
    provide: SCRIPT,
    useValue: script
  }, {
    provide: SwRegistrationOptions,
    useValue: options
  }, {
    provide: NgswCommChannel,
    useFactory: ngswCommChannelFactory,
    deps: [SwRegistrationOptions, PLATFORM_ID]
  }, {
    provide: APP_INITIALIZER,
    useFactory: ngswAppInitializer,
    deps: [Injector, SCRIPT, SwRegistrationOptions, PLATFORM_ID],
    multi: true
  }]);
}
var _ServiceWorkerModule = class _ServiceWorkerModule {
  /**
   * Register the given Angular Service Worker script.
   *
   * If `enabled` is set to `false` in the given options, the module will behave as if service
   * workers are not supported by the browser, and the service worker will not be registered.
   */
  static register(script, options = {}) {
    return {
      ngModule: _ServiceWorkerModule,
      providers: [provideServiceWorker(script, options)]
    };
  }
};
_ServiceWorkerModule.\u0275fac = function ServiceWorkerModule_Factory(__ngFactoryType__) {
  return new (__ngFactoryType__ || _ServiceWorkerModule)();
};
_ServiceWorkerModule.\u0275mod = /* @__PURE__ */ \u0275\u0275defineNgModule({
  type: _ServiceWorkerModule
});
_ServiceWorkerModule.\u0275inj = /* @__PURE__ */ \u0275\u0275defineInjector({
  providers: [SwPush, SwUpdate]
});
var ServiceWorkerModule = _ServiceWorkerModule;
(() => {
  (typeof ngDevMode === "undefined" || ngDevMode) && setClassMetadata(ServiceWorkerModule, [{
    type: NgModule,
    args: [{
      providers: [SwPush, SwUpdate]
    }]
  }], null, null);
})();

// src/main.ts
bootstrapApplication(AppComponent, {
  providers: [
    { provide: RouteReuseStrategy, useClass: IonicRouteStrategy },
    provideHttpClient(),
    provideIonicAngular(),
    provideRouter(routes, withPreloading(PreloadAllModules)),
    provideServiceWorker("ngsw-worker.js", {
      enabled: !isDevMode(),
      registrationStrategy: "registerWhenStable:30000"
    })
  ]
});
/*! Bundled license information:

@angular/service-worker/fesm2022/service-worker.mjs:
  (**
   * @license Angular v18.2.8
   * (c) 2010-2024 Google LLC. https://angular.io/
   * License: MIT
   *)
  (*!
   * @license
   * Copyright Google LLC All Rights Reserved.
   *
   * Use of this source code is governed by an MIT-style license that can be
   * found in the LICENSE file at https://angular.dev/license
   *)
*/
//# sourceMappingURL=main.js.map
