import time

import requests
from fhirclient import client
from fhirclient.models.bundle import Bundle
from fhirclient.models.device import Device

# Configure FHIR client
settings = {"app_id": "catheter_query", "api_base": "https://r4.smarthealthit.org"}
fhir_client = client.FHIRClient(settings=settings)


def check_server_status():
    """Check if the FHIR server is operational by making a simple request."""
    try:
        # Make a simple request to the server's metadata endpoint
        response = requests.get(f"{settings['api_base']}/metadata", timeout=10)
        response.raise_for_status()
        print("Server status: OK")
        return True
    except requests.exceptions.RequestException as e:
        print(f"Server status check failed: {e}")
        return False


def get_urinary_catheter_patients():
    """Fetch patients with urinary catheters using a robust approach."""
    patient_ids = set()  # Use set to avoid duplicates

    # First check if the server is operational
    if not check_server_status():
        print("FHIR server is not responding. Please try again later.")
        return

    print("Searching for devices...")

    # Try a different approach - start with a small batch size
    # Request only the essential fields we need to reduce issues with unexpected fields
    search = Device.where(
        {
            "_count": "10",  # Reduce to 10 devices per page to reduce server load
            "_elements": "type,patient",  # Only request the fields we need
        }
    )

    try:
        # Execute search
        print("Executing FHIR query...")
        bundle = search.perform(fhir_client.server)

        # Process bundle and handle pagination
        while bundle is not None:
            if bundle.entry is not None:
                for entry in bundle.entry:
                    try:
                        # Instead of using the resource model directly, use the raw data
                        # This avoids issues with unexpected fields
                        raw_data = entry.as_json().get("resource", {})

                        # Safely check if this is a urinary catheter by examining the type coding
                        is_urinary_catheter = False

                        # Safely access the type and coding fields
                        type_data = raw_data.get("type", {})
                        coding_list = type_data.get("coding", [])

                        # Check each coding entry for SNOMED CT code for urinary catheter
                        for coding in coding_list:
                            system = coding.get("system")
                            code = coding.get("code")
                            if (
                                system == "http://snomed.info/sct"
                                and code == "303620002"
                            ):
                                is_urinary_catheter = True
                                break

                        # If this is a urinary catheter and has a patient reference, add the patient ID
                        patient = raw_data.get("patient", {})
                        patient_reference = patient.get("reference")

                        if is_urinary_catheter and patient_reference:
                            patient_id = patient_reference.replace("Patient/", "")
                            patient_ids.add(patient_id)
                            print(f"Found catheter device for patient: {patient_id}")
                    except Exception as e:
                        print(f"Skipping device entry due to error: {e}")
                        continue
            # Check for next page
            next_link = next(
                (link for link in bundle.link if link.relation == "next"), None
            )
            if next_link:
                print("Fetching next page of results...")
                try:
                    # Add a small delay to avoid overwhelming the server
                    time.sleep(1)

                    # Extract the relative URL from the next link
                    # The URL might be full (https://server/Device?_count=10&page=2)
                    # or relative (/Device?_count=10&page=2)
                    next_url = next_link.url

                    # If it's a full URL, get just the path and query part
                    if next_url.startswith("http"):
                        from urllib.parse import urlparse

                        parsed = urlparse(next_url)
                        next_url = parsed.path
                        if parsed.query:
                            next_url += "?" + parsed.query

                    # Use the existing client to fetch the next page
                    next_bundle = fhir_client.server.request_json(next_url)
                    bundle = Bundle(next_bundle)
                except Exception as e:
                    print(f"Error fetching next page: {e}")
                    bundle = None
            else:
                bundle = None
        # Output results
        if patient_ids:
            print(f"Found {len(patient_ids)} patients with urinary catheters:")
            for pid in patient_ids:
                print(f"Patient ID: {pid}")
        else:
            print("No patients with urinary catheters found.")

    except requests.exceptions.HTTPError as e:
        print(f"HTTP Error occurred: {e}")
        print(
            "The server returned an error status code. Consider trying a different API or endpoint."
        )
    except requests.exceptions.ConnectionError as e:
        print(f"Connection Error: {e}")
        print(
            "Could not connect to the FHIR server. Please check your internet connection."
        )
    except requests.exceptions.Timeout as e:
        print(f"Timeout Error: {e}")
        print("The request timed out. Try again later or with a smaller batch size.")
    except Exception as e:
        print(f"Error querying FHIR server: {e}")
        print("Trying alternative approach...")
        try_alternative_approach()

    return patient_ids


def try_alternative_approach():
    """Alternative approach to find catheter information if the primary method fails."""
    print("Attempting to find patients with catheters through observation records...")
    try:
        # This is a simplified example - in a real implementation, you would
        # search for observations related to catheters
        print("This feature would search for catheter-related observations.")
        print("Implementation is pending.")
    except Exception as e:
        print(f"Alternative approach also failed: {e}")


if __name__ == "__main__":
    print("Starting FHIR Catheter Watchdog Agent...")
    get_urinary_catheter_patients()
