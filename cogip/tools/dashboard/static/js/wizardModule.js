let socket = null;
let message = null;

export function openWizardModal(msg, send_socket) {
  socket = send_socket;
  message = msg;

  let wizardName = document.getElementById("wizardName");
  wizardName.classList.add("inline");
  wizardName.textContent = msg.name;

  let checkFocus = document.getElementById("checkFocus");
  if (checkFocus) {
    checkFocus.parentNode.removeChild(checkFocus);
  }

  document.getElementById("wizardModalTitle").textContent = msg.name;

  let msgImg = document.getElementById("msg-img");
  if (msgImg) {
    msgImg.parentNode.removeChild(msgImg);
  }

  switch (msg.type) {
    case "boolean":
      displayHeaderModal();
      textButtonWizard();
      formatWizardInput(true, "checkbox", msg.value);
      break;
    case "integer":
    case "floating":
      displayHeaderModal();
      textButtonWizard();
      formatWizardInput(true, "number", msg.value);
      break;
    case "str":
      displayHeaderModal();
      textButtonWizard();
      formatWizardInput(true, "text", msg.value);
      break;
    case "message":
      displayHeaderModal(true, msg.name);
      wizardName.textContent = msg.value;

      const img = document.createElement("img");
      img.setAttribute("src", "static/img/message.svg");
      img.setAttribute("class", "inline");
      img.setAttribute("id", "msg-img");

      wizardModalTitle.parentElement.insertBefore(img, wizardModalTitle);
      wizardModalTitle.classList.add("inline");

      textButtonWizard("Ok");
      formatWizardInput(false);
      break;
    case "choice_integer":
    case "choice_floating":
    case "choice_str":
      displayHeaderModal();
      formatWizardInput(true, "radio", msg.value, msg.choices);
      textButtonWizard();
      break;
    case "select_integer":
    case "select_floating":
    case "select_str":
      displayHeaderModal();
      formatWizardInput(true, "select", msg.value, msg.choices);
      textButtonWizard();
      break;
    case "camp":
      displayHeaderModal(true, msg.name);
      wizardName.style.display = "none"; // hide
      textButtonWizard();
      formatWizardInput(true, "camp", msg.value);
      break;
    case "camera":
      displayHeaderModal(true, msg.name);
      wizardName.style.display = "none"; // hide

      const streaming = document.createElement("img");
      streaming.setAttribute("style", "width: 100%");
      streaming.setAttribute("src", `http://${window.location.hostname}:8081/`);

      const checkFocus = document.createElement("div");
      checkFocus.setAttribute("id", "checkFocus");
      checkFocus.appendChild(streaming);

      document.getElementById("modalBody").appendChild(checkFocus);

      textButtonWizard("Ok");
      formatWizardInput(false);
      break;
  }

  document.getElementById('wizardModal').classList.remove('hidden');
  document.getElementById('wizardModal').style.display = 'flex';
}

document
  .getElementById("btnSendWizard")
  .addEventListener("click", function () {
    let submittedValue = "";

    let wizardName = document.getElementById("wizardName");
    if (wizardName.textContent.toLowerCase().includes("camp")) {
      submittedValue = document
        .getElementsByClassName("active")[0]
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

    message.value = submittedValue;
    socket.emit("wizard", message);

    document.getElementById("wizardModal").classList.add("hidden");
    document.getElementById("wizardModal").style.display = "none";
  });

function displayHeaderModal(show = false, headerText = "") {
  let modalHeader = document.getElementById("modalHeader");

  if (show) {
    modalHeader.style.display = "block"; // show
    document.getElementById("wizardModalTitle").textContent =
      headerText.charAt(0).toUpperCase() + headerText.slice(1);
  } else {
    modalHeader.style.display = "none"; // hide
  }
}

function textButtonWizard(text = "Send") {
  document.getElementById("btnSendWizard").textContent = text;
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
      wizardInput.setAttribute("class", "checked:accent-red-cogip checked:border-red-cogip");
      wizardInput.checked = value;
      // wizardInput.style.display = "inline"; // show
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
        button.setAttribute("class", "w-[15px] h-[15px] rounded-md inline-block bg-white checked:accent-red-cogip")
        button.checked = isChecked;
        button.value = choice;

        const label = document.createElement("label");
        label.setAttribute("class", "text-grey-color");
        label.setAttribute("for", "choice");
        label.textContent = choice;

        choiceZone.appendChild(document.createElement("br"));
        choiceZone.appendChild(button);
        choiceZone.appendChild(label);
      });
      document.getElementById("modalBody").appendChild(choiceZone);
    } else if (typeInput === "camp") {
      wizardInput.setAttribute("type", "hidden");

      const campZone = document.createElement("div");
      campZone.setAttribute("id", "newZone");

      const listCamp = ["blue", "yellow"];

      listCamp.forEach((camp) => {
        const active = camp === value ? "active shadow-lg shadow-black outline-none" : "";
        const cssColor = "camp-" + (camp === "blue" ? "1" : "2")

        const button = document.createElement("button");
        button.setAttribute("type", "button");
        button.setAttribute("class", `h-[30px] w-[100px] mr-[15px] bg-${cssColor} border-${cssColor} rounded-md ${active}`);
        button.value = camp;

        button.addEventListener("click", function () {
          [...this.parentElement.children].forEach((sib) =>
            sib.classList.remove("active", "shadow-lg", "shadow-black", "outline-none")
          );
          this.classList.add("active", "shadow-lg", "shadow-black", "outline-none");
        });

        campZone.appendChild(button);
      });

      document.getElementById("modalBody").appendChild(campZone);
    } else {
      wizardInput.setAttribute("class", "text-grey-color bg-black rounded-md border border-slate-950 use-keyboard-input focus:outline-none focus:caret-red-cogip focus:ring-2 focus:ring-red-cogip");
      wizardInput.value = value;
      wizardInput.style.display = "inline"; // show
    }
  } else {
    wizardInput.style.display = "none"; // none
  }
}
