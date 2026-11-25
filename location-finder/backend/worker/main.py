import logging

from worker.clients.openrouteservice import OpenRouteServiceClient
from worker.clients.openpoiservice import OpenPoiServiceClient
from worker.services.routing import RoutingService
from worker.services.discovery import DiscoveryService
from worker.pipes.server import NamedPipeServer


def main() -> None:
    """Initialize and start the Location Worker."""

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    ors_client = OpenRouteServiceClient()
    ops_client = OpenPoiServiceClient()

    routing_service = RoutingService(ors_client)

    discovery_service = DiscoveryService(
        ors_client=ors_client,
        ops_client=ops_client,
        routing_service=routing_service,
    )

    server = NamedPipeServer(
        discovery_service=discovery_service,
        routing_service=routing_service,
    )

    server.serve_forever()


if __name__ == "__main__":
    main()