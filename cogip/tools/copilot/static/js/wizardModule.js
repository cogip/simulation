let socket = null;
let type = null;

export function openWizardModal(msg, send_socket) {
  socket = send_socket;

  $("#wizardName").show();
  $("#checkFocus").detach();
  $("#wizardModalTitle").text(msg.name);
  $("#wizardName").text(msg.name);

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
      $("#wizardName").text(msg.value);
      $("#wizardModalTitle").prepend(
        '<img src="static/img/message.svg"></img>'
      );
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
      $("#wizardName").hide();
      textButtonWizard();
      formatWizardInput(true, "camp", msg.value);
      break;
    case "camera":
      displayHeaderModal(true, msg.name);
      parentClassWizardName();
      classWizardName();
      $("#wizardName").hide();

      const streaming = $(
        `<div id="checkFocus"><img style="width: 100%" src="http://${window.location.hostname}:8081/"></img></div>`
      );

      $(".input-group").append(streaming);

      textButtonWizard("Ok");
      formatWizardInput(false);
      break;
  }
  $("#wizardModal").modal("show");
}

$("#btn-send-wizard").click(function () {
  let submittedValue = "";

  if ($("#wizardName").text().toLowerCase().includes("camp")) {
    submittedValue = $(".btn.active").attr("value");
  } else if ($("#wizardName").text().toLowerCase().includes("choose")) {
    submittedValue = $("input[name=choice]:checked").val();
  } else if ($("#wizardName").text().toLowerCase().includes("select")) {
    submittedValue = [];
    $("input[name=choice]:checked").each((index, element) => {
      submittedValue.push(element.value);
    });
  } else {
    submittedValue =
      $("#wizardInput").attr("type") === "checkbox"
        ? $("#wizardInput").is(":checked")
        : $("#wizardInput").val();
  }

  socket.emit("wizard", {
    type: type,
    name: $("#wizardName").text(),
    value: submittedValue,
  });

  $("#wizardModal").modal("hide");
});

function displayHeaderModal(show = false, headerText = "") {
  if (show) {
    $(".modal-header").show();
    $("#wizardModalTitle").text(
      headerText.charAt(0).toUpperCase() + headerText.slice(1)
    );
  } else {
    $(".modal-header").hide();
  }
}

function parentClassWizardName(parentClass = "input-group") {
  $("#wizardName").parent().attr("class", parentClass);
}

function classWizardName(parentClass = "input-group-text") {
  $("#wizardName").attr("class", parentClass);
}

function textButtonWizard(text = "Send") {
  $("#btn-send-wizard").text(text);
}

function formatWizardInput(showInput, typeInput, value, choices) {
  $("#newZone").detach();

  $("#wizardInput").attr("type", typeInput);
  if (showInput) {
    if (typeInput === "checkbox") {
      $("#wizardInput")
        .attr("class", "form-check-input")
        .attr("checked", value);

      $("#wizardInput").show();
    } else if (typeInput === "radio" || typeInput === "select") {
      $("#wizardInput").hide();

      const typeButton = typeInput === "radio" ? "radio" : "checkbox";
      const choiceZone = $('<div id="newZone"></div>');

      choices.forEach((choice) => {
        const isChecked =
          typeInput === "radio" ? value == choice : value.indexOf(choice) >= 0;
        const button = $(
          '<input type="' +
            typeButton +
            '" name="choice" value="' +
            choice +
            '" />'
        );
        button.attr("checked", isChecked);
        const label = $(
          '<label class="form-check-label" for="choice"> ' +
            choice +
            " </label>"
        );

        choiceZone.append(button);
        choiceZone.append(label);
      });
      $(".form-check").append(choiceZone);
    } else if (typeInput === "camp") {
      $("#wizardInput").attr("type", "hidden");
      const campZone = $('<div id="newZone"></div>');

      const listCamp = ["purple", "yellow"];

      listCamp.forEach((camp) => {
        const active = camp === value ? "active" : "";

        const button = $(
          '<button type="button" class="btn ' +
            active +
            " btn-" +
            camp +
            '"></button>'
        );
        button.attr("value", camp);

        button.on("click", function () {
          $(this).siblings().removeClass("active");
          $(this).addClass("active");
        });

        campZone.append(button);
      });

      $(".form-check").append(campZone);
    } else {
      $("#wizardInput")
        .attr("class", "form-control use-keyboard-input")
        .val(value);
      $("#wizardInput").show();
    }
  } else {
    $("#wizardInput").hide();
  }
}
