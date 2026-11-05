/**
 * SkyWatch AI - Application Controller
 *
 * Responsibilities:
 * - Initialize the application.
 * - Load astronomical events.
 * - Handle event selection.
 * - Manage AI feature selection.
 * - Submit recommendation requests.
 * - Coordinate API calls and UI updates.
 */

import {
    getEvents,
    generateRecommendation,
} from "./api.js";

import {
    renderEvents,
    renderEventDetails,
    renderFeatureForm,
    getFeaturePreferences,
    renderRecommendation,
    setLoading,
    showError,
    clearError,
    clearRecommendation,
} from "./ui.js";


// ============================================================
// Application State
// ============================================================

const state = {
    events: [],
    selectedEvent: null,
    selectedFeature: null,
    recommendationRequestId: 0,
    eventsRequestId: 0,
    isGenerating: false,
};


// ============================================================
// DOM Elements
// ============================================================

const elements = {
    dateFilterForm: document.getElementById("date-filter-form"),
    fromDate: document.getElementById("from-date"),
    toDate: document.getElementById("to-date"),

    eventsGrid: document.getElementById("events-grid"),
    eventsEmpty: document.getElementById("events-empty"),

    detailsSection: document.getElementById(
        "event-details-section"
    ),
    backButton: document.getElementById("back-to-events"),

    featureButtons: document.querySelectorAll(
        ".feature-card"
    ),
    featureFormContainer: document.getElementById(
        "feature-form-container"
    ),
    recommendationForm: document.getElementById(
        "recommendation-form"
    ),
    generateButton: document.getElementById(
        "generate-button"
    ),
    recommendationResult: document.getElementById(
        "recommendation-result"
    ),
};


// ============================================================
// Date Utilities
// ============================================================

function formatLocalDate(date) {
    const year = date.getFullYear();
    const month = String(date.getMonth() + 1).padStart(2, "0");
    const day = String(date.getDate()).padStart(2, "0");

    return `${year}-${month}-${day}`;
}


function initializeDateRange() {
    const today = new Date();

    const endDate = new Date(today);
    endDate.setDate(endDate.getDate() + 30);

    elements.fromDate.value = formatLocalDate(today);
    elements.toDate.value = formatLocalDate(endDate);
}


function validateDateRange(fromDate, toDate) {
    if (!fromDate || !toDate) {
        throw new Error("Please select both dates.");
    }

    const start = new Date(`${fromDate}T00:00:00Z`);
    const end = new Date(`${toDate}T00:00:00Z`);

    if (
        Number.isNaN(start.getTime()) ||
        Number.isNaN(end.getTime())
    ) {
        throw new Error("Please enter valid dates.");
    }

    if (start > end) {
        throw new Error(
            "The start date must not be after the end date."
        );
    }

    const days = (end - start) / (1000 * 60 * 60 * 24);

    if (days > 365) {
        throw new Error(
            "The selected date range cannot exceed 365 days."
        );
    }
}


// ============================================================
// Load Astronomical Events
// ============================================================

async function loadEvents() {
    const fromDate = elements.fromDate.value;
    const toDate = elements.toDate.value;

    clearError("events-error");

    try {
        validateDateRange(fromDate, toDate);
    } catch (error) {
        showError("events-error", error.message);
        return;
    }

    const requestId = ++state.eventsRequestId;

    setLoading("events-loading", true);

    elements.eventsGrid.replaceChildren();
    elements.eventsEmpty.hidden = true;

    resetSelectedEvent();

    try {
        const response = await getEvents(fromDate, toDate);

        if (requestId !== state.eventsRequestId) {
            return;
        }

        state.events = response.events;

        if (state.events.length === 0) {
            elements.eventsEmpty.hidden = false;
            return;
        }

        renderEvents(state.events, selectEvent);

    } catch (error) {
        if (requestId !== state.eventsRequestId) {
            return;
        }

        showError(
            "events-error",
            error.message || "Unable to load events."
        );

    } finally {
        if (requestId === state.eventsRequestId) {
            setLoading("events-loading", false);
        }
    }
}


// ============================================================
// Event Selection
// ============================================================

