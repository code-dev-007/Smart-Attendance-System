import cv2
import numpy as np
import face_recognition
import pandas as pd
import streamlit as st
from datetime import datetime, timedelta
import csv
from pathlib import Path
from PIL import Image
import plotly.express as px
import plotly.graph_objects as go

class EnhancedAttendanceSystem:
    def __init__(self):
        self.initialize_system()
        self.load_known_faces()
        
    def initialize_system(self):
        """Initialize necessary directories and files"""
        # Create required directories
        for directory in ["dataset", "attendance_records", "images"]:
            Path(directory).mkdir(exist_ok=True)
        
        # Initialize students.csv if it doesn't exist
        if not Path("students.csv").exists():
            with open("students.csv", "w", newline='') as f:
                writer = csv.writer(f)
                writer.writerow(["Name", "Course", "Section", "Roll No", "Email", "Student ID"])
                
        # Initialize settings.csv if it doesn't exist
        if not Path("settings.csv").exists():
            with open("settings.csv", "w", newline='') as f:
                writer = csv.writer(f)
                writer.writerow(["Setting", "Value"])
                writer.writerow(["late_threshold", "09:00"])
                writer.writerow(["enable_email", "True"])
                writer.writerow(["enable_whatsapp", "True"])

    def load_known_faces(self):
        """Load known faces and their encodings from the dataset"""
        self.known_face_encodings = []
        self.known_face_ids = []
        self.student_info = {}  # To store additional student info
        
        # Load student data
        try:
            students_df = pd.read_csv("students.csv")
            for _, row in students_df.iterrows():
                student_id = row['Student ID']
                self.student_info[student_id] = {
                    'name': row['Name'],
                    'course': row['Course'],
                    'section': row['Section'],
                    'roll_no': row['Roll No'],
                    'email': row['Email']
                }
        except Exception as e:
            print(f"Error loading student data: {e}")
        
        # Load face encodings
        for image_path in Path("dataset").glob("*.jpg"):
            try:
                image = face_recognition.load_image_file(str(image_path))
                encodings = face_recognition.face_encodings(image)
                if encodings:
                    self.known_face_encodings.append(encodings[0])
                    self.known_face_ids.append(image_path.stem)
            except Exception as e:
                print(f"Error loading {image_path}: {e}")

    def recognize_face(self, frame):
        """Recognize faces in the frame"""
        # Convert frame to RGB
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        
        # Find all faces in the frame
        face_locations = face_recognition.face_locations(rgb_frame)
        face_encodings = face_recognition.face_encodings(rgb_frame, face_locations)
        
        recognized_students = []
        
        for face_encoding in face_encodings:
            if len(self.known_face_encodings) > 0:
                matches = face_recognition.compare_faces(self.known_face_encodings, face_encoding)
                if True in matches:
                    first_match_index = matches.index(True)
                    student_id = self.known_face_ids[first_match_index]
                    recognized_students.append(student_id)
        
        return recognized_students, face_locations

    def mark_attendance(self, student_id):
        """Mark attendance for a student"""
        today = datetime.now().date()
        attendance_file = f"attendance_records/attendance_{today}.csv"
        current_time = datetime.now().strftime('%I:%M %p')
        
        # Create attendance file for today if it doesn't exist
        if not Path(attendance_file).exists():
            with open(attendance_file, "w", newline='') as f:
                writer = csv.writer(f)
                writer.writerow(["Student ID", "Name", "Course", "Section", "Roll No", "Email", "Time"])
        
        # Check if student already marked attendance today
        try:
            df = pd.read_csv(attendance_file)
            if student_id not in df['Student ID'].values:
                student_info = self.student_info.get(student_id, {})
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
            # Generate student ID if not provided
            if not student_id:
                student_id = f"{course[:3]}{section}{roll_no}"
            
            # Save student info
            with open("students.csv", "a", newline='') as f:
                writer = csv.writer(f)
                writer.writerow([name, course, section, roll_no, email, student_id])
            
            # Save student image
            img_path = f"dataset/{student_id}.jpg"
            image_data.save(img_path)
            
            # Reload known faces
            self.load_known_faces()
            return True, student_id
        except Exception as e:
            print(f"Error registering student: {e}")
            return False, None

    def get_attendance_records(self, start_date, end_date):
        """Get attendance records between two dates"""
        records = []
        current_date = start_date
        
        while current_date <= end_date:
            attendance_file = f"attendance_records/attendance_{current_date}.csv"
            if Path(attendance_file).exists():
                df = pd.read_csv(attendance_file)
                df['Date'] = current_date
                records.append(df)
            current_date += timedelta(days=1)
            
        if records:
            combined_records = pd.concat(records, ignore_index=True)
            students_df = pd.read_csv("students.csv")

            # Merge on Student ID to get consistent full info
            full_records = combined_records.merge(
                students_df,
                on="Student ID",
                how="left",
                suffixes=('', '_student')  # Avoids _x, _y issues
            )

            # Fill missing Name, Course, etc., if any
            for col in ['Name', 'Course', 'Section', 'Roll No', 'Email']:
               student_col = f"{col}_student"
               if student_col in full_records.columns:
                    full_records[col] = full_records[col].fillna(full_records[student_col])

            # Drop extra columns
            full_records = full_records.drop(columns=[c for c in full_records.columns if c.endswith('_student')])

            # Ensure Date column is in datetime format
            full_records['Date'] = pd.to_datetime(full_records['Date'], errors='coerce')

            # Convert Date column to string format
            full_records['Date'] = full_records['Date'].dt.strftime('%Y-%m-%d')
            
            return full_records

        return pd.DataFrame()

    def get_absent_students(self, date):
        """Get list of absent students for a specific date"""
        try:
            # Get all registered students
            all_students = pd.read_csv("students.csv")
            
            # Get present students for the date
            attendance_file = f"attendance_records/attendance_{date}.csv"
            if Path(attendance_file).exists():
                present_students = pd.read_csv(attendance_file)
                
                # Find absent students (all students not in present list)
                absent_students = all_students[~all_students['Student ID'].isin(present_students['Student ID'])]
                
                return absent_students
            else:
                # If no attendance file exists, all students are absent
                return all_students
        except Exception as e:
            print(f"Error getting absent students: {e}")
            return pd.DataFrame()

    def get_dashboard_metrics(self):
        """Get metrics for dashboard"""
        try:
            total_students = len(pd.read_csv("students.csv"))
        except:
            total_students = 0
        
        today = datetime.now().date()
        attendance_file = f"attendance_records/attendance_{today}.csv"
        
        if Path(attendance_file).exists():
            present_students = len(pd.read_csv(attendance_file))
        else:
            present_students = 0
            
        absent_students = total_students - present_students
        attendance_rate = (present_students / total_students * 100) if total_students > 0 else 0
        
        return {
            "total_students": total_students,
            "present_today": present_students,
            "absent_today": absent_students,
            "attendance_rate": attendance_rate
        }

    def get_weekly_trend(self):
        """Get weekly attendance trend data"""
        dates = [(datetime.now() - timedelta(days=x)).date() for x in range(6, -1, -1)]
        attendance_counts = []
        
        for date in dates:
            attendance_file = f"attendance_records/attendance_{date}.csv"
            if Path(attendance_file).exists():
                count = len(pd.read_csv(attendance_file))
            else:
                count = 0
            attendance_counts.append(count)
            
        return dates, attendance_counts
    
    

