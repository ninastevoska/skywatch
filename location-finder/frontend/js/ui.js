const CATEGORY_LABELS = {
    viewpoint: "Viewpoint",
    peak: "Peak",
    saddle: "Saddle",
    park: "Park",
    camp_site: "Campsite",
};

const MAX_TIME_MINUTES = {
    "driving-car": 60,
    "cycling-regular": 300,
    "foot-walking": 1200,
};

const MAX_DISTANCE_KM = 120;
const SNAP_WARNING_THRESHOLD_M = 50;


export class LocationFinderUI {
    constructor() {
        this.elements = {
            form: document.getElementById("discovery-form"),

            locationInput: document.getElementById("location-input"),
            searchLocationButton: document.getElementById("search-location-button"),
            locationSuggestions: document.getElementById("location-suggestions"),
            selectedLocation: document.getElementById("selected-location"),

            transportMode: document.getElementById("transport-mode"),
            rangeType: document.getElementById("range-type"),
            rangeValue: document.getElementById("range-value"),
            rangeValueLabel: document.getElementById("range-value-label"),
            rangeHint: document.getElementById("range-hint"),

            maxResults: document.getElementById("max-results"),
            sortBy: document.getElementById("sort-by"),
            discoverButton: document.getElementById("discover-button"),

            apiStatusIndicator: document.getElementById("api-status-indicator"),
            apiStatusText: document.getElementById("api-status-text"),
            workerStatusIndicator: document.getElementById("worker-status-indicator"),
            workerStatusText: document.getElementById("worker-status-text"),

            loadingMessage: document.getElementById("loading-message"),
            loadingText: document.getElementById("loading-text"),
            errorMessage: document.getElementById("error-message"),
            warningsContainer: document.getElementById("warnings-container"),

            resultsSummary: document.getElementById("results-summary"),
            resultsList: document.getElementById("results-list"),

            routePanel: document.getElementById("route-panel"),
            routeDetails: document.getElementById("route-details"),
            clearRouteButton: document.getElementById("clear-route-button"),
        };

        this.candidateCards = new Map();
    }

    // Service status

    setServiceStatus(apiAvailable, workerAvailable) {
        this._setStatus(
            this.elements.apiStatusIndicator,
            this.elements.apiStatusText,
            "API",
            apiAvailable
        );

        this._setStatus(
            this.elements.workerStatusIndicator,
            this.elements.workerStatusText,
            "Worker",
            workerAvailable
        );
    }

    _setStatus(indicator, text, serviceName, available) {
        indicator.classList.remove(
            "online",
            "offline",
            "checking"
        );

        if (available === null) {
            indicator.classList.add("checking");
            text.textContent = `${serviceName}: Checking...`;
            return;
        }

        indicator.classList.add(
            available ? "online" : "offline"
        );

        text.textContent =
            `${serviceName}: ${available ? "Online" : "Unavailable"}`;
    }

    // Starting location

    getLocationQuery() {
        return this.elements.locationInput.value.trim();
    }

    showLocationSuggestions(locations, onSelect) {
        const container = this.elements.locationSuggestions;

        container.replaceChildren();

        if (locations.length === 0) {
            const message = this._createElement(
                "p",
                "location-option",
                "No matching locations found."
            );

            container.append(message);
            container.hidden = false;

            return;
        }

        for (const location of locations) {
            const button = this._createElement(
                "button",
                "location-option"
            );

            button.type = "button";

            const name = this._createElement(
                "span",
                "location-name",
                location.name || "Unnamed location"
            );

            const metadata = [
                location.region,
                location.country,
            ].filter(Boolean).join(", ");

            const description = this._createElement(
                "span",
                "location-meta",
                metadata
            );

            button.append(name, description);

            button.addEventListener("click", () => {
                onSelect(location);
            });

            container.append(button);
        }

        container.hidden = false;
    }

    hideLocationSuggestions() {
        this.elements.locationSuggestions.hidden = true;
        this.elements.locationSuggestions.replaceChildren();
    }

    setSelectedLocation(location) {
        this.elements.locationInput.value =
            location.name || "Selected location";

        const description = [
            location.name || "Selected location",
            location.region,
            location.country,
        ].filter(Boolean).join(", ");

        this.elements.selectedLocation.textContent =
            `Selected: ${description}`;

        this.hideLocationSuggestions();
    }

    clearSelectedLocation() {
        this.elements.selectedLocation.textContent =
            "No starting location selected.";

        this.hideLocationSuggestions();
    }

    // Discovery preferences

