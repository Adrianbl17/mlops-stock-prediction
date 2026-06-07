const FEATURE_DISPLAY = {
  daily_return: (value) => value.toFixed(3),
  Volume:       (value) => `${(value / 1_000_000).toFixed(1)}M`,
};

function displayValue(feature, value) {
  const format = FEATURE_DISPLAY[feature];
  return format ? format(value) : String(value);
}

const FEATURE_RANGE = {
  Volume: (value) => ({ min: 0, max: value * 2 }),
};

function setSliderRange(input, feature, value) {
  const range = FEATURE_RANGE[feature];
  if (!range) return;

  const { min, max } = range(value);
  input.min = String(min);
  input.max = String(max);
}

async function loadSimulationWindow(symbol, date, modelType) {
  const response = await fetch(`/api/data?symbol=${encodeURIComponent(symbol)}&date=${encodeURIComponent(date)}`);
  const data = await response.json();

  data.window.forEach((day, dayIndex) => {
    data.feature_cols.forEach((feature, featureIndex) => {
      const input = document.querySelector(`input[data-feature="${feature}"][data-day="${dayIndex + 1}"]`);
      if (!input) return;

      const value = day.values[featureIndex];
      setSliderRange(input, feature, value);
      input.value = value;
      input.nextElementSibling.textContent = displayValue(feature, value);
    });
  });

  document.querySelector("#simulation-heading").textContent = `Simulation - ${date} - ${symbol} - ${modelType}`;
}

function handleSliderInput(e) {
  const input   = e.target;
  const feature = input.dataset.feature;
  const value   = parseFloat(input.value);

  input.nextElementSibling.textContent = displayValue(feature, value);
}

function handlePredictionRowClick(e) {
  const row       = e.currentTarget;
  const date      = row.querySelector("td").textContent;
  const symbol    = document.querySelector("#stock-select").value;
  const modelType = document.querySelector("#model-select").value;

  loadSimulationWindow(symbol, date, modelType);
}

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

export {handleModelChange, loadStocks, handlePredictionRowClick, handleSliderInput, loadSimulationWindow};
