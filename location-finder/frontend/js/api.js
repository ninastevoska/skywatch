const API_BASE_URL = "/api";


async function request(endpoint, options = {}) {
    let response;

    try {
        response = await fetch(
            `${API_BASE_URL}${endpoint}`,
            options
        );
    } catch (error) {
        throw new Error(
            "Unable to connect to the Location Finder API."
        );
    }

    let data;

    try {
        data = await response.json();
    } catch (error) {
        throw new Error(
            "The API returned an invalid response."
        );
    }

    if (!response.ok) {
        throw new Error(
            getErrorMessage(data, response.status)
        );
    }

    return data;
}


function getErrorMessage(data, statusCode) {
    const detail = data?.detail;

    // Standard application error response.
    if (typeof detail?.message === "string") {
        return detail.message;
    }

    // Simple FastAPI error response.
    if (typeof detail === "string") {
        return detail;
    }

    // FastAPI validation errors.
    if (Array.isArray(detail)) {
        return detail
            .map(error => error.msg || "Invalid input.")
            .join(" ");
    }

    return `Request failed (HTTP ${statusCode}).`;
}


function post(endpoint, payload) {
    return request(endpoint, {
        method: "POST",
        headers: {
            "Content-Type": "application/json",
        },
        body: JSON.stringify(payload),
    });
}


export function getHealth() {
    return request("/health");
}


export function searchLocations(name, limit = 10) {
    const params = new URLSearchParams({
        name: name,
        limit: String(limit),
    });

    return request(`/locations?${params}`);
}


export function discoverLocations(payload) {
    return post("/discover", payload);
}


export function getRoute(payload) {
    return post("/route", payload);
}