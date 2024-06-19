let cameraDom = document.getElementById("cameraModal");

const urlParams = new URLSearchParams(window.location.search);

window.modalCamera = function () {
  if (document.getElementById("cameraModal").style.display !== "flex") {
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
    document.getElementById("cameraModal").classList.remove("hidden");
    document.getElementById("cameraModal").style.display = "flex";
  }
};

window.closeModal = function (modalId) {
  document.getElementById(modalId).classList.add("hidden");
  document.getElementById(modalId).style.display = "none";
  const streaming = document.getElementById("streaming");
  
  if (streaming) {
    streaming.setAttribute("src", "");
    streaming.remove();
  }
}
