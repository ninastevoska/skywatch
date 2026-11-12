import {
    searchLocations,
    getWeatherForecast,
    evaluateConditions,
    findBestObservationWindows,
    streamLocationComparison,
} from "./api.js";

import {
    showStatus,
    showLocationResults,
    showSelectedLocation,
    showForecast,
    showConditions,
    showObservationWindows,
    showComparisonLocations,
    clearComparisonResults,
    showComparisonResult,
    showComparisonStatus,
} from "./ui.js";


const searchInput = document.getElementById("location-search");
const dateInput = document.getElementById("observation-date");
const hourInput = document.getElementById("observation-hour");

let selectedLocation = null;
let comparisonLocations = [];
let searchTimer = null;
let requestVersion = 0;
let comparisonController = null;


function dateString(date) {
    const year = date.getFullYear();
    const month = String(date.getMonth() + 1).padStart(2, "0");
    const day = String(date.getDate()).padStart(2, "0");

    return `${year}-${month}-${day}`;
}


function addDays(date, days) {
    const result = new Date(`${date}T12:00:00Z`);
    result.setUTCDate(result.getUTCDate() + days);
    return result.toISOString().slice(0, 10);
}


function initializeDate() {
    const today = new Date();
    const firstDate = dateString(today);
    const lastDate = addDays(firstDate, 14);

    dateInput.min = firstDate;
    dateInput.max = lastDate;
    dateInput.value = firstDate;
}


function updateAvailableHours() {
    const isLastDay = dateInput.value === dateInput.max;

    for (const option of hourInput.options) {
        const isNextDayHour = Number(option.value) < 18;
        option.disabled = isLastDay && isNextDayHour;
    }

    if (isLastDay && Number(hourInput.value) < 18) {
        hourInput.value = "21";
    }
}


// Convert local observation time to a UTC timestamp.
function localToUTC(date, hour, timezone) {
    const wallTime = new Date(`${date}T${String(hour).padStart(2, "0")}:00:00Z`);

    const formatter = new Intl.DateTimeFormat("en-GB", {
        timeZone: timezone,
        timeZoneName: "longOffset",
    });

    let timestamp = wallTime.getTime();

    for (let attempt = 0; attempt < 3; attempt++) {
        const parts = formatter.formatToParts(new Date(timestamp));
        const offset = parts.find((part) => part.type === "timeZoneName").value;

        const match = offset.match(/^GMT([+-])(\d{2}):(\d{2})$/);

        if (!match) {
            if (offset === "GMT") {
                return new Date(wallTime.getTime()).toISOString();
            }
            throw new Error("Unable to determine the location's time zone.");
        }

        const direction = match[1] === "+" ? 1 : -1;
        const minutes = direction * (
            Number(match[2]) * 60 + Number(match[3])
        );

        const corrected = wallTime.getTime() - minutes * 60_000;

        if (corrected === timestamp) {
            break;
        }

        timestamp = corrected;
    }

    return new Date(timestamp).toISOString();
}



function getObservationTimes(location) {
    const timezone = location.timezone || "UTC";
    const date = dateInput.value;
    const hour = Number(hourInput.value);
    const isLastDay = date === dateInput.max;

    const selectedDate = hour < 18 ? addDays(date, 1) : date;

    const startTime = localToUTC(date, 18, timezone);
    const endTime = localToUTC(
        addDays(date, 1),
        isLastDay ? 0 : 6,
        timezone
    );
    const selectedTime = localToUTC(selectedDate, hour, timezone);

    return { startTime, endTime, selectedTime };
}



function hideResults() {
    for (const id of [
        "forecast-section",
        "conditions-section",
        "windows-section",
    ]) {
        document.getElementById(id).hidden = true;
    }
}


async function updateForecast() {
    const version = ++requestVersion;
    hideResults();

    if (!selectedLocation) {
        showStatus("Search for and select an observation location.");
        return;
    }

    try {
        const { startTime, endTime, selectedTime } =
            getObservationTimes(selectedLocation);

        showStatus("Loading observation conditions...");

        const [forecast, conditions, windows] = await Promise.all([
            getWeatherForecast(selectedLocation, startTime, endTime),
            evaluateConditions(selectedLocation, selectedTime),
            findBestObservationWindows(selectedLocation, startTime, endTime),
        ]);

        if (version !== requestVersion) {
            return;
        }

        const timezone = selectedLocation.timezone || "UTC";

        showForecast(forecast, timezone);
        showConditions(conditions, timezone);
        showObservationWindows(windows, timezone);

        showStatus("Observation conditions updated.", "success");
    } catch (error) {
        if (version === requestVersion) {
            showStatus(error.message, "error");
        }
    }
}


