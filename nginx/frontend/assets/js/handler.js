async function loadStocks(modelType, stockSelect) {
  const response = await fetch(`/api/stocks?model_type=${encodeURIComponent(modelType)}`);
  const data = await response.json();

  stockSelect.innerHTML = "";
  data.symbols.forEach((symbol) => {
    const option = document.createElement("option");
    option.value = symbol;
    option.textContent = symbol;
    stockSelect.appendChild(option);
  });
  stockSelect.disabled = data.symbols.length <= 1;
}

function handleModelChange(e) {
  const modelSelect = e.target;
  const stockSelect = document.querySelector("#stock-select");
  loadStocks(modelSelect.value, stockSelect);
}

export {handleModelChange, loadStocks};