    updateRangeInput(resetValue = false) {
        const rangeType = this.elements.rangeType.value;
        const transportMode = this.elements.transportMode.value;

        const input = this.elements.rangeValue;

        let maximum;
        let defaultValue;

        if (rangeType === "time") {
            maximum = MAX_TIME_MINUTES[transportMode];
            defaultValue = 30;

            this.elements.rangeValueLabel.textContent =
                "Maximum travel time (minutes)";

            this.elements.rangeHint.textContent =
                `Maximum: ${maximum} minutes`;
        } else {
            maximum = MAX_DISTANCE_KM;
            defaultValue = 10;

            this.elements.rangeValueLabel.textContent =
                "Maximum travel distance (km)";

            this.elements.rangeHint.textContent =
                `Maximum: ${maximum} km`;
        }

        input.min = "1";
        input.max = String(maximum);

        if (resetValue || !input.value) {
            input.value = String(defaultValue);
        } else if (Number(input.value) > maximum) {
            input.value = String(maximum);
        }
    }

    getDiscoveryRequest(origin) {
        if (!origin) {
            throw new Error(
                "Please select a starting location."
            );
        }

        const transportMode =
            this.elements.transportMode.value;

        const rangeType =
            this.elements.rangeType.value;

        const rangeValue =
            Number(this.elements.rangeValue.value);

        const maxResults =
            Number(this.elements.maxResults.value);

        const sortBy =
            this.elements.sortBy.value;

        const categories = Array.from(
            this.elements.form.querySelectorAll(
                'input[name="categories"]:checked'
            )
        ).map(input => input.value);

        const maximum = rangeType === "time"
            ? MAX_TIME_MINUTES[transportMode]
            : MAX_DISTANCE_KM;

        if (
            !Number.isFinite(rangeValue) ||
            rangeValue < 1 ||
            rangeValue > maximum
        ) {
            throw new Error(
                `Travel limit must be between 1 and ${maximum}.`
            );
        }

        if (categories.length === 0) {
            throw new Error(
                "Please select at least one location category."
            );
        }

        if (
            !Number.isInteger(maxResults) ||
            maxResults < 1 ||
            maxResults > 50
        ) {
            throw new Error(
                "Maximum results must be between 1 and 50."
            );
        }

        // Convert user-friendly units into backend units.
        const convertedRange = rangeType === "time"
            ? rangeValue * 60
            : rangeValue * 1000;

        return {
            origin: origin,
            transport_mode: transportMode,
            range_type: rangeType,
            range_value: Math.round(convertedRange),
            categories: categories,
            max_results: maxResults,
            sort_by: sortBy,
        };
    }

    // Loading, errors and warnings

    setBusy(busy, message = "Searching for locations...") {
        this.elements.loadingText.textContent = message;
        this.elements.loadingMessage.hidden = !busy;

        const controls = this.elements.form.querySelectorAll(
            "input, select, button"
        );

        for (const control of controls) {
            control.disabled = busy;
        }

        this.elements.resultsList.querySelectorAll("button")
            .forEach(button => {
                button.disabled = busy;
            });

        this.elements.clearRouteButton.disabled = busy;
    }

    showError(message) {
        this.elements.errorMessage.textContent = message;
        this.elements.errorMessage.hidden = false;
    }

    clearError() {
        this.elements.errorMessage.textContent = "";
        this.elements.errorMessage.hidden = true;
    }

    showWarnings(warnings = []) {
        const container = this.elements.warningsContainer;

        container.replaceChildren();

        if (warnings.length === 0) {
            container.hidden = true;
            return;
        }

        const list = document.createElement("ul");

        for (const warning of warnings) {
            const item = document.createElement("li");

            item.textContent = warning;
            list.append(item);
        }

        container.append(list);
        container.hidden = false;
    }

    // Discovery results

    showResults(result, onSelect, onRouteRequested) {
        this.clearResults();

        const candidates = result.candidates;

        if (candidates.length === 0) {
            this.elements.resultsSummary.textContent =
                "No locations match the selected preferences.";

            return;
        }

        this.elements.resultsSummary.textContent =
            `Showing ${candidates.length} of ` +
            `${result.total_candidates} matching locations.`;

        for (const candidate of candidates) {
            const card = this._createCandidateCard(
                candidate,
                onSelect,
                onRouteRequested
            );

            this.elements.resultsList.append(card);

            this.candidateCards.set(
                candidate.id,
                card
            );
        }
    }

