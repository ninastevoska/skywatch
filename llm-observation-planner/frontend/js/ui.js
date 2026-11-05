/**
 * SkyWatch AI - User Interface
 *
 * Responsibilities:
 * - Render astronomical event cards.
 * - Display selected event details.
 * - Build forms for the four AI features.
 * - Read user preferences from the active form.
 * - Render structured AI recommendations.
 *
 * This module does not make HTTP requests.
 */


// ============================================================
// Configuration
// ============================================================

const FEATURE_TITLES = {
    locations: "Find Observation Locations",
    equipment: "Recommend Equipment",
    plan: "Create Observation Plan",
    facts: "Explore Event Facts",
};

const FEATURE_FIELDS = {
    locations: [
        {
            name: "origin",
            label: "Starting location",
            type: "text",
            placeholder: "e.g. Ljubljana",
            value: "Ljubljana",
            minLength: 2,
            maxLength: 150,
        },
        {
            name: "max_distance_km",
            label: "Maximum distance (km)",
            type: "number",
            value: 50,
            min: 1,
            max: 500,
        },
        {
            name: "transport",
            label: "Transportation",
            type: "select",
            options: [
                ["car", "Car"],
                ["bicycle", "Bicycle"],
                ["walking", "Walking"],
            ],
        },
        {
            name: "priority",
            label: "Observation priority",
            type: "select",
            options: [
                ["dark_sky", "Dark sky"],
                ["easy_access", "Easy access"],
                ["open_horizon", "Open horizon"],
            ],
        },
    ],

    equipment: [
        {
            name: "experience",
            label: "Experience level",
            type: "select",
            options: [
                ["beginner", "Beginner"],
                ["intermediate", "Intermediate"],
                ["experienced", "Experienced"],
            ],
        },
        {
            name: "available_equipment",
            label: "Equipment you already own",
            type: "select",
            options: [
                ["none", "None"],
                ["binoculars", "Binoculars"],
                ["telescope", "Telescope"],
            ],
        },
        {
            name: "observation_mode",
            label: "Observation mode",
            type: "select",
            options: [
                ["visual", "Visual observation"],
                ["photography", "Photography"],
            ],
        },
    ],

    plan: [
        {
            name: "origin",
            label: "Starting location",
            type: "text",
            placeholder: "e.g. Ljubljana",
            value: "Ljubljana",
            minLength: 2,
            maxLength: 150,
        },
        {
            name: "experience",
            label: "Experience level",
            type: "select",
            options: [
                ["beginner", "Beginner"],
                ["intermediate", "Intermediate"],
                ["experienced", "Experienced"],
            ],
        },
        {
            name: "duration",
            label: "Available time",
            type: "select",
            options: [
                ["under_1_hour", "Under 1 hour"],
                ["1_to_3_hours", "1 to 3 hours"],
                ["over_3_hours", "Over 3 hours"],
            ],
        },
        {
            name: "observation_mode",
            label: "Observation mode",
            type: "select",
            options: [
                ["visual", "Visual observation"],
                ["photography", "Photography"],
            ],
        },
    ],

    facts: [
        {
            name: "explanation_level",
            label: "Explanation level",
            type: "select",
            options: [
                ["simple", "Simple"],
                ["detailed", "Detailed"],
            ],
        },
        {
            name: "interest",
            label: "Area of interest",
            type: "select",
            options: [
                ["science", "Science"],
                ["history", "History"],
                ["general", "General facts"],
            ],
        },
    ],
};


// ============================================================
// DOM Helpers
// ============================================================

function getElement(id) {
    const element = document.getElementById(id);

    if (!element) {
        throw new Error(`Required UI element not found: ${id}`);
    }

    return element;
}


function createElement(tag, className = "", text = null) {
    const element = document.createElement(tag);

    if (className) {
        element.className = className;
    }

    if (text !== null && text !== undefined) {
        element.textContent = String(text);
    }

    return element;
}


function formatDate(value) {
    const date = new Date(value);

    if (Number.isNaN(date.getTime())) {
        return "Unknown date";
    }

    return new Intl.DateTimeFormat("en-GB", {
        day: "numeric",
        month: "short",
        year: "numeric",
        timeZone: "UTC",
    }).format(date);
}


function formatDateTime(value) {
    const date = new Date(value);

    if (Number.isNaN(date.getTime())) {
        return "Unknown time";
    }

    return new Intl.DateTimeFormat("en-GB", {
        day: "numeric",
        month: "short",
        year: "numeric",
        hour: "2-digit",
        minute: "2-digit",
        hour12: false,
        timeZone: "UTC",
    }).format(date) + " UTC";
}


