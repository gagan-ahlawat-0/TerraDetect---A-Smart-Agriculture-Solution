document.addEventListener("DOMContentLoaded", function () {
  // DOM Elements
  const elements = {
    form: document.getElementById("cropForm"),
    resultContainer: document.getElementById("resultContainer"),
    errorContainer: document.getElementById("errorContainer"),
    errorText: document.getElementById("errorText"),
    loadingIndicator: document.getElementById("loadingIndicator"),
    result: document.getElementById("result"),
    weatherParams: document.getElementById("weatherParams"),
    cropNameSection: document.getElementById("cropNameSection"),
    soilTypeSection: document.getElementById("soilTypeSection"),
    formTitle: document.getElementById("formTitle"),
    submitButton: document.getElementById("submitButton"),
    sensorDataSection: document.getElementById("sensorDataSection"),
  };

  // Application state
  const state = {
    mode: "crop",
    weatherSource: "manual",
    isLoading: false,
    sensorData: {},
  };

  // Initialize the application
  init();

  function init() {
    setupEventListeners();
    updateUI();
  }

  function setupEventListeners() {
    // Mode switching
    const bestCropBtn = document.getElementById("bestCropMode");
    if (bestCropBtn) bestCropBtn.addEventListener("click", () => setMode("crop"));
    const cropSuitabilityBtn = document.getElementById("cropSuitabilityMode");
    if (cropSuitabilityBtn) cropSuitabilityBtn.addEventListener("click", () => setMode("suitability"));
    const fertilizerBtn = document.getElementById("fertilizerMode");
    if (fertilizerBtn) fertilizerBtn.addEventListener("click", () => setMode("fertilizer"));

    // Weather source selection
    const manualWeatherBtn = document.getElementById("manualWeatherBtn");
    if (manualWeatherBtn) manualWeatherBtn.addEventListener("click", () => setWeatherSource("manual"));
    const apiWeatherBtn = document.getElementById("apiWeatherBtn");
    if (apiWeatherBtn) apiWeatherBtn.addEventListener("click", () => setWeatherSource("api"));
    const sensorWeatherBtn = document.getElementById("sensorWeatherBtn");
    if (sensorWeatherBtn) sensorWeatherBtn.addEventListener("click", () => setWeatherSource("sensor"));

    // Sensor data button
    const useSensorDataBtn = document.getElementById("useSensorDataBtn");
    if (useSensorDataBtn) useSensorDataBtn.addEventListener("click", useSensorData);

    // Form submission
    if (elements.form) elements.form.addEventListener("submit", handleFormSubmit);

    // Reset button
    const resetBtn = document.getElementById("resetButton");
    if (resetBtn) resetBtn.addEventListener("click", resetForm);

    // Forcibly prevent default on form
    if (elements.form) {
      elements.form.onsubmit = function(e) {
        if (e) e.preventDefault();
        return false;
      };
    }
  }

  function showMessage(msg) {
    const messageDiv = document.getElementById("message");
    if (messageDiv) {
      messageDiv.textContent = msg;
      messageDiv.style.display = "block";
    }
  }
  function clearMessage() {
    const messageDiv = document.getElementById("message");
    if (messageDiv) {
      messageDiv.textContent = "";
      messageDiv.style.display = "none";
    }
  }

  function setMode(mode) {
    state.mode = mode;

    const modeIdMap = {
      crop: "bestCropMode",
      suitability: "cropSuitabilityMode",
      fertilizer: "fertilizerMode",
    };

    document
      .querySelectorAll("#bestCropMode, #cropSuitabilityMode, #fertilizerMode")
      .forEach((btn) => btn.classList.remove("active"));

    // Add 'active' class to the currently selected mode button
    const activeButton = document.getElementById(modeIdMap[mode]);
    if (activeButton) {
      activeButton.classList.add("active");
    } else {
      console.warn(`No button found for mode: ${mode}`);
    }

    // Update the UI based on selected mode
    updateUI();
  }

  function setWeatherSource(source) {
    state.weatherSource = source;

    if (source === "api") {
      fetchWeatherAPI();
    } else if (source === "sensor") {
      showLoading(true);
      showMessage("Triggering sensors...");

      fetch("/api/thingspeak/trigger", { method: "POST" })
        .then((res) => res.json())
        .then(() => {
          showMessage("Waiting 150 seconds while sensor collects data...");

          setTimeout(() => {
            clearMessage();
            fetchSensorData();
          }, 150000); // 150 seconds
        })
        .catch((err) => {
          showError("Failed to trigger sensor.");
          clearMessage();
          showLoading(false);
          console.error(err);
        });
    }
  }

  async function fetchSensorData() {
    try {
      elements.sensorDataSection.style.display = "none";
      showLoading(true);

      const response = await fetch("/api/thingspeak/fetch");

      if (!response.ok) {
        throw new Error("Failed to fetch data from ThingSpeak");
      }

      const result = await response.json();

      if (result.status === "error") {
        throw new Error(result.message);
      }

      // Store the sensor data
      state.sensorData = result.data;

      // Display sensor data in sidebar
      document.getElementById("sensorTempDisplay").textContent =
        result.data.temperature?.toFixed(1) || "--";
      document.getElementById("sensorHumidityDisplay").textContent =
        result.data.humidity?.toFixed(1) || "--";
      document.getElementById("sensorPhDisplay").textContent =
        result.data.ph?.toFixed(1) || "--";
      document.getElementById("sensorNDisplay").textContent =
        result.data.N?.toFixed(1) || "--";
      document.getElementById("sensorPDisplay").textContent =
        result.data.P?.toFixed(1) || "--";
      document.getElementById("sensorKDisplay").textContent =
        result.data.K?.toFixed(1) || "--";
      document.getElementById("sensorMoistureDisplay").textContent =
        result.data.moisture?.toFixed(1) || "--";
      document.getElementById("sensorECDisplay").textContent =
        result.data.ec?.toFixed(1) || "--";

      elements.sensorDataSection.style.display = "block";
    } catch (error) {
      showError("Could not fetch sensor data: " + error.message);
    } finally {
      showLoading(false);
    }
  }

  function useSensorData() {
    if (Object.keys(state.sensorData).length === 0) {
      showError("No sensor data available. Please fetch sensor data first.");
      return;
    }

    // Fill form with sensor data
    const data = state.sensorData;

    if (data.temperature)
      document.getElementById("temperature").value =
        data.temperature.toFixed(1);
    if (data.humidity)
      document.getElementById("humidity").value = data.humidity.toFixed(1);
    if (data.ph) document.getElementById("ph").value = data.ph.toFixed(1);
    if (data.N) document.getElementById("N").value = data.N.toFixed(1);
    if (data.P) document.getElementById("P").value = data.P.toFixed(1);
    if (data.K) document.getElementById("K").value = data.K.toFixed(1);

    // Switch to manual mode to allow edits
    setWeatherSource("manual");
  }

  async function fetchWeatherAPI() {
    const apiKey = "3e06f57b86be4a3eb4673307251604";

    if (!navigator.geolocation) {
      showError("Geolocation is not supported by your browser");
      return;
    }

    showLoading(true);

    navigator.geolocation.getCurrentPosition(
      async (position) => {
        const latitude = position.coords.latitude;
        const longitude = position.coords.longitude;

        try {
          const response = await fetch(
            `https://api.weatherapi.com/v1/current.json?key=${apiKey}&q=${latitude},${longitude}`
          );

          if (!response.ok) {
            throw new Error(`HTTP error! Status: ${response.status}`);
          }

          const data = await response.json();

          // Get current conditions
          document.getElementById("temperature").value =
            data.current.temp_c.toFixed(1);
          document.getElementById("humidity").value =
            data.current.humidity.toFixed(1);

          const annualRainfall = data.current.precip_mm * 365; // Rough estimation
          document.getElementById("rainfall").value = Math.max(
            100,
            annualRainfall
          ).toFixed(0);

          showLoading(false);
        } catch (error) {
          showError(`Failed to fetch weather data: ${error.message}`);
          showLoading(false);
        }
      },
      (error) => {
        showError(`Geolocation error: ${error.message}`);
        showLoading(false);
      }
    );
  }

  function updateUI() {
    // Update form based on mode
    switch (state.mode) {
      case "crop":
        elements.formTitle.textContent = "Find the Best Crop";
        elements.weatherParams.style.display = "block";
        elements.cropNameSection.style.display = "none";
        elements.soilTypeSection.style.display = "none";
        elements.submitButton.innerHTML =
          '<i class="fas fa-search"></i> Recommend Crop';
        break;

      case "suitability":
        elements.formTitle.textContent = "Check Crop Suitability";
        elements.weatherParams.style.display = "block";
        elements.cropNameSection.style.display = "block";
        elements.soilTypeSection.style.display = "none";
        elements.submitButton.innerHTML =
          '<i class="fas fa-check-circle"></i> Check Suitability';
        break;

      case "fertilizer":
        elements.formTitle.textContent = "Fertilizer Recommendation";
        elements.weatherParams.style.display = "none";
        elements.cropNameSection.style.display = "block";
        elements.soilTypeSection.style.display = "block";
        elements.submitButton.innerHTML =
          '<i class="fas fa-flask"></i> Recommend Fertilizer';
        break;
    }

    // Clear previous results
    elements.resultContainer.style.display = "none";
    elements.errorContainer.style.display = "none";
  }

  async function handleFormSubmit(event) {
    console.log("Form submit intercepted by JS");
    if (event) event.preventDefault();
    else return false;

    // Reset previous results/errors
    elements.resultContainer.style.display = "none";
    elements.errorContainer.style.display = "none";

    // Validate form
    if (!validateForm()) return;

    // Show loading indicator
    showLoading(true);

    try {
      // Prepare form data
      const formData = {
        mode: state.mode,
        N: parseFloat(document.getElementById("N").value),
        P: parseFloat(document.getElementById("P").value),
        K: parseFloat(document.getElementById("K").value),
        ph: parseFloat(document.getElementById("ph").value),
        use_sensor_data: state.weatherSource === "sensor",
      };

      // Add mode-specific data
      if (state.mode === "crop" || state.mode === "suitability") {
        formData.temperature = parseFloat(
          document.getElementById("temperature").value
        );
        formData.humidity = parseFloat(
          document.getElementById("humidity").value
        );
        formData.rainfall = parseFloat(
          document.getElementById("rainfall").value
        );
      }

      if (state.mode === "suitability" || state.mode === "fertilizer") {
        formData.crop_name = document.getElementById("cropName").value;

        if (!formData.crop_name) {
          showError("Please enter a crop name");
          showLoading(false);
          return;
        }
      }

      if (state.mode === "fertilizer") {
        formData.soil = document.getElementById("soilType").value;
        formData.moisture = state.sensorData.moisture || 40; // Default to 40 if not available
        formData.ec = state.sensorData.ec || 0; // Default to 0 if not available
      }

      // Send data to the server
      const response = await fetch("/predict", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(formData),
      });

      let result;
      try {
        result = await response.json();
      } catch (jsonErr) {
        showError("Server returned invalid JSON. Check backend logs.");
        console.error("Invalid JSON response:", jsonErr);
        showLoading(false);
        return;
      }

      console.log("/predict response:", result);

      if (!response.ok || result.error) {
        showError(result.error || "Server error occurred");
        showLoading(false);
        return;
      }

      if (!result || Object.keys(result).length === 0) {
        showError("No recommendation received. Please try again.");
        showLoading(false);
        return;
      }

      // Display the result
      displayResult(result);
    } catch (error) {
      showError(error.message || "Unknown error occurred");
      console.error("handleFormSubmit error:", error);
    } finally {
      showLoading(false);
    }
  }

  function validateForm() {
    // Basic validation
    const requiredFields = ["N", "P", "K", "ph"];

    if (state.mode === "crop" || state.mode === "suitability") {
      requiredFields.push("temperature", "humidity", "rainfall");
    }

    if (state.mode === "suitability" || state.mode === "fertilizer") {
      requiredFields.push("cropName");
    }

    for (const field of requiredFields) {
      const element = document.getElementById(field);
      if (!element || element.value.trim() === "") {
        showError(
          `Please fill in the ${field
            .replace(/([A-Z])/g, " $1")
            .toLowerCase()} field`
        );
        return false;
      }
    }

    return true;
  }

  function displayResult(data) {
    const resultDiv = elements.result;
    let resultHTML = "";

    switch (state.mode) {
      case "crop":
        resultHTML = `
            <div class="recommendation-card">
              <h4><i class="fas fa-seedling"></i> Recommended Crop: <strong>${data.crop}</strong></h4>
              <p>Confidence: ${data.confidence}%</p>              
            </div>
          `;
        break;

      case "suitability":
        // Generate suitability bar color based on score
        let barColor = "#e74c3c"; // Red for low suitability
        if (data.suitability > 75) {
          barColor = "#2ecc71"; // Green for high suitability
        } else if (data.suitability > 50) {
          barColor = "#f39c12"; // Orange for medium suitability
        }

        resultHTML = `
            <div class="recommendation-card">
              <h4><i class="fas fa-check-circle"></i> Suitability Analysis for ${data.crop}</h4>
              
              <div class="suitability-bar">
                <div class="suitability-progress" style="width: ${data.suitability}%; background-color: ${barColor};">
                  ${data.suitability}%
                </div>
              </div>
              
              <h4>Recommendations:</h4>
              
              <div class="table-responsive">
                <table class="table table-striped">
                  <thead>
                    <tr>
                      <th>Parameter</th>
                      <th>Recommended Value</th>
                      <th>Observed Value</th>
                      <th>Remarks</th>
                    </tr>
                  </thead>
                  <tbody>
        `;

        // Add table rows from the table_data
        if (data.table_data && data.table_data.length > 0) {
          data.table_data.forEach((row) => {
            // Determine row color based on whether the parameter is optimal
            const rowClass =
              row.remarks === "Optimal" ? "table-success" : "table-warning";

            resultHTML += `
              <tr class="${rowClass}">
                <td>${row.parameter}</td>
                <td>${row.recommended}</td>
                <td>${row.observed}</td>
                <td>${row.remarks}</td>
              </tr>
            `;
          });
        } else {
          resultHTML += `
            <tr>
              <td colspan="4">No recommendation data available</td>
            </tr>
          `;
        }

        resultHTML += `
                  </tbody>
                </table>
              </div>
            </div>
          `;
        break;

      case "fertilizer":
        resultHTML = `
            <div class="recommendation-card">
              <h4><i class="fas fa-flask"></i> Recommended Fertilizer: <strong>${data.fertilizer}</strong></h4>
              <p><strong>Composition:</strong> ${data.composition}</p>
              <p><strong>Application:</strong> ${data.application}</p>
              
              <div class="fertilizer-details">
                <h4>Nutrient Analysis</h4>
          `;

        // Only show deficiencies if they exist
        if (
          data.deficiencies.N > 0 ||
          data.deficiencies.P > 0 ||
          data.deficiencies.K > 0
        ) {
          resultHTML += `<p><strong>Deficiencies Detected:</strong></p><ul>`;

          if (data.deficiencies.N > 0) {
            resultHTML += `<li><i class="fas fa-exclamation-triangle" style="color: #e74c3c;"></i> ${data.nitrogen_advice}</li>`;
          }

          if (data.deficiencies.P > 0) {
            resultHTML += `<li><i class="fas fa-exclamation-triangle" style="color: #e74c3c;"></i> ${data.phosphorus_advice}</li>`;
          }

          if (data.deficiencies.K > 0) {
            resultHTML += `<li><i class="fas fa-exclamation-triangle" style="color: #e74c3c;"></i> ${data.potassium_advice}</li>`;
          }

          resultHTML += `</ul>`;
        } else {
          resultHTML += `<p><i class="fas fa-check-circle" style="color: #2ecc71;"></i> Your soil has adequate nutrient levels for ${
            data.crop_name || "the selected crop"
          }.</p>`;
        }

        resultHTML += `
              </div>
            </div>
          `;
        break;
    }

    resultDiv.innerHTML = resultHTML;
    elements.resultContainer.style.display = "block";

    // Scroll to the result
    elements.resultContainer.scrollIntoView({ behavior: "smooth" });
  }
  
  function showLoading(isLoading) {
    state.isLoading = isLoading;
    elements.loadingIndicator.style.display = isLoading ? "block" : "none";
    elements.submitButton.disabled = isLoading;
  }

  function showError(message) {
    elements.errorText.textContent = message;
    elements.errorContainer.style.display = "block";

    // Scroll to the error
    elements.errorContainer.scrollIntoView({ behavior: "smooth" });
  }

  function resetForm() {
    elements.form.reset();
    elements.resultContainer.style.display = "none";
    elements.errorContainer.style.display = "none";
  }

  // Global error handler for debugging
  window.onerror = function(message, source, lineno, colno, error) {
    console.error('Global JS error:', message, 'at', source + ':' + lineno + ':' + colno, error);
  };
});
