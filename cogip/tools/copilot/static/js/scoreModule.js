let socket = null;

export function openScoreModal(score) {
  $("#displayScore").text(score);

  $("#scoreModal").modal("show");
}
