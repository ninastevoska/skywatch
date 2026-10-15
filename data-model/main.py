from datetime import date
from pathlib import Path

from src.xml_reader import read_events, read_locations, read_observations
from src.data_service import link_data
from src.filters import filter_events, filter_observations
from src.exporters import export_results


EVENT_TYPES = {
    "1": ("shower", "Meteor shower"),
    "2": ("eclipse", "Eclipse"),
    "3": ("conjunction", "Conjunction"),
    "4": ("opposition", "Opposition"),
    "5": ("moon", "Moon phase"),
    "6": ("elongation", "Elongation"),
}

EVENT_TYPE_NAMES = {code: label for code, label in EVENT_TYPES.values()}


def select_event_type():
    print("\n--- Astronomical event type ---")
    for number, (_, label) in EVENT_TYPES.items():
        print(f"{number}. {label}")

    while True:
        selection = input("\nSelection: ").strip()
        if selection in EVENT_TYPES:
            return EVENT_TYPES[selection][0]
        print("Invalid selection.")


def select_date():
    while True:
        value = input("\nFrom date (YYYY-MM-DD): ").strip()
        try:
            if len(value) != 10:
                raise ValueError
            return date.fromisoformat(value)
        except ValueError:
            print("Invalid date. Example: 2026-10-01.")


def select_cloud_cover():
    while True:
        value = input("\nMaximum cloud cover (0-100): ").strip()
        try:
            cover = int(value)
            if 0 <= cover <= 100:
                return cover
            print("Enter a number between 0 and 100.")
        except ValueError:
            print("Enter an integer.")


def select_filters(for_observations=False):
    print("\n========== FILTER SELECTION ==========")
    print("1. Astronomical event type")
    print("2. From date")
    allowed = {"1", "2"}

    if for_observations:
        print("3. Maximum cloud cover")
        allowed.add("3")

    while True:
        value = input("\nSelect filters (e.g. 1,2; Enter to go back): ").strip()
        if not value:
            return None
        choices = [item.strip() for item in value.split(",")]
        if all(item in allowed for item in choices) and len(set(choices)) == len(choices):
            break
        print("Invalid selection.")

    filters = {}
    if "1" in choices:
        filters["event_type"] = select_event_type()
    if "2" in choices:
        filters["date_from"] = select_date()
    if "3" in choices:
        filters["max_cloud_cover"] = select_cloud_cover()
    return filters


def display_events(events):
    print(f"\nEvents found: {len(events)}")
    if not events:
        print("No events match the selected filters.")
        return

    print("-" * 105)
    print(f"{'ID':<6} {'Event':<55} {'Type':<18} {'Date':<12}")
    print("-" * 105)
    for event in events:
        label = EVENT_TYPE_NAMES.get(event.type, event.type)
        print(f"{event.id:<6} {event.name:<55} {label:<18} {event.date:<12}")
    print("-" * 105)


def display_observations(records):
    print(f"\nObservations found: {len(records)}")
    if not records:
        print("No observations match the selected filters.")
        return

    print("-" * 125)
    print(
        f"{'ID':<6} {'Event':<49} {'Type':<17} "
        f"{'Location':<18} {'Date':<12} {'Cloud cover':>10}"
    )
    print("-" * 125)
    for record in records:
        observation = record.observation
        event = record.event
        location = record.location
        label = EVENT_TYPE_NAMES.get(event.type, event.type)
        location_name = location.name or "Unnamed"
        weather = observation.weather
        cloud_cover = f"{weather.cloud_cover} %" if weather is not None else "No data"
        print(
            f"{observation.id:<6} {event.name:<49} {label:<17} "
            f"{location_name:<18} {observation.date:<12} {cloud_cover:>10}"
        )
    print("-" * 125)


def events_menu(events, output_directory):
    while True:
        print("\n========== ASTRONOMICAL EVENTS ==========")
        print("1. Show all events")
        print("2. Filter events")
        print("0. Back")
        selection = input("\nSelection: ").strip()

        if selection == "1":
            display_events(events)
        elif selection == "2":
            filters = select_filters()
            if filters is not None:
                results = filter_events(events, **filters)
                display_events(results)
                export_results(results, "events", output_directory)
                print("Results saved to output/filtrirano.json and output/filtrirano.xml")
        elif selection == "0":
            break
        else:
            print("Invalid selection.")


def observations_menu(linked_observations, output_directory):
    while True:
        print("\n========== OBSERVATIONS ==========")
        print("1. Show all observations")
        print("2. Filter observations")
        print("0. Back")
        selection = input("\nSelection: ").strip()

        if selection == "1":
            display_observations(linked_observations)
        elif selection == "2":
            filters = select_filters(for_observations=True)
            if filters is not None:
                results = filter_observations(linked_observations, **filters)
                display_observations(results)
                export_results(results, "observations", output_directory)
                print("Results saved to output/filtrirano.json and output/filtrirano.xml")
                
        elif selection == "0":
            break
        else:
            print("Invalid selection.")


def main():
    project_directory = Path(__file__).resolve().parent
    data_directory = project_directory / "data"
    output_directory = Path(__file__).resolve().parent / "output"
    output_directory.mkdir(parents=True, exist_ok=True)

    events = read_events(data_directory / "events.xml")
    locations = read_locations(data_directory / "locations.xml")
    observations = read_observations(data_directory / "observations.xml")
    linked_observations = link_data(events, locations, observations)

    while True:
        print("\n========== SKYWATCH ==========")
        print("1. Astronomical events")
        print("2. Observations and weather conditions")
        print("0. Exit")
        selection = input("\nSelection: ").strip()
        if selection == "1":
            events_menu(events, output_directory)
        elif selection == "2":
            observations_menu(linked_observations, output_directory)
        elif selection == "0":
            print("\nGoodbye!")
            break
        else:
            print("Invalid selection.")


if __name__ == "__main__":
    try:
        main()
    except (KeyboardInterrupt, EOFError):
        print("\n\nProgram interrupted. Goodbye!")
