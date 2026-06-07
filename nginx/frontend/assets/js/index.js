import * as Handler from "./handler.js";

function init() {
  const modelSelect = document.querySelector("#model-select");
  const stockSelect = document.querySelector("#stock-select");

  modelSelect.addEventListener("change", Handler.handleModelChange);
  Handler.loadStocks(modelSelect.value, stockSelect);

  document.querySelectorAll("#prediction-table tbody tr").forEach((row) => {
    row.style.cursor = "pointer";
    row.addEventListener("click", Handler.handlePredictionRowClick);
  });
}

init();
