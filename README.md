# 🛡️ Catheter Watchdog Agent

This project demonstrates an **agent-based patient monitoring system** designed to flag overdue catheter changes. It uses a decision-making flow powered by **LangGraph** and includes mock data for local testing.

## 🧠 What It Does

- Checks how long a patient's catheter has been in place.
- Flags and alerts if it's overdue based on hospital policy (72 hours).
- Loops through multiple mock patients.
- Prints alerts for those needing a change.

## 🚀 Files Overview

### `watchdog_mock.py`
Main script that:

- Defines a LangGraph agent flow with 4 nodes:
  - `check_schedule`
  - `decide_action`
  - `notify_staff`
  - `reschedule`
- Uses **mock patient data** with preset catheter insertion times.
- Outputs console alerts for overdue catheters.

### `hapi/`
Contains test scripts that attempt to connect to the [HAPI FHIR public test server](https://hapi.fhir.org/). These were intended to:

- Pull real patient/device data for live testing.

🔴 **Heads up:** The HAPI server currently has **no usable catheter-related data**, so these scripts will not return useful results. For now, `watchdog_mock.py` uses mocked data to simulate a working system.

## 🧪 Running the Demo

```bash
python watchdog_mock.py
```

Expected Output:

- Alerts in terminal if mock patients have overdue catheters.
- Loops through three predefined mock patients.

## 🛠️ Next Steps (Optional Ideas)
- Replace mocks with real FHIR data if available (HAPI or internal sandbox).
- Send alerts via Slack, email, or EHR system.
- Add a UI dashboard to display alert statuses.

## ✅ Dependencies
- [LangGraph](https://github.com/langchain-ai/langgraph)
- [LangChain](https://github.com/langchain-ai/langchain)
- Python 3.9+

## 🧾 License
[MIT](LICENSE). Built for learning, prototyping, and showing off agent-powered healthcare workflows.
