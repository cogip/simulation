export function openScoreModal(score) {
  document.getElementById("displayScore").textContent = score;
  document.getElementById("scoreModal").classList.remove("hidden");
  document.getElementById("scoreModal").style.display = "flex";
};