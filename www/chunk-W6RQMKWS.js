import {
  ɵsetClassDebugInfo,
  ɵɵNgOnChangesFeature,
  ɵɵStandaloneFeature,
  ɵɵdefineComponent,
  ɵɵelement,
  ɵɵloadQuery,
  ɵɵqueryRefresh,
  ɵɵviewQuery
} from "./chunk-ASZ7S43O.js";
import {
  __commonJS,
  __objRest,
  __spreadProps,
  __spreadValues,
  __toESM
} from "./chunk-FSIFXKME.js";

// node_modules/plyr/dist/plyr.min.js
var require_plyr_min = __commonJS({
  "node_modules/plyr/dist/plyr.min.js"(exports, module) {
    "use strict";
    "object" == typeof navigator && function(e, t) {
      "object" == typeof exports && "undefined" != typeof module ? module.exports = t() : "function" == typeof define && define.amd ? define("Plyr", t) : (e = "undefined" != typeof globalThis ? globalThis : e || self).Plyr = t();
    }(exports, function() {
      "use strict";
      function e(e2, t2, i2) {
        return (t2 = function(e3) {
          var t3 = function(e4, t4) {
            if ("object" != typeof e4 || null === e4) return e4;
            var i3 = e4[Symbol.toPrimitive];
            if (void 0 !== i3) {
              var s2 = i3.call(e4, t4 || "default");
              if ("object" != typeof s2) return s2;
              throw new TypeError("@@toPrimitive must return a primitive value.");
            }
            return ("string" === t4 ? String : Number)(e4);
          }(e3, "string");
          return "symbol" == typeof t3 ? t3 : String(t3);
        }(t2)) in e2 ? Object.defineProperty(e2, t2, {
          value: i2,
          enumerable: true,
          configurable: true,
          writable: true
        }) : e2[t2] = i2, e2;
      }
      function t(e2, t2) {
        for (var i2 = 0; i2 < t2.length; i2++) {
          var s2 = t2[i2];
          s2.enumerable = s2.enumerable || false, s2.configurable = true, "value" in s2 && (s2.writable = true), Object.defineProperty(e2, s2.key, s2);
        }
      }
      function i(e2, t2, i2) {
        return t2 in e2 ? Object.defineProperty(e2, t2, {
          value: i2,
          enumerable: true,
          configurable: true,
          writable: true
        }) : e2[t2] = i2, e2;
      }
      function s(e2, t2) {
        var i2 = Object.keys(e2);
        if (Object.getOwnPropertySymbols) {
          var s2 = Object.getOwnPropertySymbols(e2);
          t2 && (s2 = s2.filter(function(t3) {
            return Object.getOwnPropertyDescriptor(e2, t3).enumerable;
          })), i2.push.apply(i2, s2);
        }
        return i2;
      }
      function n(e2) {
        for (var t2 = 1; t2 < arguments.length; t2++) {
          var n2 = null != arguments[t2] ? arguments[t2] : {};
          t2 % 2 ? s(Object(n2), true).forEach(function(t3) {
            i(e2, t3, n2[t3]);
          }) : Object.getOwnPropertyDescriptors ? Object.defineProperties(e2, Object.getOwnPropertyDescriptors(n2)) : s(Object(n2)).forEach(function(t3) {
            Object.defineProperty(e2, t3, Object.getOwnPropertyDescriptor(n2, t3));
          });
        }
        return e2;
      }
      var a = {
        addCSS: true,
        thumbWidth: 15,
        watch: true
      };
      var l = function(e2) {
        return null != e2 ? e2.constructor : null;
      }, r = function(e2, t2) {
        return !!(e2 && t2 && e2 instanceof t2);
      }, o = function(e2) {
        return null == e2;
      }, c = function(e2) {
        return l(e2) === Object;
      }, u = function(e2) {
        return l(e2) === String;
      }, h = function(e2) {
        return Array.isArray(e2);
      }, d = function(e2) {
        return r(e2, NodeList);
      }, m = {
        nullOrUndefined: o,
        object: c,
        number: function(e2) {
          return l(e2) === Number && !Number.isNaN(e2);
        },
        string: u,
        boolean: function(e2) {
          return l(e2) === Boolean;
        },
        function: function(e2) {
          return l(e2) === Function;
        },
        array: h,
        nodeList: d,
        element: function(e2) {
          return r(e2, Element);
        },
        event: function(e2) {
          return r(e2, Event);
        },
        empty: function(e2) {
          return o(e2) || (u(e2) || h(e2) || d(e2)) && !e2.length || c(e2) && !Object.keys(e2).length;
        }
      };
      function p(e2, t2) {
        if (1 > t2) {
          var i2 = function(e3) {
            var t3 = "".concat(e3).match(/(?:\.(\d+))?(?:[eE]([+-]?\d+))?$/);
            return t3 ? Math.max(0, (t3[1] ? t3[1].length : 0) - (t3[2] ? +t3[2] : 0)) : 0;
          }(t2);
          return parseFloat(e2.toFixed(i2));
        }
        return Math.round(e2 / t2) * t2;
      }
      var g = function() {
        function e2(t2, i2) {
          (function(e3, t3) {
            if (!(e3 instanceof t3)) throw new TypeError("Cannot call a class as a function");
          })(this, e2), m.element(t2) ? this.element = t2 : m.string(t2) && (this.element = document.querySelector(t2)), m.element(this.element) && m.empty(this.element.rangeTouch) && (this.config = n({}, a, {}, i2), this.init());
        }
        return function(e3, i2, s2) {
          i2 && t(e3.prototype, i2), s2 && t(e3, s2);
        }(e2, [{
          key: "init",
          value: function() {
            e2.enabled && (this.config.addCSS && (this.element.style.userSelect = "none", this.element.style.webKitUserSelect = "none", this.element.style.touchAction = "manipulation"), this.listeners(true), this.element.rangeTouch = this);
          }
        }, {
          key: "destroy",
          value: function() {
            e2.enabled && (this.config.addCSS && (this.element.style.userSelect = "", this.element.style.webKitUserSelect = "", this.element.style.touchAction = ""), this.listeners(false), this.element.rangeTouch = null);
          }
        }, {
          key: "listeners",
          value: function(e3) {
            var t2 = this, i2 = e3 ? "addEventListener" : "removeEventListener";
            ["touchstart", "touchmove", "touchend"].forEach(function(e4) {
              t2.element[i2](e4, function(e5) {
                return t2.set(e5);
              }, false);
            });
          }
        }, {
          key: "get",
          value: function(t2) {
            if (!e2.enabled || !m.event(t2)) return null;
            var i2, s2 = t2.target, n2 = t2.changedTouches[0], a2 = parseFloat(s2.getAttribute("min")) || 0, l2 = parseFloat(s2.getAttribute("max")) || 100, r2 = parseFloat(s2.getAttribute("step")) || 1, o2 = s2.getBoundingClientRect(), c2 = 100 / o2.width * (this.config.thumbWidth / 2) / 100;
            return 0 > (i2 = 100 / o2.width * (n2.clientX - o2.left)) ? i2 = 0 : 100 < i2 && (i2 = 100), 50 > i2 ? i2 -= (100 - 2 * i2) * c2 : 50 < i2 && (i2 += 2 * (i2 - 50) * c2), a2 + p(i2 / 100 * (l2 - a2), r2);
          }
        }, {
          key: "set",
          value: function(t2) {
            e2.enabled && m.event(t2) && !t2.target.disabled && (t2.preventDefault(), t2.target.value = this.get(t2), function(e3, t3) {
              if (e3 && t3) {
                var i2 = new Event(t3, {
                  bubbles: true
                });
                e3.dispatchEvent(i2);
              }
            }(t2.target, "touchend" === t2.type ? "change" : "input"));
          }
        }], [{
          key: "setup",
          value: function(t2) {
            var i2 = 1 < arguments.length && void 0 !== arguments[1] ? arguments[1] : {}, s2 = null;
            if (m.empty(t2) || m.string(t2) ? s2 = Array.from(document.querySelectorAll(m.string(t2) ? t2 : 'input[type="range"]')) : m.element(t2) ? s2 = [t2] : m.nodeList(t2) ? s2 = Array.from(t2) : m.array(t2) && (s2 = t2.filter(m.element)), m.empty(s2)) return null;
            var l2 = n({}, a, {}, i2);
            if (m.string(t2) && l2.watch) {
              var r2 = new MutationObserver(function(i3) {
                Array.from(i3).forEach(function(i4) {
                  Array.from(i4.addedNodes).forEach(function(i5) {
                    m.element(i5) && function(e3, t3) {
                      return (function() {
                        return Array.from(document.querySelectorAll(t3)).includes(this);
                      }).call(e3, t3);
                    }(i5, t2) && new e2(i5, l2);
                  });
                });
              });
              r2.observe(document.body, {
                childList: true,
                subtree: true
              });
            }
            return s2.map(function(t3) {
              return new e2(t3, i2);
            });
          }
        }, {
          key: "enabled",
          get: function() {
            return "ontouchstart" in document.documentElement;
          }
        }]), e2;
      }();
      const f = (e2) => null != e2 ? e2.constructor : null, y = (e2, t2) => Boolean(e2 && t2 && e2 instanceof t2), b = (e2) => null == e2, v = (e2) => f(e2) === Object, w = (e2) => f(e2) === String, T = (e2) => "function" == typeof e2, k = (e2) => Array.isArray(e2), C = (e2) => y(e2, NodeList), A = (e2) => b(e2) || (w(e2) || k(e2) || C(e2)) && !e2.length || v(e2) && !Object.keys(e2).length;
      var S = {
        nullOrUndefined: b,
        object: v,
        number: (e2) => f(e2) === Number && !Number.isNaN(e2),
        string: w,
        boolean: (e2) => f(e2) === Boolean,
        function: T,
        array: k,
        weakMap: (e2) => y(e2, WeakMap),
        nodeList: C,
        element: (e2) => null !== e2 && "object" == typeof e2 && 1 === e2.nodeType && "object" == typeof e2.style && "object" == typeof e2.ownerDocument,
        textNode: (e2) => f(e2) === Text,
        event: (e2) => y(e2, Event),
        keyboardEvent: (e2) => y(e2, KeyboardEvent),
        cue: (e2) => y(e2, window.TextTrackCue) || y(e2, window.VTTCue),
        track: (e2) => y(e2, TextTrack) || !b(e2) && w(e2.kind),
        promise: (e2) => y(e2, Promise) && T(e2.then),
        url: (e2) => {
          if (y(e2, window.URL)) return true;
          if (!w(e2)) return false;
          let t2 = e2;
          e2.startsWith("http://") && e2.startsWith("https://") || (t2 = `http://${e2}`);
          try {
            return !A(new URL(t2).hostname);
          } catch (e3) {
            return false;
          }
        },
        empty: A
      };
      const E = (() => {
        const e2 = document.createElement("span"), t2 = {
          WebkitTransition: "webkitTransitionEnd",
          MozTransition: "transitionend",
          OTransition: "oTransitionEnd otransitionend",
          transition: "transitionend"
        }, i2 = Object.keys(t2).find((t3) => void 0 !== e2.style[t3]);
        return !!S.string(i2) && t2[i2];
      })();
      function P(e2, t2) {
        setTimeout(() => {
          try {
            e2.hidden = true, e2.offsetHeight, e2.hidden = false;
          } catch (e3) {
          }
        }, t2);
      }
      var M = {
        isIE: Boolean(window.document.documentMode),
        isEdge: /Edge/g.test(navigator.userAgent),
        isWebKit: "WebkitAppearance" in document.documentElement.style && !/Edge/g.test(navigator.userAgent),
        isIPhone: /iPhone|iPod/gi.test(navigator.userAgent) && navigator.maxTouchPoints > 1,
        isIPadOS: "MacIntel" === navigator.platform && navigator.maxTouchPoints > 1,
        isIos: /iPad|iPhone|iPod/gi.test(navigator.userAgent) && navigator.maxTouchPoints > 1
      };
      function N(e2, t2) {
        return t2.split(".").reduce((e3, t3) => e3 && e3[t3], e2);
      }
      function x(e2 = {}, ...t2) {
        if (!t2.length) return e2;
        const i2 = t2.shift();
        return S.object(i2) ? (Object.keys(i2).forEach((t3) => {
          S.object(i2[t3]) ? (Object.keys(e2).includes(t3) || Object.assign(e2, {
            [t3]: {}
          }), x(e2[t3], i2[t3])) : Object.assign(e2, {
            [t3]: i2[t3]
          });
        }), x(e2, ...t2)) : e2;
      }
      function L(e2, t2) {
        const i2 = e2.length ? e2 : [e2];
        Array.from(i2).reverse().forEach((e3, i3) => {
          const s2 = i3 > 0 ? t2.cloneNode(true) : t2, n2 = e3.parentNode, a2 = e3.nextSibling;
          s2.appendChild(e3), a2 ? n2.insertBefore(s2, a2) : n2.appendChild(s2);
        });
      }
      function I(e2, t2) {
        S.element(e2) && !S.empty(t2) && Object.entries(t2).filter(([, e3]) => !S.nullOrUndefined(e3)).forEach(([t3, i2]) => e2.setAttribute(t3, i2));
      }
      function $(e2, t2, i2) {
        const s2 = document.createElement(e2);
        return S.object(t2) && I(s2, t2), S.string(i2) && (s2.innerText = i2), s2;
      }
      function _(e2, t2, i2, s2) {
        S.element(t2) && t2.appendChild($(e2, i2, s2));
      }
      function O(e2) {
        S.nodeList(e2) || S.array(e2) ? Array.from(e2).forEach(O) : S.element(e2) && S.element(e2.parentNode) && e2.parentNode.removeChild(e2);
      }
      function j(e2) {
        if (!S.element(e2)) return;
        let {
          length: t2
        } = e2.childNodes;
        for (; t2 > 0; ) e2.removeChild(e2.lastChild), t2 -= 1;
      }
      function q(e2, t2) {
        return S.element(t2) && S.element(t2.parentNode) && S.element(e2) ? (t2.parentNode.replaceChild(e2, t2), e2) : null;
      }
      function D(e2, t2) {
        if (!S.string(e2) || S.empty(e2)) return {};
        const i2 = {}, s2 = x({}, t2);
        return e2.split(",").forEach((e3) => {
          const t3 = e3.trim(), n2 = t3.replace(".", ""), a2 = t3.replace(/[[\]]/g, "").split("="), [l2] = a2, r2 = a2.length > 1 ? a2[1].replace(/["']/g, "") : "";
          switch (t3.charAt(0)) {
            case ".":
              S.string(s2.class) ? i2.class = `${s2.class} ${n2}` : i2.class = n2;
              break;
            case "#":
              i2.id = t3.replace("#", "");
              break;
            case "[":
              i2[l2] = r2;
          }
        }), x(s2, i2);
      }
      function H(e2, t2) {
        if (!S.element(e2)) return;
        let i2 = t2;
        S.boolean(i2) || (i2 = !e2.hidden), e2.hidden = i2;
      }
      function R(e2, t2, i2) {
        if (S.nodeList(e2)) return Array.from(e2).map((e3) => R(e3, t2, i2));
        if (S.element(e2)) {
          let s2 = "toggle";
          return void 0 !== i2 && (s2 = i2 ? "add" : "remove"), e2.classList[s2](t2), e2.classList.contains(t2);
        }
        return false;
      }
      function F(e2, t2) {
        return S.element(e2) && e2.classList.contains(t2);
      }
      function V(e2, t2) {
        const {
          prototype: i2
        } = Element;
        return (i2.matches || i2.webkitMatchesSelector || i2.mozMatchesSelector || i2.msMatchesSelector || function() {
          return Array.from(document.querySelectorAll(t2)).includes(this);
        }).call(e2, t2);
      }
      function U(e2) {
        return this.elements.container.querySelectorAll(e2);
      }
      function B(e2) {
        return this.elements.container.querySelector(e2);
      }
      function W(e2 = null, t2 = false) {
        S.element(e2) && e2.focus({
          preventScroll: true,
          focusVisible: t2
        });
      }
      const z = {
        "audio/ogg": "vorbis",
        "audio/wav": "1",
        "video/webm": "vp8, vorbis",
        "video/mp4": "avc1.42E01E, mp4a.40.2",
        "video/ogg": "theora"
      }, K = {
        audio: "canPlayType" in document.createElement("audio"),
        video: "canPlayType" in document.createElement("video"),
        check(e2, t2) {
          const i2 = K[e2] || "html5" !== t2;
          return {
            api: i2,
            ui: i2 && K.rangeInput
          };
        },
        pip: !(M.isIPhone || !S.function($("video").webkitSetPresentationMode) && (!document.pictureInPictureEnabled || $("video").disablePictureInPicture)),
        airplay: S.function(window.WebKitPlaybackTargetAvailabilityEvent),
        playsinline: "playsInline" in document.createElement("video"),
        mime(e2) {
          if (S.empty(e2)) return false;
          const [t2] = e2.split("/");
          let i2 = e2;
          if (!this.isHTML5 || t2 !== this.type) return false;
          Object.keys(z).includes(i2) && (i2 += `; codecs="${z[e2]}"`);
          try {
            return Boolean(i2 && this.media.canPlayType(i2).replace(/no/, ""));
          } catch (e3) {
            return false;
          }
        },
        textTracks: "textTracks" in document.createElement("video"),
        rangeInput: (() => {
          const e2 = document.createElement("input");
          return e2.type = "range", "range" === e2.type;
        })(),
        touch: "ontouchstart" in document.documentElement,
        transitions: false !== E,
        reducedMotion: "matchMedia" in window && window.matchMedia("(prefers-reduced-motion)").matches
      }, Y = (() => {
        let e2 = false;
        try {
          const t2 = Object.defineProperty({}, "passive", {
            get: () => (e2 = true, null)
          });
          window.addEventListener("test", null, t2), window.removeEventListener("test", null, t2);
        } catch (e3) {
        }
        return e2;
      })();
      function Q(e2, t2, i2, s2 = false, n2 = true, a2 = false) {
        if (!e2 || !("addEventListener" in e2) || S.empty(t2) || !S.function(i2)) return;
        const l2 = t2.split(" ");
        let r2 = a2;
        Y && (r2 = {
          passive: n2,
          capture: a2
        }), l2.forEach((t3) => {
          this && this.eventListeners && s2 && this.eventListeners.push({
            element: e2,
            type: t3,
            callback: i2,
            options: r2
          }), e2[s2 ? "addEventListener" : "removeEventListener"](t3, i2, r2);
        });
      }
      function X(e2, t2 = "", i2, s2 = true, n2 = false) {
        Q.call(this, e2, t2, i2, true, s2, n2);
      }
      function J(e2, t2 = "", i2, s2 = true, n2 = false) {
        Q.call(this, e2, t2, i2, false, s2, n2);
      }
      function G(e2, t2 = "", i2, s2 = true, n2 = false) {
        const a2 = (...l2) => {
          J(e2, t2, a2, s2, n2), i2.apply(this, l2);
        };
        Q.call(this, e2, t2, a2, true, s2, n2);
      }
      function Z(e2, t2 = "", i2 = false, s2 = {}) {
        if (!S.element(e2) || S.empty(t2)) return;
        const n2 = new CustomEvent(t2, {
          bubbles: i2,
          detail: __spreadProps(__spreadValues({}, s2), {
            plyr: this
          })
        });
        e2.dispatchEvent(n2);
      }
      function ee() {
        this && this.eventListeners && (this.eventListeners.forEach((e2) => {
          const {
            element: t2,
            type: i2,
            callback: s2,
            options: n2
          } = e2;
          t2.removeEventListener(i2, s2, n2);
        }), this.eventListeners = []);
      }
      function te() {
        return new Promise((e2) => this.ready ? setTimeout(e2, 0) : X.call(this, this.elements.container, "ready", e2)).then(() => {
        });
      }
      function ie(e2) {
        S.promise(e2) && e2.then(null, () => {
        });
      }
      function se(e2) {
        return S.array(e2) ? e2.filter((t2, i2) => e2.indexOf(t2) === i2) : e2;
      }
      function ne(e2, t2) {
        return S.array(e2) && e2.length ? e2.reduce((e3, i2) => Math.abs(i2 - t2) < Math.abs(e3 - t2) ? i2 : e3) : null;
      }
      function ae(e2) {
        return !(!window || !window.CSS) && window.CSS.supports(e2);
      }
      const le = [[1, 1], [4, 3], [3, 4], [5, 4], [4, 5], [3, 2], [2, 3], [16, 10], [10, 16], [16, 9], [9, 16], [21, 9], [9, 21], [32, 9], [9, 32]].reduce((e2, [t2, i2]) => __spreadProps(__spreadValues({}, e2), {
        [t2 / i2]: [t2, i2]
      }), {});
      function re(e2) {
        if (!(S.array(e2) || S.string(e2) && e2.includes(":"))) return false;
        return (S.array(e2) ? e2 : e2.split(":")).map(Number).every(S.number);
      }
      function oe(e2) {
        if (!S.array(e2) || !e2.every(S.number)) return null;
        const [t2, i2] = e2, s2 = (e3, t3) => 0 === t3 ? e3 : s2(t3, e3 % t3), n2 = s2(t2, i2);
        return [t2 / n2, i2 / n2];
      }
      function ce(e2) {
        const t2 = (e3) => re(e3) ? e3.split(":").map(Number) : null;
        let i2 = t2(e2);
        if (null === i2 && (i2 = t2(this.config.ratio)), null === i2 && !S.empty(this.embed) && S.array(this.embed.ratio) && ({
          ratio: i2
        } = this.embed), null === i2 && this.isHTML5) {
          const {
            videoWidth: e3,
            videoHeight: t3
          } = this.media;
          i2 = [e3, t3];
        }
        return oe(i2);
      }
      function ue(e2) {
        if (!this.isVideo) return {};
        const {
          wrapper: t2
        } = this.elements, i2 = ce.call(this, e2);
        if (!S.array(i2)) return {};
        const [s2, n2] = oe(i2), a2 = 100 / s2 * n2;
        if (ae(`aspect-ratio: ${s2}/${n2}`) ? t2.style.aspectRatio = `${s2}/${n2}` : t2.style.paddingBottom = `${a2}%`, this.isVimeo && !this.config.vimeo.premium && this.supported.ui) {
          const e3 = 100 / this.media.offsetWidth * parseInt(window.getComputedStyle(this.media).paddingBottom, 10), i3 = (e3 - a2) / (e3 / 50);
          this.fullscreen.active ? t2.style.paddingBottom = null : this.media.style.transform = `translateY(-${i3}%)`;
        } else this.isHTML5 && t2.classList.add(this.config.classNames.videoFixedRatio);
        return {
          padding: a2,
          ratio: i2
        };
      }
      function he(e2, t2, i2 = 0.05) {
        const s2 = e2 / t2, n2 = ne(Object.keys(le), s2);
        return Math.abs(n2 - s2) <= i2 ? le[n2] : [e2, t2];
      }
      const de = {
        getSources() {
          if (!this.isHTML5) return [];
          return Array.from(this.media.querySelectorAll("source")).filter((e2) => {
            const t2 = e2.getAttribute("type");
            return !!S.empty(t2) || K.mime.call(this, t2);
          });
        },
        getQualityOptions() {
          return this.config.quality.forced ? this.config.quality.options : de.getSources.call(this).map((e2) => Number(e2.getAttribute("size"))).filter(Boolean);
        },
        setup() {
          if (!this.isHTML5) return;
          const e2 = this;
          e2.options.speed = e2.config.speed.options, S.empty(this.config.ratio) || ue.call(e2), Object.defineProperty(e2.media, "quality", {
            get() {
              const t2 = de.getSources.call(e2).find((t3) => t3.getAttribute("src") === e2.source);
              return t2 && Number(t2.getAttribute("size"));
            },
            set(t2) {
              if (e2.quality !== t2) {
                if (e2.config.quality.forced && S.function(e2.config.quality.onChange)) e2.config.quality.onChange(t2);
                else {
                  const i2 = de.getSources.call(e2).find((e3) => Number(e3.getAttribute("size")) === t2);
                  if (!i2) return;
                  const {
                    currentTime: s2,
                    paused: n2,
                    preload: a2,
                    readyState: l2,
                    playbackRate: r2
                  } = e2.media;
                  e2.media.src = i2.getAttribute("src"), ("none" !== a2 || l2) && (e2.once("loadedmetadata", () => {
                    e2.speed = r2, e2.currentTime = s2, n2 || ie(e2.play());
                  }), e2.media.load());
                }
                Z.call(e2, e2.media, "qualitychange", false, {
                  quality: t2
                });
              }
            }
          });
        },
        cancelRequests() {
          this.isHTML5 && (O(de.getSources.call(this)), this.media.setAttribute("src", this.config.blankVideo), this.media.load(), this.debug.log("Cancelled network requests"));
        }
      };
      function me(e2, ...t2) {
        return S.empty(e2) ? e2 : e2.toString().replace(/{(\d+)}/g, (e3, i2) => t2[i2].toString());
      }
      const pe = (e2 = "", t2 = "", i2 = "") => e2.replace(new RegExp(t2.toString().replace(/([.*+?^=!:${}()|[\]/\\])/g, "\\$1"), "g"), i2.toString()), ge = (e2 = "") => e2.toString().replace(/\w\S*/g, (e3) => e3.charAt(0).toUpperCase() + e3.slice(1).toLowerCase());
      function fe(e2 = "") {
        let t2 = e2.toString();
        return t2 = function(e3 = "") {
          let t3 = e3.toString();
          return t3 = pe(t3, "-", " "), t3 = pe(t3, "_", " "), t3 = ge(t3), pe(t3, " ", "");
        }(t2), t2.charAt(0).toLowerCase() + t2.slice(1);
      }
      function ye(e2) {
        const t2 = document.createElement("div");
        return t2.appendChild(e2), t2.innerHTML;
      }
      const be = {
        pip: "PIP",
        airplay: "AirPlay",
        html5: "HTML5",
        vimeo: "Vimeo",
        youtube: "YouTube"
      }, ve = {
        get(e2 = "", t2 = {}) {
          if (S.empty(e2) || S.empty(t2)) return "";
          let i2 = N(t2.i18n, e2);
          if (S.empty(i2)) return Object.keys(be).includes(e2) ? be[e2] : "";
          const s2 = {
            "{seektime}": t2.seekTime,
            "{title}": t2.title
          };
          return Object.entries(s2).forEach(([e3, t3]) => {
            i2 = pe(i2, e3, t3);
          }), i2;
        }
      };
      class we {
        constructor(t2) {
          e(this, "get", (e2) => {
            if (!we.supported || !this.enabled) return null;
            const t3 = window.localStorage.getItem(this.key);
            if (S.empty(t3)) return null;
            const i2 = JSON.parse(t3);
            return S.string(e2) && e2.length ? i2[e2] : i2;
          }), e(this, "set", (e2) => {
            if (!we.supported || !this.enabled) return;
            if (!S.object(e2)) return;
            let t3 = this.get();
            S.empty(t3) && (t3 = {}), x(t3, e2);
            try {
              window.localStorage.setItem(this.key, JSON.stringify(t3));
            } catch (e3) {
            }
          }), this.enabled = t2.config.storage.enabled, this.key = t2.config.storage.key;
        }
        static get supported() {
          try {
            if (!("localStorage" in window)) return false;
            const e2 = "___test";
            return window.localStorage.setItem(e2, e2), window.localStorage.removeItem(e2), true;
          } catch (e2) {
            return false;
          }
        }
      }
      function Te(e2, t2 = "text") {
        return new Promise((i2, s2) => {
          try {
            const s3 = new XMLHttpRequest();
            if (!("withCredentials" in s3)) return;
            s3.addEventListener("load", () => {
              if ("text" === t2) try {
                i2(JSON.parse(s3.responseText));
              } catch (e3) {
                i2(s3.responseText);
              }
              else i2(s3.response);
            }), s3.addEventListener("error", () => {
              throw new Error(s3.status);
            }), s3.open("GET", e2, true), s3.responseType = t2, s3.send();
          } catch (e3) {
            s2(e3);
          }
        });
      }
      function ke(e2, t2) {
        if (!S.string(e2)) return;
        const i2 = "cache", s2 = S.string(t2);
        let n2 = false;
        const a2 = () => null !== document.getElementById(t2), l2 = (e3, t3) => {
          e3.innerHTML = t3, s2 && a2() || document.body.insertAdjacentElement("afterbegin", e3);
        };
        if (!s2 || !a2()) {
          const a3 = we.supported, r2 = document.createElement("div");
          if (r2.setAttribute("hidden", ""), s2 && r2.setAttribute("id", t2), a3) {
            const e3 = window.localStorage.getItem(`${i2}-${t2}`);
            if (n2 = null !== e3, n2) {
              const t3 = JSON.parse(e3);
              l2(r2, t3.content);
            }
          }
          Te(e2).then((e3) => {
            if (!S.empty(e3)) {
              if (a3) try {
                window.localStorage.setItem(`${i2}-${t2}`, JSON.stringify({
                  content: e3
                }));
              } catch (e4) {
              }
              l2(r2, e3);
            }
          }).catch(() => {
          });
        }
      }
      const Ce = (e2) => Math.trunc(e2 / 60 / 60 % 60, 10), Ae = (e2) => Math.trunc(e2 / 60 % 60, 10), Se = (e2) => Math.trunc(e2 % 60, 10);
      function Ee(e2 = 0, t2 = false, i2 = false) {
        if (!S.number(e2)) return Ee(void 0, t2, i2);
        const s2 = (e3) => `0${e3}`.slice(-2);
        let n2 = Ce(e2);
        const a2 = Ae(e2), l2 = Se(e2);
        return n2 = t2 || n2 > 0 ? `${n2}:` : "", `${i2 && e2 > 0 ? "-" : ""}${n2}${s2(a2)}:${s2(l2)}`;
      }
      const Pe = {
        getIconUrl() {
          const e2 = new URL(this.config.iconUrl, window.location), t2 = window.location.host ? window.location.host : window.top.location.host, i2 = e2.host !== t2 || M.isIE && !window.svg4everybody;
          return {
            url: this.config.iconUrl,
            cors: i2
          };
        },
        findElements() {
          try {
            return this.elements.controls = B.call(this, this.config.selectors.controls.wrapper), this.elements.buttons = {
              play: U.call(this, this.config.selectors.buttons.play),
              pause: B.call(this, this.config.selectors.buttons.pause),
              restart: B.call(this, this.config.selectors.buttons.restart),
              rewind: B.call(this, this.config.selectors.buttons.rewind),
              fastForward: B.call(this, this.config.selectors.buttons.fastForward),
              mute: B.call(this, this.config.selectors.buttons.mute),
              pip: B.call(this, this.config.selectors.buttons.pip),
              airplay: B.call(this, this.config.selectors.buttons.airplay),
              settings: B.call(this, this.config.selectors.buttons.settings),
              captions: B.call(this, this.config.selectors.buttons.captions),
              fullscreen: B.call(this, this.config.selectors.buttons.fullscreen)
            }, this.elements.progress = B.call(this, this.config.selectors.progress), this.elements.inputs = {
              seek: B.call(this, this.config.selectors.inputs.seek),
              volume: B.call(this, this.config.selectors.inputs.volume)
            }, this.elements.display = {
              buffer: B.call(this, this.config.selectors.display.buffer),
              currentTime: B.call(this, this.config.selectors.display.currentTime),
              duration: B.call(this, this.config.selectors.display.duration)
            }, S.element(this.elements.progress) && (this.elements.display.seekTooltip = this.elements.progress.querySelector(`.${this.config.classNames.tooltip}`)), true;
          } catch (e2) {
            return this.debug.warn("It looks like there is a problem with your custom controls HTML", e2), this.toggleNativeControls(true), false;
          }
        },
        createIcon(e2, t2) {
          const i2 = "http://www.w3.org/2000/svg", s2 = Pe.getIconUrl.call(this), n2 = `${s2.cors ? "" : s2.url}#${this.config.iconPrefix}`, a2 = document.createElementNS(i2, "svg");
          I(a2, x(t2, {
            "aria-hidden": "true",
            focusable: "false"
          }));
          const l2 = document.createElementNS(i2, "use"), r2 = `${n2}-${e2}`;
          return "href" in l2 && l2.setAttributeNS("http://www.w3.org/1999/xlink", "href", r2), l2.setAttributeNS("http://www.w3.org/1999/xlink", "xlink:href", r2), a2.appendChild(l2), a2;
        },
        createLabel(e2, t2 = {}) {
          const i2 = ve.get(e2, this.config);
          return $("span", __spreadProps(__spreadValues({}, t2), {
            class: [t2.class, this.config.classNames.hidden].filter(Boolean).join(" ")
          }), i2);
        },
        createBadge(e2) {
          if (S.empty(e2)) return null;
          const t2 = $("span", {
            class: this.config.classNames.menu.value
          });
          return t2.appendChild($("span", {
            class: this.config.classNames.menu.badge
          }, e2)), t2;
        },
        createButton(e2, t2) {
          const i2 = x({}, t2);
          let s2 = fe(e2);
          const n2 = {
            element: "button",
            toggle: false,
            label: null,
            icon: null,
            labelPressed: null,
            iconPressed: null
          };
          switch (["element", "icon", "label"].forEach((e3) => {
            Object.keys(i2).includes(e3) && (n2[e3] = i2[e3], delete i2[e3]);
          }), "button" !== n2.element || Object.keys(i2).includes("type") || (i2.type = "button"), Object.keys(i2).includes("class") ? i2.class.split(" ").some((e3) => e3 === this.config.classNames.control) || x(i2, {
            class: `${i2.class} ${this.config.classNames.control}`
          }) : i2.class = this.config.classNames.control, e2) {
            case "play":
              n2.toggle = true, n2.label = "play", n2.labelPressed = "pause", n2.icon = "play", n2.iconPressed = "pause";
              break;
            case "mute":
              n2.toggle = true, n2.label = "mute", n2.labelPressed = "unmute", n2.icon = "volume", n2.iconPressed = "muted";
              break;
            case "captions":
              n2.toggle = true, n2.label = "enableCaptions", n2.labelPressed = "disableCaptions", n2.icon = "captions-off", n2.iconPressed = "captions-on";
              break;
            case "fullscreen":
              n2.toggle = true, n2.label = "enterFullscreen", n2.labelPressed = "exitFullscreen", n2.icon = "enter-fullscreen", n2.iconPressed = "exit-fullscreen";
              break;
            case "play-large":
              i2.class += ` ${this.config.classNames.control}--overlaid`, s2 = "play", n2.label = "play", n2.icon = "play";
              break;
            default:
              S.empty(n2.label) && (n2.label = s2), S.empty(n2.icon) && (n2.icon = e2);
          }
          const a2 = $(n2.element);
          return n2.toggle ? (a2.appendChild(Pe.createIcon.call(this, n2.iconPressed, {
            class: "icon--pressed"
          })), a2.appendChild(Pe.createIcon.call(this, n2.icon, {
            class: "icon--not-pressed"
          })), a2.appendChild(Pe.createLabel.call(this, n2.labelPressed, {
            class: "label--pressed"
          })), a2.appendChild(Pe.createLabel.call(this, n2.label, {
            class: "label--not-pressed"
          }))) : (a2.appendChild(Pe.createIcon.call(this, n2.icon)), a2.appendChild(Pe.createLabel.call(this, n2.label))), x(i2, D(this.config.selectors.buttons[s2], i2)), I(a2, i2), "play" === s2 ? (S.array(this.elements.buttons[s2]) || (this.elements.buttons[s2] = []), this.elements.buttons[s2].push(a2)) : this.elements.buttons[s2] = a2, a2;
        },
        createRange(e2, t2) {
          const i2 = $("input", x(D(this.config.selectors.inputs[e2]), {
            type: "range",
            min: 0,
            max: 100,
            step: 0.01,
            value: 0,
            autocomplete: "off",
            role: "slider",
            "aria-label": ve.get(e2, this.config),
            "aria-valuemin": 0,
            "aria-valuemax": 100,
            "aria-valuenow": 0
          }, t2));
          return this.elements.inputs[e2] = i2, Pe.updateRangeFill.call(this, i2), g.setup(i2), i2;
        },
        createProgress(e2, t2) {
          const i2 = $("progress", x(D(this.config.selectors.display[e2]), {
            min: 0,
            max: 100,
            value: 0,
            role: "progressbar",
            "aria-hidden": true
          }, t2));
          if ("volume" !== e2) {
            i2.appendChild($("span", null, "0"));
            const t3 = {
              played: "played",
              buffer: "buffered"
            }[e2], s2 = t3 ? ve.get(t3, this.config) : "";
            i2.innerText = `% ${s2.toLowerCase()}`;
          }
          return this.elements.display[e2] = i2, i2;
        },
        createTime(e2, t2) {
          const i2 = D(this.config.selectors.display[e2], t2), s2 = $("div", x(i2, {
            class: `${i2.class ? i2.class : ""} ${this.config.classNames.display.time} `.trim(),
            "aria-label": ve.get(e2, this.config),
            role: "timer"
          }), "00:00");
          return this.elements.display[e2] = s2, s2;
        },
        bindMenuItemShortcuts(e2, t2) {
          X.call(this, e2, "keydown keyup", (i2) => {
            if (![" ", "ArrowUp", "ArrowDown", "ArrowRight"].includes(i2.key)) return;
            if (i2.preventDefault(), i2.stopPropagation(), "keydown" === i2.type) return;
            const s2 = V(e2, '[role="menuitemradio"]');
            if (!s2 && [" ", "ArrowRight"].includes(i2.key)) Pe.showMenuPanel.call(this, t2, true);
            else {
              let t3;
              " " !== i2.key && ("ArrowDown" === i2.key || s2 && "ArrowRight" === i2.key ? (t3 = e2.nextElementSibling, S.element(t3) || (t3 = e2.parentNode.firstElementChild)) : (t3 = e2.previousElementSibling, S.element(t3) || (t3 = e2.parentNode.lastElementChild)), W.call(this, t3, true));
            }
          }, false), X.call(this, e2, "keyup", (e3) => {
            "Return" === e3.key && Pe.focusFirstMenuItem.call(this, null, true);
          });
        },
        createMenuItem({
          value: e2,
          list: t2,
          type: i2,
          title: s2,
          badge: n2 = null,
          checked: a2 = false
        }) {
          const l2 = D(this.config.selectors.inputs[i2]), r2 = $("button", x(l2, {
            type: "button",
            role: "menuitemradio",
            class: `${this.config.classNames.control} ${l2.class ? l2.class : ""}`.trim(),
            "aria-checked": a2,
            value: e2
          })), o2 = $("span");
          o2.innerHTML = s2, S.element(n2) && o2.appendChild(n2), r2.appendChild(o2), Object.defineProperty(r2, "checked", {
            enumerable: true,
            get: () => "true" === r2.getAttribute("aria-checked"),
            set(e3) {
              e3 && Array.from(r2.parentNode.children).filter((e4) => V(e4, '[role="menuitemradio"]')).forEach((e4) => e4.setAttribute("aria-checked", "false")), r2.setAttribute("aria-checked", e3 ? "true" : "false");
            }
          }), this.listeners.bind(r2, "click keyup", (t3) => {
            if (!S.keyboardEvent(t3) || " " === t3.key) {
              switch (t3.preventDefault(), t3.stopPropagation(), r2.checked = true, i2) {
                case "language":
                  this.currentTrack = Number(e2);
                  break;
                case "quality":
                  this.quality = e2;
                  break;
                case "speed":
                  this.speed = parseFloat(e2);
              }
              Pe.showMenuPanel.call(this, "home", S.keyboardEvent(t3));
            }
          }, i2, false), Pe.bindMenuItemShortcuts.call(this, r2, i2), t2.appendChild(r2);
        },
        formatTime(e2 = 0, t2 = false) {
          if (!S.number(e2)) return e2;
          return Ee(e2, Ce(this.duration) > 0, t2);
        },
        updateTimeDisplay(e2 = null, t2 = 0, i2 = false) {
          S.element(e2) && S.number(t2) && (e2.innerText = Pe.formatTime(t2, i2));
        },
        updateVolume() {
          this.supported.ui && (S.element(this.elements.inputs.volume) && Pe.setRange.call(this, this.elements.inputs.volume, this.muted ? 0 : this.volume), S.element(this.elements.buttons.mute) && (this.elements.buttons.mute.pressed = this.muted || 0 === this.volume));
        },
        setRange(e2, t2 = 0) {
          S.element(e2) && (e2.value = t2, Pe.updateRangeFill.call(this, e2));
        },
        updateProgress(e2) {
          if (!this.supported.ui || !S.event(e2)) return;
          let t2 = 0;
          const i2 = (e3, t3) => {
            const i3 = S.number(t3) ? t3 : 0, s3 = S.element(e3) ? e3 : this.elements.display.buffer;
            if (S.element(s3)) {
              s3.value = i3;
              const e4 = s3.getElementsByTagName("span")[0];
              S.element(e4) && (e4.childNodes[0].nodeValue = i3);
            }
          };
          if (e2) switch (e2.type) {
            case "timeupdate":
            case "seeking":
            case "seeked":
              s2 = this.currentTime, n2 = this.duration, t2 = 0 === s2 || 0 === n2 || Number.isNaN(s2) || Number.isNaN(n2) ? 0 : (s2 / n2 * 100).toFixed(2), "timeupdate" === e2.type && Pe.setRange.call(this, this.elements.inputs.seek, t2);
              break;
            case "playing":
            case "progress":
              i2(this.elements.display.buffer, 100 * this.buffered);
          }
          var s2, n2;
        },
        updateRangeFill(e2) {
          const t2 = S.event(e2) ? e2.target : e2;
          if (S.element(t2) && "range" === t2.getAttribute("type")) {
            if (V(t2, this.config.selectors.inputs.seek)) {
              t2.setAttribute("aria-valuenow", this.currentTime);
              const e3 = Pe.formatTime(this.currentTime), i2 = Pe.formatTime(this.duration), s2 = ve.get("seekLabel", this.config);
              t2.setAttribute("aria-valuetext", s2.replace("{currentTime}", e3).replace("{duration}", i2));
            } else if (V(t2, this.config.selectors.inputs.volume)) {
              const e3 = 100 * t2.value;
              t2.setAttribute("aria-valuenow", e3), t2.setAttribute("aria-valuetext", `${e3.toFixed(1)}%`);
            } else t2.setAttribute("aria-valuenow", t2.value);
            (M.isWebKit || M.isIPadOS) && t2.style.setProperty("--value", t2.value / t2.max * 100 + "%");
          }
        },
        updateSeekTooltip(e2) {
          var t2, i2;
          if (!this.config.tooltips.seek || !S.element(this.elements.inputs.seek) || !S.element(this.elements.display.seekTooltip) || 0 === this.duration) return;
          const s2 = this.elements.display.seekTooltip, n2 = `${this.config.classNames.tooltip}--visible`, a2 = (e3) => R(s2, n2, e3);
          if (this.touch) return void a2(false);
          let l2 = 0;
          const r2 = this.elements.progress.getBoundingClientRect();
          if (S.event(e2)) l2 = 100 / r2.width * (e2.pageX - r2.left);
          else {
            if (!F(s2, n2)) return;
            l2 = parseFloat(s2.style.left, 10);
          }
          l2 < 0 ? l2 = 0 : l2 > 100 && (l2 = 100);
          const o2 = this.duration / 100 * l2;
          s2.innerText = Pe.formatTime(o2);
          const c2 = null === (t2 = this.config.markers) || void 0 === t2 || null === (i2 = t2.points) || void 0 === i2 ? void 0 : i2.find(({
            time: e3
          }) => e3 === Math.round(o2));
          c2 && s2.insertAdjacentHTML("afterbegin", `${c2.label}<br>`), s2.style.left = `${l2}%`, S.event(e2) && ["mouseenter", "mouseleave"].includes(e2.type) && a2("mouseenter" === e2.type);
        },
        timeUpdate(e2) {
          const t2 = !S.element(this.elements.display.duration) && this.config.invertTime;
          Pe.updateTimeDisplay.call(this, this.elements.display.currentTime, t2 ? this.duration - this.currentTime : this.currentTime, t2), e2 && "timeupdate" === e2.type && this.media.seeking || Pe.updateProgress.call(this, e2);
        },
        durationUpdate() {
          if (!this.supported.ui || !this.config.invertTime && this.currentTime) return;
          if (this.duration >= 2 ** 32) return H(this.elements.display.currentTime, true), void H(this.elements.progress, true);
          S.element(this.elements.inputs.seek) && this.elements.inputs.seek.setAttribute("aria-valuemax", this.duration);
          const e2 = S.element(this.elements.display.duration);
          !e2 && this.config.displayDuration && this.paused && Pe.updateTimeDisplay.call(this, this.elements.display.currentTime, this.duration), e2 && Pe.updateTimeDisplay.call(this, this.elements.display.duration, this.duration), this.config.markers.enabled && Pe.setMarkers.call(this), Pe.updateSeekTooltip.call(this);
        },
        toggleMenuButton(e2, t2) {
          H(this.elements.settings.buttons[e2], !t2);
        },
        updateSetting(e2, t2, i2) {
          const s2 = this.elements.settings.panels[e2];
          let n2 = null, a2 = t2;
          if ("captions" === e2) n2 = this.currentTrack;
          else {
            if (n2 = S.empty(i2) ? this[e2] : i2, S.empty(n2) && (n2 = this.config[e2].default), !S.empty(this.options[e2]) && !this.options[e2].includes(n2)) return void this.debug.warn(`Unsupported value of '${n2}' for ${e2}`);
            if (!this.config[e2].options.includes(n2)) return void this.debug.warn(`Disabled value of '${n2}' for ${e2}`);
          }
          if (S.element(a2) || (a2 = s2 && s2.querySelector('[role="menu"]')), !S.element(a2)) return;
          this.elements.settings.buttons[e2].querySelector(`.${this.config.classNames.menu.value}`).innerHTML = Pe.getLabel.call(this, e2, n2);
          const l2 = a2 && a2.querySelector(`[value="${n2}"]`);
          S.element(l2) && (l2.checked = true);
        },
        getLabel(e2, t2) {
          switch (e2) {
            case "speed":
              return 1 === t2 ? ve.get("normal", this.config) : `${t2}&times;`;
            case "quality":
              if (S.number(t2)) {
                const e3 = ve.get(`qualityLabel.${t2}`, this.config);
                return e3.length ? e3 : `${t2}p`;
              }
              return ge(t2);
            case "captions":
              return xe.getLabel.call(this);
            default:
              return null;
          }
        },
        setQualityMenu(e2) {
          if (!S.element(this.elements.settings.panels.quality)) return;
          const t2 = "quality", i2 = this.elements.settings.panels.quality.querySelector('[role="menu"]');
          S.array(e2) && (this.options.quality = se(e2).filter((e3) => this.config.quality.options.includes(e3)));
          const s2 = !S.empty(this.options.quality) && this.options.quality.length > 1;
          if (Pe.toggleMenuButton.call(this, t2, s2), j(i2), Pe.checkMenu.call(this), !s2) return;
          const n2 = (e3) => {
            const t3 = ve.get(`qualityBadge.${e3}`, this.config);
            return t3.length ? Pe.createBadge.call(this, t3) : null;
          };
          this.options.quality.sort((e3, t3) => {
            const i3 = this.config.quality.options;
            return i3.indexOf(e3) > i3.indexOf(t3) ? 1 : -1;
          }).forEach((e3) => {
            Pe.createMenuItem.call(this, {
              value: e3,
              list: i2,
              type: t2,
              title: Pe.getLabel.call(this, "quality", e3),
              badge: n2(e3)
            });
          }), Pe.updateSetting.call(this, t2, i2);
        },
        setCaptionsMenu() {
          if (!S.element(this.elements.settings.panels.captions)) return;
          const e2 = "captions", t2 = this.elements.settings.panels.captions.querySelector('[role="menu"]'), i2 = xe.getTracks.call(this), s2 = Boolean(i2.length);
          if (Pe.toggleMenuButton.call(this, e2, s2), j(t2), Pe.checkMenu.call(this), !s2) return;
          const n2 = i2.map((e3, i3) => ({
            value: i3,
            checked: this.captions.toggled && this.currentTrack === i3,
            title: xe.getLabel.call(this, e3),
            badge: e3.language && Pe.createBadge.call(this, e3.language.toUpperCase()),
            list: t2,
            type: "language"
          }));
          n2.unshift({
            value: -1,
            checked: !this.captions.toggled,
            title: ve.get("disabled", this.config),
            list: t2,
            type: "language"
          }), n2.forEach(Pe.createMenuItem.bind(this)), Pe.updateSetting.call(this, e2, t2);
        },
        setSpeedMenu() {
          if (!S.element(this.elements.settings.panels.speed)) return;
          const e2 = "speed", t2 = this.elements.settings.panels.speed.querySelector('[role="menu"]');
          this.options.speed = this.options.speed.filter((e3) => e3 >= this.minimumSpeed && e3 <= this.maximumSpeed);
          const i2 = !S.empty(this.options.speed) && this.options.speed.length > 1;
          Pe.toggleMenuButton.call(this, e2, i2), j(t2), Pe.checkMenu.call(this), i2 && (this.options.speed.forEach((i3) => {
            Pe.createMenuItem.call(this, {
              value: i3,
              list: t2,
              type: e2,
              title: Pe.getLabel.call(this, "speed", i3)
            });
          }), Pe.updateSetting.call(this, e2, t2));
        },
        checkMenu() {
          const {
            buttons: e2
          } = this.elements.settings, t2 = !S.empty(e2) && Object.values(e2).some((e3) => !e3.hidden);
          H(this.elements.settings.menu, !t2);
        },
        focusFirstMenuItem(e2, t2 = false) {
          if (this.elements.settings.popup.hidden) return;
          let i2 = e2;
          S.element(i2) || (i2 = Object.values(this.elements.settings.panels).find((e3) => !e3.hidden));
          const s2 = i2.querySelector('[role^="menuitem"]');
          W.call(this, s2, t2);
        },
        toggleMenu(e2) {
          const {
            popup: t2
          } = this.elements.settings, i2 = this.elements.buttons.settings;
          if (!S.element(t2) || !S.element(i2)) return;
          const {
            hidden: s2
          } = t2;
          let n2 = s2;
          if (S.boolean(e2)) n2 = e2;
          else if (S.keyboardEvent(e2) && "Escape" === e2.key) n2 = false;
          else if (S.event(e2)) {
            const s3 = S.function(e2.composedPath) ? e2.composedPath()[0] : e2.target, a2 = t2.contains(s3);
            if (a2 || !a2 && e2.target !== i2 && n2) return;
          }
          i2.setAttribute("aria-expanded", n2), H(t2, !n2), R(this.elements.container, this.config.classNames.menu.open, n2), n2 && S.keyboardEvent(e2) ? Pe.focusFirstMenuItem.call(this, null, true) : n2 || s2 || W.call(this, i2, S.keyboardEvent(e2));
        },
        getMenuSize(e2) {
          const t2 = e2.cloneNode(true);
          t2.style.position = "absolute", t2.style.opacity = 0, t2.removeAttribute("hidden"), e2.parentNode.appendChild(t2);
          const i2 = t2.scrollWidth, s2 = t2.scrollHeight;
          return O(t2), {
            width: i2,
            height: s2
          };
        },
        showMenuPanel(e2 = "", t2 = false) {
          const i2 = this.elements.container.querySelector(`#plyr-settings-${this.id}-${e2}`);
          if (!S.element(i2)) return;
          const s2 = i2.parentNode, n2 = Array.from(s2.children).find((e3) => !e3.hidden);
          if (K.transitions && !K.reducedMotion) {
            s2.style.width = `${n2.scrollWidth}px`, s2.style.height = `${n2.scrollHeight}px`;
            const e3 = Pe.getMenuSize.call(this, i2), t3 = (e4) => {
              e4.target === s2 && ["width", "height"].includes(e4.propertyName) && (s2.style.width = "", s2.style.height = "", J.call(this, s2, E, t3));
            };
            X.call(this, s2, E, t3), s2.style.width = `${e3.width}px`, s2.style.height = `${e3.height}px`;
          }
          H(n2, true), H(i2, false), Pe.focusFirstMenuItem.call(this, i2, t2);
        },
        setDownloadUrl() {
          const e2 = this.elements.buttons.download;
          S.element(e2) && e2.setAttribute("href", this.download);
        },
        create(e2) {
          const {
            bindMenuItemShortcuts: t2,
            createButton: i2,
            createProgress: s2,
            createRange: n2,
            createTime: a2,
            setQualityMenu: l2,
            setSpeedMenu: r2,
            showMenuPanel: o2
          } = Pe;
          this.elements.controls = null, S.array(this.config.controls) && this.config.controls.includes("play-large") && this.elements.container.appendChild(i2.call(this, "play-large"));
          const c2 = $("div", D(this.config.selectors.controls.wrapper));
          this.elements.controls = c2;
          const u2 = {
            class: "plyr__controls__item"
          };
          return se(S.array(this.config.controls) ? this.config.controls : []).forEach((l3) => {
            if ("restart" === l3 && c2.appendChild(i2.call(this, "restart", u2)), "rewind" === l3 && c2.appendChild(i2.call(this, "rewind", u2)), "play" === l3 && c2.appendChild(i2.call(this, "play", u2)), "fast-forward" === l3 && c2.appendChild(i2.call(this, "fast-forward", u2)), "progress" === l3) {
              const t3 = $("div", {
                class: `${u2.class} plyr__progress__container`
              }), i3 = $("div", D(this.config.selectors.progress));
              if (i3.appendChild(n2.call(this, "seek", {
                id: `plyr-seek-${e2.id}`
              })), i3.appendChild(s2.call(this, "buffer")), this.config.tooltips.seek) {
                const e3 = $("span", {
                  class: this.config.classNames.tooltip
                }, "00:00");
                i3.appendChild(e3), this.elements.display.seekTooltip = e3;
              }
              this.elements.progress = i3, t3.appendChild(this.elements.progress), c2.appendChild(t3);
            }
            if ("current-time" === l3 && c2.appendChild(a2.call(this, "currentTime", u2)), "duration" === l3 && c2.appendChild(a2.call(this, "duration", u2)), "mute" === l3 || "volume" === l3) {
              let {
                volume: t3
              } = this.elements;
              if (S.element(t3) && c2.contains(t3) || (t3 = $("div", x({}, u2, {
                class: `${u2.class} plyr__volume`.trim()
              })), this.elements.volume = t3, c2.appendChild(t3)), "mute" === l3 && t3.appendChild(i2.call(this, "mute")), "volume" === l3 && !M.isIos && !M.isIPadOS) {
                const i3 = {
                  max: 1,
                  step: 0.05,
                  value: this.config.volume
                };
                t3.appendChild(n2.call(this, "volume", x(i3, {
                  id: `plyr-volume-${e2.id}`
                })));
              }
            }
            if ("captions" === l3 && c2.appendChild(i2.call(this, "captions", u2)), "settings" === l3 && !S.empty(this.config.settings)) {
              const s3 = $("div", x({}, u2, {
                class: `${u2.class} plyr__menu`.trim(),
                hidden: ""
              }));
              s3.appendChild(i2.call(this, "settings", {
                "aria-haspopup": true,
                "aria-controls": `plyr-settings-${e2.id}`,
                "aria-expanded": false
              }));
              const n3 = $("div", {
                class: "plyr__menu__container",
                id: `plyr-settings-${e2.id}`,
                hidden: ""
              }), a3 = $("div"), l4 = $("div", {
                id: `plyr-settings-${e2.id}-home`
              }), r3 = $("div", {
                role: "menu"
              });
              l4.appendChild(r3), a3.appendChild(l4), this.elements.settings.panels.home = l4, this.config.settings.forEach((i3) => {
                const s4 = $("button", x(D(this.config.selectors.buttons.settings), {
                  type: "button",
                  class: `${this.config.classNames.control} ${this.config.classNames.control}--forward`,
                  role: "menuitem",
                  "aria-haspopup": true,
                  hidden: ""
                }));
                t2.call(this, s4, i3), X.call(this, s4, "click", () => {
                  o2.call(this, i3, false);
                });
                const n4 = $("span", null, ve.get(i3, this.config)), l5 = $("span", {
                  class: this.config.classNames.menu.value
                });
                l5.innerHTML = e2[i3], n4.appendChild(l5), s4.appendChild(n4), r3.appendChild(s4);
                const c3 = $("div", {
                  id: `plyr-settings-${e2.id}-${i3}`,
                  hidden: ""
                }), u3 = $("button", {
                  type: "button",
                  class: `${this.config.classNames.control} ${this.config.classNames.control}--back`
                });
                u3.appendChild($("span", {
                  "aria-hidden": true
                }, ve.get(i3, this.config))), u3.appendChild($("span", {
                  class: this.config.classNames.hidden
                }, ve.get("menuBack", this.config))), X.call(this, c3, "keydown", (e3) => {
                  "ArrowLeft" === e3.key && (e3.preventDefault(), e3.stopPropagation(), o2.call(this, "home", true));
                }, false), X.call(this, u3, "click", () => {
                  o2.call(this, "home", false);
                }), c3.appendChild(u3), c3.appendChild($("div", {
                  role: "menu"
                })), a3.appendChild(c3), this.elements.settings.buttons[i3] = s4, this.elements.settings.panels[i3] = c3;
              }), n3.appendChild(a3), s3.appendChild(n3), c2.appendChild(s3), this.elements.settings.popup = n3, this.elements.settings.menu = s3;
            }
            if ("pip" === l3 && K.pip && c2.appendChild(i2.call(this, "pip", u2)), "airplay" === l3 && K.airplay && c2.appendChild(i2.call(this, "airplay", u2)), "download" === l3) {
              const e3 = x({}, u2, {
                element: "a",
                href: this.download,
                target: "_blank"
              });
              this.isHTML5 && (e3.download = "");
              const {
                download: t3
              } = this.config.urls;
              !S.url(t3) && this.isEmbed && x(e3, {
                icon: `logo-${this.provider}`,
                label: this.provider
              }), c2.appendChild(i2.call(this, "download", e3));
            }
            "fullscreen" === l3 && c2.appendChild(i2.call(this, "fullscreen", u2));
          }), this.isHTML5 && l2.call(this, de.getQualityOptions.call(this)), r2.call(this), c2;
        },
        inject() {
          if (this.config.loadSprite) {
            const e3 = Pe.getIconUrl.call(this);
            e3.cors && ke(e3.url, "sprite-plyr");
          }
          this.id = Math.floor(1e4 * Math.random());
          let e2 = null;
          this.elements.controls = null;
          const t2 = {
            id: this.id,
            seektime: this.config.seekTime,
            title: this.config.title
          };
          let i2 = true;
          S.function(this.config.controls) && (this.config.controls = this.config.controls.call(this, t2)), this.config.controls || (this.config.controls = []), S.element(this.config.controls) || S.string(this.config.controls) ? e2 = this.config.controls : (e2 = Pe.create.call(this, {
            id: this.id,
            seektime: this.config.seekTime,
            speed: this.speed,
            quality: this.quality,
            captions: xe.getLabel.call(this)
          }), i2 = false);
          let s2;
          i2 && S.string(this.config.controls) && (e2 = ((e3) => {
            let i3 = e3;
            return Object.entries(t2).forEach(([e4, t3]) => {
              i3 = pe(i3, `{${e4}}`, t3);
            }), i3;
          })(e2)), S.string(this.config.selectors.controls.container) && (s2 = document.querySelector(this.config.selectors.controls.container)), S.element(s2) || (s2 = this.elements.container);
          if (s2[S.element(e2) ? "insertAdjacentElement" : "insertAdjacentHTML"]("afterbegin", e2), S.element(this.elements.controls) || Pe.findElements.call(this), !S.empty(this.elements.buttons)) {
            const e3 = (e4) => {
              const t3 = this.config.classNames.controlPressed;
              e4.setAttribute("aria-pressed", "false"), Object.defineProperty(e4, "pressed", {
                configurable: true,
                enumerable: true,
                get: () => F(e4, t3),
                set(i3 = false) {
                  R(e4, t3, i3), e4.setAttribute("aria-pressed", i3 ? "true" : "false");
                }
              });
            };
            Object.values(this.elements.buttons).filter(Boolean).forEach((t3) => {
              S.array(t3) || S.nodeList(t3) ? Array.from(t3).filter(Boolean).forEach(e3) : e3(t3);
            });
          }
          if (M.isEdge && P(s2), this.config.tooltips.controls) {
            const {
              classNames: e3,
              selectors: t3
            } = this.config, i3 = `${t3.controls.wrapper} ${t3.labels} .${e3.hidden}`, s3 = U.call(this, i3);
            Array.from(s3).forEach((e4) => {
              R(e4, this.config.classNames.hidden, false), R(e4, this.config.classNames.tooltip, true);
            });
          }
        },
        setMediaMetadata() {
          try {
            "mediaSession" in navigator && (navigator.mediaSession.metadata = new window.MediaMetadata({
              title: this.config.mediaMetadata.title,
              artist: this.config.mediaMetadata.artist,
              album: this.config.mediaMetadata.album,
              artwork: this.config.mediaMetadata.artwork
            }));
          } catch (e2) {
          }
        },
        setMarkers() {
          var e2, t2;
          if (!this.duration || this.elements.markers) return;
          const i2 = null === (e2 = this.config.markers) || void 0 === e2 || null === (t2 = e2.points) || void 0 === t2 ? void 0 : t2.filter(({
            time: e3
          }) => e3 > 0 && e3 < this.duration);
          if (null == i2 || !i2.length) return;
          const s2 = document.createDocumentFragment(), n2 = document.createDocumentFragment();
          let a2 = null;
          const l2 = `${this.config.classNames.tooltip}--visible`, r2 = (e3) => R(a2, l2, e3);
          i2.forEach((e3) => {
            const t3 = $("span", {
              class: this.config.classNames.marker
            }, ""), i3 = e3.time / this.duration * 100 + "%";
            a2 && (t3.addEventListener("mouseenter", () => {
              e3.label || (a2.style.left = i3, a2.innerHTML = e3.label, r2(true));
            }), t3.addEventListener("mouseleave", () => {
              r2(false);
            })), t3.addEventListener("click", () => {
              this.currentTime = e3.time;
            }), t3.style.left = i3, n2.appendChild(t3);
          }), s2.appendChild(n2), this.config.tooltips.seek || (a2 = $("span", {
            class: this.config.classNames.tooltip
          }, ""), s2.appendChild(a2)), this.elements.markers = {
            points: n2,
            tip: a2
          }, this.elements.progress.appendChild(s2);
        }
      };
      function Me(e2, t2 = true) {
        let i2 = e2;
        if (t2) {
          const e3 = document.createElement("a");
          e3.href = i2, i2 = e3.href;
        }
        try {
          return new URL(i2);
        } catch (e3) {
          return null;
        }
      }
      function Ne(e2) {
        const t2 = new URLSearchParams();
        return S.object(e2) && Object.entries(e2).forEach(([e3, i2]) => {
          t2.set(e3, i2);
        }), t2;
      }
      const xe = {
        setup() {
          if (!this.supported.ui) return;
          if (!this.isVideo || this.isYouTube || this.isHTML5 && !K.textTracks) return void (S.array(this.config.controls) && this.config.controls.includes("settings") && this.config.settings.includes("captions") && Pe.setCaptionsMenu.call(this));
          var e2, t2;
          if (S.element(this.elements.captions) || (this.elements.captions = $("div", D(this.config.selectors.captions)), this.elements.captions.setAttribute("dir", "auto"), e2 = this.elements.captions, t2 = this.elements.wrapper, S.element(e2) && S.element(t2) && t2.parentNode.insertBefore(e2, t2.nextSibling)), M.isIE && window.URL) {
            const e3 = this.media.querySelectorAll("track");
            Array.from(e3).forEach((e4) => {
              const t3 = e4.getAttribute("src"), i3 = Me(t3);
              null !== i3 && i3.hostname !== window.location.href.hostname && ["http:", "https:"].includes(i3.protocol) && Te(t3, "blob").then((t4) => {
                e4.setAttribute("src", window.URL.createObjectURL(t4));
              }).catch(() => {
                O(e4);
              });
            });
          }
          const i2 = se((navigator.languages || [navigator.language || navigator.userLanguage || "en"]).map((e3) => e3.split("-")[0]));
          let s2 = (this.storage.get("language") || this.config.captions.language || "auto").toLowerCase();
          "auto" === s2 && ([s2] = i2);
          let n2 = this.storage.get("captions");
          if (S.boolean(n2) || ({
            active: n2
          } = this.config.captions), Object.assign(this.captions, {
            toggled: false,
            active: n2,
            language: s2,
            languages: i2
          }), this.isHTML5) {
            const e3 = this.config.captions.update ? "addtrack removetrack" : "removetrack";
            X.call(this, this.media.textTracks, e3, xe.update.bind(this));
          }
          setTimeout(xe.update.bind(this), 0);
        },
        update() {
          const e2 = xe.getTracks.call(this, true), {
            active: t2,
            language: i2,
            meta: s2,
            currentTrackNode: n2
          } = this.captions, a2 = Boolean(e2.find((e3) => e3.language === i2));
          this.isHTML5 && this.isVideo && e2.filter((e3) => !s2.get(e3)).forEach((e3) => {
            this.debug.log("Track added", e3), s2.set(e3, {
              default: "showing" === e3.mode
            }), "showing" === e3.mode && (e3.mode = "hidden"), X.call(this, e3, "cuechange", () => xe.updateCues.call(this));
          }), (a2 && this.language !== i2 || !e2.includes(n2)) && (xe.setLanguage.call(this, i2), xe.toggle.call(this, t2 && a2)), this.elements && R(this.elements.container, this.config.classNames.captions.enabled, !S.empty(e2)), S.array(this.config.controls) && this.config.controls.includes("settings") && this.config.settings.includes("captions") && Pe.setCaptionsMenu.call(this);
        },
        toggle(e2, t2 = true) {
          if (!this.supported.ui) return;
          const {
            toggled: i2
          } = this.captions, s2 = this.config.classNames.captions.active, n2 = S.nullOrUndefined(e2) ? !i2 : e2;
          if (n2 !== i2) {
            if (t2 || (this.captions.active = n2, this.storage.set({
              captions: n2
            })), !this.language && n2 && !t2) {
              const e3 = xe.getTracks.call(this), t3 = xe.findTrack.call(this, [this.captions.language, ...this.captions.languages], true);
              return this.captions.language = t3.language, void xe.set.call(this, e3.indexOf(t3));
            }
            this.elements.buttons.captions && (this.elements.buttons.captions.pressed = n2), R(this.elements.container, s2, n2), this.captions.toggled = n2, Pe.updateSetting.call(this, "captions"), Z.call(this, this.media, n2 ? "captionsenabled" : "captionsdisabled");
          }
          setTimeout(() => {
            n2 && this.captions.toggled && (this.captions.currentTrackNode.mode = "hidden");
          });
        },
        set(e2, t2 = true) {
          const i2 = xe.getTracks.call(this);
          if (-1 !== e2) {
            if (S.number(e2)) {
              if (e2 in i2) {
                if (this.captions.currentTrack !== e2) {
                  this.captions.currentTrack = e2;
                  const s2 = i2[e2], {
                    language: n2
                  } = s2 || {};
                  this.captions.currentTrackNode = s2, Pe.updateSetting.call(this, "captions"), t2 || (this.captions.language = n2, this.storage.set({
                    language: n2
                  })), this.isVimeo && this.embed.enableTextTrack(n2), Z.call(this, this.media, "languagechange");
                }
                xe.toggle.call(this, true, t2), this.isHTML5 && this.isVideo && xe.updateCues.call(this);
              } else this.debug.warn("Track not found", e2);
            } else this.debug.warn("Invalid caption argument", e2);
          } else xe.toggle.call(this, false, t2);
        },
        setLanguage(e2, t2 = true) {
          if (!S.string(e2)) return void this.debug.warn("Invalid language argument", e2);
          const i2 = e2.toLowerCase();
          this.captions.language = i2;
          const s2 = xe.getTracks.call(this), n2 = xe.findTrack.call(this, [i2]);
          xe.set.call(this, s2.indexOf(n2), t2);
        },
        getTracks(e2 = false) {
          return Array.from((this.media || {}).textTracks || []).filter((t2) => !this.isHTML5 || e2 || this.captions.meta.has(t2)).filter((e3) => ["captions", "subtitles"].includes(e3.kind));
        },
        findTrack(e2, t2 = false) {
          const i2 = xe.getTracks.call(this), s2 = (e3) => Number((this.captions.meta.get(e3) || {}).default), n2 = Array.from(i2).sort((e3, t3) => s2(t3) - s2(e3));
          let a2;
          return e2.every((e3) => (a2 = n2.find((t3) => t3.language === e3), !a2)), a2 || (t2 ? n2[0] : void 0);
        },
        getCurrentTrack() {
          return xe.getTracks.call(this)[this.currentTrack];
        },
        getLabel(e2) {
          let t2 = e2;
          return !S.track(t2) && K.textTracks && this.captions.toggled && (t2 = xe.getCurrentTrack.call(this)), S.track(t2) ? S.empty(t2.label) ? S.empty(t2.language) ? ve.get("enabled", this.config) : e2.language.toUpperCase() : t2.label : ve.get("disabled", this.config);
        },
        updateCues(e2) {
          if (!this.supported.ui) return;
          if (!S.element(this.elements.captions)) return void this.debug.warn("No captions element to render to");
          if (!S.nullOrUndefined(e2) && !Array.isArray(e2)) return void this.debug.warn("updateCues: Invalid input", e2);
          let t2 = e2;
          if (!t2) {
            const e3 = xe.getCurrentTrack.call(this);
            t2 = Array.from((e3 || {}).activeCues || []).map((e4) => e4.getCueAsHTML()).map(ye);
          }
          const i2 = t2.map((e3) => e3.trim()).join("\n");
          if (i2 !== this.elements.captions.innerHTML) {
            j(this.elements.captions);
            const e3 = $("span", D(this.config.selectors.caption));
            e3.innerHTML = i2, this.elements.captions.appendChild(e3), Z.call(this, this.media, "cuechange");
          }
        }
      }, Le = {
        enabled: true,
        title: "",
        debug: false,
        autoplay: false,
        autopause: true,
        playsinline: true,
        seekTime: 10,
        volume: 1,
        muted: false,
        duration: null,
        displayDuration: true,
        invertTime: true,
        toggleInvert: true,
        ratio: null,
        clickToPlay: true,
        hideControls: true,
        resetOnEnd: false,
        disableContextMenu: true,
        loadSprite: true,
        iconPrefix: "plyr",
        iconUrl: "https://cdn.plyr.io/3.7.8/plyr.svg",
        blankVideo: "https://cdn.plyr.io/static/blank.mp4",
        quality: {
          default: 576,
          options: [4320, 2880, 2160, 1440, 1080, 720, 576, 480, 360, 240],
          forced: false,
          onChange: null
        },
        loop: {
          active: false
        },
        speed: {
          selected: 1,
          options: [0.5, 0.75, 1, 1.25, 1.5, 1.75, 2, 4]
        },
        keyboard: {
          focused: true,
          global: false
        },
        tooltips: {
          controls: false,
          seek: true
        },
        captions: {
          active: false,
          language: "auto",
          update: false
        },
        fullscreen: {
          enabled: true,
          fallback: true,
          iosNative: false
        },
        storage: {
          enabled: true,
          key: "plyr"
        },
        controls: ["play-large", "play", "progress", "current-time", "mute", "volume", "captions", "settings", "pip", "airplay", "fullscreen"],
        settings: ["captions", "quality", "speed"],
        i18n: {
          restart: "Restart",
          rewind: "Rewind {seektime}s",
          play: "Play",
          pause: "Pause",
          fastForward: "Forward {seektime}s",
          seek: "Seek",
          seekLabel: "{currentTime} of {duration}",
          played: "Played",
          buffered: "Buffered",
          currentTime: "Current time",
          duration: "Duration",
          volume: "Volume",
          mute: "Mute",
          unmute: "Unmute",
          enableCaptions: "Enable captions",
          disableCaptions: "Disable captions",
          download: "Download",
          enterFullscreen: "Enter fullscreen",
          exitFullscreen: "Exit fullscreen",
          frameTitle: "Player for {title}",
          captions: "Captions",
          settings: "Settings",
          pip: "PIP",
          menuBack: "Go back to previous menu",
          speed: "Speed",
          normal: "Normal",
          quality: "Quality",
          loop: "Loop",
          start: "Start",
          end: "End",
          all: "All",
          reset: "Reset",
          disabled: "Disabled",
          enabled: "Enabled",
          advertisement: "Ad",
          qualityBadge: {
            2160: "4K",
            1440: "HD",
            1080: "HD",
            720: "HD",
            576: "SD",
            480: "SD"
          }
        },
        urls: {
          download: null,
          vimeo: {
            sdk: "https://player.vimeo.com/api/player.js",
            iframe: "https://player.vimeo.com/video/{0}?{1}",
            api: "https://vimeo.com/api/oembed.json?url={0}"
          },
          youtube: {
            sdk: "https://www.youtube.com/iframe_api",
            api: "https://noembed.com/embed?url=https://www.youtube.com/watch?v={0}"
          },
          googleIMA: {
            sdk: "https://imasdk.googleapis.com/js/sdkloader/ima3.js"
          }
        },
        listeners: {
          seek: null,
          play: null,
          pause: null,
          restart: null,
          rewind: null,
          fastForward: null,
          mute: null,
          volume: null,
          captions: null,
          download: null,
          fullscreen: null,
          pip: null,
          airplay: null,
          speed: null,
          quality: null,
          loop: null,
          language: null
        },
        events: ["ended", "progress", "stalled", "playing", "waiting", "canplay", "canplaythrough", "loadstart", "loadeddata", "loadedmetadata", "timeupdate", "volumechange", "play", "pause", "error", "seeking", "seeked", "emptied", "ratechange", "cuechange", "download", "enterfullscreen", "exitfullscreen", "captionsenabled", "captionsdisabled", "languagechange", "controlshidden", "controlsshown", "ready", "statechange", "qualitychange", "adsloaded", "adscontentpause", "adscontentresume", "adstarted", "adsmidpoint", "adscomplete", "adsallcomplete", "adsimpression", "adsclick"],
        selectors: {
          editable: "input, textarea, select, [contenteditable]",
          container: ".plyr",
          controls: {
            container: null,
            wrapper: ".plyr__controls"
          },
          labels: "[data-plyr]",
          buttons: {
            play: '[data-plyr="play"]',
            pause: '[data-plyr="pause"]',
            restart: '[data-plyr="restart"]',
            rewind: '[data-plyr="rewind"]',
            fastForward: '[data-plyr="fast-forward"]',
            mute: '[data-plyr="mute"]',
            captions: '[data-plyr="captions"]',
            download: '[data-plyr="download"]',
            fullscreen: '[data-plyr="fullscreen"]',
            pip: '[data-plyr="pip"]',
            airplay: '[data-plyr="airplay"]',
            settings: '[data-plyr="settings"]',
            loop: '[data-plyr="loop"]'
          },
          inputs: {
            seek: '[data-plyr="seek"]',
            volume: '[data-plyr="volume"]',
            speed: '[data-plyr="speed"]',
            language: '[data-plyr="language"]',
            quality: '[data-plyr="quality"]'
          },
          display: {
            currentTime: ".plyr__time--current",
            duration: ".plyr__time--duration",
            buffer: ".plyr__progress__buffer",
            loop: ".plyr__progress__loop",
            volume: ".plyr__volume--display"
          },
          progress: ".plyr__progress",
          captions: ".plyr__captions",
          caption: ".plyr__caption"
        },
        classNames: {
          type: "plyr--{0}",
          provider: "plyr--{0}",
          video: "plyr__video-wrapper",
          embed: "plyr__video-embed",
          videoFixedRatio: "plyr__video-wrapper--fixed-ratio",
          embedContainer: "plyr__video-embed__container",
          poster: "plyr__poster",
          posterEnabled: "plyr__poster-enabled",
          ads: "plyr__ads",
          control: "plyr__control",
          controlPressed: "plyr__control--pressed",
          playing: "plyr--playing",
          paused: "plyr--paused",
          stopped: "plyr--stopped",
          loading: "plyr--loading",
          hover: "plyr--hover",
          tooltip: "plyr__tooltip",
          cues: "plyr__cues",
          marker: "plyr__progress__marker",
          hidden: "plyr__sr-only",
          hideControls: "plyr--hide-controls",
          isTouch: "plyr--is-touch",
          uiSupported: "plyr--full-ui",
          noTransition: "plyr--no-transition",
          display: {
            time: "plyr__time"
          },
          menu: {
            value: "plyr__menu__value",
            badge: "plyr__badge",
            open: "plyr--menu-open"
          },
          captions: {
            enabled: "plyr--captions-enabled",
            active: "plyr--captions-active"
          },
          fullscreen: {
            enabled: "plyr--fullscreen-enabled",
            fallback: "plyr--fullscreen-fallback"
          },
          pip: {
            supported: "plyr--pip-supported",
            active: "plyr--pip-active"
          },
          airplay: {
            supported: "plyr--airplay-supported",
            active: "plyr--airplay-active"
          },
          previewThumbnails: {
            thumbContainer: "plyr__preview-thumb",
            thumbContainerShown: "plyr__preview-thumb--is-shown",
            imageContainer: "plyr__preview-thumb__image-container",
            timeContainer: "plyr__preview-thumb__time-container",
            scrubbingContainer: "plyr__preview-scrubbing",
            scrubbingContainerShown: "plyr__preview-scrubbing--is-shown"
          }
        },
        attributes: {
          embed: {
            provider: "data-plyr-provider",
            id: "data-plyr-embed-id",
            hash: "data-plyr-embed-hash"
          }
        },
        ads: {
          enabled: false,
          publisherId: "",
          tagUrl: ""
        },
        previewThumbnails: {
          enabled: false,
          src: ""
        },
        vimeo: {
          byline: false,
          portrait: false,
          title: false,
          speed: true,
          transparent: false,
          customControls: true,
          referrerPolicy: null,
          premium: false
        },
        youtube: {
          rel: 0,
          showinfo: 0,
          iv_load_policy: 3,
          modestbranding: 1,
          customControls: true,
          noCookie: false
        },
        mediaMetadata: {
          title: "",
          artist: "",
          album: "",
          artwork: []
        },
        markers: {
          enabled: false,
          points: []
        }
      }, Ie = "picture-in-picture", $e = "inline", _e = {
        html5: "html5",
        youtube: "youtube",
        vimeo: "vimeo"
      }, Oe = "audio", je = "video";
      const qe = () => {
      };
      class De {
        constructor(e2 = false) {
          this.enabled = window.console && e2, this.enabled && this.log("Debugging enabled");
        }
        get log() {
          return this.enabled ? Function.prototype.bind.call(console.log, console) : qe;
        }
        get warn() {
          return this.enabled ? Function.prototype.bind.call(console.warn, console) : qe;
        }
        get error() {
          return this.enabled ? Function.prototype.bind.call(console.error, console) : qe;
        }
      }
      class He {
        constructor(t2) {
          e(this, "onChange", () => {
            if (!this.supported) return;
            const e2 = this.player.elements.buttons.fullscreen;
            S.element(e2) && (e2.pressed = this.active);
            const t3 = this.target === this.player.media ? this.target : this.player.elements.container;
            Z.call(this.player, t3, this.active ? "enterfullscreen" : "exitfullscreen", true);
          }), e(this, "toggleFallback", (e2 = false) => {
            var _a, _b;
            if (e2 ? this.scrollPosition = {
              x: (_a = window.scrollX) != null ? _a : 0,
              y: (_b = window.scrollY) != null ? _b : 0
            } : window.scrollTo(this.scrollPosition.x, this.scrollPosition.y), document.body.style.overflow = e2 ? "hidden" : "", R(this.target, this.player.config.classNames.fullscreen.fallback, e2), M.isIos) {
              let t3 = document.head.querySelector('meta[name="viewport"]');
              const i2 = "viewport-fit=cover";
              t3 || (t3 = document.createElement("meta"), t3.setAttribute("name", "viewport"));
              const s2 = S.string(t3.content) && t3.content.includes(i2);
              e2 ? (this.cleanupViewport = !s2, s2 || (t3.content += `,${i2}`)) : this.cleanupViewport && (t3.content = t3.content.split(",").filter((e3) => e3.trim() !== i2).join(","));
            }
            this.onChange();
          }), e(this, "trapFocus", (e2) => {
            if (M.isIos || M.isIPadOS || !this.active || "Tab" !== e2.key) return;
            const t3 = document.activeElement, i2 = U.call(this.player, "a[href], button:not(:disabled), input:not(:disabled), [tabindex]"), [s2] = i2, n2 = i2[i2.length - 1];
            t3 !== n2 || e2.shiftKey ? t3 === s2 && e2.shiftKey && (n2.focus(), e2.preventDefault()) : (s2.focus(), e2.preventDefault());
          }), e(this, "update", () => {
            if (this.supported) {
              let e2;
              e2 = this.forceFallback ? "Fallback (forced)" : He.nativeSupported ? "Native" : "Fallback", this.player.debug.log(`${e2} fullscreen enabled`);
            } else this.player.debug.log("Fullscreen not supported and fallback disabled");
            R(this.player.elements.container, this.player.config.classNames.fullscreen.enabled, this.supported);
          }), e(this, "enter", () => {
            this.supported && (M.isIos && this.player.config.fullscreen.iosNative ? this.player.isVimeo ? this.player.embed.requestFullscreen() : this.target.webkitEnterFullscreen() : !He.nativeSupported || this.forceFallback ? this.toggleFallback(true) : this.prefix ? S.empty(this.prefix) || this.target[`${this.prefix}Request${this.property}`]() : this.target.requestFullscreen({
              navigationUI: "hide"
            }));
          }), e(this, "exit", () => {
            if (this.supported) if (M.isIos && this.player.config.fullscreen.iosNative) this.player.isVimeo ? this.player.embed.exitFullscreen() : this.target.webkitEnterFullscreen(), ie(this.player.play());
            else if (!He.nativeSupported || this.forceFallback) this.toggleFallback(false);
            else if (this.prefix) {
              if (!S.empty(this.prefix)) {
                const e2 = "moz" === this.prefix ? "Cancel" : "Exit";
                document[`${this.prefix}${e2}${this.property}`]();
              }
            } else (document.cancelFullScreen || document.exitFullscreen).call(document);
          }), e(this, "toggle", () => {
            this.active ? this.exit() : this.enter();
          }), this.player = t2, this.prefix = He.prefix, this.property = He.property, this.scrollPosition = {
            x: 0,
            y: 0
          }, this.forceFallback = "force" === t2.config.fullscreen.fallback, this.player.elements.fullscreen = t2.config.fullscreen.container && function(e2, t3) {
            const {
              prototype: i2
            } = Element;
            return (i2.closest || function() {
              let e3 = this;
              do {
                if (V.matches(e3, t3)) return e3;
                e3 = e3.parentElement || e3.parentNode;
              } while (null !== e3 && 1 === e3.nodeType);
              return null;
            }).call(e2, t3);
          }(this.player.elements.container, t2.config.fullscreen.container), X.call(this.player, document, "ms" === this.prefix ? "MSFullscreenChange" : `${this.prefix}fullscreenchange`, () => {
            this.onChange();
          }), X.call(this.player, this.player.elements.container, "dblclick", (e2) => {
            S.element(this.player.elements.controls) && this.player.elements.controls.contains(e2.target) || this.player.listeners.proxy(e2, this.toggle, "fullscreen");
          }), X.call(this, this.player.elements.container, "keydown", (e2) => this.trapFocus(e2)), this.update();
        }
        static get nativeSupported() {
          return !!(document.fullscreenEnabled || document.webkitFullscreenEnabled || document.mozFullScreenEnabled || document.msFullscreenEnabled);
        }
        get useNative() {
          return He.nativeSupported && !this.forceFallback;
        }
        static get prefix() {
          if (S.function(document.exitFullscreen)) return "";
          let e2 = "";
          return ["webkit", "moz", "ms"].some((t2) => !(!S.function(document[`${t2}ExitFullscreen`]) && !S.function(document[`${t2}CancelFullScreen`])) && (e2 = t2, true)), e2;
        }
        static get property() {
          return "moz" === this.prefix ? "FullScreen" : "Fullscreen";
        }
        get supported() {
          return [this.player.config.fullscreen.enabled, this.player.isVideo, He.nativeSupported || this.player.config.fullscreen.fallback, !this.player.isYouTube || He.nativeSupported || !M.isIos || this.player.config.playsinline && !this.player.config.fullscreen.iosNative].every(Boolean);
        }
        get active() {
          if (!this.supported) return false;
          if (!He.nativeSupported || this.forceFallback) return F(this.target, this.player.config.classNames.fullscreen.fallback);
          const e2 = this.prefix ? this.target.getRootNode()[`${this.prefix}${this.property}Element`] : this.target.getRootNode().fullscreenElement;
          return e2 && e2.shadowRoot ? e2 === this.target.getRootNode().host : e2 === this.target;
        }
        get target() {
          var _a;
          return M.isIos && this.player.config.fullscreen.iosNative ? this.player.media : (_a = this.player.elements.fullscreen) != null ? _a : this.player.elements.container;
        }
      }
      function Re(e2, t2 = 1) {
        return new Promise((i2, s2) => {
          const n2 = new Image(), a2 = () => {
            delete n2.onload, delete n2.onerror, (n2.naturalWidth >= t2 ? i2 : s2)(n2);
          };
          Object.assign(n2, {
            onload: a2,
            onerror: a2,
            src: e2
          });
        });
      }
      const Fe = {
        addStyleHook() {
          R(this.elements.container, this.config.selectors.container.replace(".", ""), true), R(this.elements.container, this.config.classNames.uiSupported, this.supported.ui);
        },
        toggleNativeControls(e2 = false) {
          e2 && this.isHTML5 ? this.media.setAttribute("controls", "") : this.media.removeAttribute("controls");
        },
        build() {
          if (this.listeners.media(), !this.supported.ui) return this.debug.warn(`Basic support only for ${this.provider} ${this.type}`), void Fe.toggleNativeControls.call(this, true);
          S.element(this.elements.controls) || (Pe.inject.call(this), this.listeners.controls()), Fe.toggleNativeControls.call(this), this.isHTML5 && xe.setup.call(this), this.volume = null, this.muted = null, this.loop = null, this.quality = null, this.speed = null, Pe.updateVolume.call(this), Pe.timeUpdate.call(this), Pe.durationUpdate.call(this), Fe.checkPlaying.call(this), R(this.elements.container, this.config.classNames.pip.supported, K.pip && this.isHTML5 && this.isVideo), R(this.elements.container, this.config.classNames.airplay.supported, K.airplay && this.isHTML5), R(this.elements.container, this.config.classNames.isTouch, this.touch), this.ready = true, setTimeout(() => {
            Z.call(this, this.media, "ready");
          }, 0), Fe.setTitle.call(this), this.poster && Fe.setPoster.call(this, this.poster, false).catch(() => {
          }), this.config.duration && Pe.durationUpdate.call(this), this.config.mediaMetadata && Pe.setMediaMetadata.call(this);
        },
        setTitle() {
          let e2 = ve.get("play", this.config);
          if (S.string(this.config.title) && !S.empty(this.config.title) && (e2 += `, ${this.config.title}`), Array.from(this.elements.buttons.play || []).forEach((t2) => {
            t2.setAttribute("aria-label", e2);
          }), this.isEmbed) {
            const e3 = B.call(this, "iframe");
            if (!S.element(e3)) return;
            const t2 = S.empty(this.config.title) ? "video" : this.config.title, i2 = ve.get("frameTitle", this.config);
            e3.setAttribute("title", i2.replace("{title}", t2));
          }
        },
        togglePoster(e2) {
          R(this.elements.container, this.config.classNames.posterEnabled, e2);
        },
        setPoster(e2, t2 = true) {
          return t2 && this.poster ? Promise.reject(new Error("Poster already set")) : (this.media.setAttribute("data-poster", e2), this.elements.poster.removeAttribute("hidden"), te.call(this).then(() => Re(e2)).catch((t3) => {
            throw e2 === this.poster && Fe.togglePoster.call(this, false), t3;
          }).then(() => {
            if (e2 !== this.poster) throw new Error("setPoster cancelled by later call to setPoster");
          }).then(() => (Object.assign(this.elements.poster.style, {
            backgroundImage: `url('${e2}')`,
            backgroundSize: ""
          }), Fe.togglePoster.call(this, true), e2)));
        },
        checkPlaying(e2) {
          R(this.elements.container, this.config.classNames.playing, this.playing), R(this.elements.container, this.config.classNames.paused, this.paused), R(this.elements.container, this.config.classNames.stopped, this.stopped), Array.from(this.elements.buttons.play || []).forEach((e3) => {
            Object.assign(e3, {
              pressed: this.playing
            }), e3.setAttribute("aria-label", ve.get(this.playing ? "pause" : "play", this.config));
          }), S.event(e2) && "timeupdate" === e2.type || Fe.toggleControls.call(this);
        },
        checkLoading(e2) {
          this.loading = ["stalled", "waiting"].includes(e2.type), clearTimeout(this.timers.loading), this.timers.loading = setTimeout(() => {
            R(this.elements.container, this.config.classNames.loading, this.loading), Fe.toggleControls.call(this);
          }, this.loading ? 250 : 0);
        },
        toggleControls(e2) {
          const {
            controls: t2
          } = this.elements;
          if (t2 && this.config.hideControls) {
            const i2 = this.touch && this.lastSeekTime + 2e3 > Date.now();
            this.toggleControls(Boolean(e2 || this.loading || this.paused || t2.pressed || t2.hover || i2));
          }
        },
        migrateStyles() {
          Object.values(__spreadValues({}, this.media.style)).filter((e2) => !S.empty(e2) && S.string(e2) && e2.startsWith("--plyr")).forEach((e2) => {
            this.elements.container.style.setProperty(e2, this.media.style.getPropertyValue(e2)), this.media.style.removeProperty(e2);
          }), S.empty(this.media.style) && this.media.removeAttribute("style");
        }
      };
      class Ve {
        constructor(t2) {
          e(this, "firstTouch", () => {
            const {
              player: e2
            } = this, {
              elements: t3
            } = e2;
            e2.touch = true, R(t3.container, e2.config.classNames.isTouch, true);
          }), e(this, "global", (e2 = true) => {
            const {
              player: t3
            } = this;
            t3.config.keyboard.global && Q.call(t3, window, "keydown keyup", this.handleKey, e2, false), Q.call(t3, document.body, "click", this.toggleMenu, e2), G.call(t3, document.body, "touchstart", this.firstTouch);
          }), e(this, "container", () => {
            const {
              player: e2
            } = this, {
              config: t3,
              elements: i2,
              timers: s2
            } = e2;
            !t3.keyboard.global && t3.keyboard.focused && X.call(e2, i2.container, "keydown keyup", this.handleKey, false), X.call(e2, i2.container, "mousemove mouseleave touchstart touchmove enterfullscreen exitfullscreen", (t4) => {
              const {
                controls: n3
              } = i2;
              n3 && "enterfullscreen" === t4.type && (n3.pressed = false, n3.hover = false);
              let a3 = 0;
              ["touchstart", "touchmove", "mousemove"].includes(t4.type) && (Fe.toggleControls.call(e2, true), a3 = e2.touch ? 3e3 : 2e3), clearTimeout(s2.controls), s2.controls = setTimeout(() => Fe.toggleControls.call(e2, false), a3);
            });
            const n2 = () => {
              if (!e2.isVimeo || e2.config.vimeo.premium) return;
              const t4 = i2.wrapper, {
                active: s3
              } = e2.fullscreen, [n3, a3] = ce.call(e2), l2 = ae(`aspect-ratio: ${n3} / ${a3}`);
              if (!s3) return void (l2 ? (t4.style.width = null, t4.style.height = null) : (t4.style.maxWidth = null, t4.style.margin = null));
              const [r2, o2] = [Math.max(document.documentElement.clientWidth || 0, window.innerWidth || 0), Math.max(document.documentElement.clientHeight || 0, window.innerHeight || 0)], c2 = r2 / o2 > n3 / a3;
              l2 ? (t4.style.width = c2 ? "auto" : "100%", t4.style.height = c2 ? "100%" : "auto") : (t4.style.maxWidth = c2 ? o2 / a3 * n3 + "px" : null, t4.style.margin = c2 ? "0 auto" : null);
            }, a2 = () => {
              clearTimeout(s2.resized), s2.resized = setTimeout(n2, 50);
            };
            X.call(e2, i2.container, "enterfullscreen exitfullscreen", (t4) => {
              const {
                target: s3
              } = e2.fullscreen;
              if (s3 !== i2.container) return;
              if (!e2.isEmbed && S.empty(e2.config.ratio)) return;
              n2();
              ("enterfullscreen" === t4.type ? X : J).call(e2, window, "resize", a2);
            });
          }), e(this, "media", () => {
            const {
              player: e2
            } = this, {
              elements: t3
            } = e2;
            if (X.call(e2, e2.media, "timeupdate seeking seeked", (t4) => Pe.timeUpdate.call(e2, t4)), X.call(e2, e2.media, "durationchange loadeddata loadedmetadata", (t4) => Pe.durationUpdate.call(e2, t4)), X.call(e2, e2.media, "ended", () => {
              e2.isHTML5 && e2.isVideo && e2.config.resetOnEnd && (e2.restart(), e2.pause());
            }), X.call(e2, e2.media, "progress playing seeking seeked", (t4) => Pe.updateProgress.call(e2, t4)), X.call(e2, e2.media, "volumechange", (t4) => Pe.updateVolume.call(e2, t4)), X.call(e2, e2.media, "playing play pause ended emptied timeupdate", (t4) => Fe.checkPlaying.call(e2, t4)), X.call(e2, e2.media, "waiting canplay seeked playing", (t4) => Fe.checkLoading.call(e2, t4)), e2.supported.ui && e2.config.clickToPlay && !e2.isAudio) {
              const i3 = B.call(e2, `.${e2.config.classNames.video}`);
              if (!S.element(i3)) return;
              X.call(e2, t3.container, "click", (s2) => {
                ([t3.container, i3].includes(s2.target) || i3.contains(s2.target)) && (e2.touch && e2.config.hideControls || (e2.ended ? (this.proxy(s2, e2.restart, "restart"), this.proxy(s2, () => {
                  ie(e2.play());
                }, "play")) : this.proxy(s2, () => {
                  ie(e2.togglePlay());
                }, "play")));
              });
            }
            e2.supported.ui && e2.config.disableContextMenu && X.call(e2, t3.wrapper, "contextmenu", (e3) => {
              e3.preventDefault();
            }, false), X.call(e2, e2.media, "volumechange", () => {
              e2.storage.set({
                volume: e2.volume,
                muted: e2.muted
              });
            }), X.call(e2, e2.media, "ratechange", () => {
              Pe.updateSetting.call(e2, "speed"), e2.storage.set({
                speed: e2.speed
              });
            }), X.call(e2, e2.media, "qualitychange", (t4) => {
              Pe.updateSetting.call(e2, "quality", null, t4.detail.quality);
            }), X.call(e2, e2.media, "ready qualitychange", () => {
              Pe.setDownloadUrl.call(e2);
            });
            const i2 = e2.config.events.concat(["keyup", "keydown"]).join(" ");
            X.call(e2, e2.media, i2, (i3) => {
              let {
                detail: s2 = {}
              } = i3;
              "error" === i3.type && (s2 = e2.media.error), Z.call(e2, t3.container, i3.type, true, s2);
            });
          }), e(this, "proxy", (e2, t3, i2) => {
            const {
              player: s2
            } = this, n2 = s2.config.listeners[i2];
            let a2 = true;
            S.function(n2) && (a2 = n2.call(s2, e2)), false !== a2 && S.function(t3) && t3.call(s2, e2);
          }), e(this, "bind", (e2, t3, i2, s2, n2 = true) => {
            const {
              player: a2
            } = this, l2 = a2.config.listeners[s2], r2 = S.function(l2);
            X.call(a2, e2, t3, (e3) => this.proxy(e3, i2, s2), n2 && !r2);
          }), e(this, "controls", () => {
            const {
              player: e2
            } = this, {
              elements: t3
            } = e2, i2 = M.isIE ? "change" : "input";
            if (t3.buttons.play && Array.from(t3.buttons.play).forEach((t4) => {
              this.bind(t4, "click", () => {
                ie(e2.togglePlay());
              }, "play");
            }), this.bind(t3.buttons.restart, "click", e2.restart, "restart"), this.bind(t3.buttons.rewind, "click", () => {
              e2.lastSeekTime = Date.now(), e2.rewind();
            }, "rewind"), this.bind(t3.buttons.fastForward, "click", () => {
              e2.lastSeekTime = Date.now(), e2.forward();
            }, "fastForward"), this.bind(t3.buttons.mute, "click", () => {
              e2.muted = !e2.muted;
            }, "mute"), this.bind(t3.buttons.captions, "click", () => e2.toggleCaptions()), this.bind(t3.buttons.download, "click", () => {
              Z.call(e2, e2.media, "download");
            }, "download"), this.bind(t3.buttons.fullscreen, "click", () => {
              e2.fullscreen.toggle();
            }, "fullscreen"), this.bind(t3.buttons.pip, "click", () => {
              e2.pip = "toggle";
            }, "pip"), this.bind(t3.buttons.airplay, "click", e2.airplay, "airplay"), this.bind(t3.buttons.settings, "click", (t4) => {
              t4.stopPropagation(), t4.preventDefault(), Pe.toggleMenu.call(e2, t4);
            }, null, false), this.bind(t3.buttons.settings, "keyup", (t4) => {
              [" ", "Enter"].includes(t4.key) && ("Enter" !== t4.key ? (t4.preventDefault(), t4.stopPropagation(), Pe.toggleMenu.call(e2, t4)) : Pe.focusFirstMenuItem.call(e2, null, true));
            }, null, false), this.bind(t3.settings.menu, "keydown", (t4) => {
              "Escape" === t4.key && Pe.toggleMenu.call(e2, t4);
            }), this.bind(t3.inputs.seek, "mousedown mousemove", (e3) => {
              const i3 = t3.progress.getBoundingClientRect(), s2 = 100 / i3.width * (e3.pageX - i3.left);
              e3.currentTarget.setAttribute("seek-value", s2);
            }), this.bind(t3.inputs.seek, "mousedown mouseup keydown keyup touchstart touchend", (t4) => {
              const i3 = t4.currentTarget, s2 = "play-on-seeked";
              if (S.keyboardEvent(t4) && !["ArrowLeft", "ArrowRight"].includes(t4.key)) return;
              e2.lastSeekTime = Date.now();
              const n2 = i3.hasAttribute(s2), a2 = ["mouseup", "touchend", "keyup"].includes(t4.type);
              n2 && a2 ? (i3.removeAttribute(s2), ie(e2.play())) : !a2 && e2.playing && (i3.setAttribute(s2, ""), e2.pause());
            }), M.isIos) {
              const t4 = U.call(e2, 'input[type="range"]');
              Array.from(t4).forEach((e3) => this.bind(e3, i2, (e4) => P(e4.target)));
            }
            this.bind(t3.inputs.seek, i2, (t4) => {
              const i3 = t4.currentTarget;
              let s2 = i3.getAttribute("seek-value");
              S.empty(s2) && (s2 = i3.value), i3.removeAttribute("seek-value"), e2.currentTime = s2 / i3.max * e2.duration;
            }, "seek"), this.bind(t3.progress, "mouseenter mouseleave mousemove", (t4) => Pe.updateSeekTooltip.call(e2, t4)), this.bind(t3.progress, "mousemove touchmove", (t4) => {
              const {
                previewThumbnails: i3
              } = e2;
              i3 && i3.loaded && i3.startMove(t4);
            }), this.bind(t3.progress, "mouseleave touchend click", () => {
              const {
                previewThumbnails: t4
              } = e2;
              t4 && t4.loaded && t4.endMove(false, true);
            }), this.bind(t3.progress, "mousedown touchstart", (t4) => {
              const {
                previewThumbnails: i3
              } = e2;
              i3 && i3.loaded && i3.startScrubbing(t4);
            }), this.bind(t3.progress, "mouseup touchend", (t4) => {
              const {
                previewThumbnails: i3
              } = e2;
              i3 && i3.loaded && i3.endScrubbing(t4);
            }), M.isWebKit && Array.from(U.call(e2, 'input[type="range"]')).forEach((t4) => {
              this.bind(t4, "input", (t5) => Pe.updateRangeFill.call(e2, t5.target));
            }), e2.config.toggleInvert && !S.element(t3.display.duration) && this.bind(t3.display.currentTime, "click", () => {
              0 !== e2.currentTime && (e2.config.invertTime = !e2.config.invertTime, Pe.timeUpdate.call(e2));
            }), this.bind(t3.inputs.volume, i2, (t4) => {
              e2.volume = t4.target.value;
            }, "volume"), this.bind(t3.controls, "mouseenter mouseleave", (i3) => {
              t3.controls.hover = !e2.touch && "mouseenter" === i3.type;
            }), t3.fullscreen && Array.from(t3.fullscreen.children).filter((e3) => !e3.contains(t3.container)).forEach((i3) => {
              this.bind(i3, "mouseenter mouseleave", (i4) => {
                t3.controls && (t3.controls.hover = !e2.touch && "mouseenter" === i4.type);
              });
            }), this.bind(t3.controls, "mousedown mouseup touchstart touchend touchcancel", (e3) => {
              t3.controls.pressed = ["mousedown", "touchstart"].includes(e3.type);
            }), this.bind(t3.controls, "focusin", () => {
              const {
                config: i3,
                timers: s2
              } = e2;
              R(t3.controls, i3.classNames.noTransition, true), Fe.toggleControls.call(e2, true), setTimeout(() => {
                R(t3.controls, i3.classNames.noTransition, false);
              }, 0);
              const n2 = this.touch ? 3e3 : 4e3;
              clearTimeout(s2.controls), s2.controls = setTimeout(() => Fe.toggleControls.call(e2, false), n2);
            }), this.bind(t3.inputs.volume, "wheel", (t4) => {
              const i3 = t4.webkitDirectionInvertedFromDevice, [s2, n2] = [t4.deltaX, -t4.deltaY].map((e3) => i3 ? -e3 : e3), a2 = Math.sign(Math.abs(s2) > Math.abs(n2) ? s2 : n2);
              e2.increaseVolume(a2 / 50);
              const {
                volume: l2
              } = e2.media;
              (1 === a2 && l2 < 1 || -1 === a2 && l2 > 0) && t4.preventDefault();
            }, "volume", false);
          }), this.player = t2, this.lastKey = null, this.focusTimer = null, this.lastKeyDown = null, this.handleKey = this.handleKey.bind(this), this.toggleMenu = this.toggleMenu.bind(this), this.firstTouch = this.firstTouch.bind(this);
        }
        handleKey(e2) {
          const {
            player: t2
          } = this, {
            elements: i2
          } = t2, {
            key: s2,
            type: n2,
            altKey: a2,
            ctrlKey: l2,
            metaKey: r2,
            shiftKey: o2
          } = e2, c2 = "keydown" === n2, u2 = c2 && s2 === this.lastKey;
          if (a2 || l2 || r2 || o2) return;
          if (!s2) return;
          if (c2) {
            const n3 = document.activeElement;
            if (S.element(n3)) {
              const {
                editable: s3
              } = t2.config.selectors, {
                seek: a3
              } = i2.inputs;
              if (n3 !== a3 && V(n3, s3)) return;
              if (" " === e2.key && V(n3, 'button, [role^="menuitem"]')) return;
            }
            switch ([" ", "ArrowLeft", "ArrowUp", "ArrowRight", "ArrowDown", "0", "1", "2", "3", "4", "5", "6", "7", "8", "9", "c", "f", "k", "l", "m"].includes(s2) && (e2.preventDefault(), e2.stopPropagation()), s2) {
              case "0":
              case "1":
              case "2":
              case "3":
              case "4":
              case "5":
              case "6":
              case "7":
              case "8":
              case "9":
                u2 || (h2 = parseInt(s2, 10), t2.currentTime = t2.duration / 10 * h2);
                break;
              case " ":
              case "k":
                u2 || ie(t2.togglePlay());
                break;
              case "ArrowUp":
                t2.increaseVolume(0.1);
                break;
              case "ArrowDown":
                t2.decreaseVolume(0.1);
                break;
              case "m":
                u2 || (t2.muted = !t2.muted);
                break;
              case "ArrowRight":
                t2.forward();
                break;
              case "ArrowLeft":
                t2.rewind();
                break;
              case "f":
                t2.fullscreen.toggle();
                break;
              case "c":
                u2 || t2.toggleCaptions();
                break;
              case "l":
                t2.loop = !t2.loop;
            }
            "Escape" === s2 && !t2.fullscreen.usingNative && t2.fullscreen.active && t2.fullscreen.toggle(), this.lastKey = s2;
          } else this.lastKey = null;
          var h2;
        }
        toggleMenu(e2) {
          Pe.toggleMenu.call(this.player, e2);
        }
      }
      "undefined" != typeof globalThis ? globalThis : "undefined" != typeof window ? window : "undefined" != typeof global ? global : "undefined" != typeof self && self;
      var Ue = function(e2, t2) {
        return e2(t2 = {
          exports: {}
        }, t2.exports), t2.exports;
      }(function(e2, t2) {
        e2.exports = function() {
          var e3 = function() {
          }, t3 = {}, i2 = {}, s2 = {};
          function n2(e4, t4) {
            e4 = e4.push ? e4 : [e4];
            var n3, a3, l3, r3 = [], o3 = e4.length, c3 = o3;
            for (n3 = function(e5, i3) {
              i3.length && r3.push(e5), --c3 || t4(r3);
            }; o3--; ) a3 = e4[o3], (l3 = i2[a3]) ? n3(a3, l3) : (s2[a3] = s2[a3] || []).push(n3);
          }
          function a2(e4, t4) {
            if (e4) {
              var n3 = s2[e4];
              if (i2[e4] = t4, n3) for (; n3.length; ) n3[0](e4, t4), n3.splice(0, 1);
            }
          }
          function l2(t4, i3) {
            t4.call && (t4 = {
              success: t4
            }), i3.length ? (t4.error || e3)(i3) : (t4.success || e3)(t4);
          }
          function r2(t4, i3, s3, n3) {
            var a3, l3, o3 = document, c3 = s3.async, u2 = (s3.numRetries || 0) + 1, h2 = s3.before || e3, d2 = t4.replace(/[\?|#].*$/, ""), m2 = t4.replace(/^(css|img)!/, "");
            n3 = n3 || 0, /(^css!|\.css$)/.test(d2) ? ((l3 = o3.createElement("link")).rel = "stylesheet", l3.href = m2, (a3 = "hideFocus" in l3) && l3.relList && (a3 = 0, l3.rel = "preload", l3.as = "style")) : /(^img!|\.(png|gif|jpg|svg|webp)$)/.test(d2) ? (l3 = o3.createElement("img")).src = m2 : ((l3 = o3.createElement("script")).src = t4, l3.async = void 0 === c3 || c3), l3.onload = l3.onerror = l3.onbeforeload = function(e4) {
              var o4 = e4.type[0];
              if (a3) try {
                l3.sheet.cssText.length || (o4 = "e");
              } catch (e5) {
                18 != e5.code && (o4 = "e");
              }
              if ("e" == o4) {
                if ((n3 += 1) < u2) return r2(t4, i3, s3, n3);
              } else if ("preload" == l3.rel && "style" == l3.as) return l3.rel = "stylesheet";
              i3(t4, o4, e4.defaultPrevented);
            }, false !== h2(t4, l3) && o3.head.appendChild(l3);
          }
          function o2(e4, t4, i3) {
            var s3, n3, a3 = (e4 = e4.push ? e4 : [e4]).length, l3 = a3, o3 = [];
            for (s3 = function(e5, i4, s4) {
              if ("e" == i4 && o3.push(e5), "b" == i4) {
                if (!s4) return;
                o3.push(e5);
              }
              --a3 || t4(o3);
            }, n3 = 0; n3 < l3; n3++) r2(e4[n3], s3, i3);
          }
          function c2(e4, i3, s3) {
            var n3, r3;
            if (i3 && i3.trim && (n3 = i3), r3 = (n3 ? s3 : i3) || {}, n3) {
              if (n3 in t3) throw "LoadJS";
              t3[n3] = true;
            }
            function c3(t4, i4) {
              o2(e4, function(e5) {
                l2(r3, e5), t4 && l2({
                  success: t4,
                  error: i4
                }, e5), a2(n3, e5);
              }, r3);
            }
            if (r3.returnPromise) return new Promise(c3);
            c3();
          }
          return c2.ready = function(e4, t4) {
            return n2(e4, function(e5) {
              l2(t4, e5);
            }), c2;
          }, c2.done = function(e4) {
            a2(e4, []);
          }, c2.reset = function() {
            t3 = {}, i2 = {}, s2 = {};
          }, c2.isDefined = function(e4) {
            return e4 in t3;
          }, c2;
        }();
      });
      function Be(e2) {
        return new Promise((t2, i2) => {
          Ue(e2, {
            success: t2,
            error: i2
          });
        });
      }
      function We(e2) {
        e2 && !this.embed.hasPlayed && (this.embed.hasPlayed = true), this.media.paused === e2 && (this.media.paused = !e2, Z.call(this, this.media, e2 ? "play" : "pause"));
      }
      const ze = {
        setup() {
          const e2 = this;
          R(e2.elements.wrapper, e2.config.classNames.embed, true), e2.options.speed = e2.config.speed.options, ue.call(e2), S.object(window.Vimeo) ? ze.ready.call(e2) : Be(e2.config.urls.vimeo.sdk).then(() => {
            ze.ready.call(e2);
          }).catch((t2) => {
            e2.debug.warn("Vimeo SDK (player.js) failed to load", t2);
          });
        },
        ready() {
          const e2 = this, t2 = e2.config.vimeo, _a = t2, {
            premium: i2,
            referrerPolicy: s2
          } = _a, n2 = __objRest(_a, [
            "premium",
            "referrerPolicy"
          ]);
          let a2 = e2.media.getAttribute("src"), l2 = "";
          S.empty(a2) ? (a2 = e2.media.getAttribute(e2.config.attributes.embed.id), l2 = e2.media.getAttribute(e2.config.attributes.embed.hash)) : l2 = function(e3) {
            const t3 = e3.match(/^.*(vimeo.com\/|video\/)(\d+)(\?.*&*h=|\/)+([\d,a-f]+)/);
            return t3 && 5 === t3.length ? t3[4] : null;
          }(a2);
          const r2 = l2 ? {
            h: l2
          } : {};
          i2 && Object.assign(n2, {
            controls: false,
            sidedock: false
          });
          const o2 = Ne(__spreadValues(__spreadValues({
            loop: e2.config.loop.active,
            autoplay: e2.autoplay,
            muted: e2.muted,
            gesture: "media",
            playsinline: e2.config.playsinline
          }, r2), n2)), c2 = (u2 = a2, S.empty(u2) ? null : S.number(Number(u2)) ? u2 : u2.match(/^.*(vimeo.com\/|video\/)(\d+).*/) ? RegExp.$2 : u2);
          var u2;
          const h2 = $("iframe"), d2 = me(e2.config.urls.vimeo.iframe, c2, o2);
          if (h2.setAttribute("src", d2), h2.setAttribute("allowfullscreen", ""), h2.setAttribute("allow", ["autoplay", "fullscreen", "picture-in-picture", "encrypted-media", "accelerometer", "gyroscope"].join("; ")), S.empty(s2) || h2.setAttribute("referrerPolicy", s2), i2 || !t2.customControls) h2.setAttribute("data-poster", e2.poster), e2.media = q(h2, e2.media);
          else {
            const t3 = $("div", {
              class: e2.config.classNames.embedContainer,
              "data-poster": e2.poster
            });
            t3.appendChild(h2), e2.media = q(t3, e2.media);
          }
          t2.customControls || Te(me(e2.config.urls.vimeo.api, d2)).then((t3) => {
            !S.empty(t3) && t3.thumbnail_url && Fe.setPoster.call(e2, t3.thumbnail_url).catch(() => {
            });
          }), e2.embed = new window.Vimeo.Player(h2, {
            autopause: e2.config.autopause,
            muted: e2.muted
          }), e2.media.paused = true, e2.media.currentTime = 0, e2.supported.ui && e2.embed.disableTextTrack(), e2.media.play = () => (We.call(e2, true), e2.embed.play()), e2.media.pause = () => (We.call(e2, false), e2.embed.pause()), e2.media.stop = () => {
            e2.pause(), e2.currentTime = 0;
          };
          let {
            currentTime: m2
          } = e2.media;
          Object.defineProperty(e2.media, "currentTime", {
            get: () => m2,
            set(t3) {
              const {
                embed: i3,
                media: s3,
                paused: n3,
                volume: a3
              } = e2, l3 = n3 && !i3.hasPlayed;
              s3.seeking = true, Z.call(e2, s3, "seeking"), Promise.resolve(l3 && i3.setVolume(0)).then(() => i3.setCurrentTime(t3)).then(() => l3 && i3.pause()).then(() => l3 && i3.setVolume(a3)).catch(() => {
              });
            }
          });
          let p2 = e2.config.speed.selected;
          Object.defineProperty(e2.media, "playbackRate", {
            get: () => p2,
            set(t3) {
              e2.embed.setPlaybackRate(t3).then(() => {
                p2 = t3, Z.call(e2, e2.media, "ratechange");
              }).catch(() => {
                e2.options.speed = [1];
              });
            }
          });
          let {
            volume: g2
          } = e2.config;
          Object.defineProperty(e2.media, "volume", {
            get: () => g2,
            set(t3) {
              e2.embed.setVolume(t3).then(() => {
                g2 = t3, Z.call(e2, e2.media, "volumechange");
              });
            }
          });
          let {
            muted: f2
          } = e2.config;
          Object.defineProperty(e2.media, "muted", {
            get: () => f2,
            set(t3) {
              const i3 = !!S.boolean(t3) && t3;
              e2.embed.setMuted(!!i3 || e2.config.muted).then(() => {
                f2 = i3, Z.call(e2, e2.media, "volumechange");
              });
            }
          });
          let y2, {
            loop: b2
          } = e2.config;
          Object.defineProperty(e2.media, "loop", {
            get: () => b2,
            set(t3) {
              const i3 = S.boolean(t3) ? t3 : e2.config.loop.active;
              e2.embed.setLoop(i3).then(() => {
                b2 = i3;
              });
            }
          }), e2.embed.getVideoUrl().then((t3) => {
            y2 = t3, Pe.setDownloadUrl.call(e2);
          }).catch((e3) => {
            this.debug.warn(e3);
          }), Object.defineProperty(e2.media, "currentSrc", {
            get: () => y2
          }), Object.defineProperty(e2.media, "ended", {
            get: () => e2.currentTime === e2.duration
          }), Promise.all([e2.embed.getVideoWidth(), e2.embed.getVideoHeight()]).then((t3) => {
            const [i3, s3] = t3;
            e2.embed.ratio = he(i3, s3), ue.call(this);
          }), e2.embed.setAutopause(e2.config.autopause).then((t3) => {
            e2.config.autopause = t3;
          }), e2.embed.getVideoTitle().then((t3) => {
            e2.config.title = t3, Fe.setTitle.call(this);
          }), e2.embed.getCurrentTime().then((t3) => {
            m2 = t3, Z.call(e2, e2.media, "timeupdate");
          }), e2.embed.getDuration().then((t3) => {
            e2.media.duration = t3, Z.call(e2, e2.media, "durationchange");
          }), e2.embed.getTextTracks().then((t3) => {
            e2.media.textTracks = t3, xe.setup.call(e2);
          }), e2.embed.on("cuechange", ({
            cues: t3 = []
          }) => {
            const i3 = t3.map((e3) => function(e4) {
              const t4 = document.createDocumentFragment(), i4 = document.createElement("div");
              return t4.appendChild(i4), i4.innerHTML = e4, t4.firstChild.innerText;
            }(e3.text));
            xe.updateCues.call(e2, i3);
          }), e2.embed.on("loaded", () => {
            if (e2.embed.getPaused().then((t3) => {
              We.call(e2, !t3), t3 || Z.call(e2, e2.media, "playing");
            }), S.element(e2.embed.element) && e2.supported.ui) {
              e2.embed.element.setAttribute("tabindex", -1);
            }
          }), e2.embed.on("bufferstart", () => {
            Z.call(e2, e2.media, "waiting");
          }), e2.embed.on("bufferend", () => {
            Z.call(e2, e2.media, "playing");
          }), e2.embed.on("play", () => {
            We.call(e2, true), Z.call(e2, e2.media, "playing");
          }), e2.embed.on("pause", () => {
            We.call(e2, false);
          }), e2.embed.on("timeupdate", (t3) => {
            e2.media.seeking = false, m2 = t3.seconds, Z.call(e2, e2.media, "timeupdate");
          }), e2.embed.on("progress", (t3) => {
            e2.media.buffered = t3.percent, Z.call(e2, e2.media, "progress"), 1 === parseInt(t3.percent, 10) && Z.call(e2, e2.media, "canplaythrough"), e2.embed.getDuration().then((t4) => {
              t4 !== e2.media.duration && (e2.media.duration = t4, Z.call(e2, e2.media, "durationchange"));
            });
          }), e2.embed.on("seeked", () => {
            e2.media.seeking = false, Z.call(e2, e2.media, "seeked");
          }), e2.embed.on("ended", () => {
            e2.media.paused = true, Z.call(e2, e2.media, "ended");
          }), e2.embed.on("error", (t3) => {
            e2.media.error = t3, Z.call(e2, e2.media, "error");
          }), t2.customControls && setTimeout(() => Fe.build.call(e2), 0);
        }
      };
      function Ke(e2) {
        e2 && !this.embed.hasPlayed && (this.embed.hasPlayed = true), this.media.paused === e2 && (this.media.paused = !e2, Z.call(this, this.media, e2 ? "play" : "pause"));
      }
      function Ye(e2) {
        return e2.noCookie ? "https://www.youtube-nocookie.com" : "http:" === window.location.protocol ? "http://www.youtube.com" : void 0;
      }
      const Qe = {
        setup() {
          if (R(this.elements.wrapper, this.config.classNames.embed, true), S.object(window.YT) && S.function(window.YT.Player)) Qe.ready.call(this);
          else {
            const e2 = window.onYouTubeIframeAPIReady;
            window.onYouTubeIframeAPIReady = () => {
              S.function(e2) && e2(), Qe.ready.call(this);
            }, Be(this.config.urls.youtube.sdk).catch((e3) => {
              this.debug.warn("YouTube API failed to load", e3);
            });
          }
        },
        getTitle(e2) {
          Te(me(this.config.urls.youtube.api, e2)).then((e3) => {
            if (S.object(e3)) {
              const {
                title: t2,
                height: i2,
                width: s2
              } = e3;
              this.config.title = t2, Fe.setTitle.call(this), this.embed.ratio = he(s2, i2);
            }
            ue.call(this);
          }).catch(() => {
            ue.call(this);
          });
        },
        ready() {
          const e2 = this, t2 = e2.config.youtube, i2 = e2.media && e2.media.getAttribute("id");
          if (!S.empty(i2) && i2.startsWith("youtube-")) return;
          let s2 = e2.media.getAttribute("src");
          S.empty(s2) && (s2 = e2.media.getAttribute(this.config.attributes.embed.id));
          const n2 = (a2 = s2, S.empty(a2) ? null : a2.match(/^.*(youtu.be\/|v\/|u\/\w\/|embed\/|watch\?v=|&v=)([^#&?]*).*/) ? RegExp.$2 : a2);
          var a2;
          const l2 = $("div", {
            id: `${e2.provider}-${Math.floor(1e4 * Math.random())}`,
            "data-poster": t2.customControls ? e2.poster : void 0
          });
          if (e2.media = q(l2, e2.media), t2.customControls) {
            const t3 = (e3) => `https://i.ytimg.com/vi/${n2}/${e3}default.jpg`;
            Re(t3("maxres"), 121).catch(() => Re(t3("sd"), 121)).catch(() => Re(t3("hq"))).then((t4) => Fe.setPoster.call(e2, t4.src)).then((t4) => {
              t4.includes("maxres") || (e2.elements.poster.style.backgroundSize = "cover");
            }).catch(() => {
            });
          }
          e2.embed = new window.YT.Player(e2.media, {
            videoId: n2,
            host: Ye(t2),
            playerVars: x({}, {
              autoplay: e2.config.autoplay ? 1 : 0,
              hl: e2.config.hl,
              controls: e2.supported.ui && t2.customControls ? 0 : 1,
              disablekb: 1,
              playsinline: e2.config.playsinline && !e2.config.fullscreen.iosNative ? 1 : 0,
              cc_load_policy: e2.captions.active ? 1 : 0,
              cc_lang_pref: e2.config.captions.language,
              widget_referrer: window ? window.location.href : null
            }, t2),
            events: {
              onError(t3) {
                if (!e2.media.error) {
                  const i3 = t3.data, s3 = {
                    2: "The request contains an invalid parameter value. For example, this error occurs if you specify a video ID that does not have 11 characters, or if the video ID contains invalid characters, such as exclamation points or asterisks.",
                    5: "The requested content cannot be played in an HTML5 player or another error related to the HTML5 player has occurred.",
                    100: "The video requested was not found. This error occurs when a video has been removed (for any reason) or has been marked as private.",
                    101: "The owner of the requested video does not allow it to be played in embedded players.",
                    150: "The owner of the requested video does not allow it to be played in embedded players."
                  }[i3] || "An unknown error occurred";
                  e2.media.error = {
                    code: i3,
                    message: s3
                  }, Z.call(e2, e2.media, "error");
                }
              },
              onPlaybackRateChange(t3) {
                const i3 = t3.target;
                e2.media.playbackRate = i3.getPlaybackRate(), Z.call(e2, e2.media, "ratechange");
              },
              onReady(i3) {
                if (S.function(e2.media.play)) return;
                const s3 = i3.target;
                Qe.getTitle.call(e2, n2), e2.media.play = () => {
                  Ke.call(e2, true), s3.playVideo();
                }, e2.media.pause = () => {
                  Ke.call(e2, false), s3.pauseVideo();
                }, e2.media.stop = () => {
                  s3.stopVideo();
                }, e2.media.duration = s3.getDuration(), e2.media.paused = true, e2.media.currentTime = 0, Object.defineProperty(e2.media, "currentTime", {
                  get: () => Number(s3.getCurrentTime()),
                  set(t3) {
                    e2.paused && !e2.embed.hasPlayed && e2.embed.mute(), e2.media.seeking = true, Z.call(e2, e2.media, "seeking"), s3.seekTo(t3);
                  }
                }), Object.defineProperty(e2.media, "playbackRate", {
                  get: () => s3.getPlaybackRate(),
                  set(e3) {
                    s3.setPlaybackRate(e3);
                  }
                });
                let {
                  volume: a3
                } = e2.config;
                Object.defineProperty(e2.media, "volume", {
                  get: () => a3,
                  set(t3) {
                    a3 = t3, s3.setVolume(100 * a3), Z.call(e2, e2.media, "volumechange");
                  }
                });
                let {
                  muted: l3
                } = e2.config;
                Object.defineProperty(e2.media, "muted", {
                  get: () => l3,
                  set(t3) {
                    const i4 = S.boolean(t3) ? t3 : l3;
                    l3 = i4, s3[i4 ? "mute" : "unMute"](), s3.setVolume(100 * a3), Z.call(e2, e2.media, "volumechange");
                  }
                }), Object.defineProperty(e2.media, "currentSrc", {
                  get: () => s3.getVideoUrl()
                }), Object.defineProperty(e2.media, "ended", {
                  get: () => e2.currentTime === e2.duration
                });
                const r2 = s3.getAvailablePlaybackRates();
                e2.options.speed = r2.filter((t3) => e2.config.speed.options.includes(t3)), e2.supported.ui && t2.customControls && e2.media.setAttribute("tabindex", -1), Z.call(e2, e2.media, "timeupdate"), Z.call(e2, e2.media, "durationchange"), clearInterval(e2.timers.buffering), e2.timers.buffering = setInterval(() => {
                  e2.media.buffered = s3.getVideoLoadedFraction(), (null === e2.media.lastBuffered || e2.media.lastBuffered < e2.media.buffered) && Z.call(e2, e2.media, "progress"), e2.media.lastBuffered = e2.media.buffered, 1 === e2.media.buffered && (clearInterval(e2.timers.buffering), Z.call(e2, e2.media, "canplaythrough"));
                }, 200), t2.customControls && setTimeout(() => Fe.build.call(e2), 50);
              },
              onStateChange(i3) {
                const s3 = i3.target;
                clearInterval(e2.timers.playing);
                switch (e2.media.seeking && [1, 2].includes(i3.data) && (e2.media.seeking = false, Z.call(e2, e2.media, "seeked")), i3.data) {
                  case -1:
                    Z.call(e2, e2.media, "timeupdate"), e2.media.buffered = s3.getVideoLoadedFraction(), Z.call(e2, e2.media, "progress");
                    break;
                  case 0:
                    Ke.call(e2, false), e2.media.loop ? (s3.stopVideo(), s3.playVideo()) : Z.call(e2, e2.media, "ended");
                    break;
                  case 1:
                    t2.customControls && !e2.config.autoplay && e2.media.paused && !e2.embed.hasPlayed ? e2.media.pause() : (Ke.call(e2, true), Z.call(e2, e2.media, "playing"), e2.timers.playing = setInterval(() => {
                      Z.call(e2, e2.media, "timeupdate");
                    }, 50), e2.media.duration !== s3.getDuration() && (e2.media.duration = s3.getDuration(), Z.call(e2, e2.media, "durationchange")));
                    break;
                  case 2:
                    e2.muted || e2.embed.unMute(), Ke.call(e2, false);
                    break;
                  case 3:
                    Z.call(e2, e2.media, "waiting");
                }
                Z.call(e2, e2.elements.container, "statechange", false, {
                  code: i3.data
                });
              }
            }
          });
        }
      }, Xe = {
        setup() {
          this.media ? (R(this.elements.container, this.config.classNames.type.replace("{0}", this.type), true), R(this.elements.container, this.config.classNames.provider.replace("{0}", this.provider), true), this.isEmbed && R(this.elements.container, this.config.classNames.type.replace("{0}", "video"), true), this.isVideo && (this.elements.wrapper = $("div", {
            class: this.config.classNames.video
          }), L(this.media, this.elements.wrapper), this.elements.poster = $("div", {
            class: this.config.classNames.poster
          }), this.elements.wrapper.appendChild(this.elements.poster)), this.isHTML5 ? de.setup.call(this) : this.isYouTube ? Qe.setup.call(this) : this.isVimeo && ze.setup.call(this)) : this.debug.warn("No media element found!");
        }
      };
      class Je {
        constructor(t2) {
          e(this, "load", () => {
            this.enabled && (S.object(window.google) && S.object(window.google.ima) ? this.ready() : Be(this.player.config.urls.googleIMA.sdk).then(() => {
              this.ready();
            }).catch(() => {
              this.trigger("error", new Error("Google IMA SDK failed to load"));
            }));
          }), e(this, "ready", () => {
            var e2;
            this.enabled || ((e2 = this).manager && e2.manager.destroy(), e2.elements.displayContainer && e2.elements.displayContainer.destroy(), e2.elements.container.remove()), this.startSafetyTimer(12e3, "ready()"), this.managerPromise.then(() => {
              this.clearSafetyTimer("onAdsManagerLoaded()");
            }), this.listeners(), this.setupIMA();
          }), e(this, "setupIMA", () => {
            this.elements.container = $("div", {
              class: this.player.config.classNames.ads
            }), this.player.elements.container.appendChild(this.elements.container), google.ima.settings.setVpaidMode(google.ima.ImaSdkSettings.VpaidMode.ENABLED), google.ima.settings.setLocale(this.player.config.ads.language), google.ima.settings.setDisableCustomPlaybackForIOS10Plus(this.player.config.playsinline), this.elements.displayContainer = new google.ima.AdDisplayContainer(this.elements.container, this.player.media), this.loader = new google.ima.AdsLoader(this.elements.displayContainer), this.loader.addEventListener(google.ima.AdsManagerLoadedEvent.Type.ADS_MANAGER_LOADED, (e2) => this.onAdsManagerLoaded(e2), false), this.loader.addEventListener(google.ima.AdErrorEvent.Type.AD_ERROR, (e2) => this.onAdError(e2), false), this.requestAds();
          }), e(this, "requestAds", () => {
            const {
              container: e2
            } = this.player.elements;
            try {
              const t3 = new google.ima.AdsRequest();
              t3.adTagUrl = this.tagUrl, t3.linearAdSlotWidth = e2.offsetWidth, t3.linearAdSlotHeight = e2.offsetHeight, t3.nonLinearAdSlotWidth = e2.offsetWidth, t3.nonLinearAdSlotHeight = e2.offsetHeight, t3.forceNonLinearFullSlot = false, t3.setAdWillPlayMuted(!this.player.muted), this.loader.requestAds(t3);
            } catch (e3) {
              this.onAdError(e3);
            }
          }), e(this, "pollCountdown", (e2 = false) => {
            if (!e2) return clearInterval(this.countdownTimer), void this.elements.container.removeAttribute("data-badge-text");
            this.countdownTimer = setInterval(() => {
              const e3 = Ee(Math.max(this.manager.getRemainingTime(), 0)), t3 = `${ve.get("advertisement", this.player.config)} - ${e3}`;
              this.elements.container.setAttribute("data-badge-text", t3);
            }, 100);
          }), e(this, "onAdsManagerLoaded", (e2) => {
            if (!this.enabled) return;
            const t3 = new google.ima.AdsRenderingSettings();
            t3.restoreCustomPlaybackStateOnAdBreakComplete = true, t3.enablePreloading = true, this.manager = e2.getAdsManager(this.player, t3), this.cuePoints = this.manager.getCuePoints(), this.manager.addEventListener(google.ima.AdErrorEvent.Type.AD_ERROR, (e3) => this.onAdError(e3)), Object.keys(google.ima.AdEvent.Type).forEach((e3) => {
              this.manager.addEventListener(google.ima.AdEvent.Type[e3], (e4) => this.onAdEvent(e4));
            }), this.trigger("loaded");
          }), e(this, "addCuePoints", () => {
            S.empty(this.cuePoints) || this.cuePoints.forEach((e2) => {
              if (0 !== e2 && -1 !== e2 && e2 < this.player.duration) {
                const t3 = this.player.elements.progress;
                if (S.element(t3)) {
                  const i2 = 100 / this.player.duration * e2, s2 = $("span", {
                    class: this.player.config.classNames.cues
                  });
                  s2.style.left = `${i2.toString()}%`, t3.appendChild(s2);
                }
              }
            });
          }), e(this, "onAdEvent", (e2) => {
            const {
              container: t3
            } = this.player.elements, i2 = e2.getAd(), s2 = e2.getAdData();
            switch (((e3) => {
              Z.call(this.player, this.player.media, `ads${e3.replace(/_/g, "").toLowerCase()}`);
            })(e2.type), e2.type) {
              case google.ima.AdEvent.Type.LOADED:
                this.trigger("loaded"), this.pollCountdown(true), i2.isLinear() || (i2.width = t3.offsetWidth, i2.height = t3.offsetHeight);
                break;
              case google.ima.AdEvent.Type.STARTED:
                this.manager.setVolume(this.player.volume);
                break;
              case google.ima.AdEvent.Type.ALL_ADS_COMPLETED:
                this.player.ended ? this.loadAds() : this.loader.contentComplete();
                break;
              case google.ima.AdEvent.Type.CONTENT_PAUSE_REQUESTED:
                this.pauseContent();
                break;
              case google.ima.AdEvent.Type.CONTENT_RESUME_REQUESTED:
                this.pollCountdown(), this.resumeContent();
                break;
              case google.ima.AdEvent.Type.LOG:
                s2.adError && this.player.debug.warn(`Non-fatal ad error: ${s2.adError.getMessage()}`);
            }
          }), e(this, "onAdError", (e2) => {
            this.cancel(), this.player.debug.warn("Ads error", e2);
          }), e(this, "listeners", () => {
            const {
              container: e2
            } = this.player.elements;
            let t3;
            this.player.on("canplay", () => {
              this.addCuePoints();
            }), this.player.on("ended", () => {
              this.loader.contentComplete();
            }), this.player.on("timeupdate", () => {
              t3 = this.player.currentTime;
            }), this.player.on("seeked", () => {
              const e3 = this.player.currentTime;
              S.empty(this.cuePoints) || this.cuePoints.forEach((i2, s2) => {
                t3 < i2 && i2 < e3 && (this.manager.discardAdBreak(), this.cuePoints.splice(s2, 1));
              });
            }), window.addEventListener("resize", () => {
              this.manager && this.manager.resize(e2.offsetWidth, e2.offsetHeight, google.ima.ViewMode.NORMAL);
            });
          }), e(this, "play", () => {
            const {
              container: e2
            } = this.player.elements;
            this.managerPromise || this.resumeContent(), this.managerPromise.then(() => {
              this.manager.setVolume(this.player.volume), this.elements.displayContainer.initialize();
              try {
                this.initialized || (this.manager.init(e2.offsetWidth, e2.offsetHeight, google.ima.ViewMode.NORMAL), this.manager.start()), this.initialized = true;
              } catch (e3) {
                this.onAdError(e3);
              }
            }).catch(() => {
            });
          }), e(this, "resumeContent", () => {
            this.elements.container.style.zIndex = "", this.playing = false, ie(this.player.media.play());
          }), e(this, "pauseContent", () => {
            this.elements.container.style.zIndex = 3, this.playing = true, this.player.media.pause();
          }), e(this, "cancel", () => {
            this.initialized && this.resumeContent(), this.trigger("error"), this.loadAds();
          }), e(this, "loadAds", () => {
            this.managerPromise.then(() => {
              this.manager && this.manager.destroy(), this.managerPromise = new Promise((e2) => {
                this.on("loaded", e2), this.player.debug.log(this.manager);
              }), this.initialized = false, this.requestAds();
            }).catch(() => {
            });
          }), e(this, "trigger", (e2, ...t3) => {
            const i2 = this.events[e2];
            S.array(i2) && i2.forEach((e3) => {
              S.function(e3) && e3.apply(this, t3);
            });
          }), e(this, "on", (e2, t3) => (S.array(this.events[e2]) || (this.events[e2] = []), this.events[e2].push(t3), this)), e(this, "startSafetyTimer", (e2, t3) => {
            this.player.debug.log(`Safety timer invoked from: ${t3}`), this.safetyTimer = setTimeout(() => {
              this.cancel(), this.clearSafetyTimer("startSafetyTimer()");
            }, e2);
          }), e(this, "clearSafetyTimer", (e2) => {
            S.nullOrUndefined(this.safetyTimer) || (this.player.debug.log(`Safety timer cleared from: ${e2}`), clearTimeout(this.safetyTimer), this.safetyTimer = null);
          }), this.player = t2, this.config = t2.config.ads, this.playing = false, this.initialized = false, this.elements = {
            container: null,
            displayContainer: null
          }, this.manager = null, this.loader = null, this.cuePoints = null, this.events = {}, this.safetyTimer = null, this.countdownTimer = null, this.managerPromise = new Promise((e2, t3) => {
            this.on("loaded", e2), this.on("error", t3);
          }), this.load();
        }
        get enabled() {
          const {
            config: e2
          } = this;
          return this.player.isHTML5 && this.player.isVideo && e2.enabled && (!S.empty(e2.publisherId) || S.url(e2.tagUrl));
        }
        get tagUrl() {
          const {
            config: e2
          } = this;
          if (S.url(e2.tagUrl)) return e2.tagUrl;
          return `https://go.aniview.com/api/adserver6/vast/?${Ne({
            AV_PUBLISHERID: "58c25bb0073ef448b1087ad6",
            AV_CHANNELID: "5a0458dc28a06145e4519d21",
            AV_URL: window.location.hostname,
            cb: Date.now(),
            AV_WIDTH: 640,
            AV_HEIGHT: 480,
            AV_CDIM2: e2.publisherId
          })}`;
        }
      }
      function Ge(e2 = 0, t2 = 0, i2 = 255) {
        return Math.min(Math.max(e2, t2), i2);
      }
      const Ze = (e2) => {
        const t2 = [];
        return e2.split(/\r\n\r\n|\n\n|\r\r/).forEach((e3) => {
          const i2 = {};
          e3.split(/\r\n|\n|\r/).forEach((e4) => {
            if (S.number(i2.startTime)) {
              if (!S.empty(e4.trim()) && S.empty(i2.text)) {
                const t3 = e4.trim().split("#xywh=");
                [i2.text] = t3, t3[1] && ([i2.x, i2.y, i2.w, i2.h] = t3[1].split(","));
              }
            } else {
              const t3 = e4.match(/([0-9]{2})?:?([0-9]{2}):([0-9]{2}).([0-9]{2,3})( ?--> ?)([0-9]{2})?:?([0-9]{2}):([0-9]{2}).([0-9]{2,3})/);
              t3 && (i2.startTime = 60 * Number(t3[1] || 0) * 60 + 60 * Number(t3[2]) + Number(t3[3]) + Number(`0.${t3[4]}`), i2.endTime = 60 * Number(t3[6] || 0) * 60 + 60 * Number(t3[7]) + Number(t3[8]) + Number(`0.${t3[9]}`));
            }
          }), i2.text && t2.push(i2);
        }), t2;
      }, et = (e2, t2) => {
        const i2 = {};
        return e2 > t2.width / t2.height ? (i2.width = t2.width, i2.height = 1 / e2 * t2.width) : (i2.height = t2.height, i2.width = e2 * t2.height), i2;
      };
      class tt {
        constructor(t2) {
          e(this, "load", () => {
            this.player.elements.display.seekTooltip && (this.player.elements.display.seekTooltip.hidden = this.enabled), this.enabled && this.getThumbnails().then(() => {
              this.enabled && (this.render(), this.determineContainerAutoSizing(), this.listeners(), this.loaded = true);
            });
          }), e(this, "getThumbnails", () => new Promise((e2) => {
            const {
              src: t3
            } = this.player.config.previewThumbnails;
            if (S.empty(t3)) throw new Error("Missing previewThumbnails.src config attribute");
            const i2 = () => {
              this.thumbnails.sort((e3, t4) => e3.height - t4.height), this.player.debug.log("Preview thumbnails", this.thumbnails), e2();
            };
            if (S.function(t3)) t3((e3) => {
              this.thumbnails = e3, i2();
            });
            else {
              const e3 = (S.string(t3) ? [t3] : t3).map((e4) => this.getThumbnail(e4));
              Promise.all(e3).then(i2);
            }
          })), e(this, "getThumbnail", (e2) => new Promise((t3) => {
            Te(e2).then((i2) => {
              const s2 = {
                frames: Ze(i2),
                height: null,
                urlPrefix: ""
              };
              s2.frames[0].text.startsWith("/") || s2.frames[0].text.startsWith("http://") || s2.frames[0].text.startsWith("https://") || (s2.urlPrefix = e2.substring(0, e2.lastIndexOf("/") + 1));
              const n2 = new Image();
              n2.onload = () => {
                s2.height = n2.naturalHeight, s2.width = n2.naturalWidth, this.thumbnails.push(s2), t3();
              }, n2.src = s2.urlPrefix + s2.frames[0].text;
            });
          })), e(this, "startMove", (e2) => {
            if (this.loaded && S.event(e2) && ["touchmove", "mousemove"].includes(e2.type) && this.player.media.duration) {
              if ("touchmove" === e2.type) this.seekTime = this.player.media.duration * (this.player.elements.inputs.seek.value / 100);
              else {
                var t3, i2;
                const s2 = this.player.elements.progress.getBoundingClientRect(), n2 = 100 / s2.width * (e2.pageX - s2.left);
                this.seekTime = this.player.media.duration * (n2 / 100), this.seekTime < 0 && (this.seekTime = 0), this.seekTime > this.player.media.duration - 1 && (this.seekTime = this.player.media.duration - 1), this.mousePosX = e2.pageX, this.elements.thumb.time.innerText = Ee(this.seekTime);
                const a2 = null === (t3 = this.player.config.markers) || void 0 === t3 || null === (i2 = t3.points) || void 0 === i2 ? void 0 : i2.find(({
                  time: e3
                }) => e3 === Math.round(this.seekTime));
                a2 && this.elements.thumb.time.insertAdjacentHTML("afterbegin", `${a2.label}<br>`);
              }
              this.showImageAtCurrentTime();
            }
          }), e(this, "endMove", () => {
            this.toggleThumbContainer(false, true);
          }), e(this, "startScrubbing", (e2) => {
            (S.nullOrUndefined(e2.button) || false === e2.button || 0 === e2.button) && (this.mouseDown = true, this.player.media.duration && (this.toggleScrubbingContainer(true), this.toggleThumbContainer(false, true), this.showImageAtCurrentTime()));
          }), e(this, "endScrubbing", () => {
            this.mouseDown = false, Math.ceil(this.lastTime) === Math.ceil(this.player.media.currentTime) ? this.toggleScrubbingContainer(false) : G.call(this.player, this.player.media, "timeupdate", () => {
              this.mouseDown || this.toggleScrubbingContainer(false);
            });
          }), e(this, "listeners", () => {
            this.player.on("play", () => {
              this.toggleThumbContainer(false, true);
            }), this.player.on("seeked", () => {
              this.toggleThumbContainer(false);
            }), this.player.on("timeupdate", () => {
              this.lastTime = this.player.media.currentTime;
            });
          }), e(this, "render", () => {
            this.elements.thumb.container = $("div", {
              class: this.player.config.classNames.previewThumbnails.thumbContainer
            }), this.elements.thumb.imageContainer = $("div", {
              class: this.player.config.classNames.previewThumbnails.imageContainer
            }), this.elements.thumb.container.appendChild(this.elements.thumb.imageContainer);
            const e2 = $("div", {
              class: this.player.config.classNames.previewThumbnails.timeContainer
            });
            this.elements.thumb.time = $("span", {}, "00:00"), e2.appendChild(this.elements.thumb.time), this.elements.thumb.imageContainer.appendChild(e2), S.element(this.player.elements.progress) && this.player.elements.progress.appendChild(this.elements.thumb.container), this.elements.scrubbing.container = $("div", {
              class: this.player.config.classNames.previewThumbnails.scrubbingContainer
            }), this.player.elements.wrapper.appendChild(this.elements.scrubbing.container);
          }), e(this, "destroy", () => {
            this.elements.thumb.container && this.elements.thumb.container.remove(), this.elements.scrubbing.container && this.elements.scrubbing.container.remove();
          }), e(this, "showImageAtCurrentTime", () => {
            this.mouseDown ? this.setScrubbingContainerSize() : this.setThumbContainerSizeAndPos();
            const e2 = this.thumbnails[0].frames.findIndex((e3) => this.seekTime >= e3.startTime && this.seekTime <= e3.endTime), t3 = e2 >= 0;
            let i2 = 0;
            this.mouseDown || this.toggleThumbContainer(t3), t3 && (this.thumbnails.forEach((t4, s2) => {
              this.loadedImages.includes(t4.frames[e2].text) && (i2 = s2);
            }), e2 !== this.showingThumb && (this.showingThumb = e2, this.loadImage(i2)));
          }), e(this, "loadImage", (e2 = 0) => {
            const t3 = this.showingThumb, i2 = this.thumbnails[e2], {
              urlPrefix: s2
            } = i2, n2 = i2.frames[t3], a2 = i2.frames[t3].text, l2 = s2 + a2;
            if (this.currentImageElement && this.currentImageElement.dataset.filename === a2) this.showImage(this.currentImageElement, n2, e2, t3, a2, false), this.currentImageElement.dataset.index = t3, this.removeOldImages(this.currentImageElement);
            else {
              this.loadingImage && this.usingSprites && (this.loadingImage.onload = null);
              const i3 = new Image();
              i3.src = l2, i3.dataset.index = t3, i3.dataset.filename = a2, this.showingThumbFilename = a2, this.player.debug.log(`Loading image: ${l2}`), i3.onload = () => this.showImage(i3, n2, e2, t3, a2, true), this.loadingImage = i3, this.removeOldImages(i3);
            }
          }), e(this, "showImage", (e2, t3, i2, s2, n2, a2 = true) => {
            this.player.debug.log(`Showing thumb: ${n2}. num: ${s2}. qual: ${i2}. newimg: ${a2}`), this.setImageSizeAndOffset(e2, t3), a2 && (this.currentImageContainer.appendChild(e2), this.currentImageElement = e2, this.loadedImages.includes(n2) || this.loadedImages.push(n2)), this.preloadNearby(s2, true).then(this.preloadNearby(s2, false)).then(this.getHigherQuality(i2, e2, t3, n2));
          }), e(this, "removeOldImages", (e2) => {
            Array.from(this.currentImageContainer.children).forEach((t3) => {
              if ("img" !== t3.tagName.toLowerCase()) return;
              const i2 = this.usingSprites ? 500 : 1e3;
              if (t3.dataset.index !== e2.dataset.index && !t3.dataset.deleting) {
                t3.dataset.deleting = true;
                const {
                  currentImageContainer: e3
                } = this;
                setTimeout(() => {
                  e3.removeChild(t3), this.player.debug.log(`Removing thumb: ${t3.dataset.filename}`);
                }, i2);
              }
            });
          }), e(this, "preloadNearby", (e2, t3 = true) => new Promise((i2) => {
            setTimeout(() => {
              const s2 = this.thumbnails[0].frames[e2].text;
              if (this.showingThumbFilename === s2) {
                let n2;
                n2 = t3 ? this.thumbnails[0].frames.slice(e2) : this.thumbnails[0].frames.slice(0, e2).reverse();
                let a2 = false;
                n2.forEach((e3) => {
                  const t4 = e3.text;
                  if (t4 !== s2 && !this.loadedImages.includes(t4)) {
                    a2 = true, this.player.debug.log(`Preloading thumb filename: ${t4}`);
                    const {
                      urlPrefix: e4
                    } = this.thumbnails[0], s3 = e4 + t4, n3 = new Image();
                    n3.src = s3, n3.onload = () => {
                      this.player.debug.log(`Preloaded thumb filename: ${t4}`), this.loadedImages.includes(t4) || this.loadedImages.push(t4), i2();
                    };
                  }
                }), a2 || i2();
              }
            }, 300);
          })), e(this, "getHigherQuality", (e2, t3, i2, s2) => {
            if (e2 < this.thumbnails.length - 1) {
              let n2 = t3.naturalHeight;
              this.usingSprites && (n2 = i2.h), n2 < this.thumbContainerHeight && setTimeout(() => {
                this.showingThumbFilename === s2 && (this.player.debug.log(`Showing higher quality thumb for: ${s2}`), this.loadImage(e2 + 1));
              }, 300);
            }
          }), e(this, "toggleThumbContainer", (e2 = false, t3 = false) => {
            const i2 = this.player.config.classNames.previewThumbnails.thumbContainerShown;
            this.elements.thumb.container.classList.toggle(i2, e2), !e2 && t3 && (this.showingThumb = null, this.showingThumbFilename = null);
          }), e(this, "toggleScrubbingContainer", (e2 = false) => {
            const t3 = this.player.config.classNames.previewThumbnails.scrubbingContainerShown;
            this.elements.scrubbing.container.classList.toggle(t3, e2), e2 || (this.showingThumb = null, this.showingThumbFilename = null);
          }), e(this, "determineContainerAutoSizing", () => {
            (this.elements.thumb.imageContainer.clientHeight > 20 || this.elements.thumb.imageContainer.clientWidth > 20) && (this.sizeSpecifiedInCSS = true);
          }), e(this, "setThumbContainerSizeAndPos", () => {
            const {
              imageContainer: e2
            } = this.elements.thumb;
            if (this.sizeSpecifiedInCSS) {
              if (e2.clientHeight > 20 && e2.clientWidth < 20) {
                const t3 = Math.floor(e2.clientHeight * this.thumbAspectRatio);
                e2.style.width = `${t3}px`;
              } else if (e2.clientHeight < 20 && e2.clientWidth > 20) {
                const t3 = Math.floor(e2.clientWidth / this.thumbAspectRatio);
                e2.style.height = `${t3}px`;
              }
            } else {
              const t3 = Math.floor(this.thumbContainerHeight * this.thumbAspectRatio);
              e2.style.height = `${this.thumbContainerHeight}px`, e2.style.width = `${t3}px`;
            }
            this.setThumbContainerPos();
          }), e(this, "setThumbContainerPos", () => {
            const e2 = this.player.elements.progress.getBoundingClientRect(), t3 = this.player.elements.container.getBoundingClientRect(), {
              container: i2
            } = this.elements.thumb, s2 = t3.left - e2.left + 10, n2 = t3.right - e2.left - i2.clientWidth - 10, a2 = this.mousePosX - e2.left - i2.clientWidth / 2, l2 = Ge(a2, s2, n2);
            i2.style.left = `${l2}px`, i2.style.setProperty("--preview-arrow-offset", a2 - l2 + "px");
          }), e(this, "setScrubbingContainerSize", () => {
            const {
              width: e2,
              height: t3
            } = et(this.thumbAspectRatio, {
              width: this.player.media.clientWidth,
              height: this.player.media.clientHeight
            });
            this.elements.scrubbing.container.style.width = `${e2}px`, this.elements.scrubbing.container.style.height = `${t3}px`;
          }), e(this, "setImageSizeAndOffset", (e2, t3) => {
            if (!this.usingSprites) return;
            const i2 = this.thumbContainerHeight / t3.h;
            e2.style.height = e2.naturalHeight * i2 + "px", e2.style.width = e2.naturalWidth * i2 + "px", e2.style.left = `-${t3.x * i2}px`, e2.style.top = `-${t3.y * i2}px`;
          }), this.player = t2, this.thumbnails = [], this.loaded = false, this.lastMouseMoveTime = Date.now(), this.mouseDown = false, this.loadedImages = [], this.elements = {
            thumb: {},
            scrubbing: {}
          }, this.load();
        }
        get enabled() {
          return this.player.isHTML5 && this.player.isVideo && this.player.config.previewThumbnails.enabled;
        }
        get currentImageContainer() {
          return this.mouseDown ? this.elements.scrubbing.container : this.elements.thumb.imageContainer;
        }
        get usingSprites() {
          return Object.keys(this.thumbnails[0].frames[0]).includes("w");
        }
        get thumbAspectRatio() {
          return this.usingSprites ? this.thumbnails[0].frames[0].w / this.thumbnails[0].frames[0].h : this.thumbnails[0].width / this.thumbnails[0].height;
        }
        get thumbContainerHeight() {
          if (this.mouseDown) {
            const {
              height: e2
            } = et(this.thumbAspectRatio, {
              width: this.player.media.clientWidth,
              height: this.player.media.clientHeight
            });
            return e2;
          }
          return this.sizeSpecifiedInCSS ? this.elements.thumb.imageContainer.clientHeight : Math.floor(this.player.media.clientWidth / this.thumbAspectRatio / 4);
        }
        get currentImageElement() {
          return this.mouseDown ? this.currentScrubbingImageElement : this.currentThumbnailImageElement;
        }
        set currentImageElement(e2) {
          this.mouseDown ? this.currentScrubbingImageElement = e2 : this.currentThumbnailImageElement = e2;
        }
      }
      const it = {
        insertElements(e2, t2) {
          S.string(t2) ? _(e2, this.media, {
            src: t2
          }) : S.array(t2) && t2.forEach((t3) => {
            _(e2, this.media, t3);
          });
        },
        change(e2) {
          N(e2, "sources.length") ? (de.cancelRequests.call(this), this.destroy.call(this, () => {
            this.options.quality = [], O(this.media), this.media = null, S.element(this.elements.container) && this.elements.container.removeAttribute("class");
            const {
              sources: t2,
              type: i2
            } = e2, [{
              provider: s2 = _e.html5,
              src: n2
            }] = t2, a2 = "html5" === s2 ? i2 : "div", l2 = "html5" === s2 ? {} : {
              src: n2
            };
            Object.assign(this, {
              provider: s2,
              type: i2,
              supported: K.check(i2, s2, this.config.playsinline),
              media: $(a2, l2)
            }), this.elements.container.appendChild(this.media), S.boolean(e2.autoplay) && (this.config.autoplay = e2.autoplay), this.isHTML5 && (this.config.crossorigin && this.media.setAttribute("crossorigin", ""), this.config.autoplay && this.media.setAttribute("autoplay", ""), S.empty(e2.poster) || (this.poster = e2.poster), this.config.loop.active && this.media.setAttribute("loop", ""), this.config.muted && this.media.setAttribute("muted", ""), this.config.playsinline && this.media.setAttribute("playsinline", "")), Fe.addStyleHook.call(this), this.isHTML5 && it.insertElements.call(this, "source", t2), this.config.title = e2.title, Xe.setup.call(this), this.isHTML5 && Object.keys(e2).includes("tracks") && it.insertElements.call(this, "track", e2.tracks), (this.isHTML5 || this.isEmbed && !this.supported.ui) && Fe.build.call(this), this.isHTML5 && this.media.load(), S.empty(e2.previewThumbnails) || (Object.assign(this.config.previewThumbnails, e2.previewThumbnails), this.previewThumbnails && this.previewThumbnails.loaded && (this.previewThumbnails.destroy(), this.previewThumbnails = null), this.config.previewThumbnails.enabled && (this.previewThumbnails = new tt(this))), this.fullscreen.update();
          }, true)) : this.debug.warn("Invalid source format");
        }
      };
      class st {
        constructor(t2, i2) {
          if (e(this, "play", () => S.function(this.media.play) ? (this.ads && this.ads.enabled && this.ads.managerPromise.then(() => this.ads.play()).catch(() => ie(this.media.play())), this.media.play()) : null), e(this, "pause", () => this.playing && S.function(this.media.pause) ? this.media.pause() : null), e(this, "togglePlay", (e2) => (S.boolean(e2) ? e2 : !this.playing) ? this.play() : this.pause()), e(this, "stop", () => {
            this.isHTML5 ? (this.pause(), this.restart()) : S.function(this.media.stop) && this.media.stop();
          }), e(this, "restart", () => {
            this.currentTime = 0;
          }), e(this, "rewind", (e2) => {
            this.currentTime -= S.number(e2) ? e2 : this.config.seekTime;
          }), e(this, "forward", (e2) => {
            this.currentTime += S.number(e2) ? e2 : this.config.seekTime;
          }), e(this, "increaseVolume", (e2) => {
            const t3 = this.media.muted ? 0 : this.volume;
            this.volume = t3 + (S.number(e2) ? e2 : 0);
          }), e(this, "decreaseVolume", (e2) => {
            this.increaseVolume(-e2);
          }), e(this, "airplay", () => {
            K.airplay && this.media.webkitShowPlaybackTargetPicker();
          }), e(this, "toggleControls", (e2) => {
            if (this.supported.ui && !this.isAudio) {
              const t3 = F(this.elements.container, this.config.classNames.hideControls), i3 = void 0 === e2 ? void 0 : !e2, s3 = R(this.elements.container, this.config.classNames.hideControls, i3);
              if (s3 && S.array(this.config.controls) && this.config.controls.includes("settings") && !S.empty(this.config.settings) && Pe.toggleMenu.call(this, false), s3 !== t3) {
                const e3 = s3 ? "controlshidden" : "controlsshown";
                Z.call(this, this.media, e3);
              }
              return !s3;
            }
            return false;
          }), e(this, "on", (e2, t3) => {
            X.call(this, this.elements.container, e2, t3);
          }), e(this, "once", (e2, t3) => {
            G.call(this, this.elements.container, e2, t3);
          }), e(this, "off", (e2, t3) => {
            J(this.elements.container, e2, t3);
          }), e(this, "destroy", (e2, t3 = false) => {
            if (!this.ready) return;
            const i3 = () => {
              document.body.style.overflow = "", this.embed = null, t3 ? (Object.keys(this.elements).length && (O(this.elements.buttons.play), O(this.elements.captions), O(this.elements.controls), O(this.elements.wrapper), this.elements.buttons.play = null, this.elements.captions = null, this.elements.controls = null, this.elements.wrapper = null), S.function(e2) && e2()) : (ee.call(this), de.cancelRequests.call(this), q(this.elements.original, this.elements.container), Z.call(this, this.elements.original, "destroyed", true), S.function(e2) && e2.call(this.elements.original), this.ready = false, setTimeout(() => {
                this.elements = null, this.media = null;
              }, 200));
            };
            this.stop(), clearTimeout(this.timers.loading), clearTimeout(this.timers.controls), clearTimeout(this.timers.resized), this.isHTML5 ? (Fe.toggleNativeControls.call(this, true), i3()) : this.isYouTube ? (clearInterval(this.timers.buffering), clearInterval(this.timers.playing), null !== this.embed && S.function(this.embed.destroy) && this.embed.destroy(), i3()) : this.isVimeo && (null !== this.embed && this.embed.unload().then(i3), setTimeout(i3, 200));
          }), e(this, "supports", (e2) => K.mime.call(this, e2)), this.timers = {}, this.ready = false, this.loading = false, this.failed = false, this.touch = K.touch, this.media = t2, S.string(this.media) && (this.media = document.querySelectorAll(this.media)), (window.jQuery && this.media instanceof jQuery || S.nodeList(this.media) || S.array(this.media)) && (this.media = this.media[0]), this.config = x({}, Le, st.defaults, i2 || {}, (() => {
            try {
              return JSON.parse(this.media.getAttribute("data-plyr-config"));
            } catch (e2) {
              return {};
            }
          })()), this.elements = {
            container: null,
            fullscreen: null,
            captions: null,
            buttons: {},
            display: {},
            progress: {},
            inputs: {},
            settings: {
              popup: null,
              menu: null,
              panels: {},
              buttons: {}
            }
          }, this.captions = {
            active: null,
            currentTrack: -1,
            meta: /* @__PURE__ */ new WeakMap()
          }, this.fullscreen = {
            active: false
          }, this.options = {
            speed: [],
            quality: []
          }, this.debug = new De(this.config.debug), this.debug.log("Config", this.config), this.debug.log("Support", K), S.nullOrUndefined(this.media) || !S.element(this.media)) return void this.debug.error("Setup failed: no suitable element passed");
          if (this.media.plyr) return void this.debug.warn("Target already setup");
          if (!this.config.enabled) return void this.debug.error("Setup failed: disabled by config");
          if (!K.check().api) return void this.debug.error("Setup failed: no support");
          const s2 = this.media.cloneNode(true);
          s2.autoplay = false, this.elements.original = s2;
          const n2 = this.media.tagName.toLowerCase();
          let a2 = null, l2 = null;
          switch (n2) {
            case "div":
              if (a2 = this.media.querySelector("iframe"), S.element(a2)) {
                if (l2 = Me(a2.getAttribute("src")), this.provider = function(e2) {
                  return /^(https?:\/\/)?(www\.)?(youtube\.com|youtube-nocookie\.com|youtu\.?be)\/.+$/.test(e2) ? _e.youtube : /^https?:\/\/player.vimeo.com\/video\/\d{0,9}(?=\b|\/)/.test(e2) ? _e.vimeo : null;
                }(l2.toString()), this.elements.container = this.media, this.media = a2, this.elements.container.className = "", l2.search.length) {
                  const e2 = ["1", "true"];
                  e2.includes(l2.searchParams.get("autoplay")) && (this.config.autoplay = true), e2.includes(l2.searchParams.get("loop")) && (this.config.loop.active = true), this.isYouTube ? (this.config.playsinline = e2.includes(l2.searchParams.get("playsinline")), this.config.youtube.hl = l2.searchParams.get("hl")) : this.config.playsinline = true;
                }
              } else this.provider = this.media.getAttribute(this.config.attributes.embed.provider), this.media.removeAttribute(this.config.attributes.embed.provider);
              if (S.empty(this.provider) || !Object.values(_e).includes(this.provider)) return void this.debug.error("Setup failed: Invalid provider");
              this.type = je;
              break;
            case "video":
            case "audio":
              this.type = n2, this.provider = _e.html5, this.media.hasAttribute("crossorigin") && (this.config.crossorigin = true), this.media.hasAttribute("autoplay") && (this.config.autoplay = true), (this.media.hasAttribute("playsinline") || this.media.hasAttribute("webkit-playsinline")) && (this.config.playsinline = true), this.media.hasAttribute("muted") && (this.config.muted = true), this.media.hasAttribute("loop") && (this.config.loop.active = true);
              break;
            default:
              return void this.debug.error("Setup failed: unsupported type");
          }
          this.supported = K.check(this.type, this.provider), this.supported.api ? (this.eventListeners = [], this.listeners = new Ve(this), this.storage = new we(this), this.media.plyr = this, S.element(this.elements.container) || (this.elements.container = $("div"), L(this.media, this.elements.container)), Fe.migrateStyles.call(this), Fe.addStyleHook.call(this), Xe.setup.call(this), this.config.debug && X.call(this, this.elements.container, this.config.events.join(" "), (e2) => {
            this.debug.log(`event: ${e2.type}`);
          }), this.fullscreen = new He(this), (this.isHTML5 || this.isEmbed && !this.supported.ui) && Fe.build.call(this), this.listeners.container(), this.listeners.global(), this.config.ads.enabled && (this.ads = new Je(this)), this.isHTML5 && this.config.autoplay && this.once("canplay", () => ie(this.play())), this.lastSeekTime = 0, this.config.previewThumbnails.enabled && (this.previewThumbnails = new tt(this))) : this.debug.error("Setup failed: no support");
        }
        get isHTML5() {
          return this.provider === _e.html5;
        }
        get isEmbed() {
          return this.isYouTube || this.isVimeo;
        }
        get isYouTube() {
          return this.provider === _e.youtube;
        }
        get isVimeo() {
          return this.provider === _e.vimeo;
        }
        get isVideo() {
          return this.type === je;
        }
        get isAudio() {
          return this.type === Oe;
        }
        get playing() {
          return Boolean(this.ready && !this.paused && !this.ended);
        }
        get paused() {
          return Boolean(this.media.paused);
        }
        get stopped() {
          return Boolean(this.paused && 0 === this.currentTime);
        }
        get ended() {
          return Boolean(this.media.ended);
        }
        set currentTime(e2) {
          if (!this.duration) return;
          const t2 = S.number(e2) && e2 > 0;
          this.media.currentTime = t2 ? Math.min(e2, this.duration) : 0, this.debug.log(`Seeking to ${this.currentTime} seconds`);
        }
        get currentTime() {
          return Number(this.media.currentTime);
        }
        get buffered() {
          const {
            buffered: e2
          } = this.media;
          return S.number(e2) ? e2 : e2 && e2.length && this.duration > 0 ? e2.end(0) / this.duration : 0;
        }
        get seeking() {
          return Boolean(this.media.seeking);
        }
        get duration() {
          const e2 = parseFloat(this.config.duration), t2 = (this.media || {}).duration, i2 = S.number(t2) && t2 !== 1 / 0 ? t2 : 0;
          return e2 || i2;
        }
        set volume(e2) {
          let t2 = e2;
          S.string(t2) && (t2 = Number(t2)), S.number(t2) || (t2 = this.storage.get("volume")), S.number(t2) || ({
            volume: t2
          } = this.config), t2 > 1 && (t2 = 1), t2 < 0 && (t2 = 0), this.config.volume = t2, this.media.volume = t2, !S.empty(e2) && this.muted && t2 > 0 && (this.muted = false);
        }
        get volume() {
          return Number(this.media.volume);
        }
        set muted(e2) {
          let t2 = e2;
          S.boolean(t2) || (t2 = this.storage.get("muted")), S.boolean(t2) || (t2 = this.config.muted), this.config.muted = t2, this.media.muted = t2;
        }
        get muted() {
          return Boolean(this.media.muted);
        }
        get hasAudio() {
          return !this.isHTML5 || !!this.isAudio || Boolean(this.media.mozHasAudio) || Boolean(this.media.webkitAudioDecodedByteCount) || Boolean(this.media.audioTracks && this.media.audioTracks.length);
        }
        set speed(e2) {
          let t2 = null;
          S.number(e2) && (t2 = e2), S.number(t2) || (t2 = this.storage.get("speed")), S.number(t2) || (t2 = this.config.speed.selected);
          const {
            minimumSpeed: i2,
            maximumSpeed: s2
          } = this;
          t2 = Ge(t2, i2, s2), this.config.speed.selected = t2, setTimeout(() => {
            this.media && (this.media.playbackRate = t2);
          }, 0);
        }
        get speed() {
          return Number(this.media.playbackRate);
        }
        get minimumSpeed() {
          return this.isYouTube ? Math.min(...this.options.speed) : this.isVimeo ? 0.5 : 0.0625;
        }
        get maximumSpeed() {
          return this.isYouTube ? Math.max(...this.options.speed) : this.isVimeo ? 2 : 16;
        }
        set quality(e2) {
          const t2 = this.config.quality, i2 = this.options.quality;
          if (!i2.length) return;
          let s2 = [!S.empty(e2) && Number(e2), this.storage.get("quality"), t2.selected, t2.default].find(S.number), n2 = true;
          if (!i2.includes(s2)) {
            const e3 = ne(i2, s2);
            this.debug.warn(`Unsupported quality option: ${s2}, using ${e3} instead`), s2 = e3, n2 = false;
          }
          t2.selected = s2, this.media.quality = s2, n2 && this.storage.set({
            quality: s2
          });
        }
        get quality() {
          return this.media.quality;
        }
        set loop(e2) {
          const t2 = S.boolean(e2) ? e2 : this.config.loop.active;
          this.config.loop.active = t2, this.media.loop = t2;
        }
        get loop() {
          return Boolean(this.media.loop);
        }
        set source(e2) {
          it.change.call(this, e2);
        }
        get source() {
          return this.media.currentSrc;
        }
        get download() {
          const {
            download: e2
          } = this.config.urls;
          return S.url(e2) ? e2 : this.source;
        }
        set download(e2) {
          S.url(e2) && (this.config.urls.download = e2, Pe.setDownloadUrl.call(this));
        }
        set poster(e2) {
          this.isVideo ? Fe.setPoster.call(this, e2, false).catch(() => {
          }) : this.debug.warn("Poster can only be set for video");
        }
        get poster() {
          return this.isVideo ? this.media.getAttribute("poster") || this.media.getAttribute("data-poster") : null;
        }
        get ratio() {
          if (!this.isVideo) return null;
          const e2 = oe(ce.call(this));
          return S.array(e2) ? e2.join(":") : e2;
        }
        set ratio(e2) {
          this.isVideo ? S.string(e2) && re(e2) ? (this.config.ratio = oe(e2), ue.call(this)) : this.debug.error(`Invalid aspect ratio specified (${e2})`) : this.debug.warn("Aspect ratio can only be set for video");
        }
        set autoplay(e2) {
          this.config.autoplay = S.boolean(e2) ? e2 : this.config.autoplay;
        }
        get autoplay() {
          return Boolean(this.config.autoplay);
        }
        toggleCaptions(e2) {
          xe.toggle.call(this, e2, false);
        }
        set currentTrack(e2) {
          xe.set.call(this, e2, false), xe.setup.call(this);
        }
        get currentTrack() {
          const {
            toggled: e2,
            currentTrack: t2
          } = this.captions;
          return e2 ? t2 : -1;
        }
        set language(e2) {
          xe.setLanguage.call(this, e2, false);
        }
        get language() {
          return (xe.getCurrentTrack.call(this) || {}).language;
        }
        set pip(e2) {
          if (!K.pip) return;
          const t2 = S.boolean(e2) ? e2 : !this.pip;
          S.function(this.media.webkitSetPresentationMode) && this.media.webkitSetPresentationMode(t2 ? Ie : $e), S.function(this.media.requestPictureInPicture) && (!this.pip && t2 ? this.media.requestPictureInPicture() : this.pip && !t2 && document.exitPictureInPicture());
        }
        get pip() {
          return K.pip ? S.empty(this.media.webkitPresentationMode) ? this.media === document.pictureInPictureElement : this.media.webkitPresentationMode === Ie : null;
        }
        setPreviewThumbnails(e2) {
          this.previewThumbnails && this.previewThumbnails.loaded && (this.previewThumbnails.destroy(), this.previewThumbnails = null), Object.assign(this.config.previewThumbnails, e2), this.config.previewThumbnails.enabled && (this.previewThumbnails = new tt(this));
        }
        static supported(e2, t2) {
          return K.check(e2, t2);
        }
        static loadSprite(e2, t2) {
          return ke(e2, t2);
        }
        static setup(e2, t2 = {}) {
          let i2 = null;
          return S.string(e2) ? i2 = Array.from(document.querySelectorAll(e2)) : S.nodeList(e2) ? i2 = Array.from(e2) : S.array(e2) && (i2 = e2.filter(S.element)), S.empty(i2) ? null : i2.map((e3) => new st(e3, t2));
        }
      }
      var nt;
      return st.defaults = (nt = Le, JSON.parse(JSON.stringify(nt))), st;
    });
  }
});

// src/app/components/plyr-player/plyr-player.component.ts
var import_plyr = __toESM(require_plyr_min());
var _c0 = ["player"];
var _PlyrPlayerComponent = class _PlyrPlayerComponent {
  ngOnInit() {
  }
  ionViewDidEnter() {
    var _a;
    if ((_a = this.playerRef) == null ? void 0 : _a.nativeElement) {
      this.initializePlayer();
    }
  }
  ngOnChanges() {
    if (this.player && this.videoSrc) {
      this.updateVideoSource();
    }
  }
  initializePlayer() {
    this.player = new import_plyr.default(this.playerRef.nativeElement, {
      controls: ["play", "progress", "volume", "fullscreen"]
    });
    if (this.videoSrc) {
      this.updateVideoSource();
    }
  }
  updateVideoSource() {
    this.player.source = {
      type: "video",
      sources: [
        {
          src: this.videoSrc,
          type: "video/mp4"
        }
      ]
    };
  }
  ngOnDestroy() {
    if (this.player) {
      this.player.destroy();
    }
  }
};
_PlyrPlayerComponent.\u0275fac = function PlyrPlayerComponent_Factory(__ngFactoryType__) {
  return new (__ngFactoryType__ || _PlyrPlayerComponent)();
};
_PlyrPlayerComponent.\u0275cmp = /* @__PURE__ */ \u0275\u0275defineComponent({ type: _PlyrPlayerComponent, selectors: [["app-plyr-player"]], viewQuery: function PlyrPlayerComponent_Query(rf, ctx) {
  if (rf & 1) {
    \u0275\u0275viewQuery(_c0, 5);
  }
  if (rf & 2) {
    let _t;
    \u0275\u0275queryRefresh(_t = \u0275\u0275loadQuery()) && (ctx.playerRef = _t.first);
  }
}, inputs: { videoSrc: "videoSrc" }, standalone: true, features: [\u0275\u0275NgOnChangesFeature, \u0275\u0275StandaloneFeature], decls: 2, vars: 0, consts: [["player", ""], ["controls", ""]], template: function PlyrPlayerComponent_Template(rf, ctx) {
  if (rf & 1) {
    \u0275\u0275element(0, "video", 1, 0);
  }
} });
var PlyrPlayerComponent = _PlyrPlayerComponent;
(() => {
  (typeof ngDevMode === "undefined" || ngDevMode) && \u0275setClassDebugInfo(PlyrPlayerComponent, { className: "PlyrPlayerComponent" });
})();

export {
  PlyrPlayerComponent
};
//# sourceMappingURL=chunk-W6RQMKWS.js.map
