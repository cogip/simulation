export function onConnection(socket) {
  console.log("Connected to Server.");
  socket.emit("connected");

  document.getElementById("connection").innerHTML =
    "<pre class=\"text-grey-color text-sm inline\"><img class=\"mr-5 w-[20px] inline\" src=\"static/img/check_green_circle.svg\">" +
    window.location.origin +
    "</pre>";
}

export function onDisconnect() {
  console.log("Disconnected from Server.");
  document.getElementById("connection").innerHTML =
    "<pre class=\"text-grey-color text-sm inline\"><img class=\"inline\" src=\"static/img/cross_red_circle.svg\"></pre>";
}

export function onMenu(menu, type, socket) {
  var typeNav = document.getElementById("nav-" + type);
  while (typeNav.firstChild) typeNav.removeChild(typeNav.firstChild);

  var h1 = document.createElement("h1");
  h1.setAttribute("class", "small text-grey-color");
  h1.innerHTML = menu.name; // display title for menu
  typeNav.appendChild(h1);

  const divButton = document.createElement("div");
  divButton.classList.add("max-h-[72vh]", "overflow-y-auto");

  // add all buttons menu
  for (let value in menu.entries) {
    if (!menu.entries[value]["cmd"].startsWith("_")) {
      let newButtonMenu = document.createElement("button");
      newButtonMenu.setAttribute("type", "button");
      newButtonMenu.setAttribute("class", "px-4 py-2 mb-2 bg-gray-800 text-grey-color rounded hover:bg-gray-700 focus:outline-none ");
      newButtonMenu.innerHTML = menu.entries[value]["desc"];
      newButtonMenu.addEventListener("click", function () {
        var cmd = menu.entries[value]["cmd"]
        console.log(type + "_cmd", cmd);
        if (type == "tool") {
          socket.emit(type + "_cmd", cmd);
        }
        else {
          socket.emit(type + "_cmd", 1, cmd);
        }
      });

      if (menu.entries[value]["desc"].includes("<")) {
        let divRow = document.createElement("div");

        let inputParams = document.createElement("input");
        inputParams.setAttribute("class", "use-keyboard-input");
        inputParams.setAttribute("type", "number");

        divRow.appendChild(newButtonMenu);
        divRow.appendChild(inputParams);
        divButton.appendChild(divRow);
      } else {
        divButton.appendChild(newButtonMenu);
        divButton.appendChild(document.createElement("br"));
      }
    }

    typeNav.appendChild(divButton);
  }
}
