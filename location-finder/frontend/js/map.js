const COLORS = {
    origin: "#c491a8",
    viewpoint: "#79b5af",
    peak: "#aa9bc9",
    saddle: "#c9ad7f",
    park: "#8fb58a",
    camp_site: "#c9848d",
    selected: "#f2d58a",
    white: "#f8fafc",
    border: "#243047",
};

const DEFAULT_CENTER = [46.1512, 14.9955];
const DEFAULT_ZOOM = 8;

const CATEGORY_LABELS = {
    viewpoint: "Viewpoint",
    peak: "Peak",
    saddle: "Saddle",
    park: "Park",
    camp_site: "Campsite",
};

export class LocationMap {
    constructor(containerId) {
        this.map = L.map(containerId).setView(
            DEFAULT_CENTER,
            DEFAULT_ZOOM
        );

        this._initializeBaseMap();

        this.isochroneLayer = L.layerGroup().addTo(this.map);
        this.originLayer = L.layerGroup().addTo(this.map);
        this.candidatesLayer = L.layerGroup().addTo(this.map);
        this.routeLayer = L.layerGroup().addTo(this.map);

        this.candidateMarkers = new Map();
        this.candidateData = new Map();
        this.selectedCandidateId = null;
    }

    _initializeBaseMap() {
        L.tileLayer(
            "https://tile.openstreetmap.org/{z}/{x}/{y}.png",
            {
                attribution:
                    '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
                maxZoom: 19,
            }
        ).addTo(this.map);
    }

    _toLatLng(coordinates) {
        return [
            coordinates.latitude,
            coordinates.longitude,
        ];
    }

    _getCandidateColor(candidate) {
        const primaryCategory = candidate.categories?.[0];

        switch (primaryCategory) {
            case "viewpoint":
                return COLORS.viewpoint;
            case "peak":
                return COLORS.peak;
            case "saddle":
                return COLORS.saddle;
            case "park":
                return COLORS.park;
            case "camp_site":
                return COLORS.camp_site;
            default:
                return COLORS.viewpoint;
        }
    }

    _createPinIcon({
        fillColor,
        innerColor = COLORS.white,
        size = 34,
        selected = false,
        label = "",
    }) {
        const strokeColor = selected
            ? COLORS.selected
            : COLORS.border;

        const strokeWidth = selected ? 3 : 2;
        const glowColor = selected
            ? "rgba(242, 213, 138, 0.45)"
            : "rgba(36, 48, 71, 0.18)";

        const fontSize = Math.round(size * 0.34);
        const iconHeight = Math.round(size * 1.35);
        const centerX = 16;
        const centerY = 13;

        const svg = `
            <svg
                xmlns="http://www.w3.org/2000/svg"
                width="${size}"
                height="${iconHeight}"
                viewBox="0 0 32 44"
            >
                <defs>
                    <filter id="marker-shadow" x="-50%" y="-50%" width="200%" height="200%">
                        <feDropShadow dx="0" dy="2" stdDeviation="2" flood-color="${glowColor}"/>
                    </filter>
                </defs>

                <g filter="url(#marker-shadow)">
                    <path
                        d="M16 2 C9 2 4 7 4 14 C4 24 16 40 16 40 C16 40 28 24 28 14 C28 7 23 2 16 2 Z"
                        fill="${fillColor}"
                        stroke="${strokeColor}"
                        stroke-width="${strokeWidth}"
                    />
                    <circle
                        cx="${centerX}"
                        cy="${centerY}"
                        r="7"
                        fill="${innerColor}"
                        opacity="0.95"
                    />
                    ${
                        label
                            ? `
                            <text
                                x="${centerX}"
                                y="${centerY + 1}"
                                text-anchor="middle"
                                dominant-baseline="middle"
                                font-family="Segoe UI, Arial, sans-serif"
                                font-size="${fontSize}"
                                font-weight="700"
                                fill="${fillColor}"
                            >
                                ${label}
                            </text>
                        `
                            : ""
                    }
                </g>
            </svg>
        `;

        return L.divIcon({
            className: "",
            html: svg,
            iconSize: [size, iconHeight],
            iconAnchor: [size / 2, iconHeight - 2],
            popupAnchor: [0, -iconHeight + 10],
        });
    }

    _createOriginIcon() {
        return this._createPinIcon({
            fillColor: COLORS.origin,
            innerColor: COLORS.white,
            size: 36,
            label: "●",
        });
    }

    _createCandidateIcon(candidate) {
        return this._createPinIcon({
            fillColor: this._getCandidateColor(candidate),
            innerColor: COLORS.white,
            size: 34,
            label: "•",
        });
    }

    _createSelectedCandidateIcon(candidate) {
        return this._createPinIcon({
            fillColor: this._getCandidateColor(candidate),
            innerColor: COLORS.white,
            size: 42,
            selected: true,
            label: "•",
        });
    }

    showOrigin(location, focus = true) {
        this.originLayer.clearLayers();

        const marker = L.marker(
            this._toLatLng(location.coordinates),
            {
                icon: this._createOriginIcon(),
                keyboard: true,
            }
        );

        const popup = document.createElement("div");
        popup.className = "map-popup";

        const title = document.createElement("h3");
        title.textContent = location.name || "Starting location";

        const description = document.createElement("p");
        description.textContent = "Starting location";

        popup.append(title, description);

        marker.bindPopup(popup);
        marker.addTo(this.originLayer);

        if (focus) {
            this.map.setView(
                this._toLatLng(location.coordinates),
                13
            );
        }
    }