def create_ui():
    """Create the main UI"""
    st.set_page_config(page_title="Smart Attendance System", layout="wide", page_icon="📊")
    
    # Custom CSS
    st.markdown("""
        <style>
        .main {
            padding: 0rem 1rem;
        }
        .stButton>button {
            width: 100%;
            border-radius: 5px;
            height: 3em;
            background-color: #4CAF50;
            color: white;
        }
        .css-1d391kg {
            padding: 1rem;
        }
        .metric-card {
            background-color: #1e1e1e;
            padding: 1rem;
            border-radius: 10px;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        }
        </style>
    """, unsafe_allow_html=True)
    
    # Initialize system
    if 'attendance_system' not in st.session_state:
        st.session_state.attendance_system = EnhancedAttendanceSystem()
        st.session_state.camera_active = False
        st.session_state.marked_today = set()
    
    # Sidebar navigation
    with st.sidebar:
        logo_path = "images\\logo.png"
        if Path(logo_path).exists():
            st.image(logo_path, width=100)
        else:
            st.warning("Logo image not found at 'images/logo.png'")
        nav_selection = st.selectbox(
            "Navigation",
            ["Dashboard", "Mark Attendance", "Register Student", "View Records", "Absent Students", "Settings"]
        )
    
    # Page routing
    if nav_selection == "Dashboard":
        show_dashboard()
    elif nav_selection == "Mark Attendance":
        show_attendance_page()
    elif nav_selection == "Register Student":
        show_registration_page()
    elif nav_selection == "View Records":
        show_records_page()
    elif nav_selection == "Absent Students":
        show_absent_students_page()
    elif nav_selection == "Settings":
        show_settings_page()
    
    # Footer
    st.markdown("<div style='text-align: center; margin-top: 2rem; size:10px;'>© 2025 Automatic Attendance System Using Facial Recognition <br>Developed by Sanath Shukla </div>", unsafe_allow_html=True)

