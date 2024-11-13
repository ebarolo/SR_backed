import {
  getElementRoot
} from "./chunk-X6PYF5VD.js";
import {
  Host,
  createEvent,
  getElement,
  h,
  registerInstance
} from "./chunk-D2XNQ3S7.js";
import {
  __async
} from "./chunk-FSIFXKME.js";

// node_modules/@ionic/core/dist/esm/ion-picker.entry.js
var pickerIosCss = ":host{display:-ms-flexbox;display:flex;position:relative;-ms-flex-align:center;align-items:center;-ms-flex-pack:center;justify-content:center;width:100%;height:200px;direction:ltr;z-index:0}:host .picker-before,:host .picker-after{position:absolute;width:100%;-webkit-transform:translateZ(0);transform:translateZ(0);z-index:1;pointer-events:none}:host .picker-before{top:0;height:83px}:host .picker-before{inset-inline-start:0}:host .picker-after{top:116px;height:84px}:host .picker-after{inset-inline-start:0}:host .picker-highlight{border-radius:var(--highlight-border-radius, 8px);left:0;right:0;top:50%;bottom:0;-webkit-margin-start:auto;margin-inline-start:auto;-webkit-margin-end:auto;margin-inline-end:auto;margin-top:0;margin-bottom:0;position:absolute;width:calc(100% - 16px);height:34px;-webkit-transform:translateY(-50%);transform:translateY(-50%);background:var(--highlight-background);z-index:-1}:host input{position:absolute;top:0;left:0;right:0;bottom:0;width:100%;height:100%;margin:0;padding:0;border:0;outline:0;clip:rect(0 0 0 0);opacity:0;overflow:hidden;-webkit-appearance:none;-moz-appearance:none}:host ::slotted(ion-picker-column:first-of-type){text-align:start}:host ::slotted(ion-picker-column:last-of-type){text-align:end}:host ::slotted(ion-picker-column:only-child){text-align:center}:host .picker-before{background:-webkit-gradient(linear, left top, left bottom, color-stop(20%, rgba(var(--fade-background-rgb, var(--background-rgb, var(--ion-background-color-rgb, 255, 255, 255))), 1)), to(rgba(var(--fade-background-rgb, var(--background-rgb, var(--ion-background-color-rgb, 255, 255, 255))), 0.8)));background:linear-gradient(to bottom, rgba(var(--fade-background-rgb, var(--background-rgb, var(--ion-background-color-rgb, 255, 255, 255))), 1) 20%, rgba(var(--fade-background-rgb, var(--background-rgb, var(--ion-background-color-rgb, 255, 255, 255))), 0.8) 100%)}:host .picker-after{background:-webkit-gradient(linear, left bottom, left top, color-stop(20%, rgba(var(--fade-background-rgb, var(--background-rgb, var(--ion-background-color-rgb, 255, 255, 255))), 1)), to(rgba(var(--fade-background-rgb, var(--background-rgb, var(--ion-background-color-rgb, 255, 255, 255))), 0.8)));background:linear-gradient(to top, rgba(var(--fade-background-rgb, var(--background-rgb, var(--ion-background-color-rgb, 255, 255, 255))), 1) 20%, rgba(var(--fade-background-rgb, var(--background-rgb, var(--ion-background-color-rgb, 255, 255, 255))), 0.8) 100%)}:host .picker-highlight{background:var(--highlight-background, var(--ion-color-step-150, var(--ion-background-color-step-150, #eeeeef)))}";
var IonPickerIosStyle0 = pickerIosCss;
var pickerMdCss = ":host{display:-ms-flexbox;display:flex;position:relative;-ms-flex-align:center;align-items:center;-ms-flex-pack:center;justify-content:center;width:100%;height:200px;direction:ltr;z-index:0}:host .picker-before,:host .picker-after{position:absolute;width:100%;-webkit-transform:translateZ(0);transform:translateZ(0);z-index:1;pointer-events:none}:host .picker-before{top:0;height:83px}:host .picker-before{inset-inline-start:0}:host .picker-after{top:116px;height:84px}:host .picker-after{inset-inline-start:0}:host .picker-highlight{border-radius:var(--highlight-border-radius, 8px);left:0;right:0;top:50%;bottom:0;-webkit-margin-start:auto;margin-inline-start:auto;-webkit-margin-end:auto;margin-inline-end:auto;margin-top:0;margin-bottom:0;position:absolute;width:calc(100% - 16px);height:34px;-webkit-transform:translateY(-50%);transform:translateY(-50%);background:var(--highlight-background);z-index:-1}:host input{position:absolute;top:0;left:0;right:0;bottom:0;width:100%;height:100%;margin:0;padding:0;border:0;outline:0;clip:rect(0 0 0 0);opacity:0;overflow:hidden;-webkit-appearance:none;-moz-appearance:none}:host ::slotted(ion-picker-column:first-of-type){text-align:start}:host ::slotted(ion-picker-column:last-of-type){text-align:end}:host ::slotted(ion-picker-column:only-child){text-align:center}:host .picker-before{background:-webkit-gradient(linear, left top, left bottom, color-stop(20%, rgba(var(--fade-background-rgb, var(--background-rgb, var(--ion-background-color-rgb, 255, 255, 255))), 1)), color-stop(90%, rgba(var(--fade-background-rgb, var(--background-rgb, var(--ion-background-color-rgb, 255, 255, 255))), 0)));background:linear-gradient(to bottom, rgba(var(--fade-background-rgb, var(--background-rgb, var(--ion-background-color-rgb, 255, 255, 255))), 1) 20%, rgba(var(--fade-background-rgb, var(--background-rgb, var(--ion-background-color-rgb, 255, 255, 255))), 0) 90%)}:host .picker-after{background:-webkit-gradient(linear, left bottom, left top, color-stop(30%, rgba(var(--fade-background-rgb, var(--background-rgb, var(--ion-background-color-rgb, 255, 255, 255))), 1)), color-stop(90%, rgba(var(--fade-background-rgb, var(--background-rgb, var(--ion-background-color-rgb, 255, 255, 255))), 0)));background:linear-gradient(to top, rgba(var(--fade-background-rgb, var(--background-rgb, var(--ion-background-color-rgb, 255, 255, 255))), 1) 30%, rgba(var(--fade-background-rgb, var(--background-rgb, var(--ion-background-color-rgb, 255, 255, 255))), 0) 90%)}";
var IonPickerMdStyle0 = pickerMdCss;
var Picker = class {
  constructor(hostRef) {
    registerInstance(this, hostRef);
    this.ionInputModeChange = createEvent(this, "ionInputModeChange", 7);
    this.useInputMode = false;
    this.isInHighlightBounds = (ev) => {
      const {
        highlightEl
      } = this;
      if (!highlightEl) {
        return false;
      }
      const bbox = highlightEl.getBoundingClientRect();
      const outsideX = ev.clientX < bbox.left || ev.clientX > bbox.right;
      const outsideY = ev.clientY < bbox.top || ev.clientY > bbox.bottom;
      if (outsideX || outsideY) {
        return false;
      }
      return true;
    };
    this.onFocusOut = (ev) => {
      const {
        relatedTarget
      } = ev;
      if (!relatedTarget || relatedTarget.tagName !== "ION-PICKER-COLUMN" && relatedTarget !== this.inputEl) {
        this.exitInputMode();
      }
    };
    this.onFocusIn = (ev) => {
      const {
        target
      } = ev;
      if (target.tagName !== "ION-PICKER-COLUMN") {
        return;
      }
      if (!this.actionOnClick) {
        const columnEl = target;
        const allowInput = columnEl.numericInput;
        if (allowInput) {
          this.enterInputMode(columnEl, false);
        } else {
          this.exitInputMode();
        }
      }
    };
    this.onClick = () => {
      const {
        actionOnClick
      } = this;
      if (actionOnClick) {
        actionOnClick();
        this.actionOnClick = void 0;
      }
    };
    this.onPointerDown = (ev) => {
      const {
        useInputMode,
        inputModeColumn,
        el
      } = this;
      if (this.isInHighlightBounds(ev)) {
        if (useInputMode) {
          if (ev.target.tagName === "ION-PICKER-COLUMN") {
            if (inputModeColumn && inputModeColumn === ev.target) {
              this.actionOnClick = () => {
                this.enterInputMode();
              };
            } else {
              this.actionOnClick = () => {
                this.enterInputMode(ev.target);
              };
            }
          } else {
            this.actionOnClick = () => {
              this.exitInputMode();
            };
          }
        } else {
          const columns = el.querySelectorAll("ion-picker-column.picker-column-numeric-input");
          const columnEl = columns.length === 1 ? ev.target : void 0;
          this.actionOnClick = () => {
            this.enterInputMode(columnEl);
          };
        }
        return;
      }
      this.actionOnClick = () => {
        this.exitInputMode();
      };
    };
    this.enterInputMode = (columnEl, focusInput = true) => {
      const {
        inputEl,
        el
      } = this;
      if (!inputEl) {
        return;
      }
      const hasInputColumn = el.querySelector("ion-picker-column.picker-column-numeric-input");
      if (!hasInputColumn) {
        return;
      }
      this.useInputMode = true;
      this.inputModeColumn = columnEl;
      if (focusInput) {
        if (this.destroyKeypressListener) {
          this.destroyKeypressListener();
          this.destroyKeypressListener = void 0;
        }
        inputEl.focus();
      } else {
        el.addEventListener("keypress", this.onKeyPress);
        this.destroyKeypressListener = () => {
          el.removeEventListener("keypress", this.onKeyPress);
        };
      }
      this.emitInputModeChange();
    };
    this.onKeyPress = (ev) => {
      const {
        inputEl
      } = this;
      if (!inputEl) {
        return;
      }
      const parsedValue = parseInt(ev.key, 10);
      if (!Number.isNaN(parsedValue)) {
        inputEl.value += ev.key;
        this.onInputChange();
      }
    };
    this.selectSingleColumn = () => {
      const {
        inputEl,
        inputModeColumn,
        singleColumnSearchTimeout
      } = this;
      if (!inputEl || !inputModeColumn) {
        return;
      }
      const options = Array.from(inputModeColumn.querySelectorAll("ion-picker-column-option")).filter((el) => el.disabled !== true);
      if (singleColumnSearchTimeout) {
        clearTimeout(singleColumnSearchTimeout);
      }
      this.singleColumnSearchTimeout = setTimeout(() => {
        inputEl.value = "";
        this.singleColumnSearchTimeout = void 0;
      }, 1e3);
      if (inputEl.value.length >= 3) {
        const startIndex = inputEl.value.length - 2;
        const newString = inputEl.value.substring(startIndex);
        inputEl.value = newString;
        this.selectSingleColumn();
        return;
      }
      const findItemFromCompleteValue = options.find(({
        textContent
      }) => {
        const parsedText = textContent.replace(/^0+(?=[1-9])|0+(?=0$)/, "");
        return parsedText === inputEl.value;
      });
      if (findItemFromCompleteValue) {
        inputModeColumn.setValue(findItemFromCompleteValue.value);
        return;
      }
      if (inputEl.value.length === 2) {
        const changedCharacter = inputEl.value.substring(inputEl.value.length - 1);
        inputEl.value = changedCharacter;
        this.selectSingleColumn();
      }
    };
    this.searchColumn = (colEl, value, zeroBehavior = "start") => {
      const behavior = zeroBehavior === "start" ? /^0+/ : /0$/;
      const option = Array.from(colEl.querySelectorAll("ion-picker-column-option")).find((el) => {
        return el.disabled !== true && el.textContent.replace(behavior, "") === value;
      });
      if (option) {
        colEl.setValue(option.value);
      }
    };
    this.selectMultiColumn = () => {
      const {
        inputEl,
        el
      } = this;
      if (!inputEl) {
        return;
      }
      const numericPickers = Array.from(el.querySelectorAll("ion-picker-column")).filter((col) => col.numericInput);
      const firstColumn = numericPickers[0];
      const lastColumn = numericPickers[1];
      let value = inputEl.value;
      let minuteValue;
      switch (value.length) {
        case 1:
          this.searchColumn(firstColumn, value);
          break;
        case 2:
          const firstCharacter = inputEl.value.substring(0, 1);
          value = firstCharacter === "0" || firstCharacter === "1" ? inputEl.value : firstCharacter;
          this.searchColumn(firstColumn, value);
          if (value.length === 1) {
            minuteValue = inputEl.value.substring(inputEl.value.length - 1);
            this.searchColumn(lastColumn, minuteValue, "end");
          }
          break;
        case 3:
          const firstCharacterAgain = inputEl.value.substring(0, 1);
          value = firstCharacterAgain === "0" || firstCharacterAgain === "1" ? inputEl.value.substring(0, 2) : firstCharacterAgain;
          this.searchColumn(firstColumn, value);
          minuteValue = value.length === 1 ? inputEl.value.substring(1) : inputEl.value.substring(2);
          this.searchColumn(lastColumn, minuteValue, "end");
          break;
        case 4:
          const firstCharacterAgainAgain = inputEl.value.substring(0, 1);
          value = firstCharacterAgainAgain === "0" || firstCharacterAgainAgain === "1" ? inputEl.value.substring(0, 2) : firstCharacterAgainAgain;
          this.searchColumn(firstColumn, value);
          const minuteValueAgain = value.length === 1 ? inputEl.value.substring(1, inputEl.value.length) : inputEl.value.substring(2, inputEl.value.length);
          this.searchColumn(lastColumn, minuteValueAgain, "end");
          break;
        default:
          const startIndex = inputEl.value.length - 4;
          const newString = inputEl.value.substring(startIndex);
          inputEl.value = newString;
          this.selectMultiColumn();
          break;
      }
    };
    this.onInputChange = () => {
      const {
        useInputMode,
        inputEl,
        inputModeColumn
      } = this;
      if (!useInputMode || !inputEl) {
        return;
      }
      if (inputModeColumn) {
        this.selectSingleColumn();
      } else {
        this.selectMultiColumn();
      }
    };
    this.emitInputModeChange = () => {
      const {
        useInputMode,
        inputModeColumn
      } = this;
      this.ionInputModeChange.emit({
        useInputMode,
        inputModeColumn
      });
    };
  }
  /**
   * When the picker is interacted with
   * we need to prevent touchstart so other
   * gestures do not fire. For example,
   * scrolling on the wheel picker
   * in ion-datetime should not cause
   * a card modal to swipe to close.
   */
  preventTouchStartPropagation(ev) {
    ev.stopPropagation();
  }
  componentWillLoad() {
    getElementRoot(this.el).addEventListener("focusin", this.onFocusIn);
    getElementRoot(this.el).addEventListener("focusout", this.onFocusOut);
  }
  /**
   * @internal
   * Exits text entry mode for the picker
   * This method blurs the hidden input
   * and cause the keyboard to dismiss.
   */
  exitInputMode() {
    return __async(this, null, function* () {
      const {
        inputEl,
        useInputMode
      } = this;
      if (!useInputMode || !inputEl) {
        return;
      }
      this.useInputMode = false;
      this.inputModeColumn = void 0;
      inputEl.blur();
      inputEl.value = "";
      if (this.destroyKeypressListener) {
        this.destroyKeypressListener();
        this.destroyKeypressListener = void 0;
      }
      this.emitInputModeChange();
    });
  }
  render() {
    return h(Host, {
      key: "f92214a09dc85b65873676f40fde2b802960e704",
      onPointerDown: (ev) => this.onPointerDown(ev),
      onClick: () => this.onClick()
    }, h("input", {
      key: "6da37f75aca4ea1c9cb3bc733ebda2116279f313",
      "aria-hidden": "true",
      tabindex: -1,
      inputmode: "numeric",
      type: "number",
      onKeyDown: (ev) => {
        var _a;
        if (ev.key === "Enter") {
          (_a = this.inputEl) === null || _a === void 0 ? void 0 : _a.blur();
        }
      },
      ref: (el) => this.inputEl = el,
      onInput: () => this.onInputChange(),
      onBlur: () => this.exitInputMode()
    }), h("div", {
      key: "298e99d83dd3f5bf2798150bab0bb4024af472fa",
      class: "picker-before"
    }), h("div", {
      key: "ea578f04eb562a4dc6d6cc92de133dcb9fb7f42a",
      class: "picker-after"
    }), h("div", {
      key: "84567824956dfe967992a629904836ba8b75b3ec",
      class: "picker-highlight",
      ref: (el) => this.highlightEl = el
    }), h("slot", {
      key: "df81f8fb90e1f649b608328034528f5c31c70c3b"
    }));
  }
  get el() {
    return getElement(this);
  }
};
Picker.style = {
  ios: IonPickerIosStyle0,
  md: IonPickerMdStyle0
};
export {
  Picker as ion_picker
};
/*! Bundled license information:

@ionic/core/dist/esm/ion-picker.entry.js:
  (*!
   * (C) Ionic http://ionicframework.com - MIT License
   *)
*/
//# sourceMappingURL=ion-picker.entry-DQ4RD56X.js.map
