# app.py

import cv2
import numpy as np
import face_recognition
import pandas as pd
import streamlit as st
from datetime import datetime, timedelta
import csv
from pathlib import Path
from PIL import Image
import plotly.graph_objects as go

from app import create_ui

class EnhancedAttendanceSystem:
    def __init__(self):
        self.initialize_system()
        self.load_known_faces()

    def initialize_system(self):
        """Initialize necessary directories and files"""
        for directory in ["dataset", "attendance_records", "images"]:
            Path(directory).mkdir(exist_ok=True)

        if not Path("students.csv").exists():
            with open("students.csv", "w", newline='') as f:
                writer = csv.writer(f)
                writer.writerow(["Name", "Course", "Section", "Roll No", "Email", "Student ID"])

        if not Path("settings.csv").exists():
            with open("settings.csv", "w", newline='') as f:
                writer = csv.writer(f)
                writer.writerow(["Setting", "Value"])
                writer.writerow(["late_threshold", "09:00"])
                writer.writerow(["enable_email", "True"])
                writer.writerow(["enable_whatsapp", "True"])

    def load_known_faces(self):
        """Load known faces and student info"""
        self.known_face_encodings = []
        self.known_face_ids = []
        self.student_info = {}

        try:
            students_df = pd.read_csv("students.csv")
            students_df = students_df.drop_duplicates(subset="Student ID")  # remove duplicates
            for _, row in students_df.iterrows():
                student_id = str(row['Student ID']).strip()
                if pd.notna(student_id) and student_id != "":
                    self.student_info[student_id] = {
                        'name': row['Name'],
                        'course': row['Course'],
                        'section': row['Section'],
                        'roll_no': row['Roll No'],
                        'email': row['Email']
                    }
        except Exception as e:
            print(f"Error loading student data: {e}")

        for image_path in Path("dataset").glob("*.jpg"):
            try:
                student_id = image_path.stem
                if student_id in self.student_info:
                    image = face_recognition.load_image_file(str(image_path))
                    encodings = face_recognition.face_encodings(image)
                    if encodings:
                        self.known_face_encodings.append(encodings[0])
                        self.known_face_ids.append(student_id)
            except Exception as e:
                print(f"Error loading {image_path}: {e}")

    def recognize_face(self, frame):
        """Recognize faces and return student names"""
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        face_locations = face_recognition.face_locations(rgb_frame)
        face_encodings = face_recognition.face_encodings(rgb_frame, face_locations)

        recognized_students = []

        for face_encoding in face_encodings:
            if len(self.known_face_encodings) > 0:
                matches = face_recognition.compare_faces(self.known_face_encodings, face_encoding)
                face_distances = face_recognition.face_distance(self.known_face_encodings, face_encoding)
                best_match_index = np.argmin(face_distances)
                if matches[best_match_index]:
                    student_id = self.known_face_ids[best_match_index]
                    recognized_students.append(student_id)

        return recognized_students, face_locations

    def mark_attendance(self, student_id):
        """Mark attendance for a student without duplication"""
        today = datetime.now().date()
        attendance_file = f"attendance_records/attendance_{today}.csv"
        current_time = datetime.now().strftime("%H:%M:%S")

        if not Path(attendance_file).exists():
            with open(attendance_file, "w", newline='') as f:
                writer = csv.writer(f)
                writer.writerow(["Student ID", "Name", "Course", "Section", "Roll No", "Email", "Time"])

        try:
            df = pd.read_csv(attendance_file)
            if student_id not in df['Student ID'].values:
                student_info = self.student_info.get(student_id)
                if student_info:
                    with open(attendance_file, "a", newline='') as f:
                        writer = csv.writer(f)
                        writer.writerow([
                            student_id,
                            student_info.get('name', ''),
                            student_info.get('course', ''),
                            student_info.get('section', ''),
                            student_info.get('roll_no', ''),
                            student_info.get('email', ''),
                            current_time
                        ])
                    return True
        except Exception as e:
            print(f"Error marking attendance: {e}")
        return False

    def register_student(self, name, course, section, roll_no, email, image_data, student_id=None):
        """Register a new student"""
        try:
            if not student_id:
                student_id = f"{course[:3]}{section}{roll_no}"

            students_df = pd.read_csv("students.csv")

            # Check if the student already exists
            if student_id in students_df['Student ID'].values:
                return False, student_id

            with open("students.csv", "a", newline='') as f:
                writer = csv.writer(f)
                writer.writerow([name, course, section, roll_no, email, student_id])

            img_path = f"dataset/{student_id}.jpg"
            image_data.save(img_path)

            self.load_known_faces()
            return True, student_id
        except Exception as e:
            print(f"Error registering student: {e}")
            return False, None
        
