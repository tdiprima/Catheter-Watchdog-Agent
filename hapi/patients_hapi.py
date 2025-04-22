"""
I was right; there are no patients with catheters in this dataset.
Have a look at the FHIR_SERVER.
"""
import requests

# ------------------ Config ------------------
FHIR_SERVER = "https://hapi.fhir.org/baseR4"


# ------------------ Helper Functions ------------------
def fetch_patients_with_catheters():
    """Search for patients with catheter devices on the HAPI FHIR server."""
    url = f"{FHIR_SERVER}/Device?type=catheter&_include=Device:patient"
    response = requests.get(url)
    bundle = response.json()
    patient_ids = set()
    for entry in bundle.get("entry", []):
        resource = entry.get("resource", {})
        if resource.get("resourceType") == "Patient":
            patient_ids.add(resource.get("id"))
        elif resource.get("resourceType") == "Device":
            patient_ref = resource.get("patient", {}).get("reference", "")
            if patient_ref.startswith("Patient/"):
                patient_ids.add(patient_ref.split("/")[1])
    return list(patient_ids)


# ------------------ Run the Agent ------------------
if __name__ == "__main__":
    patients = fetch_patients_with_catheters()
    if not patients:
        print("No patients with catheter data found.")
    else:
        for patient_id in patients:
            print(patient_id)