function formatLabel(value) {
    return String(value)
        .replaceAll("_", " ")
        .replace(/\b\w/g, (character) => character.toUpperCase());
}


// ============================================================
// Astronomical Event Cards
// ============================================================

export function renderEvents(events, onSelect) {
    const container = getElement("events-grid");

    container.replaceChildren();

    for (const event of events) {
        const card = createElement("button", "event-card");

        card.type = "button";
        card.addEventListener("click", () => onSelect(event));

        const top = createElement("div", "event-card-top");

        const kind = createElement(
            "span",
            "event-kind",
            formatLabel(event.kind)
        );

        const date = createElement(
            "span",
            "event-date",
            formatDate(event.time)
        );

        top.append(kind, date);

        const title = createElement(
            "h3",
            "event-card-title",
            event.title
        );

        const description = createElement(
            "p",
            "event-card-description",
            event.description || "Explore this astronomical event."
        );

        const footer = createElement("div", "event-card-footer");

        const action = createElement(
            "span",
            "event-card-action",
            "Explore event →"
        );

        footer.append(action);

        card.append(top, title, description, footer);
        container.append(card);
    }
}


// ============================================================
// Selected Event Details
// ============================================================

export function renderEventDetails(event) {
    const container = getElement("selected-event-details");

    container.replaceChildren();

    const card = createElement("article", "event-detail-card");

    const header = createElement("div", "event-detail-header");
    const headingGroup = createElement("div");

    const kind = createElement(
        "span",
        "event-kind",
        formatLabel(event.kind)
    );

    const title = createElement(
        "h3",
        "event-detail-title",
        event.title
    );

    headingGroup.append(kind, title);
    header.append(headingGroup);

    const description = createElement(
        "p",
        "event-detail-description",
        event.description || "No description is available."
    );

    const metadata = createElement("div", "event-detail-meta");

    appendMetadata(metadata, "Event date", formatDateTime(event.time));
    appendMetadata(metadata, "Event type", formatLabel(event.kind));

    for (const [key, value] of Object.entries(
        event.circumstances || {}
    )) {
        if (value === null || typeof value === "object") {
            continue;
        }

        appendMetadata(
            metadata,
            formatLabel(key),
            String(value)
        );
    }

    card.append(header, description, metadata);
    container.append(card);
}


function appendMetadata(container, label, value) {
    const item = createElement("div", "meta-item");

    const labelElement = createElement(
        "span",
        "meta-label",
        label
    );

    const valueElement = createElement(
        "span",
        "meta-value",
        value
    );

    item.append(labelElement, valueElement);
    container.append(item);
}


// ============================================================
// Dynamic AI Feature Forms
// ============================================================

export function renderFeatureForm(feature) {
    const fields = FEATURE_FIELDS[feature];

    if (!fields) {
        throw new Error(`Unsupported AI feature: ${feature}`);
    }

    const container = getElement("dynamic-form-fields");
    const title = getElement("feature-form-title");

    container.replaceChildren();
    container.className = "dynamic-form-grid";

    title.textContent = FEATURE_TITLES[feature];

    for (const field of fields) {
        container.append(createFormField(field));
    }

    getElement("feature-form-container").hidden = false;
}


function createFormField(field) {
    const group = createElement("div", "form-group");

    const label = createElement("label", "", field.label);
    label.htmlFor = `field-${field.name}`;

    let input;

    if (field.type === "select") {
        input = createElement("select");

        for (const [value, text] of field.options) {
            const option = createElement("option", "", text);

            option.value = value;
            input.append(option);
        }

    } else {
        input = createElement("input");

        input.type = field.type;

        if (field.placeholder) {
            input.placeholder = field.placeholder;
        }

        if (field.value !== undefined) {
            input.value = String(field.value);
        }

        if (field.min !== undefined) {
            input.min = String(field.min);
        }

        if (field.max !== undefined) {
            input.max = String(field.max);
        }

        if (field.minLength !== undefined) {
            input.minLength = field.minLength;
        }

        if (field.maxLength !== undefined) {
            input.maxLength = field.maxLength;
        }
    }

    input.id = `field-${field.name}`;
    input.name = field.name;
    input.required = true;

    group.append(label, input);

    return group;
}


// ============================================================
// Read User Preferences
// ============================================================

