const streaming = $(
  `<img style="width: 100%" src="http://${window.location.hostname}:8081/"></img>`
);

let cameraDom = document.getElementById("cameraModal");

window.modalCamera = function () {
  $("#displayFlux").append(streaming);
};

cameraDom.addEventListener("hide.bs.modal", function () {
  streaming.detach();
});
