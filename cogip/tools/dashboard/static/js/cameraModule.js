let cameraDom = document.getElementById("cameraModal");

const urlParams = new URLSearchParams(window.location.search);
const robotId = urlParams.get("robot_id");

window.modalCamera = function () {
  const streaming = document.createElement("img");
  streaming.setAttribute("id", "streaming");
  streaming.setAttribute("style", "width: 100%");
  streaming.setAttribute("loading", "lazy");

  const hostname = robotId === "0" ? "beacon" : "robot" + robotId;
  const port = robotId === "0" ? "90" : "8" + robotId;
  streaming.setAttribute(
    "src",
    `http://${hostname}:80${port}/`
  );

  document.getElementById("displayFlux").appendChild(streaming);
};

cameraDom.addEventListener("hide.bs.modal", function () {
  const streaming = document.getElementById("streaming");
  streaming.setAttribute("src", "");
  streaming.remove();
});
