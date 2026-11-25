import {
    getHealth,
    searchLocations,
    discoverLocations,
    getRoute,
} from "./api.js";

import { LocationMap } from "./map.js";
import { LocationFinderUI } from "./ui.js";


const HEALTH_CHECK_INTERVAL_MS = 10000;


class LocationFinderApp {
    constructor() {
        this.ui = new LocationFinderUI();
        this.map = new LocationMap("map");

        this.state = {
            origin: null,
            discoveryResult: null,
            selectedCandidate: null,
            busy: false,
            healthChecking: false,
        };

        this.healthTimer = null;
    }

    initialize() {
        this._registerEvents();

        this.ui.updateRangeInput();
        this.ui.setServiceStatus(null, null);

        this._startHealthMonitoring();
    }

    // Event registration

    _registerEvents() {
        const elements = this.ui.elements;

        elements.searchLocationButton.addEventListener(
            "click",
            () => this._searchLocations()
        );

        elements.locationInput.addEventListener(
            "keydown",
            event => {
                if (event.key === "Enter") {
                    event.preventDefault();
                    this._searchLocations();
                }
            }
        );

        elements.locationInput.addEventListener(
            "input",
            () => this._handleLocationInputChange()
        );

        elements.transportMode.addEventListener(
            "change",
            () => this.ui.updateRangeInput()
        );

        elements.rangeType.addEventListener(
            "change",
            () => this.ui.updateRangeInput(true)
        );

        elements.form.addEventListener(
            "submit",
            event => {
                event.preventDefault();
                this._discoverLocations();
            }
        );

        elements.clearRouteButton.addEventListener(
            "click",
            () => this._clearRoute()
        );

        window.addEventListener(
            "pagehide",
            () => this._stopHealthMonitoring()
        );

        window.addEventListener(
            "pageshow",
            () => this._startHealthMonitoring()
        );
    }

    // Service health monitoring

    _startHealthMonitoring() {
        if (this.healthTimer !== null) {
            return;
        }

        this._checkHealth();

        this.healthTimer = window.setInterval(
            () => this._checkHealth(),
            HEALTH_CHECK_INTERVAL_MS
        );
    }

    _stopHealthMonitoring() {
        if (this.healthTimer !== null) {
            window.clearInterval(this.healthTimer);
            this.healthTimer = null;
        }
    }

    async _checkHealth() {
        if (
            this.state.busy ||
            this.state.healthChecking
        ) {
            return;
        }

        this.state.healthChecking = true;

        try {
            const health = await getHealth();

            if (!this.state.busy) {
                this.ui.setServiceStatus(
                    health.api_available,
                    health.worker_available
                );
            }
        } catch (error) {
            if (!this.state.busy) {
                this.ui.setServiceStatus(false, false);
            }
        } finally {
            this.state.healthChecking = false;
        }
    }

    // Starting location search

    async _searchLocations() {
        if (this.state.busy) {
            return;
        }

        this.ui.clearError();

        const query = this.ui.getLocationQuery();

        if (query.length < 2) {
            this.ui.showError(
                "Please enter at least two characters."
            );

            return;
        }

        this.ui.hideLocationSuggestions();

        this._setBusy(
            true,
            "Searching for starting locations..."
        );

        try {
            const result = await searchLocations(query);

            this.ui.showLocationSuggestions(
                result.locations,
                location => this._selectOrigin(location)
            );
        } catch (error) {
            this.ui.showError(error.message);
        } finally {
            this._setBusy(false);
        }
    }

    _selectOrigin(location) {
        if (this.state.busy) {
            return;
        }

        this._clearDiscovery();

        this.state.origin = location;

        this.ui.setSelectedLocation(location);
        this.ui.clearError();

        this.map.showOrigin(location);
    }

    _handleLocationInputChange() {
        this.state.origin = null;

        this._clearDiscovery();

        this.ui.clearSelectedLocation();
        this.ui.clearError();

        this.map.originLayer.clearLayers();
    }

    // Candidate discovery

    async _discoverLocations() {
        if (this.state.busy) {
            return;
        }

        this.ui.clearError();

        let request;

        try {
            request = this.ui.getDiscoveryRequest(
                this.state.origin
            );
        } catch (error) {
            this.ui.showError(error.message);
            return;
        }

        this._clearDiscovery();

        this.ui.hideLocationSuggestions();

        this._setBusy(
            true,
            "Searching for reachable locations. " +
            "Waiting for the Location Worker if necessary..."
        );

        try {
            const result = await discoverLocations(request);

            this.state.discoveryResult = result;

            this.ui.setServiceStatus(true, true);

            this.map.showOrigin(result.origin, false);
            this.map.showIsochrone(result.isochrone);

            this.map.showCandidates(
                result.candidates,
                candidate => this._requestRoute(candidate)
            );

            this.ui.showResults(
                result,
                candidate => this._selectCandidate(candidate),
                candidate => this._requestRoute(candidate)
            );

            this.ui.showWarnings(result.warnings || []);

            this.map.fitDiscoveryBounds();
        } catch (error) {
            this.ui.showError(error.message);
        } finally {
            this._setBusy(false);
            this._checkHealth();
        }
    }

    // Candidate selection

    _selectCandidate(candidate) {
        if (this.state.busy) {
            return;
        }

        this._clearRoute();

        this.state.selectedCandidate = candidate;

        this.ui.selectCandidate(candidate.id);
        this.map.selectCandidate(candidate.id);
    }

    // Route discovery

    async _requestRoute(candidate) {
        if (
            this.state.busy ||
            !this.state.discoveryResult
        ) {
            return;
        }

        this.ui.clearError();

        this._clearRoute();

        this.state.selectedCandidate = candidate;

        this.ui.selectCandidate(candidate.id);
        this.map.selectCandidate(candidate.id, false);

        const discoveryResult = this.state.discoveryResult;

        const request = {
            origin: discoveryResult.origin.coordinates,

            destination:
                candidate.snapped_coordinates ||
                candidate.coordinates,

            transport_mode:
                discoveryResult.transport_mode,
        };

        this._setBusy(
            true,
            "Calculating navigation route..."
        );

        try {
            const route = await getRoute(request);

            this.ui.setServiceStatus(true, true);

            this.map.showRoute(route);
            this.ui.showRoute(route, candidate);
        } catch (error) {
            this.ui.showError(error.message);
        } finally {
            this._setBusy(false);
            this._checkHealth();
        }
    }

    // State management

    _setBusy(busy, message) {
        this.state.busy = busy;

        this.ui.setBusy(busy, message);
    }

    _clearRoute() {
        this.map.clearRoute();
        this.map.clearSelection();

        this.ui.clearRoute();
        this.ui.clearSelection();

        this.state.selectedCandidate = null;
    }

    _clearDiscovery() {
        this._clearRoute();

        this.state.discoveryResult = null;

        this.map.clearDiscovery();

        this.ui.clearResults();
        this.ui.showWarnings([]);
    }
}


// Application entry point.

const app = new LocationFinderApp();

app.initialize();