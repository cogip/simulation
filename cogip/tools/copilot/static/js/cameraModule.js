let cameraDom = document.getElementById("cameraModal");

window.modalCamera = function () {
  const streaming = $(
    `<img id="streaming" style="width: 100%" loading="lazy" src="http://${window.location.hostname}:8081/"></img>`
  );

  $("#displayFlux").append(streaming);
};

cameraDom.addEventListener("hide.bs.modal", function () {
  $("#streaming").attr("src", "");
  $("#streaming").remove();
});