    showIsochrone(geometry) {
        this.isochroneLayer.clearLayers();

        if (!geometry) {
            return;
        }

        const layer = L.geoJSON(geometry, {
            style: {
                color: COLORS.viewpoint,
                weight: 2,
                opacity: 0.9,
                fillColor: COLORS.viewpoint,
                fillOpacity: 0.12,
                dashArray: "6 4",
            },
            interactive: false,
        });

        layer.addTo(this.isochroneLayer);
        layer.bringToBack();
    }

    showCandidates(candidates, onRouteRequested) {
        this.clearCandidates();

        for (const candidate of candidates) {
            const marker = L.marker(
                this._toLatLng(candidate.coordinates),
                {
                    icon: this._createCandidateIcon(candidate),
                    keyboard: true,
                }
            );

            const popup = this._createCandidatePopup(
                candidate,
                onRouteRequested
            );

            marker.bindPopup(popup);
            marker.addTo(this.candidatesLayer);

            this.candidateMarkers.set(candidate.id, marker);
            this.candidateData.set(candidate.id, candidate);
        }
    }

    _createCandidatePopup(candidate, onRouteRequested) {
        const popup = document.createElement("div");
        popup.className = "map-popup";

        const title = document.createElement("h3");
        title.textContent = candidate.name || "Unnamed location";

        const categories = document.createElement("p");
        categories.textContent = candidate.categories
            .map(category => CATEGORY_LABELS[category] || category)
            .join(", ");

        const distance = document.createElement("p");
        distance.textContent =
            `Travel distance: ${
                this._formatDistance(candidate.travel_distance_m)
            }`;

        const duration = document.createElement("p");
        duration.textContent =
            `Travel time: ${
                this._formatDuration(candidate.travel_duration_seconds)
            }`;

        const routeButton = document.createElement("button");
        routeButton.type = "button";
        routeButton.className = "button button-secondary";
        routeButton.textContent = "Show route";

        routeButton.addEventListener("click", () => {
            this.map.closePopup();
            onRouteRequested(candidate);
        });

        popup.append(
            title,
            categories,
            distance,
            duration,
            routeButton
        );

        return popup;
    }

    selectCandidate(candidateId, focus = true) {
        this.clearSelection();

        const marker = this.candidateMarkers.get(candidateId);
        const candidate = this.candidateData.get(candidateId);

        if (!marker || !candidate) {
            return;
        }

        this.selectedCandidateId = candidateId;

        marker.setIcon(
            this._createSelectedCandidateIcon(candidate)
        );
        marker.setZIndexOffset(1000);

        if (focus) {
            this.map.panTo(marker.getLatLng());
            marker.openPopup();
        }
    }

    clearSelection() {
        const marker = this.candidateMarkers.get(
            this.selectedCandidateId
        );

        const candidate = this.candidateData.get(
            this.selectedCandidateId
        );

        if (marker && candidate) {
            marker.setIcon(
                this._createCandidateIcon(candidate)
            );
            marker.setZIndexOffset(0);
        }

        this.selectedCandidateId = null;
    }

    showRoute(route) {
        this.clearRoute();

        const layer = L.geoJSON(route.geometry, {
            style: {
                color: COLORS.peak,
                weight: 5,
                opacity: 0.95,
                lineCap: "round",
                lineJoin: "round",
            },
        });

        layer.addTo(this.routeLayer);
        layer.bringToFront();

        this.candidateMarkers.forEach(marker => {
            marker.setZIndexOffset(500);
        });

        const selectedMarker = this.candidateMarkers.get(
            this.selectedCandidateId
        );

        if (selectedMarker) {
            selectedMarker.setZIndexOffset(1000);
        }

        const bounds = layer.getBounds();

        if (bounds.isValid()) {
            this.map.fitBounds(bounds, {
                padding: [40, 40],
                maxZoom: 16,
            });
        }
    }

    fitDiscoveryBounds() {
        const layers = L.featureGroup([
            ...this.isochroneLayer.getLayers(),
            ...this.originLayer.getLayers(),
            ...this.candidatesLayer.getLayers(),
        ]);

        const bounds = layers.getBounds();

        if (bounds.isValid()) {
            this.map.fitBounds(bounds, {
                padding: [30, 30],
                maxZoom: 14,
            });
        }
    }

    clearCandidates() {
        this.clearSelection();
        this.candidatesLayer.clearLayers();
        this.candidateMarkers.clear();
        this.candidateData.clear();
    }

    clearRoute() {
        this.routeLayer.clearLayers();
    }

    clearDiscovery() {
        this.isochroneLayer.clearLayers();
        this.clearCandidates();
        this.clearRoute();
        this.map.closePopup();
    }

    _formatDistance(meters) {
        if (meters == null) {
            return "Unavailable";
        }

        if (meters < 1000) {
            return `${Math.round(meters)} m`;
        }

        return `${(meters / 1000).toFixed(2)} km`;
    }

    _formatDuration(seconds) {
        if (seconds == null) {
            return "Unavailable";
        }

        return `${(seconds / 60).toFixed(1)} min`;
    }
}