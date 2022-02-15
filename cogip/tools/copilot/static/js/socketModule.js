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

export function onMenu(menu) {
  $("#menu").empty();
  $("#menu").html("<h1>" + menu.name + "</h1>"); // display title for menu

  // add all buttons menu
  for (let value in menu.entries) {
    if (!menu.entries[value]["cmd"].startsWith("_")) {
      let inputParams = "";
      if (menu.entries[value]["desc"].includes("<")) {
        inputParams = `<input type="text" placeholder="kp"/>`;
      }
      let newButtonMenu = $(
        `<div><button type='button' class='btn btn-light btn-sm'>${menu.entries[value]["desc"]}</button>${inputParams}</div>`
      );
      $("#menu").append(newButtonMenu);
    }
  }
}
