// addEventListener to adapt board to window size

let pose_current = undefined;
let obstacles = [];

export function updatePoseCurrent(new_pose) {
  pose_current = new_pose;
}

export function updateObstacles(new_obstacles) {
  obstacles = new_obstacles;
}

let ratioX = null;
let ratioY = null;

export function resizeCanvas() {
  const footerHeight = $(".footer").outerHeight();
  const menuWidth = $("#menu").outerWidth();

  let htmlCanvas = document.getElementById("board");
  htmlCanvas.height =
    window.innerHeight -
    footerHeight -
    ($("#board").outerHeight(true) - $("#board").outerHeight());
  htmlCanvas.width =
    window.innerWidth -
    menuWidth -
    ($("#board").outerWidth(true) - $("#board").outerWidth());

  let background = new Image();
  background.src = "static/img/ground2022.png"; // default background size 2000x3000 --> ratio 2/3

  let imgWidth = htmlCanvas.width;
  let imgHeight = (imgWidth * 2) / 3;

  if (imgHeight > htmlCanvas.height) {
    imgHeight = htmlCanvas.height;
    imgWidth = (imgHeight * 3) / 2;
  }

  const context = htmlCanvas.getContext("2d");

  context.canvas.width = imgWidth;
  context.canvas.height = imgHeight;

  context.translate(htmlCanvas.width / 2, 0); // x invert

  htmlCanvas.addEventListener("click", function (event) {
    console.log(getMousePos(this, event));
  });

  ratioX = imgWidth / 3000;
  ratioY = imgHeight / 2000;
}

function getMousePos(canvas, evt) {
  var transX = canvas.width / 2;
  var transY = 0;
  var rect = canvas.getBoundingClientRect();
  return {
    x: evt.clientX - rect.left - transX,
    y: evt.clientY - rect.top - transY,
  };
}

export function displayMsg(msg) {
  $("#msg").empty();

  let mode = null;
  switch (msg.mode) {
    case 0:
      mode = "STOP";
      break;
    case 1:
      mode = "IDLE";
      break;
    case 2:
      mode = "BLOCKED";
      break;
    case 3:
      mode = "RUNNING";
      break;
    case 4:
      mode = "RUNNING_SPEED";
      break;
    case 5:
      mode = "PASSTHROUGH";
      break;
  }

  if (
    pose_current !== undefined &&
    !isNaN(pose_current.x) &&
    !isNaN(pose_current.y)
  ) {
    const formatMsg = $(
      `<pre>Cycle: ${msg.cycle} / X: ${pose_current.x.toFixed(
        2
      )} / Y: ${pose_current.y.toFixed(
        2
      )} / Angle: ${pose_current.O.toFixed(2)} / Mode: ${mode}</pre>`
    );
    $("#msg").append(formatMsg);
  }
}

let robot = new Image();
robot.src = "static/img/robot.png";

let order = new Image();
order.src = "static/img/robot.png";

export function drawBoardElement(msg) {
  // get board dom element
  let htmlCanvas = document.getElementById("board");
  const context = htmlCanvas.getContext("2d");

  // clear area
  context.clearRect(
    -htmlCanvas.width / 2,
    0,
    htmlCanvas.width,
    htmlCanvas.height
  );

  // draw robot
  // init robot position
  if (
    pose_current !== undefined &&
    !isNaN(pose_current.x) &&
    !isNaN(pose_current.y)
  ) {
    const robotX = pose_current.x;
    const robotY = pose_current.y;
    const robotO = pose_current.O;
    drawRobot(robotX, robotY, robotO, context);
  }

  // draw order
  if (msg.pose_order) {
    // init order position
    const orderX = msg.pose_order.x;
    const orderY = msg.pose_order.y;
    const orderO = msg.pose_order.O;

    context.save();
    context.filter = "opacity(60%)";
    drawRobot(orderX, orderY, orderO, context);
    context.restore();
  }

  // draw path
  if (msg.path.length) {
    for (let i = 0; i < msg.path.length - 1; i++) {
      const startPoint = msg.path[i];
      const endPoint = msg.path[i + 1];

      drawPath(startPoint, endPoint, context);
    }
  }

  // draw obstacles
  if (obstacles.length) {
    obstacles.forEach(function (obstacle) {
      drawObstacles(obstacle, context);
    });
  }
}

function drawRobot(x, y, O, context) {
  let robotWidth = robot.width * ratioX;
  let robotHeight = robot.height * ratioY;

  context.save();
  context.translate(-x * ratioX, y * ratioY);
  context.rotate(-(O * Math.PI) / 180);
  context.drawImage(
    robot,
    -robotWidth / 2,
    -robotHeight / 2,
    robotWidth,
    robotHeight
  );
  context.restore();
}

function drawPath(startPoint, endPoint, context) {
  context.save();
  context.strokeStyle = "blue";
  context.lineWidth = 2;
  context.beginPath();
  context.moveTo(-startPoint.x * ratioX, startPoint.y * ratioY);
  context.lineTo(-endPoint.x * ratioX, endPoint.y * ratioY);
  context.closePath();
  context.stroke();
  context.restore();
}

function drawObstacles(obstacle, context) {
  let obstacleX = -obstacle.x * ratioX;
  let obstacleY = obstacle.y * ratioY;

  context.save();
  context.fillStyle = "red";
  context.filter = "opacity(20%)";

  if (obstacle.radius) {
    let radius = obstacle.radius * ratioX;

    context.beginPath();
    context.arc(obstacleX, obstacleY, radius, 0, 2 * Math.PI);
    context.fill();
    context.closePath();
  } else {
    let angle = obstacle.angle;
    let length_x = obstacle.length_x * ratioX;
    let length_y = obstacle.length_y * ratioY;

    context.translate(obstacleX, obstacleY);
    context.rotate(-(angle * Math.PI) / 180);
    context.fillRect(-length_x / 2, -length_y / 2, length_x, length_y);
  }

  context.restore();
}
