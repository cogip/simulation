let cameraDom = document.getElementById("cameraModal");

window.modalCamera = function () {
  const streaming = document.createElement("img");
  streaming.setAttribute("id", "streaming");
  streaming.setAttribute("style", "width: 100%");
  streaming.setAttribute("loading", "lazy");
  streaming.setAttribute("src", `http://${window.location.hostname}:8081/`);

  document.getElementById("displayFlux").appendChild(streaming);
};

cameraDom.addEventListener("hide.bs.modal", function () {
  const streaming = document.getElementById("streaming");
  streaming.setAttribute("src", "");
  streaming.remove();
});
