"""
LangGraph + FHIR "Catheter Watchdog" Agent (with Mock Data)
"""
from langgraph.graph import StateGraph, END
from langchain_core.runnables import RunnableLambda
import datetime
import time
from pydantic import BaseModel

# ------------------ Config ------------------
CHANGE_INTERVAL_HOURS = 72  # hospital protocol


# ------------------ Helper Functions ------------------
def fetch_patients_with_catheters():
    """Mock patient IDs with catheter devices."""
    return ["patient-001", "patient-002", "patient-003"]


def fetch_catheter_data(patient_id):
    """Mock catheter insertion times for test patients."""
    now = datetime.datetime.now(datetime.timezone.utc)
    patient_offsets = {
        "patient-001": 100,  # 100 hours ago (overdue)
        "patient-002": 12,   # 12 hours ago (recent)
        "patient-003": 70,   # 70 hours ago (borderline, safely under 72)
    }
    offset_hours = patient_offsets.get(patient_id)
    if offset_hours is not None:
        inserted_time = now - datetime.timedelta(hours=offset_hours)
        inserted_iso = inserted_time.strftime("%Y-%m-%dT%H:%M:%SZ")
        return {
            "patient_id": patient_id,
            "inserted": inserted_iso,
            "device": {"id": "mock-device", "type": "catheter"}
        }
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
    return {
        "catheter_data": catheter_data,
        "hours_since": hours
    }


def decide_action_node(state):
    if state.hours_since > CHANGE_INTERVAL_HOURS:
        return {"status": "overdue"}
    elif state.hours_since > CHANGE_INTERVAL_HOURS - 2:
        return {"status": "borderline"}
    else:
        return {"status": "ok"}


def notify_staff_node(state):
    patient = state.catheter_data["patient_id"]
    print(f"🚨 ALERT: Patient {patient} needs catheter change! {state.hours_since:.1f} hours since insertion.")
    return {"notified": True}


def reschedule_node(state):
    print("⏱️ Rescheduling check in 24 hours...")
    time.sleep(1)  # Simulating delay. Replace with cron in prod.
    return {}


# ------------------ Build LangGraph ------------------
# Define a minimal state schema for LangGraph using Pydantic
class State(BaseModel):
    patient_id: str
    catheter_data: dict = None
    hours_since: float = None
    status: str = None


graph = StateGraph(state_schema=State)

# Add nodes
graph.add_node("check_schedule", RunnableLambda(check_schedule_node))
graph.add_node("decide_action", RunnableLambda(decide_action_node))
graph.add_node("notify_staff", RunnableLambda(notify_staff_node))
graph.add_node("reschedule", RunnableLambda(reschedule_node))

# Set entry point and edges
graph.set_entry_point("check_schedule")
graph.add_edge("check_schedule", "decide_action")
graph.add_conditional_edges("decide_action", lambda state: state.status, {
    "overdue": "notify_staff",
    "borderline": "reschedule",
    "ok": "reschedule",
    "no_data": END
})
graph.add_edge("notify_staff", "reschedule")
graph.add_edge("reschedule", END)

app = graph.compile()


# ------------------ Print Summary ------------------
def print_summary(patient_id, result):
    status = result.get("status")
    if status == "ok":
        icon = "✅"
    elif status == "overdue":
        icon = "🛑"
    elif status == "borderline":
        icon = "⚠️"
    else:
        icon = "❓"

    print(f"{icon} Summary for {patient_id}: {result}")
    print("-" * 40)


# ------------------ Run the Agent ------------------
if __name__ == "__main__":
    mock_patients = fetch_patients_with_catheters()
    for patient_id in mock_patients:
        print(f"\n▶ Running agent for patient {patient_id}...")
        result = app.invoke({"patient_id": patient_id})
        print_summary(patient_id, result)
