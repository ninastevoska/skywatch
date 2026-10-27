
"""Download PC-Axis datasets from remote data sources."""

from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


DATASET_URL = (
    "https://pxweb.stat.si/SiStatData/Resources/PX/"
    "Databases/Data/2164466S.PX"
)

REQUEST_TIMEOUT = 30


class PXFetchError(Exception):
    """Raised when a PC-Axis dataset cannot be downloaded."""


def fetch_px(
    url: str = DATASET_URL,
    timeout: int = REQUEST_TIMEOUT,
) -> bytes:
    """Download a PC-Axis dataset and return its raw content.

    Args:
        url: Direct URL to the PC-Axis file.
        timeout: Maximum time in seconds for blocking network operations.

    Returns:
        The downloaded PC-Axis file as bytes.

    Raises:
        PXFetchError: If the request fails or returns empty content.
    """
    request = Request(
        url,
        headers={"User-Agent": "SkyWatch-AstroDestination/1.0"},
    )

    try:
        with urlopen(request, timeout=timeout) as response:
            if response.status != 200:
                raise PXFetchError(
                    f"Unexpected HTTP status: {response.status}"
                )

            content = response.read()

    except HTTPError as exc:
        raise PXFetchError(
            f"HTTP {exc.code} while downloading the dataset."
        ) from exc

    except (URLError, TimeoutError, OSError) as exc:
        raise PXFetchError(
            f"Failed to download the PC-Axis dataset: {exc}"
        ) from exc

    if not content:
        raise PXFetchError("The downloaded PC-Axis dataset is empty.")

    return content
