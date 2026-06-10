const MAX_DATE_RANGE_DAYS = 90;

function handleStartDateChange(e) {
  const startDate    = e.target.value;
  const endDateInput = document.querySelector("#end-date");
  if (!startDate) return;

  const maxEndDate = new Date(startDate);
  maxEndDate.setDate(maxEndDate.getDate() + MAX_DATE_RANGE_DAYS);

  endDateInput.min = startDate;
  endDateInput.max = maxEndDate.toISOString().slice(0, 10);

  if (endDateInput.value && endDateInput.value > endDateInput.max) {
    endDateInput.value = endDateInput.max;
  }
}

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

async function saveToHistory({ symbol, modelType, date, prediction, confidence, isSimulation }) {
  const response = await fetch("/api/history", {
    method:  "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      symbol,
      model_type:    modelType,
      date,
      prediction,
      confidence,
      is_simulation: isSimulation,
    }),
  });

  if (!response.ok) throw new Error("Failed to save to history");
}

async function handleSaveToHistoryClick(button, entry) {
  const originalText = button.textContent;
  button.disabled    = true;

  try {
    await saveToHistory(entry);
    button.textContent = "Saved";
    loadHistory();
  } catch {
    button.textContent = "Save failed";
    button.disabled    = false;
    setTimeout(() => { button.textContent = originalText; }, 2000);
  }
}

function buildHistoryRow(entry) {
  const row = document.createElement("tr");

  [
    entry.symbol,
    entry.model_type,
    entry.date,
    entry.prediction,
    `${Math.round(entry.confidence * 100)}%`,
    entry.is_simulation ? "yes" : "no",
    entry.predicted_at,
  ].forEach((text) => {
    const cell = document.createElement("td");
    cell.textContent = text;
    row.appendChild(cell);
  });

  return row;
}

async function loadHistory() {
  const response = await fetch("/api/history");
  const entries  = await response.json();

  const tbody = document.querySelector("#history-table tbody");
  tbody.innerHTML = "";
  entries.forEach((entry) => tbody.appendChild(buildHistoryRow(entry)));
}

let simState    = null;
let lastSimResult = null;

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

  simState      = { symbol, date, modelType, featureCols: data.feature_cols, window: data.window };
  lastSimResult = null;

  document.querySelector("#simulation-panel").classList.remove("hidden");
  document.querySelector("#simulation-heading").textContent = `Simulation - ${date} - ${symbol} - ${modelType}`;

  const saveSimButton = document.querySelector("#save-simulation-button");
  saveSimButton.textContent = "Save to History";
  saveSimButton.disabled    = true;
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
  lastSimResult = result;

  document.querySelector("#baseline-prediction").textContent  = result.baseline_prediction;
  document.querySelector("#baseline-confidence").textContent  = `${Math.round(result.baseline_confidence * 100)}%`;
  document.querySelector("#simulated-prediction").textContent = result.simulated_prediction;
  document.querySelector("#simulated-confidence").textContent = `${Math.round(result.simulated_confidence * 100)}%`;
  document.querySelector("#simulation-delta").textContent     = result.delta;

  const saveSimButton = document.querySelector("#save-simulation-button");
  saveSimButton.textContent = "Save to History";
  saveSimButton.disabled    = false;
}

async function handleSaveSimulationClick(e) {
  if (!simState || !lastSimResult) return;

  await handleSaveToHistoryClick(e.currentTarget, {
    symbol:       simState.symbol,
    modelType:    simState.modelType,
    date:         simState.date,
    prediction:   lastSimResult.simulated_prediction,
    confidence:   lastSimResult.simulated_confidence,
    isSimulation: true,
  });
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

  const saveCell   = document.createElement("td");
  const saveButton = document.createElement("button");
  saveButton.textContent = "Save to History";
  saveButton.addEventListener("click", (e) => {
    e.stopPropagation();
    handleSaveToHistoryClick(e.currentTarget, {
      symbol:       document.querySelector("#stock-select").value,
      modelType:    document.querySelector("#model-select").value,
      date:         result.date,
      prediction:   result.prediction,
      confidence:   result.confidence,
      isSimulation: false,
    });
  });
  saveCell.appendChild(saveButton);
  row.appendChild(saveCell);

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

export {handleModelChange, loadStocks, handlePredictionRowClick, handleSliderInput, handlePredictClick, loadSimulationWindow, handleSimulateClick, handleSaveSimulationClick, handleResetClick, handleStartDateChange, loadHistory};
