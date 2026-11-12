const API_BASE = "/api";


async function request(path, options = {}) {
    const response = await fetch(`${API_BASE}${path}`, options);

    if (!response.ok) {
        let message = `Request failed (${response.status}).`;

        try {
            const error = await response.json();
            message = error.detail || message;
        } catch {
            // Keep the default error message.
        }

        throw new Error(
            typeof message === "string" ? message : JSON.stringify(message)
        );
    }

    return response.json();
}


function post(path, data) {
    return request(path, {
        method: "POST",
        headers: {
            "Content-Type": "application/json",
        },
        body: JSON.stringify(data),
    });
}


export async function searchLocations(query) {
    return request(`/locations?query=${encodeURIComponent(query)}`);
}


export async function getWeatherForecast(location, startTime, endTime) {
    return post("/forecast", {
        location,
        start_time: startTime,
        end_time: endTime,
    });
}


export async function evaluateConditions(location, time) {
    return post("/conditions", {
        location,
        time,
    });
}


export async function findBestObservationWindows(
    location,
    startTime,
    endTime
) {
    return post("/windows", {
        location,
        start_time: startTime,
        end_time: endTime,
    });
}


export async function streamLocationComparison(
    locations,
    startTime,
    endTime,
    onLocation,
    signal
) {
    const response = await fetch(`${API_BASE}/compare/stream`, {
        method: "POST",
        headers: {
            "Content-Type": "application/json",
            "Accept": "text/event-stream",
        },
        body: JSON.stringify({
            locations,
            start_time: startTime,
            end_time: endTime,
        }),
        signal,
    });

    if (!response.ok) {
        throw new Error(`Comparison request failed (${response.status}).`);
    }

    if (!response.body) {
        throw new Error("Streaming is not supported by this browser.");
    }

    const reader = response.body.getReader();
    const decoder = new TextDecoder();
    let buffer = "";
    let completed = false;

    function processEvent(block) {
        let eventType = "message";
        const dataLines = [];

        for (const line of block.split("\n")) {
            if (line.startsWith("event:")) {
                eventType = line.slice(6).trim();
            } else if (line.startsWith("data:")) {
                dataLines.push(line.slice(5).trimStart());
            }
        }

        if (!dataLines.length) {
            return;
        }

        const data = JSON.parse(dataLines.join("\n"));

        if (eventType === "location") {
            onLocation(data);
        } else if (eventType === "error") {
            throw new Error(data.message || "Location comparison failed.");
        } else if (eventType === "complete") {
            completed = true;
        }
    }

    try {
        while (true) {
            const { value, done } = await reader.read();

            if (done) {
                break;
            }

            buffer += decoder.decode(value, { stream: true });
            buffer = buffer.replace(/\r\n/g, "\n");

            let separator;

            while ((separator = buffer.indexOf("\n\n")) !== -1) {
                const block = buffer.slice(0, separator);
                buffer = buffer.slice(separator + 2);
                processEvent(block);
            }
        }

        buffer += decoder.decode();

        if (buffer.trim()) {
            processEvent(buffer.trim());
        }

        if (!completed) {
            throw new Error("Comparison stream ended unexpectedly.");
        }
    } finally {
        reader.releaseLock();
    }
}
