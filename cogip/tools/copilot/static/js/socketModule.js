export function onConnection() {
  console.log("Connected to Copilot.");
  $("#connection").html(
    "<pre>Connected to " + window.location.origin + "</pre>"
  );
}

export function onDisconnect() {
  console.log("Disconnected.");
  $("#connection").html("<pre>Disconnected.</pre>");
}

export function onMenu(menu, socket) {
  $("#menu").empty();
  $("#menu").html("<h1 class=small >" + menu.name + "</h1>"); // display title for menu

  const divButton = $('<div id="divButtons"></div>');
  // add all buttons menu
  for (let value in menu.entries) {
    if (!menu.entries[value]["cmd"].startsWith("_")) {
      let inputParams = "";

      let newButtonMenu = $(
        `<button type='button' class='btn btn-dark'>${menu.entries[value]["desc"]}</button>`
      ).click(function () {
        socket.emit("cmd", menu.entries[value]["cmd"]);
      });

      if (menu.entries[value]["desc"].includes("<")) {
        let divRow = $('<div class="input-group"></div>');
        inputParams = `<input class="form-control use-keyboard-input" type="number" />`;

        divRow.append(newButtonMenu);
        divRow.append(inputParams);
        divButton.append(divRow);
      } else {
        divButton.append(newButtonMenu);
        divButton.append("<br>");
      }
    }

    $("#menu").append(divButton);
  }
}

export function onReset(socket) {
  socket.emit("break");
}