function stopComparison() {
    if (comparisonController) {
        comparisonController.abort();
        comparisonController = null;
    }
}


async function updateComparison() {
    stopComparison();
    clearComparisonResults();

    if (comparisonLocations.length < 2) {
        showComparisonStatus(
            "Select at least two locations to start a comparison."
        );
        return;
    }

    comparisonController = new AbortController();
    const controller = comparisonController;

    try {
        // Compare all locations within the same UTC interval.
        const { startTime, endTime } =
            getObservationTimes(selectedLocation);

        showComparisonStatus("Comparing observation locations...");

        let received = 0;

        await streamLocationComparison(
            comparisonLocations,
            startTime,
            endTime,
            (result) => {
                if (controller.signal.aborted) {
                    return;
                }

                const location = comparisonLocations.find(
                    (item) =>
                        item.name === result.location.name &&
                        item.latitude === result.location.latitude &&
                        item.longitude === result.location.longitude
                );

                showComparisonResult(
                    result,
                    location?.timezone || "UTC"
                );

                received++;
                showComparisonStatus(
                    `Received ${received} of ${comparisonLocations.length} results.`
                );
            },
            controller.signal
        );

        if (!controller.signal.aborted) {
            showComparisonStatus("Location comparison completed.");
        }
    } catch (error) {
        if (error.name !== "AbortError") {
            showComparisonStatus(`Comparison failed: ${error.message}`);
        }
    }
}


function addComparisonLocation(location) {
    const exists = comparisonLocations.some(
        (item) =>
            item.latitude === location.latitude &&
            item.longitude === location.longitude
    );

    if (!exists && comparisonLocations.length < 10) {
        comparisonLocations.push(location);
    }

    showComparisonLocations(comparisonLocations, removeComparisonLocation);
    updateComparison();
}


function removeComparisonLocation(index) {
    comparisonLocations.splice(index, 1);

    showComparisonLocations(comparisonLocations, removeComparisonLocation);
    updateComparison();
}


function selectLocation(location) {
    selectedLocation = location;

    searchInput.value = location.name;

    showSelectedLocation(location);
    addComparisonLocation(location);
    updateForecast();
}


searchInput.addEventListener("input", () => {
    clearTimeout(searchTimer);

    const query = searchInput.value.trim();

    if (query.length < 2) {
        showLocationResults([], () => { });
        return;
    }

    searchTimer = setTimeout(async () => {
        try {
            const locations = await searchLocations(query);

            if (searchInput.value.trim() === query) {
                showLocationResults(locations, selectLocation);
            }
        } catch (error) {
            showStatus(error.message, "error");
        }
    }, 300);
});


document.getElementById("use-coordinates").addEventListener("click", () => {

    const latitudeInput = document.getElementById("latitude").value.trim();
    const longitudeInput = document.getElementById("longitude").value.trim();

    if (!latitudeInput || !longitudeInput) {
        showStatus("Please enter both latitude and longitude.", "error");
        return;
    }

    const latitude = Number(latitudeInput);
    const longitude = Number(longitudeInput);


    if (
        !Number.isFinite(latitude) ||
        !Number.isFinite(longitude) ||
        latitude < -90 ||
        latitude > 90 ||
        longitude < -180 ||
        longitude > 180
    ) {
        showStatus("Please enter valid coordinates.", "error");
        return;
    }

    selectLocation({
        name: `Coordinates (${latitude}, ${longitude})`,
        latitude,
        longitude,
        timezone: "UTC",
    });
});



dateInput.addEventListener("change", () => {
    updateAvailableHours();
    updateForecast();
    updateComparison();
});



hourInput.addEventListener("change", updateForecast);



initializeDate();
updateAvailableHours();

showStatus("Search for and select an observation location.");

showComparisonStatus("Select at least two locations to compare conditions.");
