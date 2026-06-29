# 🎓 Smart Attendance System

An automated attendance tracking system built with **Streamlit** and **Face Recognition**, featuring a clean dark-themed web interface for managing student attendance with real-time camera-based face detection.

---

## 📸 Screenshots

### 🏠 Dashboard
![Dashboard](screenshots/dashboard.png)

The main dashboard displays:
- **Total Students** registered in the system
- **Present Today** count
- **Absent Today** count
- **Attendance Rate** percentage
- **Weekly Attendance Trend** line chart
- **Today's Attendance Distribution** pie chart

---

### 📸 Mark Attendance
![Mark Attendance](screenshots/mark_attendance.png)

- Select attendance method: **Face Recognition**
- Click **Start Camera** to activate webcam
- System automatically detects and recognizes faces
- Recognized students are marked present in real-time
- **Recently Marked** panel shows latest entries

---

### 👤 Register New Student
![Register Student](screenshots/register_student.png)

Fill in student details:
- **Name** (required)
- **Course** (required)
- **Section** (required)
- **Roll No** (required)
- **Email** (optional)
- **Student ID** (auto-generated if left blank)
- Capture photo using the embedded **camera widget**
- Click **Register Student** to save

---

### 📋 Attendance Records
![View Records](screenshots/view_records.png)

- Select **Start Date** and **End Date**
- Records are fetched and displayed in a table
- Option to **Download Records** as CSV

---

### ❌ Absent Students
![Absent Students](screenshots/absent_students.png)

- Select a **date** to view absentees
- Click **Show Absent Students**
- Displays list of students who were not present
- Option to download the absent list as CSV

---

### ⚙️ Settings
![Settings](screenshots/settings.png)

Configure system behaviour:
- **Late Attendance Threshold** — set time after which attendance is marked late (e.g. 09:30)
- **Enable Email Alerts** — sends notification emails
- **Enable WhatsApp Alerts** — sends WhatsApp notifications
- Enter **Email Address** or **WhatsApp Number** as needed
- Click **Save Settings** to persist changes

---

## 📁 Project Structure

```
smart_attendance/
├── app.py                        # Main Streamlit entry point
├── requirements.txt              # Python dependencies
├── packages.txt                  # System-level dependencies
├── students.csv                  # Student database
├── settings.csv                  # Saved app settings
│
├── pages/                        # One file per screen
│   ├── __init__.py
│   ├── dashboard.py              # Dashboard with charts
│   ├── mark_attendance.py        # Live camera face recognition
│   ├── register_student.py       # Student registration form
│   ├── view_records.py           # Date-range attendance records
│   ├── absent_students.py        # Absent student report
│   └── settings.py               # App configuration
│
├── utils/                        # Shared backend logic
│   ├── __init__.py
│   └── system.py                 # AttendanceSystem core class
│
├── assets/                       # Static files
│   ├── logo.png                  # Sidebar logo
│   └── haarcascade_frontalface_default.xml
│
├── dataset/                      # Student face images (auto-created)
├── attendance_records/           # Daily attendance CSVs (auto-created)
└── screenshots/                  # README screenshots
```

---

## 🚀 Installation

### 1. Clone the repository
```bash
git clone https://github.com/your-username/smart-attendance.git
cd smart-attendance
```

### 2. Install system packages (Linux / Streamlit Cloud)
```bash
sudo apt-get install cmake libgl1-mesa-glx
```

### 3. Create virtual environment
```bash
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
```

### 4. Install Python dependencies
```bash
pip install -r requirements.txt
```

---

## ▶️ Run

```bash
streamlit run app.py
```

Open **http://localhost:8501** in your browser.

---

## 🛠️ Dependencies

| Package | Purpose |
|---|---|
| `streamlit` | Web UI framework |
| `opencv-python-headless` | Camera & image processing |
| `face_recognition` | Face detection & matching |
| `numpy` | Numerical operations |
| `pandas` | CSV data handling |
| `plotly` | Interactive charts |
| `Pillow` | Image handling |

Full list in `requirements.txt`.

---

## ⚙️ System Requirements

- Python **3.8+**
- Webcam (for registration & attendance marking)
- Minimum **4 GB RAM** (face_recognition is CPU-intensive)
- Good lighting for accurate face detection

---

## 🔧 Troubleshooting

| Problem | Solution |
|---|---|
| Camera not working | Allow camera access in browser settings |
| Face not recognized | Ensure good lighting; re-register with a clearer photo |
| Slow recognition | Reduce number of registered faces; check CPU usage |
| `dlib` install error | Install `cmake` system package first |

---

## 📄 License

MIT License © 2025 — Developed by **Sanath Shukla**
