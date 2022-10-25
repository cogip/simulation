let socket = null;
let type = null;

export function openWizardModal(msg, send_socket) {
  socket = send_socket;

  let wizardName = document.getElementById("wizardName");
  wizardName.style.display = "inline"; // show
  wizardName.textContent = msg.name;

  let checkFocus = document.getElementById("checkFocus");
  if (checkFocus) {
    checkFocus.parentNode.removeChild(checkFocus);
  }

  let wizardModalTitle = document.getElementById("wizardModalTitle");
  wizardModalTitle.textContent = msg.name;

  let msgImg = document.getElementById("msg-img");
  if (msgImg) {
    msgImg.parentNode.removeChild(msgImg);
  }

  type = msg.type;
  switch (msg.type) {
    case "boolean":
      displayHeaderModal();
      parentClassWizardName("form-check");
      classWizardName("form-check-label");
      textButtonWizard();
      formatWizardInput(true, "checkbox", msg.value);
      break;
    case "integer":
    case "floating":
      displayHeaderModal();
      parentClassWizardName();
      classWizardName();
      textButtonWizard();
      formatWizardInput(true, "number", msg.value);
      break;
    case "str":
      displayHeaderModal();
      parentClassWizardName();
      classWizardName();
      textButtonWizard();
      formatWizardInput(true, "text", msg.value);
      break;
    case "message":
      displayHeaderModal(true, msg.name);
      parentClassWizardName();
      classWizardName();
      wizardName.textContent = msg.value;

      const img = document.createElement("img");
      img.setAttribute("src", "static/img/message.svg");
      img.setAttribute("id", "msg-img");

      wizardModalTitle.parentElement.insertBefore(img, wizardModalTitle);
      wizardModalTitle.setAttribute("style", "display: inline;");

      textButtonWizard("Ok");
      formatWizardInput(false);
      break;
    case "choice_integer":
    case "choice_floating":
    case "choice_str":
      displayHeaderModal();
      parentClassWizardName("form-check");
      classWizardName("form-check-label");
      formatWizardInput(true, "radio", msg.value, msg.choices);
      textButtonWizard();
      break;
    case "select_integer":
    case "select_floating":
    case "select_str":
      displayHeaderModal();
      parentClassWizardName("form-check");
      classWizardName("form-check-label");
      formatWizardInput(true, "select", msg.value, msg.choices);
      textButtonWizard();
      break;
    case "camp":
      displayHeaderModal(true, msg.name);
      parentClassWizardName("form-check");
      classWizardName("form-check-label");
      wizardName.style.display = "none"; // hide
      textButtonWizard();
      formatWizardInput(true, "camp", msg.value);
      break;
    case "camera":
      displayHeaderModal(true, msg.name);
      parentClassWizardName();
      classWizardName();
      wizardName.style.display = "none"; // hide

      const streaming = document.createElement("img");
      streaming.setAttribute("style", "width: 100%");
      streaming.setAttribute("src", `http://${window.location.hostname}:8081/`);

      const checkFocus = document.createElement("div");
      checkFocus.setAttribute("id", "checkFocus");
      checkFocus.appendChild(streaming);

      document.getElementsByClassName("input-group")[0].appendChild(checkFocus);

      textButtonWizard("Ok");
      formatWizardInput(false);
      break;
  }

  let wizardModal = document.getElementById("wizardModal");
  wizardModal.style.display = "block"; // show
}

document
  .getElementById("btn-send-wizard")
  .addEventListener("click", function () {
    let submittedValue = "";

    let wizardName = document.getElementById("wizardName");
    if (wizardName.textContent.toLowerCase().includes("camp")) {
      submittedValue = document
        .getElementsByClassName("btn active")[0]
        .getAttribute("value");
    } else if (wizardName.textContent.toLowerCase().includes("choose")) {
      submittedValue = document.querySelector(
        "input[name=choice]:checked"
      ).value;
    } else if (wizardName.textContent.toLowerCase().includes("select")) {
      submittedValue = [];
      document
        .querySelectorAll("input[name=choice]:checked")
        .forEach((element) => {
          submittedValue.push(element.value);
        });
    } else {
      let wizardInput = document.getElementById("wizardInput");
      submittedValue =
        wizardInput.getAttribute("type") === "checkbox"
          ? wizardInput.checked
          : wizardInput.value;
    }

    socket.emit("wizard", {
      type: type,
      name: wizardName.textContent,
      value: submittedValue,
    });

    document.getElementById("wizardModal").style.display = "none"; // hide
  });

function displayHeaderModal(show = false, headerText = "") {
  let modalHeader = document.getElementsByClassName("modal-header")[0];

  if (show) {
    modalHeader.style.display = "inline"; // show
    document.getElementById("wizardModalTitle").textContent =
      headerText.charAt(0).toUpperCase() + headerText.slice(1);
  } else {
    modalHeader.style.display = "none"; // hide
  }
}

function parentClassWizardName(parentClass = "input-group") {
  document
    .getElementById("wizardName")
    .parentElement.setAttribute("class", parentClass);
}

function classWizardName(parentClass = "input-group-text") {
  document.getElementById("wizardName").setAttribute("class", parentClass);
}

function textButtonWizard(text = "Send") {
  document.getElementById("btn-send-wizard").textContent = text;
}

function formatWizardInput(showInput, typeInput, value, choices) {
  let newZone = document.getElementById("newZone");
  if (newZone) {
    newZone.parentNode.removeChild(newZone);
  }
  let wizardInput = document.getElementById("wizardInput");
  wizardInput.setAttribute("type", typeInput);
  if (showInput) {
    if (typeInput === "checkbox") {
      wizardInput.setAttribute("class", "form-check-input");
      wizardInput.checked = value;
      wizardInput.style.display = "inline"; // show
    } else if (typeInput === "radio" || typeInput === "select") {
      wizardInput.style.display = "none"; // none

      const typeButton = typeInput === "radio" ? "radio" : "checkbox";

      const choiceZone = document.createElement("div");
      choiceZone.setAttribute("id", "newZone");

      choices.forEach((choice) => {
        const isChecked =
          typeInput === "radio" ? value == choice : value.indexOf(choice) >= 0;

        const button = document.createElement("input");
        button.setAttribute("type", typeButton);
        button.setAttribute("name", "choice");
        button.checked = isChecked;
        button.value = choice;

        const label = document.createElement("label");
        label.setAttribute("class", "form-check-label");
        label.setAttribute("for", "choice");
        label.textContent = choice;

        choiceZone.appendChild(button);
        choiceZone.appendChild(label);
      });
      document.getElementsByClassName("form-check")[0].appendChild(choiceZone);
    } else if (typeInput === "camp") {
      wizardInput.setAttribute("type", "hidden");

      const campZone = document.createElement("div");
      campZone.setAttribute("id", "newZone");

      const listCamp = ["purple", "yellow"];

      listCamp.forEach((camp) => {
        const active = camp === value ? "active" : "";

        const button = document.createElement("button");
        button.setAttribute("type", "button");
        button.setAttribute("class", `btn ${active} btn-${camp}`);
        button.value = camp;

        button.addEventListener("click", function () {
          [...this.parentElement.children].forEach((sib) =>
            sib.classList.remove("active")
          );
          this.classList.add("active");
        });

        campZone.appendChild(button);
      });

      document.getElementsByClassName("form-check")[0].appendChild(campZone);
    } else {
      wizardInput.setAttribute("class", "form-control use-keyboard-input");
      wizardInput.value = value;
      wizardInput.style.display = "inline"; // show
    }
  } else {
    wizardInput.style.display = "none"; // none
  }
}
