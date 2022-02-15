// addEventListener to adapt board to window size

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

  background.onload = function () {
    context.drawImage(
      background,
      -htmlCanvas.width / 2,
      0,
      imgWidth,
      imgHeight
    );
  };

  context.translate(htmlCanvas.width / 2, 0);
}
