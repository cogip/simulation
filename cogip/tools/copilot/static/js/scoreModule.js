export function openScoreModal(score) {
  document.getElementById("displayScore").textContent = score;

  const scoreModal = new bootstrap.Modal("#scoreModal");
  scoreModal.show(document.getElementById("scoreModal"));
}
