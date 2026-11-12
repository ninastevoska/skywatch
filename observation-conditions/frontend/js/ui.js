function element(id) {
    return document.getElementById(id);
}


export function formatTime(value, timezone = "UTC") {
    return new Intl.DateTimeFormat("en-GB", {
        timeZone: timezone,
        hour: "2-digit",
        minute: "2-digit",
        hour12: false,
    }).format(new Date(value));
}


export function formatDateTime(value, timezone = "UTC") {
    return new Intl.DateTimeFormat("en-GB", {
        timeZone: timezone,
        day: "2-digit",
        month: "short",
        hour: "2-digit",
        minute: "2-digit",
        hour12: false,
    }).format(new Date(value));
}


function ratingClass(rating) {
    return rating.toLowerCase().replace(/\s+/g, "-");
}


function createRating(rating) {
    const badge = document.createElement("span");
    badge.className = `rating ${ratingClass(rating)}`;
    badge.textContent = rating;
    return badge;
}


export function showStatus(message, type = "") {
    const status = element("status-message");
    status.textContent = message;
    status.className = `status-message ${type}`;
}


export function showLocationResults(locations, onSelect) {
    const container = element("location-results");
    container.replaceChildren();

    if (!locations.length) {
        container.textContent = "No locations found.";
        return;
    }

    locations.forEach((location) => {
        const button = document.createElement("button");
        button.type = "button";
        button.className = "location-option";

        const name = document.createElement("strong");
        name.textContent = location.name;

        const details = document.createElement("small");
        details.textContent = [
            location.region,
            location.country,
        ].filter(Boolean).join(", ");

        button.append(name, details);
        button.addEventListener("click", () => onSelect(location));

        container.appendChild(button);
    });
}


export function showSelectedLocation(location) {
    const container = element("selected-location");

    container.textContent = (
        `Selected: ${location.name} ` +
        `(${location.latitude.toFixed(4)}, ${location.longitude.toFixed(4)})`
    );

    container.hidden = false;
    element("location-results").replaceChildren();
}


export function showForecast(forecast, timezone = "UTC") {
    const section = element("forecast-section");
    const container = element("forecast-content");

    container.replaceChildren();

    const grid = document.createElement("div");
    grid.className = "weather-grid";

    forecast.hourly.forEach((weather) => {
        const item = document.createElement("div");
        item.className = "weather-item";

        const time = document.createElement("strong");
        time.textContent = formatDateTime(weather.time, timezone);

        const details = document.createElement("p");
        details.textContent = (
            `Clouds: ${weather.cloud_cover}% | ` +
            `Rain: ${weather.precipitation_probability}% | ` +
            `Wind: ${weather.wind_speed} km/h`
        );

        item.append(time, details);
        grid.appendChild(item);
    });

    container.appendChild(grid);
    section.hidden = false;
}


export function showConditions(result, timezone = "UTC") {
    const section = element("conditions-section");
    const container = element("conditions-content");

    container.replaceChildren();

    const score = document.createElement("div");
    score.className = "score-value";
    score.textContent = `${result.score.toFixed(1)}/100`;

    const time = document.createElement("p");
    time.textContent = `Conditions at ${formatDateTime(result.time, timezone)}`;

    const reasons = document.createElement("ul");
    reasons.className = "result-list";

    result.reasons.forEach((reason) => {
        const item = document.createElement("li");
        item.textContent = reason;
        reasons.appendChild(item);
    });

    container.append(score, createRating(result.rating), time, reasons);
    section.hidden = false;
}


export function showObservationWindows(result, timezone = "UTC") {
    const section = element("windows-section");
    const container = element("windows-content");

    container.replaceChildren();

    if (!result.windows.length) {
        container.textContent = "No observation windows available.";
        section.hidden = false;
        return;
    }

    result.windows.forEach((window) => {
        const item = document.createElement("div");
        item.className = "window-item";

        const title = document.createElement("h3");
        title.textContent = (
            `${formatDateTime(window.start_time, timezone)} – ` +
            `${formatDateTime(window.end_time, timezone)}`
        );

        const description = document.createElement("p");
        description.textContent = window.is_recommended
            ? "Recommended observation window"
            : "Best available hour (conditions are not recommended)";

        const score = document.createElement("p");
        score.textContent = `Average score: ${window.average_score}/100`;

        item.append(
            title,
            createRating(window.rating),
            description,
            score
        );

        container.appendChild(item);
    });

    section.hidden = false;
}


export function showComparisonLocations(locations, onRemove) {
    const container = element("comparison-locations");
    container.replaceChildren();

    locations.forEach((location, index) => {
        const chip = document.createElement("span");
        chip.className = "location-chip";

        const name = document.createElement("span");
        name.textContent = location.name;

        const remove = document.createElement("button");
        remove.type = "button";
        remove.textContent = "×";
        remove.setAttribute("aria-label", `Remove ${location.name}`);
        remove.addEventListener("click", () => onRemove(index));

        chip.append(name, remove);
        container.appendChild(chip);
    });
}


export function clearComparisonResults() {
    element("comparison-results").replaceChildren();
}


export function showComparisonResult(result, timezone = "UTC") {
    const container = element("comparison-results");
    const item = document.createElement("div");
    item.className = "comparison-item";

    const title = document.createElement("h3");
    title.textContent = result.location.name;

    item.appendChild(title);

    if (result.error) {
        const error = document.createElement("p");
        error.textContent = result.error;
        item.appendChild(error);
    } else {
        const score = document.createElement("p");
        score.textContent = `Best score: ${result.score}/100`;

        const time = document.createElement("p");
        time.textContent = (
            `Best time: ${formatDateTime(result.best_time, timezone)}`
        );

        item.append(
            createRating(result.rating),
            score,
            time
        );
    }

    container.appendChild(item);
}


export function showComparisonStatus(message) {
    element("comparison-status").textContent = message;
}