export function getFeaturePreferences(feature) {
    if (!FEATURE_FIELDS[feature]) {
        throw new Error(`Unsupported AI feature: ${feature}`);
    }

    const form = getElement("recommendation-form");
    const formData = new FormData(form);

    const preferences = { feature };

    for (const field of FEATURE_FIELDS[feature]) {
        const value = formData.get(field.name);

        if (value === null) {
            throw new Error(
                `Missing preference: ${field.name}`
            );
        }

        preferences[field.name] =
            field.type === "number"
                ? Number(value)
                : String(value).trim();
    }

    return preferences;
}


// ============================================================
// AI Recommendation Results
// ============================================================

export function renderRecommendation(response) {
    const container = getElement("recommendation-result");

    container.replaceChildren();

    const { feature, result } = response;

    if (!FEATURE_TITLES[feature]) {
        throw new Error(`Unsupported AI feature: ${feature}`);
    }

    const header = createElement("div", "result-header");

    const title = createElement(
        "h3",
        "",
        FEATURE_TITLES[feature]
    );

    const subtitle = createElement(
        "p",
        "",
        result.event_name
    );

    header.append(title, subtitle);
    container.append(header);

    switch (feature) {
        case "locations":
            renderLocationResults(container, result);
            break;

        case "equipment":
            renderEquipmentResults(container, result);
            break;

        case "plan":
            renderPlanResults(container, result);
            break;

        case "facts":
            renderFactsResults(container, result);
            break;
    }

    if (result.warning) {
        appendWarning(container, result.warning);
    }

    container.hidden = false;
}


// ============================================================
// Location Recommendations
// ============================================================


function renderLocationResults(container, result) {
    if (!result.observable) {
        const message = createElement(
            "p",
            "result-explanation",
            "This event is not suitable for direct observation."
        );

        container.append(message);
    }

    if (result.locations && result.locations.length > 0) {
        appendResultCards(
            container,
            result.locations,
            (location) => location.name,
            (location) => location.reason
        );

        appendNotice(
            container,
            "Suggested locations are not verified for distance, "
            + "accessibility, weather, or observing conditions."
        );
    }

    appendAdvice(container, result.general_advice);
}



// ============================================================
// Equipment Recommendations
// ============================================================

function renderEquipmentResults(container, result) {
    appendResultCards(
        container,
        result.equipment || [],
        (item) => item.name,
        (item) => item.reason
    );

    appendAdvice(container, result.general_advice);
}


// ============================================================
// Observation Plans
// ============================================================

function renderPlanResults(container, result) {
    appendResultCards(
        container,
        result.steps || [],
        (step) => `${step.step}. ${step.title}`,
        (step) => step.description
    );

    appendAdvice(container, result.general_advice);
}


// ============================================================
// Astronomical Facts
// ============================================================

function renderFactsResults(container, result) {
    const explanation = createElement(
        "p",
        "result-explanation",
        result.explanation
    );

    container.append(explanation);

    appendResultCards(
        container,
        result.facts || [],
        (fact) => fact.title,
        (fact) => fact.description
    );
}


// ============================================================
// Shared Result Components
// ============================================================

function appendResultCards(
    container,
    items,
    getTitle,
    getDescription
) {
    const list = createElement("div", "result-list");

    for (const item of items) {
        const card = createElement("article", "result-card");

        const title = createElement(
            "h4",
            "",
            getTitle(item)
        );

        const description = createElement(
            "p",
            "",
            getDescription(item)
        );

        card.append(title, description);
        list.append(card);
    }

    container.append(list);
}


function appendAdvice(container, advice) {
    if (!advice) {
        return;
    }

    const section = createElement("div", "result-advice");

    const label = createElement(
        "strong",
        "",
        "General advice"
    );

    const text = createElement("p", "", advice);

    section.append(label, text);
    container.append(section);
}


function appendWarning(container, warning) {
    const section = createElement("div", "result-warning");

    const label = createElement("strong", "", "Important: ");
    const text = createElement("span", "", warning);

    section.append(label, text);
    container.append(section);
}


function appendNotice(container, message) {
    const section = createElement(
        "div",
        "result-warning",
        message
    );

    container.append(section);
}


// ============================================================
// UI State Helpers
// ============================================================

export function setLoading(elementId, isLoading) {
    getElement(elementId).hidden = !isLoading;
}


export function showError(elementId, message) {
    const element = getElement(elementId);

    element.textContent = message;
    element.hidden = false;
}


export function clearError(elementId) {
    const element = getElement(elementId);

    element.textContent = "";
    element.hidden = true;
}


export function clearRecommendation() {
    const container = getElement("recommendation-result");

    container.replaceChildren();
    container.hidden = true;

    clearError("recommendation-error");
}
