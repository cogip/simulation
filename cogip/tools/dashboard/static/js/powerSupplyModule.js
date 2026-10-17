const unknown = "—";
const rails = ["p3V3", "p5V0", "p7V5", "pxVx", "p12V0"];
const pgoodRails = ["p3V3", "p5V0", "p7V5", "pxVx"]; // 12V rail has no power good signal, always shown as OK

// Display a state as an OK/fault icon followed by a text, or only unknownText if the state is unknown (null)
function setState(id, ok, text, unknownText = unknown) {
  const element = document.getElementById(id);
  if (!element) return;

  if (ok === null) {
    element.textContent = unknownText;
    return;
  }

  const img = document.createElement("img");
  img.classList.add("inline", "mr-2", "w-[20px]");
  img.src = `static/img/${ok ? "check_green_circle" : "cross_red_circle"}.svg`;
  element.replaceChildren(img, text);
}

function setText(id, text) {
  const element = document.getElementById(id);
  if (element) element.textContent = text;
}

export function openPowerSupplyModal() {
  const modal = document.getElementById("powerSupplyModal");
  modal.classList.remove("hidden");
  modal.classList.add("flex");
}

export function updateEmergencyStop(status) {
  const released = status ? !status.emergency_stop_engaged : null;
  setState("powerEmergencyStop", released, released ? "Released" : "Engaged");
  setState("emergencyStop", released, "Emergency stop", "Emergency stop");
}

export function updatePowerSource(status) {
  const battery = status ? status.battery_valid : null;
  const dcSupply = status ? status.dc_supply_valid : null;
  setState("powerBattery", battery, battery ? "Connected" : "Disconnected");
  setState("powerDcSupply", dcSupply, dcSupply ? "Connected" : "Disconnected");
}

export function updatePowerRailsStatus(status) {
  pgoodRails.forEach((rail) => {
    const pgood = status ? status[`${rail}_pgood`] : null;
    setState(`rail_${rail}_pgood`, pgood, pgood ? "OK" : "Fault");
  });
}

export function updatePowerRailsMeasures(measures) {
  rails.forEach((rail) => {
    const measure = measures ? measures[rail] : null;
    setText(`rail_${rail}_voltage`, measure ? (measure.voltage_mv / 1000).toFixed(2) : unknown);
    setText(`rail_${rail}_current`, measure ? measure.current_ma.toFixed(0) : unknown);
    setText(`rail_${rail}_power`, measure ? ((measure.voltage_mv * measure.current_ma) / 1e6).toFixed(2) : unknown);
  });
}

// Back to unknown states, used when the connection with the server is lost
export function reset() {
  updateEmergencyStop(null);
  updatePowerSource(null);
  updatePowerRailsStatus(null);
  updatePowerRailsMeasures(null);
}
