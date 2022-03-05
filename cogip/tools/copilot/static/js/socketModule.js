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
      if (menu.entries[value]["desc"].includes("<")) {
        inputParams = `<input class="use-keyboard-input" />`;
      }

      let newButtonMenu = $(
        `<div><button type='button' class='btn btn-light btn-sm'>${menu.entries[value]["desc"]}</button>${inputParams}</div>`
      ).click(function () {
        socket.emit("cmd", menu.entries[value]["cmd"]);
      });

      divButton.append(newButtonMenu);
    }

    $("#menu").append(divButton);
  }
}
