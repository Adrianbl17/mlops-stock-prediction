import * as Handler from "./handler.js";

function init() {
  const modelSelect = document.querySelector("#model-select");
  const stockSelect = document.querySelector("#stock-select");

  modelSelect.addEventListener("change", Handler.handleModelChange);
  Handler.loadStocks(modelSelect.value, stockSelect);
}

init();
