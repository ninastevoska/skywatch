/**
 * SkyWatch AI - API Client
 *
 * Handles communication between the frontend and FastAPI backend.
 * No UI rendering or application state belongs in this file.
 */


// ============================================================
// Configuration
// ============================================================

const API_BASE_URL = "http://127.0.0.1:8000";

const API_ENDPOINTS = {
    events: "/api/events",
    recommendations: "/api/recommendations",
};


// ============================================================
// Error Handling
// ============================================================

export class ApiError extends Error {
    constructor(message, status = null) {
        super(message);

        this.name = "ApiError";
        this.status = status;
    }
}


// ============================================================
// HTTP Requests
// ============================================================

async function apiRequest(endpoint, options = {}) {
    let response;

    try {
        response = await fetch(`${API_BASE_URL}${endpoint}`, {
            ...options,
            headers: {
                "Accept": "application/json",
                ...options.headers,
            },
        });
    } catch {
        throw new ApiError(
            "Unable to connect to the SkyWatch AI server."
        );
    }

    let data;

    try {
        data = await response.json();
    } catch {
        throw new ApiError(
            "The server returned an invalid JSON response.",
            response.status
        );
    }

    if (!response.ok) {
        const message =
            typeof data.detail === "string"
                ? data.detail
                : "The request could not be completed.";

        throw new ApiError(message, response.status);
    }

    return data;
}


// ============================================================
// Astronomical Events
// ============================================================

/**
 * Retrieve astronomical events for a selected date range.
 *
 * @param {string} fromDate - Start date (YYYY-MM-DD).
 * @param {string} toDate - End date (YYYY-MM-DD).
 * @returns {Promise<object>} EventsResponse.
 */
export async function getEvents(fromDate, toDate) {
    const params = new URLSearchParams();

    if (fromDate) {
        params.set("from_date", fromDate);
    }

    if (toDate) {
        params.set("to_date", toDate);
    }

    const query = params.toString();

    const endpoint = query
        ? `${API_ENDPOINTS.events}?${query}`
        : API_ENDPOINTS.events;

    return apiRequest(endpoint);
}


// ============================================================
// AI Recommendations
// ============================================================

/**
 * Generate an AI recommendation for an astronomical event.
 *
 * @param {object} event - Selected astronomical event.
 * @param {object} preferences - Feature and user preferences.
 * @returns {Promise<object>} RecommendationResponse.
 */
export async function generateRecommendation(event, preferences) {
    return apiRequest(API_ENDPOINTS.recommendations, {
        method: "POST",
        headers: {
            "Content-Type": "application/json",
        },
        body: JSON.stringify({
            event,
            preferences,
        }),
    });
}
