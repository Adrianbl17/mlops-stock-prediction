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

let simState = null;

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

  simState = { symbol, date, modelType, featureCols: data.feature_cols, window: data.window };

  document.querySelector("#simulation-heading").textContent = `Simulation - ${date} - ${symbol} - ${modelType}`;
}

function collectSimulationFeatures() {
  return simState.window.map((day, dayIndex) => {
    const values = [...day.values];

    simState.featureCols.forEach((feature, featureIndex) => {
      const input = document.querySelector(`input[data-feature="${feature}"][data-day="${dayIndex + 1}"]`);
      if (!input) return;

      values[featureIndex] = parseFloat(input.value);
    });

    return values;
  });
}

async function handleSimulateClick() {
  if (!simState) return;

  const response = await fetch("/api/simulate", {
    method:  "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      symbol:     simState.symbol,
      model_type: simState.modelType,
      date:       simState.date,
      features:   collectSimulationFeatures(),
    }),
  });
  const result = await response.json();

  document.querySelector("#baseline-prediction").textContent  = result.baseline_prediction;
  document.querySelector("#baseline-confidence").textContent  = `${Math.round(result.baseline_confidence * 100)}%`;
  document.querySelector("#simulated-prediction").textContent = result.simulated_prediction;
  document.querySelector("#simulated-confidence").textContent = `${Math.round(result.simulated_confidence * 100)}%`;
  document.querySelector("#simulation-delta").textContent     = result.delta;
}

function handleResetClick() {
  if (!simState) return;

  loadSimulationWindow(simState.symbol, simState.date, simState.modelType);
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

function buildPredictionRow(result) {
  const row = document.createElement("tr");
  row.style.cursor = "pointer";

  const correctText = result.correct === null ? "" : (result.correct ? "yes" : "no");

  [
    result.date,
    result.prediction,
    `${Math.round(result.confidence * 100)}%`,
    result.actual ?? "",
    correctText,
  ].forEach((text) => {
    const cell = document.createElement("td");
    cell.textContent = text;
    row.appendChild(cell);
  });

  row.addEventListener("click", handlePredictionRowClick);
  return row;
}

async function handlePredictClick() {
  const symbol    = document.querySelector("#stock-select").value;
  const modelType = document.querySelector("#model-select").value;
  const startDate = document.querySelector("#start-date").value;
  const endDate   = document.querySelector("#end-date").value;

  const response = await fetch("/api/predict", {
    method:  "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      symbol,
      model_type: modelType,
      start_date: startDate,
      end_date:   endDate,
    }),
  });
  const results = await response.json();

  const tbody = document.querySelector("#prediction-table tbody");
  tbody.innerHTML = "";
  results.forEach((result) => tbody.appendChild(buildPredictionRow(result)));
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

export {handleModelChange, loadStocks, handlePredictionRowClick, handleSliderInput, handlePredictClick, loadSimulationWindow, handleSimulateClick, handleResetClick};