    _createCandidateCard(
        candidate,
        onSelect,
        onRouteRequested
    ) {
        const card = this._createElement(
            "article",
            "candidate-card"
        );

        const title = this._createElement(
            "h3",
            "candidate-name",
            candidate.name || "Unnamed location"
        );

        const categories = this._createElement(
            "div",
            "candidate-categories"
        );

        for (const category of candidate.categories) {
            const tag = this._createElement(
                "span",
                `category-tag ${category}`,
                CATEGORY_LABELS[category] || category
            );

            categories.append(tag);
        }

        const metrics = this._createElement(
            "div",
            "candidate-metrics"
        );

        metrics.append(
            this._createMetric(
                "Travel distance",
                this.formatDistance(candidate.travel_distance_m)
            ),

            this._createMetric(
                "Travel time",
                this.formatDuration(candidate.travel_duration_seconds)
            ),

            this._createMetric(
                "Straight-line distance",
                this.formatDistance(candidate.straight_line_distance_m)
            ),

            this._createMetric(
                "Network offset",
                this.formatDistance(candidate.snapped_distance_m)
            )
        );

        card.append(title, categories, metrics);

        if (
            candidate.snapped_distance_m != null &&
            candidate.snapped_distance_m >
                SNAP_WARNING_THRESHOLD_M
        ) {
            const warning = this._createElement(
                "p",
                "candidate-warning",
                `The location is approximately ${
                    this.formatDistance(candidate.snapped_distance_m)
                } from the navigation network. ` +
                "Additional access may be required."
            );

            card.append(warning);
        }

        const actions = this._createElement(
            "div",
            "candidate-actions"
        );

        const mapButton = this._createElement(
            "button",
            "button button-secondary",
            "Show on map"
        );

        mapButton.type = "button";

        mapButton.addEventListener("click", () => {
            onSelect(candidate);
        });

        const routeButton = this._createElement(
            "button",
            "button button-primary",
            "Show route"
        );

        routeButton.type = "button";

        routeButton.addEventListener("click", () => {
            onRouteRequested(candidate);
        });

        actions.append(mapButton, routeButton);
        card.append(actions);

        return card;
    }

    selectCandidate(candidateId, scroll = false) {
        this.clearSelection();

        const card = this.candidateCards.get(candidateId);

        if (!card) {
            return;
        }

        card.classList.add("selected");

        if (scroll) {
            card.scrollIntoView({
                behavior: "smooth",
                block: "nearest",
            });
        }
    }

    clearSelection() {
        this.candidateCards.forEach(card => {
            card.classList.remove("selected");
        });
    }

    clearResults() {
        this.elements.resultsList.replaceChildren();
        this.candidateCards.clear();

        this.elements.resultsSummary.textContent =
            "Search for locations to see results.";
    }

    // Route information

    showRoute(route, candidate) {
        const container = this.elements.routeDetails;

        container.replaceChildren();

        const title = this._createElement(
            "p",
            "route-title",
            candidate.name || "Unnamed location"
        );

        const metrics = this._createElement(
            "div",
            "route-metrics"
        );

        metrics.append(
            this._createMetric(
                "Route distance",
                this.formatDistance(route.distance_m)
            ),

            this._createMetric(
                "Route duration",
                this.formatDuration(route.duration_seconds)
            )
        );

        container.append(title, metrics);

        for (const warning of route.warnings || []) {
            container.append(
                this._createElement(
                    "p",
                    "candidate-warning",
                    warning
                )
            );
        }

        if (
            candidate.snapped_distance_m != null &&
            candidate.snapped_distance_m >
                SNAP_WARNING_THRESHOLD_M
        ) {
            container.append(
                this._createElement(
                    "p",
                    "candidate-warning",
                    "The navigation route may not reach the " +
                    "exact observation location."
                )
            );
        }

        this.elements.routePanel.hidden = false;
    }

    clearRoute() {
        this.elements.routeDetails.replaceChildren();
        this.elements.routePanel.hidden = true;
    }

    // Reusable UI helpers

    _createElement(tag, className, text = null) {
        const element = document.createElement(tag);

        if (className) {
            element.className = className;
        }

        if (text !== null) {
            element.textContent = text;
        }

        return element;
    }

    _createMetric(label, value) {
        const metric = this._createElement(
            "div",
            "metric"
        );

        metric.append(
            this._createElement(
                "span",
                "metric-label",
                label
            ),

            this._createElement(
                "span",
                "metric-value",
                value
            )
        );

        return metric;
    }

    formatDistance(meters) {
        if (meters == null) {
            return "Unavailable";
        }

        if (meters < 1000) {
            return `${Math.round(meters)} m`;
        }

        return `${(meters / 1000).toFixed(2)} km`;
    }

    formatDuration(seconds) {
        if (seconds == null) {
            return "Unavailable";
        }

        return `${(seconds / 60).toFixed(1)} min`;
    }
}