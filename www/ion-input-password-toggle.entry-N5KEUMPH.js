import {
  createColorClasses
} from "./chunk-ZPVV3IUV.js";
import {
  eye,
  eyeOff
} from "./chunk-Y2OY2WAF.js";
import {
  printIonWarning
} from "./chunk-52T2EOVQ.js";
import {
  getIonMode
} from "./chunk-FE643L4S.js";
import {
  Host,
  getElement,
  h,
  registerInstance
} from "./chunk-D2XNQ3S7.js";
import "./chunk-FSIFXKME.js";

// node_modules/@ionic/core/dist/esm/ion-input-password-toggle.entry.js
var iosInputPasswordToggleCss = "";
var IonInputPasswordToggleIosStyle0 = iosInputPasswordToggleCss;
var mdInputPasswordToggleCss = "";
var IonInputPasswordToggleMdStyle0 = mdInputPasswordToggleCss;
var InputPasswordToggle = class {
  constructor(hostRef) {
    registerInstance(this, hostRef);
    this.togglePasswordVisibility = () => {
      const {
        inputElRef
      } = this;
      if (!inputElRef) {
        return;
      }
      inputElRef.type = inputElRef.type === "text" ? "password" : "text";
    };
    this.color = void 0;
    this.showIcon = void 0;
    this.hideIcon = void 0;
    this.type = "password";
  }
  /**
   * Whenever the input type changes we need to re-run validation to ensure the password
   * toggle is being used with the correct input type. If the application changes the type
   * outside of this component we also need to re-render so the correct icon is shown.
   */
  onTypeChange(newValue) {
    if (newValue !== "text" && newValue !== "password") {
      printIonWarning(`ion-input-password-toggle only supports inputs of type "text" or "password". Input of type "${newValue}" is not compatible.`, this.el);
      return;
    }
  }
  connectedCallback() {
    const {
      el
    } = this;
    const inputElRef = this.inputElRef = el.closest("ion-input");
    if (!inputElRef) {
      printIonWarning("No ancestor ion-input found for ion-input-password-toggle. This component must be slotted inside of an ion-input.", el);
      return;
    }
    this.type = inputElRef.type;
  }
  disconnectedCallback() {
    this.inputElRef = null;
  }
  render() {
    var _a, _b;
    const {
      color,
      type
    } = this;
    const mode = getIonMode(this);
    const showPasswordIcon = (_a = this.showIcon) !== null && _a !== void 0 ? _a : eye;
    const hidePasswordIcon = (_b = this.hideIcon) !== null && _b !== void 0 ? _b : eyeOff;
    const isPasswordVisible = type === "text";
    return h(Host, {
      key: "d9811e25bfeb2aa197352bb9be852e9e420739d5",
      class: createColorClasses(color, {
        [mode]: true
      })
    }, h("ion-button", {
      key: "1eaea1442b248fb2b8d61538b27274e647a07804",
      mode,
      color,
      fill: "clear",
      shape: "round",
      "aria-checked": isPasswordVisible ? "true" : "false",
      "aria-label": "show password",
      role: "switch",
      type: "button",
      onPointerDown: (ev) => {
        ev.preventDefault();
      },
      onClick: this.togglePasswordVisibility
    }, h("ion-icon", {
      key: "9c88de8f4631d9bde222ce2edf6950d639e04773",
      slot: "icon-only",
      "aria-hidden": "true",
      icon: isPasswordVisible ? hidePasswordIcon : showPasswordIcon
    })));
  }
  get el() {
    return getElement(this);
  }
  static get watchers() {
    return {
      "type": ["onTypeChange"]
    };
  }
};
InputPasswordToggle.style = {
  ios: IonInputPasswordToggleIosStyle0,
  md: IonInputPasswordToggleMdStyle0
};
export {
  InputPasswordToggle as ion_input_password_toggle
};
/*! Bundled license information:

@ionic/core/dist/esm/ion-input-password-toggle.entry.js:
  (*!
   * (C) Ionic http://ionicframework.com - MIT License
   *)
*/
//# sourceMappingURL=ion-input-password-toggle.entry-N5KEUMPH.js.map
