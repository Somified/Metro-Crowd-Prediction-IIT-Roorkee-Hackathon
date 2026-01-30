# Metro Crowd Prediction – IIT Roorkee Hackathon

This repository contains the **completed backend** for a metro crowd guidance system.  
The backend provides **coach-level relative crowd estimation**, policy awareness, and accessibility modeling for the Delhi Metro (Blue & Yellow Lines).

Frontend work will be done on a separate branch.
If you are a collaborator, please create a new branch before proceeding. do not merge directly with main.
---

## ✅ Backend Status
**Backend (v1) is complete and frozen.**  
It is ready for integration with the frontend.

---

## 🚀 Features Implemented

- Coach-level **relative crowd estimation** (8 coaches)
- Time-of-day demand modeling (peak / off-peak)
- Directional bias (UP / DOWN)
- Line-level baseline bias
- **Interchange station bias** (e.g., Rajiv Chowk, Hauz Khas)
- Automatic line inference for single-line stations
- Explicit handling of interchange stations
- Strict enforcement of **women-reserved coach**
- Continuous **accessibility score (0–1)** based on crowd + coach position
- Privacy-safe, sensor-agnostic, explainable logic

---

## 🛠 Tech Stack
- **Python**
- **FastAPI**
- **Uvicorn**

---

## 💻 How to Run Locally

1. Clone the repository
```bash
git clone https://github.com/Somified/Metro-Crowd-Prediction-IIT-Roorkee-Hackathon.git
cd Metro-Crowd-Prediction-IIT-Roorkee-Hackathon
2. Install dependencies
pip install fastapi uvicorn

3.Run backend server
uvicorn app.main:app --reload

4️⃣ Access the API
Root check: http://127.0.0.1:8000
Interactive docs: http://127.0.0.1:8000/docs

