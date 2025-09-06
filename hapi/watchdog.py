"""
LangGraph + FHIR "Catheter Watchdog" Agent
Automatically monitor patients' catheter change schedules and flag when a change is overdue.
"""

import datetime
import time

import requests
from langchain_core.runnables import RunnableLambda
from langgraph.graph import END, StateGraph
from pydantic import BaseModel

# ------------------ Config ------------------
FHIR_SERVER = "https://hapi.fhir.org/baseR4"
CHANGE_INTERVAL_HOURS = 72  # hospital protocol


# Define a minimal state schema for LangGraph using Pydantic
class State(BaseModel):
    patient_id: str
    catheter_data: dict = None
    hours_since: float = None
    status: str = None


# ------------------ Helper Functions ------------------
def fetch_patients_with_catheters():
    """Search for patients with catheter devices on the HAPI FHIR server."""
    url = f"{FHIR_SERVER}/Device?type=catheter&_include=Device:patient"
    bundle = requests.get(url).json()
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


def fetch_catheter_data(patient_id):
    """Mocked logic: Searches for Device data tagged as catheter for a patient."""
    url = f"{FHIR_SERVER}/Device?patient={patient_id}&type=catheter"
    bundle = requests.get(url).json()
    entries = bundle.get("entry", [])
    if not entries:
        return None

    # Assume first catheter device is relevant
    catheter = entries[0]["resource"]
    inserted = catheter.get("meta", {}).get("lastUpdated")  # Simplified
    if inserted:
        return {"patient_id": patient_id, "inserted": inserted, "device": catheter}
    return None


def hours_since_insertion(iso_time):
    inserted_time = datetime.datetime.fromisoformat(iso_time.replace("Z", "+00:00"))
    now = datetime.datetime.now(datetime.timezone.utc)
    delta = now - inserted_time
    return delta.total_seconds() / 3600


# ------------------ Nodes ------------------


def check_schedule_node(state):
    catheter_data = fetch_catheter_data(state.patient_id)
    if not catheter_data:
        return {"status": "no_data"}
    hours = hours_since_insertion(catheter_data["inserted"])
    return {"catheter_data": catheter_data, "hours_since": hours}


def decide_action_node(state):
    if state.hours_since is None:
        return {"status": "no_data"}
    if state.hours_since > CHANGE_INTERVAL_HOURS:
        return {"status": "overdue"}
    return {"status": "ok"}


def notify_staff_node(state):
    patient = state.catheter_data["patient_id"]
    print(
        f"🚨 ALERT: Patient {patient} needs catheter change! {state.hours_since:.1f} hours since insertion."
    )
    return {"notified": True}


def reschedule_node(state):
    print("⏱️ Rescheduling check in 24 hours...")
    time.sleep(1)  # Simulating delay. Replace with cron in prod.
    return {}


# ------------------ Build LangGraph ------------------
graph = StateGraph(state_schema=State)

# Add nodes
graph.add_node("check_schedule", RunnableLambda(check_schedule_node))
graph.add_node("decide_action", RunnableLambda(decide_action_node))
graph.add_node("notify_staff", RunnableLambda(notify_staff_node))
graph.add_node("reschedule", RunnableLambda(reschedule_node))

# Set entry point and edges
graph.set_entry_point("check_schedule")
graph.add_edge("check_schedule", "decide_action")
graph.add_conditional_edges(
    "decide_action",
    lambda state: state.status,
    {"overdue": "notify_staff", "ok": "reschedule", "no_data": END},
)
graph.add_edge("notify_staff", "reschedule")
graph.add_edge("reschedule", "check_schedule")

app = graph.compile()

# ------------------ Run the Agent ------------------
if __name__ == "__main__":
    # sample_patient_id = "example"  # Replace with real patient ID in HAPI
    # app.invoke({"patient_id": sample_patient_id})
    patients = fetch_patients_with_catheters()
    if not patients:
        print("No patients with catheter data found.")
    else:
        for patient_id in patients:
            print(f"\n▶ Running agent for patient {patient_id}...")
            app.invoke({"patient_id": patient_id})