function selectEvent(event) {
    // Invalidate any pending recommendation response.
    state.recommendationRequestId++;

    state.selectedEvent = event;
    state.selectedFeature = null;

    renderEventDetails(event);

    resetFeatureSelection();
    clearRecommendation();

    setLoading("recommendation-loading", false);
    setGenerating(false);

    elements.detailsSection.hidden = false;

    elements.detailsSection.scrollIntoView({
        behavior: "smooth",
        block: "start",
    });
}


function resetSelectedEvent() {
    state.recommendationRequestId++;

    state.selectedEvent = null;
    state.selectedFeature = null;

    elements.detailsSection.hidden = true;

    resetFeatureSelection();
    clearRecommendation();

    setLoading("recommendation-loading", false);
    setGenerating(false);
}


function backToEvents() {
    resetSelectedEvent();

    document.getElementById("events-heading").scrollIntoView({
        behavior: "smooth",
        block: "start",
    });
}


// ============================================================
// AI Feature Selection
// ============================================================

function selectFeature(feature) {
    if (!state.selectedEvent) {
        return;
    }

    // Prevent an older AI response from appearing in a new feature.
    state.recommendationRequestId++;

    state.selectedFeature = feature;

    resetFeatureSelection();
    clearRecommendation();

    setLoading("recommendation-loading", false);
    setGenerating(false);

    renderFeatureForm(feature);

    for (const button of elements.featureButtons) {
        const isActive = button.dataset.feature === feature;

        button.classList.toggle("active", isActive);

        button.setAttribute(
            "aria-pressed",
            String(isActive)
        );
    }

    elements.featureFormContainer.scrollIntoView({
        behavior: "smooth",
        block: "nearest",
    });
}


function resetFeatureSelection() {
    elements.featureFormContainer.hidden = true;

    for (const button of elements.featureButtons) {
        button.classList.remove("active");
        button.setAttribute("aria-pressed", "false");
    }
}


// ============================================================
// Generate AI Recommendation
// ============================================================

async function handleRecommendationSubmit() {
    if (
        !state.selectedEvent ||
        !state.selectedFeature ||
        state.isGenerating
    ) {
        return;
    }

    const event = state.selectedEvent;
    const feature = state.selectedFeature;

    clearRecommendation();

    let preferences;

    try {
        preferences = getFeaturePreferences(feature);
    } catch (error) {
        showError(
            "recommendation-error",
            error.message || "Invalid form input."
        );
        return;
    }

    const requestId = ++state.recommendationRequestId;

    setGenerating(true);
    setLoading("recommendation-loading", true);

    try {
        const response = await generateRecommendation(
            event,
            preferences
        );

        if (requestId !== state.recommendationRequestId) {
            return;
        }

        renderRecommendation(response);

        elements.recommendationResult.scrollIntoView({
            behavior: "smooth",
            block: "start",
        });

    } catch (error) {
        if (requestId !== state.recommendationRequestId) {
            return;
        }

        showError(
            "recommendation-error",
            error.message ||
                "Unable to generate the AI recommendation."
        );

    } finally {
        if (requestId === state.recommendationRequestId) {
            setLoading("recommendation-loading", false);
            setGenerating(false);
        }
    }
}


function setGenerating(isGenerating) {
    state.isGenerating = isGenerating;

    elements.generateButton.disabled = isGenerating;

    elements.generateButton.textContent = isGenerating
        ? "Generating..."
        : "Generate AI Recommendation";
}


// ============================================================
// Event Listeners
// ============================================================

function registerEventListeners() {
    elements.dateFilterForm.addEventListener(
        "submit",
        async (event) => {
            event.preventDefault();
            await loadEvents();
        }
    );

    elements.backButton.addEventListener(
        "click",
        backToEvents
    );

    for (const button of elements.featureButtons) {
        button.setAttribute("aria-pressed", "false");

        button.addEventListener("click", () => {
            selectFeature(button.dataset.feature);
        });
    }

    elements.recommendationForm.addEventListener(
        "submit",
        async (event) => {
            event.preventDefault();
            await handleRecommendationSubmit();
        }
    );
}


// ============================================================
// Application Initialization
// ============================================================

async function initializeApp() {
    initializeDateRange();
    registerEventListeners();

    await loadEvents();
}


// ============================================================
// Start Application
// ============================================================

initializeApp();
