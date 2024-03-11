let cameraDom = document.getElementById("cameraModal");

const urlParams = new URLSearchParams(window.location.search);

window.modalCamera = function () {
  const streaming = document.createElement("img");
  streaming.setAttribute("id", "streaming");
  streaming.setAttribute("style", "width: 100%");
  streaming.setAttribute("loading", "lazy");

  let hostname = null;
  let port = null;
  hostname = window.location.hostname
  port = parseInt(window.location.port) + 20;

  streaming.setAttribute(
    "src",
    `http://${hostname}:${port}/`
  );

  document.getElementById("displayFlux").appendChild(streaming);
};

cameraDom.addEventListener("hide.bs.modal", function () {
  const streaming = document.getElementById("streaming");
  streaming.setAttribute("src", "");
  streaming.remove();
});
