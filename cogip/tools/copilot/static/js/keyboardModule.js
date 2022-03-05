export const virtualKeyboard = {
  elements: {
    main: null,
    keysContainer: null,
    keys: [],
  },

  eventHandlers: {
    oninput: null,
    onclose: null,
  },

  properties: {
    value: "",
    capsLock: false,
  },

  init() {
    // Create main elements
    const parent = document.createElement("div");
    parent.classList.add("row");
    this.elements.main = document.createElement("div");
    this.elements.keysContainer = document.createElement("div");

    // Setup main elements
    this.elements.main.classList.add(
      "keyboard",
      "keyboard--hidden",
      "w-25",
      "offset-md-5"
    );
    this.elements.keysContainer.classList.add("keyboard__keys");
    this.elements.keysContainer.appendChild(this._createKeys());

    this.elements.keys =
      this.elements.keysContainer.querySelectorAll(".keyboard__key");

    // Add to DOM
    this.elements.main.appendChild(this.elements.keysContainer);
    parent.append(this.elements.main);
    document.body.appendChild(parent);
  },

  _createKeys() {
    const fragment = document.createDocumentFragment();
    const keyLayout = [
      "9",
      "8",
      "7",
      "6",
      "5",
      "4",
      "3",
      "2",
      "1",
      "0",
      ".",
      "backspace",
    ];

    keyLayout.forEach((key) => {
      const keyElement = document.createElement("button");
      const insertLineBreak = ["7", "4", "1"].indexOf(key) !== -1;

      // Add attributes/classes
      keyElement.setAttribute("type", "button");
      keyElement.classList.add("keyboard__key");

      if (key == "backspace") {
        keyElement.innerHTML = '<img src="static/img/backspace.svg"></img>';

        keyElement.addEventListener("click", () => {
          this.properties.value = this.properties.value.substring(
            0,
            this.properties.value.length - 1
          );
          this._triggerEvent("oninput");
        });
      } else {
        keyElement.textContent = key.toLowerCase();

        keyElement.addEventListener("focus", () => {
          this.properties.value += this.properties.capsLock
            ? key.toUpperCase()
            : key.toLowerCase();
          this._triggerEvent("oninput");
        });
      }

      fragment.appendChild(keyElement);

      if (insertLineBreak) {
        fragment.appendChild(document.createElement("br"));
      }
    });

    return fragment;
  },

  _triggerEvent(handlerName) {
    if (typeof this.eventHandlers[handlerName] == "function") {
      this.eventHandlers[handlerName](this.properties.value);
    }
  },

  open(initialValue, oninput, onclose) {
    this.properties.value = initialValue || "";
    this.eventHandlers.oninput = oninput;
    this.eventHandlers.onclose = onclose;
    this.elements.main.classList.remove("keyboard--hidden");
  },

  close() {
    this.properties.value = "";
    this.eventHandlers.oninput = oninput;
    this.eventHandlers.onclose = onclose;
    this.elements.main.classList.add("keyboard--hidden");
  },

  _actualize() {
    // Automatically use keyboard for elements with .use-keyboard-input
    document.querySelectorAll(".use-keyboard-input").forEach((element) => {
      element.addEventListener("click", () => {
        virtualKeyboard.open(element.value, (currentValue) => {
          element.value = currentValue;
        });
      });
    });

    let virtualKeyboard = this;
    $(document).on("click", function (event) {
      if (
        $(event.target).closest(".use-keyboard-input").length === 0 &&
        $(event.target).closest(".keyboard__key").length === 0
      ) {
        virtualKeyboard.close();
      }
    });
  },
};