def show_dashboard():
    """Display dashboard page"""
    st.title("📊 Attendance Dashboard")
    
    # Get metrics
    metrics = st.session_state.attendance_system.get_dashboard_metrics()
    
    # Display metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Students", metrics["total_students"])
    with col2:
        st.metric("Present Today", metrics["present_today"])
    with col3:
        st.metric("Absent Today", metrics["absent_today"])
    with col4:
        st.metric("Attendance Rate", f"{metrics['attendance_rate']:.1f}%")
    
    # Weekly trend
    dates, counts = st.session_state.attendance_system.get_weekly_trend()
    
    # Create charts
    col1, col2 = st.columns(2)
    
    with col1:
        fig_trend = go.Figure()
        fig_trend.add_trace(go.Scatter(
            x=[d.strftime("%Y-%m-%d") for d in dates],
            y=counts,
            mode='lines+markers',
            name='Attendance'
        ))
        fig_trend.update_layout(
            title="Weekly Attendance Trend",
            xaxis_title="Date",
            yaxis_title="Students Present",
            template="plotly_dark"
        )
        st.plotly_chart(fig_trend, use_container_width=True)
    
    with col2:
        fig_pie = go.Figure(data=[go.Pie(
            labels=['Present', 'Absent'],
            values=[metrics["present_today"], metrics["absent_today"]],
            hole=.3
        )])
        fig_pie.update_layout(
            title="Today's Attendance Distribution",
            template="plotly_dark"
        )
        st.plotly_chart(fig_pie, use_container_width=True)

def show_attendance_page():
    """Display attendance marking page"""
    st.title("📸 Mark Attendance")
    
    method = st.radio("Select Attendance Method", ["Face Recognition"])
    
    if method == "Face Recognition":
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
                    
                    # Draw rectangles around faces
                    for (top, right, bottom, left), student_id in zip(face_locations, recognized_students):
                        cv2.rectangle(frame, (left, top), (right, bottom), (0, 255, 0), 2)
                        cv2.putText(frame, student_id, (left, top - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 255, 0), 2)
                    
                    # Mark attendance for recognized students
                    for student_id in recognized_students:
                        if student_id not in st.session_state.marked_today:
                            if st.session_state.attendance_system.mark_attendance(student_id):
                                st.session_state.marked_today.add(student_id)
                                st.success(f"Attendance marked for Student {student_id}")
                    
                    stframe.image(frame, channels="BGR")
                
                cap.release()
        
        with col2:
            st.subheader("Recently Marked")
            for student_id in list(st.session_state.marked_today)[-5:]:
                st.write(f"✅ {student_id}")
    
    
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
                st.success(f"Student registered successfully! Student ID: {generated_id}")
                st.balloons()
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

def show_absent_students_page():
    """Display absent students page"""
    st.title("❌ Absent Students")
    
    selected_date = st.date_input("Select Date", datetime.now().date())
    
    if st.button("Show Absent Students"):
        absent_students = st.session_state.attendance_system.get_absent_students(selected_date)
        
        if not absent_students.empty:
            st.subheader(f"Absent Students on {selected_date.strftime('%Y-%m-%d')}")
            
            # Calculate total students for percentage
            total_students = len(absent_students) + len(st.session_state.attendance_system.get_attendance_records(selected_date, selected_date))
            
            # Display metrics
            col1, col2 = st.columns(2)
            with col1:
                st.metric("Total Absent Students", len(absent_students))
            with col2:
                st.metric("Absent Percentage", f"{(len(absent_students)/total_students*100):.1f}%")
            
            # Display absent students table
            st.dataframe(absent_students, use_container_width=True)
            
            # Download button
            st.download_button(
                "Download Absent List",
                absent_students.to_csv(index=False),
                f"absent_students_{selected_date}.csv",
                "text/csv"
            )
        else:
            st.info(f"No absent students found for {selected_date.strftime('%Y-%m-%d')}")

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
        datetime.strptime(settings_df.loc["late_threshold", "Value"], "%H:%M").time() if "late_threshold" in settings_df.index else datetime.strptime("09:00", "%H:%M").time()
    )

    st.subheader("Alert Settings")
    enable_email = st.checkbox(
        "Enable Email Alerts",
        bool(settings_df.loc["enable_email", "Value"] == "True") if "enable_email" in settings_df.index else False
    )
    enable_whatsapp = st.checkbox(
        "Enable WhatsApp Alerts",
        bool(settings_df.loc["enable_whatsapp", "Value"] == "True") if "enable_whatsapp" in settings_df.index else False
    )

    if enable_email:
        email_address = st.text_input("Email Address", value=settings_df.loc["email_address", "Value"] if "email_address" in settings_df.index else "")
    else:
        email_address = ""

    if enable_whatsapp:
        whatsapp_number = st.text_input("WhatsApp Number", value=settings_df.loc["whatsapp_number", "Value"] if "whatsapp_number" in settings_df.index else "")
    else:
        whatsapp_number = ""

    if st.button("Save Settings"):
        settings_df.loc["late_threshold", "Value"] = late_threshold.strftime("%H:%M")
        settings_df.loc["enable_email", "Value"] = str(enable_email)
        settings_df.loc["enable_whatsapp", "Value"] = str(enable_whatsapp)
        settings_df.loc["email_address", "Value"] = email_address
        settings_df.loc["whatsapp_number", "Value"] = whatsapp_number

        settings_df.to_csv("settings.csv")

        st.success("Settings saved successfully!")

if __name__ == "__main__":
    create_ui()