def show_attendance_page():
    """Display attendance marking page"""
    st.title("📸 Mark Attendance")

    col1, col2 = st.columns([3, 1])

    with col1:
        if st.button("Start Camera" if not st.session_state.camera_active else "Stop Camera"):
            st.session_state.camera_active = not st.session_state.camera_active

        if st.session_state.camera_active:
            stframe = st.empty()
            cap = cv2.VideoCapture(0)

            while st.session_state.camera_active:
                ret, frame = cap.read()
                if not ret:
                    st.error("Failed to access camera")
                    break

                # Recognize faces
                recognized_students, face_locations = st.session_state.attendance_system.recognize_face(frame)

                # Draw rectangles around faces with names
                for (top, right, bottom, left), student_id in zip(face_locations, recognized_students):
                    name = st.session_state.attendance_system.student_info.get(student_id, {}).get('name', 'Unknown')
                    cv2.rectangle(frame, (left, top), (right, bottom), (0, 255, 0), 2)
                    cv2.putText(frame, name, (left, top - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)

                # Mark attendance for recognized students
                for student_id in recognized_students:
                    if student_id not in st.session_state.marked_today:
                        if st.session_state.attendance_system.mark_attendance(student_id):
                            st.session_state.marked_today.add(student_id)
                            student_name = st.session_state.attendance_system.student_info.get(student_id, {}).get('name', '')
                            st.success(f"Attendance marked for {student_name}")

                stframe.image(frame, channels="BGR")

            cap.release()

    with col2:
        st.subheader("Recently Marked")
        for student_id in list(st.session_state.marked_today)[-5:]:
            student_name = st.session_state.attendance_system.student_info.get(student_id, {}).get('name', '')
            st.write(f"✅ {student_name}")

def show_registration_page():
    """Display student registration page"""
    st.title("👤 Register New Student")

    col1, col2 = st.columns(2)

    with col1:
        name = st.text_input("Name*", placeholder="Full name")
        course = st.text_input("Course*", placeholder="e.g. Computer Science")
        section = st.text_input("Section*", placeholder="e.g. A")
        roll_no = st.text_input("Roll No*", placeholder="e.g. 123")
        email = st.text_input("Email", placeholder="optional@example.com")
        student_id = st.text_input("Student ID", placeholder="Leave blank to auto-generate")

    with col2:
        st.write("Take Photo*")
        photo = st.camera_input("Capture")

    if st.button("Register Student"):
        if name and course and section and roll_no and photo:
            success, generated_id = st.session_state.attendance_system.register_student(
                name, course, section, roll_no, email, Image.open(photo), student_id
            )
            if success:
                st.success(f"Student {name} registered successfully!")
                st.balloons()
            else:
                st.error("Registration failed. Try again.")
        else:
            st.error("Please fill all required fields (*)")

def show_records_page():
    """Display attendance records page"""
    st.title("📋 Attendance Records")

    col1, col2 = st.columns(2)

    with col1:
        start_date = st.date_input("Start Date", datetime.now().date())
    with col2:
        end_date = st.date_input("End Date", datetime.now().date())

    if start_date and end_date:
        if start_date <= end_date:
            records = st.session_state.attendance_system.get_attendance_records(start_date, end_date)

            if not records.empty:
                st.download_button(
                    "Download Records",
                    records.to_csv(index=False),
                    "attendance_records.csv",
                    "text/csv"
                )
                st.dataframe(records, use_container_width=True)
            else:
                st.info("No records found for selected date range")
        else:
            st.error("End date must be after start date")

def show_settings_page():
    """Display settings page"""
    st.title("⚙️ Settings")

    # Load current settings
    try:
        settings_df = pd.read_csv("settings.csv", index_col="Setting")
    except FileNotFoundError:
        settings_df = pd.DataFrame(columns=["Setting", "Value"])

    st.subheader("Attendance Settings")
    late_threshold = st.time_input(
        "Late Attendance Threshold",
        datetime.strptime(settings_df.loc["late_threshold", "Value"], "%H:%M").time()
        if "late_threshold" in settings_df.index else datetime.strptime("09:00", "%H:%M").time()
    )

    if st.button("Save Settings"):
        settings_df.loc["late_threshold", "Value"] = late_threshold.strftime("%H:%M")
        settings_df.to_csv("settings.csv")
        st.success("Settings saved successfully!")

# --- CSS Styling ---
st.markdown("""
    <style>
        .sidebar .sidebar-content {
            background-image: linear-gradient(#f5f7fa, #c3cfe2);
            padding: 1rem;
        }
        .profile-card {
            background: white;
            padding: 1rem;
            border-radius: 10px;
            box-shadow: 2px 2px 10px rgba(0,0,0,0.1);
            text-align: center;
            margin-bottom: 2rem;
        }
        .profile-card img {
            border-radius: 50%;
            width: 120px;
            height: 120px;
            object-fit: cover;
            margin-bottom: 10px;
        }
        .profile-card h3 {
            margin: 0;
            font-size: 1.2rem;
            color: #333;
        }
    </style>
""", unsafe_allow_html=True)




if __name__ == "__main__":

    with st.sidebar:
        st.markdown('<div class="profile-card">', unsafe_allow_html=True)
        st.image("images/logo.png", width=120)
        st.markdown("<h3>Smart Attendance</h3>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

        page = st.radio("Navigation", ("Attendance", "Register", "Records", "Settings"))

    create_ui()

