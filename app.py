import streamlit as st
import sqlite3
import hashlib
from datetime import datetime
import pandas as pd
import os
import base64
import mimetypes

# ============================================================
# OPTIONAL LIBRARIES
# ============================================================

try:
    import ollama
    OLLAMA_AVAILABLE = True
except ImportError:
    OLLAMA_AVAILABLE = False


try:
    from pypdf import PdfReader
    PDF_AVAILABLE = True
except ImportError:
    PDF_AVAILABLE = False


try:
    from docx import Document
    DOCX_AVAILABLE = True
except ImportError:
    DOCX_AVAILABLE = False


st.set_page_config(
    page_title="AI Teaching Assistant",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)


# ================= BACKGROUND IMAGE =================

def set_background(image_path):

    if not os.path.exists(image_path):
        st.error(f"Background image not found: {image_path}")
        return

    with open(image_path, "rb") as image_file:
        encoded = base64.b64encode(image_file.read()).decode()

    mime_type = mimetypes.guess_type(image_path)[0] or "image/jpeg"

    st.markdown(
        f"""
        <style>

        .stApp {{
            background-image: url("data:{mime_type};base64,{encoded}") !important;
            background-size: cover !important;
            background-position: center !important;
            background-repeat: no-repeat !important;
            background-attachment: fixed !important;
        }}

        header[data-testid="stHeader"] {{
            background: transparent !important;
        }}

        .block-container {{
            background: transparent !important;
        }}

        </style>
        """,
        unsafe_allow_html=True
    )


# background.jpg must be in same folder as app.py
background_path = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "background.jpg"
)

set_background(background_path)

# ============================================================
# CONFIGURATION
# ============================================================

DB_NAME = "students.db"
OLLAMA_MODEL = "llama3.2"

# Computer field courses available for Student Login/Registration
COMPUTER_COURSES = [
    "BCA",
    "B.Sc. Computer Science",
    "B.Tech Computer Science",
    "Computer Engineering",
    "Information Technology (IT)",
    "Web Development",
    "Python Programming",
    "Data Science",
    "Artificial Intelligence (AI)",
    "Machine Learning",
    "Cyber Security",
    "Cloud Computing",
    "Computer Networking",
    "Software Development",
    "Database Management",
    "Mobile App Development",
    "Game Development",
    "UI/UX Design"
]


# ============================================================
# DATABASE CONNECTION
# ============================================================

def get_connection():

    conn = sqlite3.connect(
        DB_NAME,
        check_same_thread=False
    )

    return conn


# ============================================================
# PASSWORD HASHING
# ============================================================

def hash_password(password):

    return hashlib.sha256(
        password.encode()
    ).hexdigest()


# ============================================================
# DATABASE INITIALIZATION
# ============================================================

def init_database():

    conn = get_connection()

    cursor = conn.cursor()

    # --------------------------------------------------------
    # USERS TABLE
    # --------------------------------------------------------

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            name TEXT NOT NULL,

            username TEXT UNIQUE NOT NULL,

            email TEXT,

            password TEXT NOT NULL,

            role TEXT NOT NULL,

            course TEXT DEFAULT 'BCA',

            created_at TEXT

        )
    """)


    # --------------------------------------------------------
    # AI HISTORY TABLE
    # --------------------------------------------------------

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS ai_history (

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            student_id INTEGER,

            question TEXT,

            answer TEXT,

            created_at TEXT

        )
    """)


    # --------------------------------------------------------
    # QUIZ RESULTS TABLE
    # --------------------------------------------------------

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS quiz_results (

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            student_id INTEGER,

            subject TEXT,

            score INTEGER,

            total INTEGER,

            percentage REAL,

            created_at TEXT

        )
    """)


    # --------------------------------------------------------
    # NOTES TABLE
    # --------------------------------------------------------

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS notes (

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            teacher_id INTEGER,

            title TEXT NOT NULL,

            subject TEXT DEFAULT 'General',

            content TEXT,

            file_name TEXT,

            created_at TEXT

        )
    """)


    conn.commit()

    conn.close()


# ============================================================
# DATABASE MIGRATION
# FIX OLD DATABASE TABLE
# ============================================================

def update_database():

    conn = get_connection()

    cursor = conn.cursor()

    # Get existing columns from notes table

    cursor.execute(
        "PRAGMA table_info(notes)"
    )

    columns = [
        column[1]
        for column in cursor.fetchall()
    ]


    # Add subject column if missing

    if "subject" not in columns:

        try:

            cursor.execute("""
                ALTER TABLE notes
                ADD COLUMN subject TEXT
                DEFAULT 'General'
            """)

            conn.commit()

        except Exception as error:

            print(
                "Database migration error:",
                error
            )


    # Add course column if missing (for existing databases)
    cursor.execute(
        "PRAGMA table_info(users)"
    )

    user_columns = [
        column[1]
        for column in cursor.fetchall()
    ]

    if "course" not in user_columns:
        try:
            cursor.execute("""
                ALTER TABLE users
                ADD COLUMN course TEXT
                DEFAULT 'BCA'
            """)

            conn.commit()

        except Exception as error:
            print(
                "Users course migration error:",
                error
            )

    conn.close()


# ============================================================
# CREATE DEFAULT USERS
# ============================================================

def create_default_users():

    conn = get_connection()

    cursor = conn.cursor()


    # --------------------------------------------------------
    # ADMIN / TEACHER
    # --------------------------------------------------------

    cursor.execute(
        """
        SELECT id
        FROM users
        WHERE username = ?
        """,
        ("admin",)
    )

    admin = cursor.fetchone()


    if admin is None:

        cursor.execute("""
            INSERT INTO users (

                name,
                username,
                email,
                password,
                role,
                created_at

            )

            VALUES (?, ?, ?, ?, ?, ?)
        """, (

            "Admin Teacher",

            "admin",

            "admin@gmail.com",

            hash_password("admin123"),

            "Teacher",

            datetime.now().strftime(
                "%Y-%m-%d %H:%M:%S"
            )

        ))


    # --------------------------------------------------------
    # DEMO STUDENT
    # --------------------------------------------------------

    cursor.execute(
        """
        SELECT id
        FROM users
        WHERE username = ?
        """,
        ("student",)
    )

    student = cursor.fetchone()


    if student is None:

        cursor.execute("""
            INSERT INTO users (

                name,
                username,
                email,
                password,
                role,
                course,
                created_at

            )

            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (

            "Demo Student",

            "student",

            "student@gmail.com",

            hash_password("student123"),

            "Student",

            "BCA",

            datetime.now().strftime(
                "%Y-%m-%d %H:%M:%S"
            )

        ))


    conn.commit()

    conn.close()


# ============================================================
# INITIALIZE DATABASE
# ============================================================

init_database()

update_database()

create_default_users()


# ============================================================
# CUSTOM CSS
# ============================================================

st.markdown("""

<style>

/* ==========================================================
   MAIN BACKGROUND
========================================================== */

.stApp {
    background: linear-gradient(
        135deg,
        #f4f7ff,
        #eef2ff
    );
}

/* ==========================================================
   MAIN CONTAINER
========================================================== */

.block-container {

    padding-top: 2rem;

    padding-left: 3rem;

    padding-right: 3rem;

}


/* ==========================================================
   HERO SECTION
========================================================== */

.hero {

    padding: 35px;

    border-radius: 22px;

    background:
    linear-gradient(
        135deg,
        #667eea,
        #764ba2
    );

    color: white;

    margin-bottom: 25px;

    box-shadow:

        0px 10px 30px

        rgba(
            102,
            126,
            234,
            0.25
        );

}


.hero h1 {

    font-size: 38px;

    margin-bottom: 8px;

}


.hero p {

    font-size: 18px;

}


/* ==========================================================
   LOGIN BACKGROUND
========================================================== */

.login-background {

    padding: 40px;

    border-radius: 25px;

    background:

    linear-gradient(
        135deg,
        #667eea,
        #764ba2,
        #6a11cb
    );

    margin-bottom: 30px;

    color: white;

    text-align: center;

}


/* ==========================================================
   LOGIN CARD
========================================================== */

.login-card {

    background: white;

    padding: 35px;

    border-radius: 20px;

    box-shadow:

        0px 10px 35px

        rgba(
            0,
            0,
            0,
            0.10
        );

}


/* ==========================================================
   CARD
========================================================== */

.card {

    padding: 25px;

    border-radius: 18px;

    background: white;

    box-shadow:

        0px 4px 15px

        rgba(
            0,
            0,
            0,
            0.08
        );

    margin-bottom: 20px;

}


/* ==========================================================
   BUTTON
========================================================== */

.stButton > button {

    width: 100%;

    border-radius: 10px;

    height: 45px;

    font-weight: bold;

}


/* ==========================================================
   SIDEBAR
========================================================== */

section[data-testid="stSidebar"] {

    background:

    linear-gradient(
        180deg,
        #667eea,
        #764ba2
    );

}


section[data-testid="stSidebar"] * {

    color: white;

}


/* ==========================================================
   METRIC
========================================================== */

div[data-testid="stMetric"] {

    background: white;

    padding: 15px;

    border-radius: 15px;

    box-shadow:

        0px 4px 12px

        rgba(
            0,
            0,
            0,
            0.08
        );

}

</style>

""", unsafe_allow_html=True)


# ============================================================
# SESSION STATE
# ============================================================

if "logged_in" not in st.session_state:

    st.session_state.logged_in = False


if "user_id" not in st.session_state:

    st.session_state.user_id = None


if "username" not in st.session_state:

    st.session_state.username = None


if "name" not in st.session_state:

    st.session_state.name = None


if "role" not in st.session_state:

    st.session_state.role = None


if "course" not in st.session_state:

    st.session_state.course = None


# ============================================================
# LOGIN USER
# ============================================================

def login_user(username, password):

    conn = get_connection()

    cursor = conn.cursor()

    cursor.execute("""
        SELECT

            id,

            name,

            username,

            role,

            COALESCE(course, 'BCA')

        FROM users

        WHERE username = ?

        AND password = ?

    """, (

        username,

        hash_password(password)

    ))

    user = cursor.fetchone()

    conn.close()

    return user


# ============================================================
# REGISTER STUDENT
# ============================================================

def register_student(
    name,
    username,
    email,
    password,
    course
):

    conn = get_connection()

    cursor = conn.cursor()

    try:

        cursor.execute("""
            INSERT INTO users (

                name,
                username,
                email,
                password,
                role,
                course,
                created_at

            )

            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (

            name,

            username,

            email,

            hash_password(password),

            "Student",

            course,

            datetime.now().strftime(
                "%Y-%m-%d %H:%M:%S"
            )

        ))

        conn.commit()

        return True

    except sqlite3.IntegrityError:

        return False

    finally:

        conn.close()


# ============================================================
# CHECK OLLAMA
# ============================================================

def check_ollama():

    if not OLLAMA_AVAILABLE:

        return (
            False,
            "Ollama Python library is not installed."
        )


    try:

        ollama.list()

        return (
            True,
            f"Connected to {OLLAMA_MODEL}"
        )

    except Exception:

        return (
            False,
            "Ollama is not running."
        )


# ============================================================
# GENERATE AI ANSWER
# ============================================================

def generate_answer(question):

    if not OLLAMA_AVAILABLE:

        return """
❌ Ollama Python library is not installed.

Install it using:

pip install ollama
"""


    system_prompt = """
You are an AI Teaching Assistant.

Help students learn clearly.

Rules:

1. Explain concepts simply.
2. Give step-by-step explanations.
3. Use examples.
4. Keep answers educational.
5. Help students understand concepts.
6. Answer programming questions with examples.
"""


    try:

        response = ollama.chat(

            model=OLLAMA_MODEL,

            messages=[

                {

                    "role": "system",

                    "content": system_prompt

                },

                {

                    "role": "user",

                    "content": question

                }

            ]

        )


        return response[
            "message"
        ][
            "content"
        ]


    except Exception as error:

        return f"""
❌ Error connecting to Llama 3.2.

{str(error)}

Please check:

1. Ollama is installed.
2. Ollama application is running.
3. Run:

ollama pull llama3.2
"""


# ============================================================
# SAVE AI HISTORY
# ============================================================

def save_ai_history(
    student_id,
    question,
    answer
):

    conn = get_connection()

    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO ai_history (

            student_id,

            question,

            answer,

            created_at

        )

        VALUES (?, ?, ?, ?)
    """, (

        student_id,

        question,

        answer,

        datetime.now().strftime(
            "%Y-%m-%d %H:%M:%S"
        )

    ))

    conn.commit()

    conn.close()


# ============================================================
# LOGIN PAGE
# ============================================================

def login_page():

    st.markdown("""
    <div class="hero">
       <h1 style="text-align: center;">
         🤖 AI Teaching Assistant
       </h1>
    </div>
     """, unsafe_allow_html=True)


    left, center, right = st.columns(
        [1, 2, 1]
    )


    with center:

        tab1, tab2 = st.tabs([

            "🔐 Login",

            "📝 Student Registration"

        ])


        # ----------------------------------------------------
        # LOGIN
        # ----------------------------------------------------

        with tab1:

            st.subheader(
                "Welcome  👋"
            )


            username = st.text_input(
                "Username",
                key="login_username"
            )


            password = st.text_input(
                "Password",
                type="password",
                key="login_password"
            )


            role = st.selectbox(

                "Login As",

                [

                    "Student",

                    "Teacher / Admin"

                ]

            )


            selected_course = None

            if role == "Student":

                selected_course = st.selectbox(

                    "🎓 Select Computer Course",

                    COMPUTER_COURSES,

                    key="login_course"

                )


            if st.button(
                "🚀 Login",
                use_container_width=True
            ):

                if not username or not password:

                    st.warning(
                        "Please enter username and password."
                    )

                else:

                    user = login_user(
                        username,
                        password
                    )


                    if user:

                        (
                            user_id,
                            name,
                            db_username,
                            db_role,
                            db_course
                        ) = user


                        if (
                            role == "Student"
                            and
                            db_role != "Student"
                        ):

                            st.error(
                                "This account is Teacher / Admin."
                            )


                        elif (
                            role == "Teacher / Admin"
                            and
                            db_role != "Teacher"
                        ):

                            st.error(
                                "This account is Student."
                            )


                        elif (
                            role == "Student"
                            and
                            selected_course != db_course
                        ):

                            st.error(
                                f"This student account is registered for "
                                f"{db_course}. Please select the same course."
                            )


                        else:

                            st.session_state.logged_in = True

                            st.session_state.user_id = user_id

                            st.session_state.username = db_username

                            st.session_state.name = name

                            st.session_state.role = db_role
                            st.session_state.course = db_course

                            st.rerun()


                    else:

                        st.error(
                            "Invalid username or password."
                        )


            st.divider()


            st.info(
                "👨‍🏫 Teacher/Admin: admin / admin123"
            )

            st.info(
                "👨‍🎓 Student: student / student123"
            )


        # ----------------------------------------------------
        # REGISTRATION
        # ----------------------------------------------------

        with tab2:

            st.subheader(
                "Create Student Account"
            )


            name = st.text_input(
                "Full Name",
                key="reg_name"
            )


            username = st.text_input(
                "Username",
                key="reg_username"
            )


            email = st.text_input(
                "Email",
                key="reg_email"
            )


            course = st.selectbox(

                "🎓 Select Computer Course",

                COMPUTER_COURSES,

                key="reg_course"

            )


            password = st.text_input(

                "Password",

                type="password",

                key="reg_password"

            )


            confirm_password = st.text_input(

                "Confirm Password",

                type="password",

                key="reg_confirm"

            )


            if st.button(

                "📝 Register",

                use_container_width=True

            ):


                if (
                    not name
                    or
                    not username
                    or
                    not password
                ):

                    st.warning(
                        "Please fill all required fields."
                    )


                elif password != confirm_password:

                    st.error(
                        "Passwords do not match."
                    )


                else:

                    success = register_student(

                        name,

                        username,

                        email,

                        password,

                        course

                    )


                    if success:

                        st.success(
                            "Registration successful! Please login."
                        )

                    else:

                        st.error(
                            "Username already exists."
                        )


# ============================================================
# SIDEBAR
# ============================================================

def sidebar():

    st.sidebar.title(
        "🤖 AI Assistant"
    )


    st.sidebar.write(

        f"👤 {st.session_state.name}"

    )

    if st.session_state.role == "Student":

        st.sidebar.write(

            f"🎓 Course: {st.session_state.course}"

        )


    if st.session_state.role == "Teacher":

        st.sidebar.success(
            "👨‍🏫 Teacher / Admin"
        )

    else:

        st.sidebar.success(
            "👨‍🎓 Student"
        )


    st.sidebar.divider()


    if st.session_state.role == "Student":

        pages = [

            "Dashboard",

            "AI Assistant",

            "Quiz",

            "Notes",

            "Performance",

            "Recommendations",

            "History"

        ]

    else:

        pages = [

            "Dashboard",

            "AI Assistant",

            "Upload Notes",

            "Students",

            "Quiz Analytics"

        ]


    page = st.sidebar.radio(

        "📌 Navigation",

        pages

    )


    st.sidebar.divider()


    status, message = check_ollama()


    if status:

        st.sidebar.success(
            "🟢 Llama 3.2 Connected"
        )

    else:

        st.sidebar.warning(
            "🔴 Ollama Offline"
        )


    st.sidebar.divider()


    if st.sidebar.button(

        "🚪 Logout",

        use_container_width=True

    ):

        st.session_state.logged_in = False

        st.session_state.user_id = None

        st.session_state.username = None

        st.session_state.name = None

        st.session_state.role = None

        st.session_state.course = None

        st.rerun()


    return page


# ============================================================
# STUDENT DASHBOARD
# ============================================================

def student_dashboard():

    st.markdown(f"""
    <div class="hero">
    <h1>Welcome 👋</h1>
    <p>Learn smarter with Llama 3.2 AI.</p>
    <p><b>🎓 Your Course:</b> {st.session_state.course}</p>
</div>
""", unsafe_allow_html=True)


    conn = get_connection()


    questions = conn.execute("""

        SELECT COUNT(*)

        FROM ai_history

        WHERE student_id = ?

    """, (

        st.session_state.user_id,

    )).fetchone()[0]


    quizzes = conn.execute("""

        SELECT COUNT(*)

        FROM quiz_results

        WHERE student_id = ?

    """, (

        st.session_state.user_id,

    )).fetchone()[0]


    average = conn.execute("""

        SELECT AVG(percentage)

        FROM quiz_results

        WHERE student_id = ?

    """, (

        st.session_state.user_id,

    )).fetchone()[0]


    conn.close()


    if average is None:

        average = 0


    c1, c2, c3, c4 = st.columns(4)


    c1.metric(
        "🤖 AI Questions",
        questions
    )


    c2.metric(
        "📝 Quiz Attempts",
        quizzes
    )


    c3.metric(
        "📊 Average Score",
        f"{average:.1f}%"
    )


    c4.metric(
        "🤖 AI Model",
        "Llama 3.2"
    )


    st.divider()


    st.subheader(
        "📚 Learning Modules"
    )


    c1, c2, c3 = st.columns(3)


    with c1:

        st.markdown("""

        <div class="card">

        <h3>
        🤖 AI Doubt Solver
        </h3>

        <p>
        Ask questions and learn
        with Llama 3.2.
        </p>

        </div>

        """, unsafe_allow_html=True)


    with c2:

        st.markdown("""

        <div class="card">

        <h3>
        📝 Smart Quiz
        </h3>

        <p>
        Practice quizzes and
        improve your knowledge.
        </p>

        </div>

        """, unsafe_allow_html=True)


    with c3:

        st.markdown("""

        <div class="card">

        <h3>
        🎯 Recommendations
        </h3>

        <p>
        Get recommendations
        based on performance.
        </p>

        </div>

        """, unsafe_allow_html=True)


# ============================================================
# AI ASSISTANT PAGE
# ============================================================

def ai_assistant_page():

    st.title(
        "🤖 AI Teaching Assistant"
    )

    st.caption(
        "Powered by Ollama + Llama 3.2"
    )


    status, message = check_ollama()


    if status:

        st.success(
            "🟢 Llama 3.2 Connected"
        )

    else:

        st.warning(
            message
        )


    question = st.text_area(

        "Ask your academic question",

        height=150,

        placeholder="Example: Explain Machine Learning in simple words."

    )


    if st.button(

        "✨ Ask Llama 3.2",

        use_container_width=True

    ):


        if not question.strip():

            st.warning(
                "Please enter a question."
            )

            return


        with st.spinner(

            "🤖 Llama 3.2 is thinking..."

        ):

            answer = generate_answer(
                question
            )


        st.markdown(
            "## 💡 AI Answer"
        )

        st.write(
            answer
        )


        if st.session_state.role == "Student":

            save_ai_history(

                st.session_state.user_id,

                question,

                answer

            )


# ============================================================
# QUIZ QUESTIONS
# ============================================================

# ============================================================
# COURSE-WISE QUIZ QUESTIONS
# ============================================================

QUIZ_DATA = {

    # ========================================================
    # 1. BCA
    # ========================================================
    "BCA": {
        "Computer Fundamentals": [
            ("What is the brain of a computer?",
             ["CPU", "RAM", "Hard Disk", "Monitor"], "CPU"),

            ("Which device is used to enter data?",
             ["Keyboard", "Monitor", "Printer", "Speaker"], "Keyboard"),

            ("What does RAM stand for?",
             ["Random Access Memory",
              "Read Access Memory",
              "Run Access Memory",
              "Rapid Access Machine"],
             "Random Access Memory"),

            ("Which is an output device?",
             ["Keyboard", "Mouse", "Monitor", "Scanner"], "Monitor"),

            ("Which software manages computer hardware?",
             ["Operating System", "MS Word", "Browser", "Calculator"],
             "Operating System")
        ],

        "Programming": [
            ("Which keyword is used to define a function in Python?",
             ["def", "function", "fun", "define"], "def"),

            ("Which data structure stores multiple values?",
             ["List", "Integer", "Boolean", "Float"], "List"),

            ("Which symbol is used for comments in Python?",
             ["//", "#", "/*", "--"], "#"),

            ("Which statement is used for decision making?",
             ["if", "for", "print", "input"], "if"),

            ("Which loop is commonly used to iterate over a sequence?",
             ["for", "if", "switch", "case"], "for")
        ],

        "Database": [
            ("What does DBMS stand for?",
             ["Database Management System",
              "Data Basic Management System",
              "Database Machine System",
              "Data Management Software"],
             "Database Management System"),

            ("Which language is used to query databases?",
             ["SQL", "HTML", "CSS", "Python"], "SQL"),

            ("Which command retrieves data?",
             ["SELECT", "DELETE", "DROP", "UPDATE"], "SELECT"),

            ("Which key uniquely identifies a record?",
             ["Primary Key", "Foreign Key", "Candidate Key", "Normal Key"],
             "Primary Key"),

            ("Which command adds a new record?",
             ["INSERT", "SELECT", "DROP", "ALTER"], "INSERT")
        ]
    },


    # ========================================================
    # 2. B.Sc. Computer Science
    # ========================================================
    "B.Sc. Computer Science": {
        "Data Structures": [
            ("Which data structure follows LIFO?",
             ["Stack", "Queue", "Array", "Tree"], "Stack"),

            ("Which data structure follows FIFO?",
             ["Stack", "Queue", "Tree", "Graph"], "Queue"),

            ("Which structure contains nodes and edges?",
             ["Graph", "Stack", "Queue", "Array"], "Graph"),

            ("Which structure has root and child nodes?",
             ["Tree", "Queue", "Stack", "Array"], "Tree"),

            ("Which data structure stores elements sequentially?",
             ["Array", "Graph", "Tree", "Heap"], "Array")
        ],

        "Algorithms": [
            ("Which algorithm is used for sorting?",
             ["Bubble Sort", "Binary Search", "DFS", "BFS"], "Bubble Sort"),

            ("Binary search works on?",
             ["Sorted data", "Random data", "Images", "Audio"], "Sorted data"),

            ("Which algorithm finds shortest path?",
             ["Dijkstra", "Bubble Sort", "Binary Search", "Selection Sort"],
             "Dijkstra"),

            ("What is algorithm complexity used for?",
             ["Measuring efficiency", "Designing UI",
              "Creating databases", "Sending emails"],
             "Measuring efficiency"),

            ("Which is a searching algorithm?",
             ["Binary Search", "Bubble Sort", "Merge Sort", "Quick Sort"],
             "Binary Search")
        ],

        "Operating Systems": [
            ("What is an operating system?",
             ["System software", "Application software",
              "Programming language", "Database"],
             "System software"),

            ("Which manages processes?",
             ["Operating System", "Compiler", "Browser", "Editor"],
             "Operating System"),

            ("Which is a process state?",
             ["Running", "Printing", "Typing", "Scanning"], "Running"),

            ("What is multitasking?",
             ["Running multiple tasks",
              "Deleting tasks",
              "Formatting disk",
              "Installing software"],
             "Running multiple tasks"),

            ("Which manages memory?",
             ["Operating System", "Keyboard", "Printer", "Monitor"],
             "Operating System")
        ]
    },


    # ========================================================
    # 3. B.Tech Computer Science
    # ========================================================
    "B.Tech Computer Science": {
        "Data Structures and Algorithms": [
            ("Which structure uses FIFO?",
             ["Queue", "Stack", "Tree", "Graph"], "Queue"),

            ("Which structure uses LIFO?",
             ["Stack", "Queue", "Graph", "Array"], "Stack"),

            ("Which algorithm uses divide and conquer?",
             ["Merge Sort", "Bubble Sort", "Linear Search", "BFS"],
             "Merge Sort"),

            ("Which algorithm searches a sorted array efficiently?",
             ["Binary Search", "Linear Search", "Bubble Sort", "DFS"],
             "Binary Search"),

            ("Which algorithm can find shortest paths?",
             ["Dijkstra", "Bubble Sort", "Selection Sort", "Linear Search"],
             "Dijkstra")
        ],

        "Computer Networks": [
            ("What does LAN stand for?",
             ["Local Area Network",
              "Large Area Network",
              "Long Access Network",
              "Local Access Node"],
             "Local Area Network"),

            ("Which protocol is used for web pages?",
             ["HTTP", "FTP", "SMTP", "POP3"], "HTTP"),

            ("Which device connects different networks?",
             ["Router", "Keyboard", "Monitor", "Printer"], "Router"),

            ("What does IP stand for?",
             ["Internet Protocol",
              "Internal Program",
              "Internet Program",
              "Input Protocol"],
             "Internet Protocol"),

            ("Which protocol is connection-oriented?",
             ["TCP", "UDP", "IP", "HTTP"], "TCP")
        ],

        "Operating Systems": [
            ("Which manages system resources?",
             ["Operating System", "Browser", "Compiler", "Editor"],
             "Operating System"),

            ("What is a process?",
             ["Program in execution",
              "Database table",
              "Network cable",
              "File extension"],
             "Program in execution"),

            ("What is deadlock?",
             ["Processes waiting indefinitely",
              "Fast execution",
              "File deletion",
              "Memory cleaning"],
             "Processes waiting indefinitely"),

            ("Which is a CPU scheduling algorithm?",
             ["FCFS", "HTML", "SQL", "HTTP"], "FCFS"),

            ("What is virtual memory?",
             ["Memory using disk space",
              "Only RAM",
              "Only ROM",
              "CPU cache"],
             "Memory using disk space")
        ]
    },


    # ========================================================
    # 4. Computer Engineering
    # ========================================================
    "Computer Engineering": {
        "Computer Architecture": [
            ("Which unit performs arithmetic operations?",
             ["ALU", "RAM", "ROM", "Hard Disk"], "ALU"),

            ("What does CPU stand for?",
             ["Central Processing Unit",
              "Computer Processing Unit",
              "Central Program Unit",
              "Computer Program Utility"],
             "Central Processing Unit"),

            ("Which memory is volatile?",
             ["RAM", "ROM", "SSD", "DVD"], "RAM"),

            ("Which stores instructions temporarily?",
             ["Cache", "Printer", "Keyboard", "Monitor"], "Cache"),

            ("Which is a CPU component?",
             ["Control Unit", "Printer", "Scanner", "Speaker"],
             "Control Unit")
        ],

        "Digital Electronics": [
            ("Which gate gives output 1 only when both inputs are 1?",
             ["AND", "OR", "NOT", "XOR"], "AND"),

            ("Which gate reverses the input?",
             ["NOT", "AND", "OR", "NAND"], "NOT"),

            ("Which number system uses 0 and 1?",
             ["Binary", "Decimal", "Octal", "Hexadecimal"], "Binary"),

            ("How many bits are in one byte?",
             ["8", "4", "16", "32"], "8"),

            ("Which is a universal gate?",
             ["NAND", "AND", "OR", "XOR"], "NAND")
        ]
    },


    # ========================================================
    # 5. Information Technology
    # ========================================================
    "Information Technology (IT)": {
        "IT Fundamentals": [
            ("What does IT stand for?",
             ["Information Technology",
              "Internet Technology",
              "Information Tool",
              "Integrated Technology"],
             "Information Technology"),

            ("Which is an operating system?",
             ["Windows", "HTML", "SQL", "Python"], "Windows"),

            ("Which stores data permanently?",
             ["Hard Disk", "RAM", "Cache", "Register"], "Hard Disk"),

            ("Which is a web browser?",
             ["Chrome", "Python", "Linux", "MySQL"], "Chrome"),

            ("Which device connects computers in a network?",
             ["Switch", "Keyboard", "Monitor", "Scanner"], "Switch")
        ],

        "Web Technology": [
            ("Which language creates web page structure?",
             ["HTML", "CSS", "SQL", "Python"], "HTML"),

            ("Which language styles web pages?",
             ["CSS", "HTML", "SQL", "C"], "CSS"),

            ("Which language adds interactivity to websites?",
             ["JavaScript", "HTML", "SQL", "CSS"], "JavaScript"),

            ("What does URL stand for?",
             ["Uniform Resource Locator",
              "Universal Resource Link",
              "Uniform Reference Link",
              "User Resource Locator"],
             "Uniform Resource Locator"),

            ("Which protocol is commonly used for secure websites?",
             ["HTTPS", "FTP", "SMTP", "POP"], "HTTPS")
        ]
    },


    # ========================================================
    # 6. Web Development
    # ========================================================
    "Web Development": {
        "HTML": [
            ("HTML stands for?",
             ["HyperText Markup Language",
              "HighText Machine Language",
              "Hyper Tool Markup Language",
              "Home Text Language"],
             "HyperText Markup Language"),

            ("Which tag creates a heading?",
             ["<h1>", "<p>", "<br>", "<div>"], "<h1>"),

            ("Which tag creates a hyperlink?",
             ["<a>", "<link>", "<url>", "<href>"], "<a>"),

            ("Which tag displays an image?",
             ["<img>", "<image>", "<pic>", "<src>"], "<img>"),

            ("Which tag creates a paragraph?",
             ["<p>", "<para>", "<text>", "<pg>"], "<p>")
        ],

        "CSS": [
            ("CSS is used for?",
             ["Styling web pages", "Database management",
              "Server management", "Data storage"],
             "Styling web pages"),

            ("CSS stands for?",
             ["Cascading Style Sheets",
              "Computer Style System",
              "Creative Style Sheet",
              "Colorful Style System"],
             "Cascading Style Sheets"),

            ("Which property changes text color?",
             ["color", "font", "text-color", "background"],
             "color"),

            ("Which property changes background color?",
             ["background-color", "bg", "color-bg", "back"],
             "background-color"),

            ("Which symbol represents a class selector?",
             [".", "#", "*", "@"], ".")
        ],

        "JavaScript": [
            ("JavaScript is mainly used for?",
             ["Web interactivity", "Database storage",
              "Operating system", "Hardware design"],
             "Web interactivity"),

            ("Which keyword declares a variable?",
             ["let", "varname", "variable", "define"],
             "let"),

            ("Which symbol is used for strict equality?",
             ["===", "=", "!=", "=>"], "==="),

            ("Which function displays a message?",
             ["alert()", "message()", "show()", "display()"],
             "alert()"),

            ("Which language runs in web browsers?",
             ["JavaScript", "SQL", "Python only", "C"],
             "JavaScript")
        ]
    },


    # ========================================================
    # 7. Python Programming
    # ========================================================
    "Python Programming": {
        "Python Basics": [
            ("Which keyword defines a function?",
             ["def", "function", "fun", "define"], "def"),

            ("Which function prints output?",
             ["print()", "show()", "display()", "output()"], "print()"),

            ("Which function takes user input?",
             ["input()", "get()", "read()", "scan()"], "input()"),

            ("Which symbol starts a comment?",
             ["#", "//", "/*", "--"], "#"),

            ("Which data type stores True or False?",
             ["Boolean", "String", "List", "Float"], "Boolean")
        ],

        "Python Data Structures": [
            ("Which collection is ordered and mutable?",
             ["List", "Tuple", "Set", "String"], "List"),

            ("Which collection is immutable?",
             ["Tuple", "List", "Dictionary", "Set"], "Tuple"),

            ("Which stores key-value pairs?",
             ["Dictionary", "List", "Tuple", "Set"], "Dictionary"),

            ("Which removes duplicate values?",
             ["Set", "List", "Tuple", "String"], "Set"),

            ("Which function returns list length?",
             ["len()", "length()", "size()", "count()"], "len()")
        ]
    },


    # ========================================================
    # 8. Data Science
    # ========================================================
    "Data Science": {
        "Data Analysis": [
            ("Which library is commonly used for data analysis?",
             ["Pandas", "HTML", "CSS", "SQLite"], "Pandas"),

            ("Which library is used for numerical computation?",
             ["NumPy", "HTML", "Flask", "Bootstrap"], "NumPy"),

            ("What is data cleaning?",
             ["Removing or correcting bad data",
              "Creating passwords",
              "Designing websites",
              "Installing software"],
             "Removing or correcting bad data"),

            ("What is a dataset?",
             ["Collection of data",
              "Computer hardware",
              "Network protocol",
              "Operating system"],
             "Collection of data"),

            ("Which chart is useful for comparing categories?",
             ["Bar chart", "Password", "Database", "Compiler"],
             "Bar chart")
        ],

        "Statistics": [
            ("What is the average called in statistics?",
             ["Mean", "Mode", "Range", "Median only"], "Mean"),

            ("Which value occurs most frequently?",
             ["Mode", "Mean", "Range", "Variance"], "Mode"),

            ("What is median?",
             ["Middle value", "Largest value",
              "Smallest value", "Total value"],
             "Middle value"),

            ("What measures data spread?",
             ["Standard deviation", "Mean",
              "Mode", "Count"],
             "Standard deviation"),

            ("What is correlation?",
             ["Relationship between variables",
              "Data deletion",
              "File compression",
              "Password protection"],
             "Relationship between variables")
        ]
    },


    # ========================================================
    # 9. Artificial Intelligence
    # ========================================================
    "Artificial Intelligence (AI)": {
        "Artificial Intelligence": [
            ("AI stands for?",
             ["Artificial Intelligence",
              "Automated Information",
              "Advanced Internet",
              "Artificial Input"],
             "Artificial Intelligence"),

            ("Which is an AI application?",
             ["Chatbot", "Keyboard", "Printer", "Monitor"],
             "Chatbot"),

            ("Which is a branch of AI?",
             ["Natural Language Processing",
              "File Management",
              "Word Processing",
              "Desktop Publishing"],
             "Natural Language Processing"),

            ("What does an AI model learn from?",
             ["Data", "Keyboard", "Monitor", "Printer"],
             "Data"),

            ("What is the goal of AI?",
             ["Perform intelligent tasks",
              "Only store files",
              "Only print documents",
              "Only browse websites"],
             "Perform intelligent tasks")
        ],

        "Expert Systems": [
            ("What is an expert system?",
             ["AI system using knowledge and rules",
              "Database",
              "Compiler",
              "Operating system"],
             "AI system using knowledge and rules"),

            ("Where is expert knowledge stored?",
             ["Knowledge Base", "RAM", "CPU", "Hard Disk"],
             "Knowledge Base"),

            ("What applies rules to facts?",
             ["Inference Engine", "Browser",
              "Compiler", "Editor"],
             "Inference Engine"),

            ("Rules are commonly written as?",
             ["IF-THEN", "FOR-NEXT", "HTML-CSS", "GET-POST"],
             "IF-THEN"),

            ("MYCIN was an example of?",
             ["Expert System", "Operating System",
              "Database", "Browser"],
             "Expert System")
        ]
    },


    # ========================================================
    # 10. Machine Learning
    # ========================================================
    "Machine Learning": {
        "Machine Learning Basics": [
            ("Which is supervised learning?",
             ["Linear Regression", "K-Means", "PCA", "Apriori"],
             "Linear Regression"),

            ("Which algorithm is used for clustering?",
             ["K-Means", "Linear Regression",
              "Decision Tree", "SVM"],
             "K-Means"),

            ("What is training data?",
             ["Data used to train a model",
              "Random data", "Only output data", "Error messages"],
             "Data used to train a model"),

            ("What is a feature?",
             ["Input variable", "Password",
              "Database", "Output file"],
             "Input variable"),

            ("What is overfitting?",
             ["Good training performance but poor new-data performance",
              "No training data",
              "Fast model",
              "Small dataset"],
             "Good training performance but poor new-data performance")
        ],

        "ML Algorithms": [
            ("Which is a classification algorithm?",
             ["Decision Tree", "K-Means", "PCA", "Apriori"],
             "Decision Tree"),

            ("What does regression predict?",
             ["Continuous values", "Only categories",
              "Only images", "Only text"],
             "Continuous values"),

            ("Which algorithm is used for dimensionality reduction?",
             ["PCA", "K-Means", "Linear Regression", "Decision Tree"],
             "PCA"),

            ("Which algorithm is commonly used for classification?",
             ["Logistic Regression", "K-Means",
              "PCA", "Apriori"],
             "Logistic Regression"),

            ("Which metric is common for classification?",
             ["Accuracy", "CPU speed",
              "File size", "RAM"],
             "Accuracy")
        ]
    },


    # ========================================================
    # 11. Cyber Security
    # ========================================================
    "Cyber Security": {
        "Cyber Security Basics": [
            ("What is cybersecurity?",
             ["Protection of computer systems and data",
              "Website design",
              "Database creation",
              "Video editing"],
             "Protection of computer systems and data"),

            ("What is malware?",
             ["Malicious software", "Database",
              "Browser", "Operating system"],
             "Malicious software"),

            ("What is phishing?",
             ["Fake attempt to steal information",
              "Data backup",
              "Software update",
              "File compression"],
             "Fake attempt to steal information"),

            ("What is a firewall?",
             ["Network security system",
              "Database",
              "Programming language",
              "Browser"],
             "Network security system"),

            ("What is encryption?",
             ["Converting data into protected form",
              "Deleting data",
              "Copying files",
              "Formatting disk"],
             "Converting data into protected form")
        ],

        "Network Security": [
            ("Which protocol provides secure web communication?",
             ["HTTPS", "HTTP", "FTP", "SMTP"], "HTTPS"),

            ("What does VPN stand for?",
             ["Virtual Private Network",
              "Very Personal Network",
              "Virtual Public Node",
              "Verified Private Node"],
             "Virtual Private Network"),

            ("Which is a strong authentication method?",
             ["Multi-factor authentication",
              "Simple password",
              "Username only",
              "Email only"],
             "Multi-factor authentication"),

            ("What is a security vulnerability?",
             ["Weakness in a system",
              "Strong password",
              "Backup",
              "Firewall"],
             "Weakness in a system"),

            ("What is a Trojan?",
             ["Malicious program disguised as legitimate software",
              "Antivirus",
              "Firewall",
              "Backup"],
             "Malicious program disguised as legitimate software")
        ]
    },


    # ========================================================
    # 12. Cloud Computing
    # ========================================================
    "Cloud Computing": {
        "Cloud Fundamentals": [
            ("What is cloud computing?",
             ["Using computing resources over the internet",
              "Only local storage",
              "Computer repair",
              "Offline programming"],
             "Using computing resources over the internet"),

            ("Which is a cloud service model?",
             ["IaaS", "HTML", "SQL", "CPU"],
             "IaaS"),

            ("What does SaaS stand for?",
             ["Software as a Service",
              "System as a Software",
              "Storage as a System",
              "Software and Storage"],
             "Software as a Service"),

            ("Which is a cloud provider?",
             ["AWS", "HTML", "Python", "SQLite"],
             "AWS"),

            ("What is cloud storage?",
             ["Storing data on remote servers",
              "Only RAM storage",
              "CPU cache",
              "Keyboard memory"],
             "Storing data on remote servers")
        ],

        "Cloud Services": [
            ("What does IaaS provide?",
             ["Infrastructure resources",
              "Only software",
              "Only documents",
              "Only email"],
             "Infrastructure resources"),

            ("What does PaaS provide?",
             ["Platform for application development",
              "Only hardware",
              "Only storage",
              "Only networking"],
             "Platform for application development"),

            ("Which cloud model is shared by many users?",
             ["Public Cloud", "Private Cloud",
              "Local Cloud", "Personal Cloud"],
             "Public Cloud"),

            ("Which model is dedicated to one organization?",
             ["Private Cloud", "Public Cloud",
              "Open Cloud", "Shared Cloud"],
             "Private Cloud"),

            ("Cloud computing can improve?",
             ["Scalability", "Keyboard speed",
              "Screen size", "Printer speed"],
             "Scalability")
        ]
    },


    # ========================================================
    # 13. Computer Networking
    # ========================================================
    "Computer Networking": {
        "Networking Basics": [
            ("What does LAN stand for?",
             ["Local Area Network",
              "Large Area Network",
              "Long Area Network",
              "Local Access Network"],
             "Local Area Network"),

            ("Which device forwards packets between networks?",
             ["Router", "Switch", "Keyboard", "Monitor"],
             "Router"),

            ("What does IP stand for?",
             ["Internet Protocol",
              "Internet Program",
              "Internal Protocol",
              "Input Program"],
             "Internet Protocol"),

            ("Which device connects devices in a LAN?",
             ["Switch", "Printer", "Scanner", "CPU"],
             "Switch"),

            ("Which protocol is used for email sending?",
             ["SMTP", "HTTP", "FTP", "DNS"],
             "SMTP")
        ],

        "Networking Protocols": [
            ("Which protocol is connection-oriented?",
             ["TCP", "UDP", "IP", "DNS"], "TCP"),

            ("Which protocol is connectionless?",
             ["UDP", "TCP", "HTTP", "FTP"], "UDP"),

            ("Which protocol translates domain names to IP addresses?",
             ["DNS", "HTTP", "FTP", "SMTP"], "DNS"),

            ("Which protocol transfers files?",
             ["FTP", "DNS", "SMTP", "ARP"], "FTP"),

            ("Which protocol is used for web communication?",
             ["HTTP", "SMTP", "FTP", "POP3"], "HTTP")
        ]
    },


    # ========================================================
    # 14. Software Development
    # ========================================================
    "Software Development": {
        "SDLC": [
            ("What does SDLC stand for?",
             ["Software Development Life Cycle",
              "System Data Life Cycle",
              "Software Design Language Code",
              "System Development Level Cycle"],
             "Software Development Life Cycle"),

            ("Which is an SDLC phase?",
             ["Testing", "Printing", "Scanning", "Typing"],
             "Testing"),

            ("What happens during requirement analysis?",
             ["Requirements are identified",
              "Code is deleted",
              "Hardware is repaired",
              "Files are printed"],
             "Requirements are identified"),

            ("Which model follows sequential phases?",
             ["Waterfall", "Random", "Circular", "Parallel"],
             "Waterfall"),

            ("What is software testing?",
             ["Finding errors in software",
              "Creating hardware",
              "Formatting disk",
              "Sending email"],
             "Finding errors in software")
        ],

        "Software Testing": [
            ("What is a bug?",
             ["Error in software", "Feature",
              "Database", "Network"],
             "Error in software"),

            ("What is unit testing?",
             ["Testing individual components",
              "Testing entire company",
              "Testing hardware",
              "Testing internet"],
             "Testing individual components"),

            ("What is integration testing?",
             ["Testing combined modules",
              "Testing one variable",
              "Testing keyboard",
              "Testing printer"],
             "Testing combined modules"),

            ("What is regression testing?",
             ["Testing after changes",
              "Deleting software",
              "Installing OS",
              "Formatting disk"],
             "Testing after changes"),

            ("What is debugging?",
             ["Finding and fixing errors",
              "Creating users",
              "Installing RAM",
              "Designing hardware"],
             "Finding and fixing errors")
        ]
    },


    # ========================================================
    # 15. Database Management
    # ========================================================
    "Database Management": {
        "DBMS": [
            ("DBMS stands for?",
             ["Database Management System",
              "Data Backup Management System",
              "Database Machine System",
              "Data Management Software"],
             "Database Management System"),

            ("Which language is used to manage relational databases?",
             ["SQL", "HTML", "CSS", "JavaScript"], "SQL"),

            ("Which key uniquely identifies a record?",
             ["Primary Key", "Foreign Key",
              "Normal Key", "Simple Key"],
             "Primary Key"),

            ("Which key links two tables?",
             ["Foreign Key", "Primary Key",
              "Candidate Key", "Super Key"],
             "Foreign Key"),

            ("Which command retrieves records?",
             ["SELECT", "INSERT", "DELETE", "DROP"],
             "SELECT")
        ],

        "SQL": [
            ("Which command adds data?",
             ["INSERT", "SELECT", "DROP", "ALTER"], "INSERT"),

            ("Which command modifies data?",
             ["UPDATE", "SELECT", "DROP", "CREATE"], "UPDATE"),

            ("Which command removes records?",
             ["DELETE", "SELECT", "INSERT", "ALTER"], "DELETE"),

            ("Which command creates a table?",
             ["CREATE", "SELECT", "INSERT", "DELETE"], "CREATE"),

            ("Which clause filters records?",
             ["WHERE", "FROM", "ORDER", "GROUP"],
             "WHERE")
        ]
    },


    # ========================================================
    # 16. Mobile App Development
    # ========================================================
    "Mobile App Development": {
        "Mobile Development": [
            ("Which OS is widely used for mobile applications?",
             ["Android", "Linux only", "DOS", "Unix only"],
             "Android"),

            ("Which language is commonly used for Android development?",
             ["Kotlin", "HTML", "SQL", "CSS"], "Kotlin"),

            ("What is an APK?",
             ["Android application package",
              "Apple program key",
              "Application password key",
              "Android process kernel"],
             "Android application package"),

            ("What is an Activity in Android?",
             ["A screen/component of an app",
              "Database",
              "Network cable",
              "Compiler"],
             "A screen/component of an app"),

            ("Which file defines Android app permissions?",
             ["AndroidManifest.xml",
              "index.html",
              "style.css",
              "database.sql"],
             "AndroidManifest.xml")
        ],

        "Mobile UI": [
            ("What is UI?",
             ["User Interface", "Universal Internet",
              "User Input", "Utility Interface"],
             "User Interface"),

            ("What is responsive design?",
             ["UI adapts to different screen sizes",
              "Only desktop design",
              "Database design",
              "Network design"],
             "UI adapts to different screen sizes"),

            ("What is a button used for?",
             ["User interaction", "Data storage",
              "CPU processing", "Network routing"],
             "User interaction"),

            ("What is navigation in a mobile app?",
             ["Moving between screens",
              "Deleting data",
              "Formatting phone",
              "Installing OS"],
             "Moving between screens"),

            ("What is an app notification?",
             ["Message shown to the user",
              "Database record",
              "CPU instruction",
              "File extension"],
             "Message shown to the user")
        ]
    },


    # ========================================================
    # 17. Game Development
    # ========================================================
    "Game Development": {
        "Game Programming": [
            ("What is a game engine?",
             ["Software used to create games",
              "Database",
              "Operating system",
              "Web browser"],
             "Software used to create games"),

            ("Which engine is popular for game development?",
             ["Unity", "SQLite", "Excel", "Apache"],
             "Unity"),

            ("What is a game loop?",
             ["Repeatedly updates game state",
              "Database query",
              "File upload",
              "Network cable"],
             "Repeatedly updates game state"),

            ("What is collision detection?",
             ["Detecting object interactions",
              "Creating database",
              "Sending email",
              "Loading webpage"],
             "Detecting object interactions"),

            ("What is a sprite?",
             ["2D game object/image",
              "Database table",
              "Network device",
              "Compiler"],
             "2D game object/image")
        ],

        "Game Design": [
            ("What is gameplay?",
             ["How a game is played",
              "Database design",
              "Network configuration",
              "File management"],
             "How a game is played"),

            ("What is a game level?",
             ["A section/stage of a game",
              "Programming language",
              "Database",
              "Operating system"],
             "A section/stage of a game"),

            ("What is an NPC?",
             ["Non-Player Character",
              "New Program Code",
              "Network Processing Computer",
              "Normal Player Control"],
             "Non-Player Character"),

            ("What is game physics?",
             ["Simulation of movement and forces",
              "Database storage",
              "Web styling",
              "File compression"],
             "Simulation of movement and forces"),

            ("What is a game asset?",
             ["Game resource such as image, sound or model",
              "Database key",
              "Network protocol",
              "CPU register"],
             "Game resource such as image, sound or model")
        ]
    },


    # ========================================================
    # 18. UI/UX Design
    # ========================================================
    "UI/UX Design": {
        "UI Design": [
            ("UI stands for?",
             ["User Interface",
              "Universal Internet",
              "User Information",
              "Utility Input"],
             "User Interface"),

            ("UX stands for?",
             ["User Experience",
              "User Extension",
              "Universal Experience",
              "User Execution"],
             "User Experience"),

            ("Which improves readability?",
             ["Good typography", "Random colors",
              "Tiny text", "Too many fonts"],
             "Good typography"),

            ("What is a wireframe?",
             ["Basic layout of a design",
              "Database",
              "Programming language",
              "Network protocol"],
             "Basic layout of a design"),

            ("What is a prototype?",
             ["Interactive design model",
              "Final database",
              "Operating system",
              "Network device"],
             "Interactive design model")
        ],

        "UX Design": [
            ("What is user experience?",
             ["Overall experience of a user",
              "Database structure",
              "Computer hardware",
              "Network speed"],
             "Overall experience of a user"),

            ("Why is usability important?",
             ["Makes products easier to use",
              "Increases file size",
              "Deletes data",
              "Slows application"],
             "Makes products easier to use"),

            ("What is user research?",
             ["Understanding user needs",
              "Writing code only",
              "Creating databases",
              "Installing software"],
             "Understanding user needs"),

            ("What is accessibility?",
             ["Making design usable by more people",
              "Adding more colors only",
              "Increasing file size",
              "Removing buttons"],
             "Making design usable by more people"),

            ("What is consistency in UI?",
             ["Using similar design patterns",
              "Changing every screen",
              "Removing navigation",
              "Using random layouts"],
             "Using similar design patterns")
        ]
    }
}

# ============================================================
# QUIZ PAGE
# ============================================================

# ============================================================
# COURSE-WISE QUIZ PAGE
# ============================================================

def quiz_page():

    st.title("📝 Smart Quiz")

    # --------------------------------------------------------
    # STUDENT COURSE
    # --------------------------------------------------------

    student_course = st.session_state.course

    st.success(
        f"🎓 Course: {student_course}"
    )

    # --------------------------------------------------------
    # CHECK COURSE EXISTS
    # --------------------------------------------------------

    if student_course not in QUIZ_DATA:

        st.error(
            "Quiz is not available for this course yet."
        )

        return

    # --------------------------------------------------------
    # SELECT SUBJECT
    # --------------------------------------------------------

    subjects = list(
        QUIZ_DATA[student_course].keys()
    )

    subject = st.selectbox(
        "📚 Select Quiz Subject",
        subjects
    )

    # --------------------------------------------------------
    # GET QUESTIONS
    # --------------------------------------------------------

    quiz = QUIZ_DATA[
        student_course
    ][
        subject
    ]

    st.info(
        f"📖 {student_course} → {subject}"
    )

    st.write(
        f"Total Questions: {len(quiz)}"
    )

    st.divider()

    # --------------------------------------------------------
    # STORE ANSWERS
    # --------------------------------------------------------

    answers = {}

    # --------------------------------------------------------
    # DISPLAY QUESTIONS
    # --------------------------------------------------------

    for i, item in enumerate(quiz):

        question = item[0]

        options = item[1]

        st.markdown(
            f"### Q{i + 1}. {question}"
        )

        answers[i] = st.radio(
            "Choose Answer:",
            options,
            key=f"quiz_{student_course}_{subject}_{i}"
        )

        st.divider()

    # --------------------------------------------------------
    # SUBMIT QUIZ
    # --------------------------------------------------------

    if st.button(
        "🚀 Submit Quiz",
        use_container_width=True
    ):

        score = 0

        # ----------------------------------------------------
        # CHECK ANSWERS
        # ----------------------------------------------------

        for i, item in enumerate(quiz):

            correct_answer = item[2]

            if answers[i] == correct_answer:

                score += 1

        # ----------------------------------------------------
        # CALCULATE RESULT
        # ----------------------------------------------------

        total = len(quiz)

        percentage = (
            score / total
        ) * 100

        # ----------------------------------------------------
        # DISPLAY RESULT
        # ----------------------------------------------------

        st.success(
            f"🎉 Quiz Completed!"
        )

        st.metric(
            "Score",
            f"{score}/{total}"
        )

        st.metric(
            "Percentage",
            f"{percentage:.1f}%"
        )

        # ----------------------------------------------------
        # PERFORMANCE MESSAGE
        # ----------------------------------------------------

        if percentage >= 80:

            st.success(
                "🟢 Excellent! Keep it up!"
            )

        elif percentage >= 50:

            st.warning(
                "🟡 Good! Practice more."
            )

        else:

            st.error(
                "🔴 Need improvement. "
                "Read Notes and ask AI Assistant."
            )

        # ----------------------------------------------------
        # SAVE RESULT
        # ----------------------------------------------------

        conn = get_connection()

        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO quiz_results (

                student_id,

                subject,

                score,

                total,

                percentage,

                created_at

            )

            VALUES (?, ?, ?, ?, ?, ?)
        """, (

            st.session_state.user_id,

            f"{student_course} - {subject}",

            score,

            total,

            percentage,

            datetime.now().strftime(
                "%Y-%m-%d %H:%M:%S"
            )

        ))

        conn.commit()

        conn.close()

        st.success(
            "✅ Quiz result saved successfully!"
        )


# ============================================================
# FILE TEXT EXTRACTION
# ============================================================

def extract_file_text(uploaded_file):

    try:

        filename = uploaded_file.name.lower()


        # TXT

        if filename.endswith(".txt"):

            return uploaded_file.read().decode(

                "utf-8",

                errors="ignore"

            )


        # PDF

        elif filename.endswith(".pdf"):

            if not PDF_AVAILABLE:

                return (
                    "Install pypdf using: "
                    "pip install pypdf"
                )


            reader = PdfReader(
                uploaded_file
            )


            text = ""


            for page in reader.pages:

                page_text = page.extract_text()


                if page_text:

                    text += (
                        page_text
                        +
                        "\n"
                    )


            return text


        # DOCX

        elif filename.endswith(".docx"):

            if not DOCX_AVAILABLE:

                return (
                    "Install python-docx using: "
                    "pip install python-docx"
                )


            doc = Document(
                uploaded_file
            )


            return "\n".join(

                paragraph.text

                for paragraph

                in doc.paragraphs

            )


        return (
            "Unsupported file."
        )


    except Exception as error:

        return (
            f"Error reading file: {error}"
        )


# ============================================================
# TEACHER NOTES PAGE
# ============================================================

def teacher_notes_page():

    st.title(
        "📤 Upload Notes"
    )


    subject = st.selectbox(

        "Select Course Notes ",

        [
             "BCA",
             "B.Sc. Computer Science",
             "B.Tech Computer Science",
             "Computer Engineering",
             "Information Technology (IT)",
             "Web Development",
             "Python Programming",
             "Data Science",
             "Artificial Intelligence (AI)",
             "Machine Learning",
             "Cyber Security",
             "Cloud Computing",
             "Computer Networking",
             "Software Development",
             "Database Management",
             "Mobile App Development",
             "Game Development",
             "UI/UX Design"
        ]

    )


    title = st.text_input(
        "Note Title"
    )


    uploaded_file = st.file_uploader(

        "Upload Notes File",

        type=[

            "pdf",

            "txt",

            "docx"

        ]

    )


    extracted_text = ""


    if uploaded_file:

        extracted_text = extract_file_text(
            uploaded_file
        )


        st.success(

            f"Uploaded: {uploaded_file.name}"

        )


    content = st.text_area(

        "Notes Content",

        value=extracted_text,

        height=300

    )


    if st.button(

        "💾 Save Notes",

        use_container_width=True

    ):


        if not title:

            st.warning(
                "Please enter note title."
            )

            return


        if not content.strip():

            st.warning(
                "Please enter notes content."
            )

            return


        file_name = ""


        if uploaded_file:

            file_name = uploaded_file.name


        conn = get_connection()


        cursor = conn.cursor()


        cursor.execute("""

            INSERT INTO notes (

                teacher_id,

                title,

                subject,

                content,

                file_name,

                created_at

            )

            VALUES (?, ?, ?, ?, ?, ?)

        """, (

            st.session_state.user_id,

            title,

            subject,

            content,

            file_name,

            datetime.now().strftime(
                "%Y-%m-%d %H:%M:%S"
            )

        ))


        conn.commit()

        conn.close()


        st.success(
            "Notes saved successfully!"
        )


# ============================================================
# STUDENT NOTES PAGE
# ============================================================

def student_notes_page():

    st.title(
        "📚 Available Notes"
    )


    conn = get_connection()


    try:

        df = pd.read_sql_query("""

            SELECT

                id,

                title,

                subject,

                content,

                file_name,

                created_at

            FROM notes

            ORDER BY id DESC

        """, conn)


    except Exception as error:

        conn.close()

        st.error(
            f"Database Error: {error}"
        )

        return


    conn.close()


    if df.empty:

        st.info(
            "No notes uploaded yet."
        )

        return


    subjects = [

        "All"

    ] + list(

        df["subject"]
        .fillna("General")
        .unique()

    )


    selected_subject = st.selectbox(

        "Filter by Subject",

        subjects

    )


    if selected_subject != "All":

        df = df[

            df["subject"]
            .fillna("General")
            ==
            selected_subject

        ]


    for _, row in df.iterrows():

        subject_value = row["subject"]


        if pd.isna(subject_value):

            subject_value = "General"


        with st.expander(

            f"📘 {row['title']} | {subject_value}"

        ):


            st.markdown(

                f"### {row['title']}"

            )


            st.caption(

                f"Subject: {subject_value}"

            )


            st.write(

                row["content"]

            )


            if (

                row["file_name"]

                and

                not pd.isna(
                    row["file_name"]
                )

            ):

                st.caption(

                    f"📎 File: "
                    f"{row['file_name']}"

                )


            st.caption(

                f"Uploaded: "
                f"{row['created_at']}"

            )


# ============================================================
# PERFORMANCE PAGE
# ============================================================

def performance_page():

    st.title(
        "📊 My Performance"
    )


    conn = get_connection()


    df = pd.read_sql_query("""

        SELECT

            subject,

            score,

            total,

            percentage,

            created_at

        FROM quiz_results

        WHERE student_id = ?

        ORDER BY id DESC

    """, conn, params=(

        st.session_state.user_id,

    ))


    conn.close()


    if df.empty:

        st.info(
            "No quiz results available yet."
        )

        return


    average = df[
        "percentage"
    ].mean()


    best = df[
        "percentage"
    ].max()


    attempts = len(df)


    c1, c2, c3 = st.columns(3)


    c1.metric(

        "Average Score",

        f"{average:.1f}%"

    )


    c2.metric(

        "Best Score",

        f"{best:.1f}%"

    )


    c3.metric(

        "Quiz Attempts",

        attempts

    )


    st.divider()


    st.subheader(
        "📈 Subject Performance"
    )


    chart_df = (

        df.groupby(
            "subject"
        )[
            "percentage"
        ]

        .mean()

    )


    st.bar_chart(
        chart_df
    )


    st.divider()


    st.subheader(
        "📋 Quiz History"
    )


    st.dataframe(

        df,

        use_container_width=True

    )


# ============================================================
# RECOMMENDATIONS PAGE
# ============================================================

def recommendations_page():

    st.title(
        "🎯 Learning Recommendations"
    )


    conn = get_connection()


    data = conn.execute("""

        SELECT

            subject,

            AVG(percentage)

        FROM quiz_results

        WHERE student_id = ?

        GROUP BY subject

    """, (

        st.session_state.user_id,

    )).fetchall()


    conn.close()


    if not data:

        st.info(

            "Complete quizzes to receive recommendations."

        )

        return


    for subject, percentage in data:


        if percentage < 50:

            st.error(

                f"""
### 🔴 {subject}

Average Score: {percentage:.1f}%

Recommendation:

Study basic concepts, read notes,
and ask AI Assistant for help.
"""

            )


        elif percentage < 75:

            st.warning(

                f"""
### 🟡 {subject}

Average Score: {percentage:.1f}%

Recommendation:

Practice more quizzes and
review important topics.
"""

            )


        else:

            st.success(

                f"""
### 🟢 {subject}

Average Score: {percentage:.1f}%

Excellent performance!

Try advanced topics.
"""

            )


# ============================================================
# HISTORY PAGE
# ============================================================

def history_page():

    st.title(
        "📜 Learning History"
    )


    conn = get_connection()


    ai_data = conn.execute("""

        SELECT

            question,

            answer,

            created_at

        FROM ai_history

        WHERE student_id = ?

        ORDER BY id DESC

    """, (

        st.session_state.user_id,

    )).fetchall()


    conn.close()


    if not ai_data:

        st.info(
            "No AI questions yet."
        )

        return


    for question, answer, created_at in ai_data:

        with st.expander(

            f"❓ {question[:80]}"

        ):

            st.markdown(
                "### Answer"
            )

            st.write(
                answer
            )

            st.caption(
                created_at
            )


# ============================================================
# TEACHER DASHBOARD
# ============================================================

def teacher_dashboard():

    st.markdown("""
    <div class="hero">
    <h1>👨‍🏫 Teacher Dashboard</h1>
    <p>Manage students, notes and performance analytics.</p>
</div>
""", unsafe_allow_html=True)


    conn = get_connection()


    students = conn.execute("""

        SELECT COUNT(*)

        FROM users

        WHERE role = 'Student'

    """).fetchone()[0]


    quiz_attempts = conn.execute("""

        SELECT COUNT(*)

        FROM quiz_results

    """).fetchone()[0]


    average = conn.execute("""

        SELECT AVG(percentage)

        FROM quiz_results

    """).fetchone()[0]


    notes_count = conn.execute("""

        SELECT COUNT(*)

        FROM notes

    """).fetchone()[0]


    subject_data = conn.execute("""

        SELECT

            subject,

            AVG(percentage)

        FROM quiz_results

        GROUP BY subject

    """).fetchall()


    conn.close()


    if average is None:

        average = 0


    c1, c2, c3, c4 = st.columns(4)


    c1.metric(
        "👨‍🎓 Students",
        students
    )


    c2.metric(
        "📝 Quiz Attempts",
        quiz_attempts
    )


    c3.metric(
        "📊 Average Score",
        f"{average:.1f}%"
    )


    c4.metric(
        "📚 Notes",
        notes_count
    )


    st.divider()


    st.subheader(
        "📊 Subject Performance"
    )


    if subject_data:

        df = pd.DataFrame(

            subject_data,

            columns=[

                "Subject",

                "Average Score"

            ]

        )


        st.bar_chart(

            df.set_index(
                "Subject"
            )

        )

    else:

        st.info(
            "No quiz data available."
        )


# ============================================================
# STUDENTS PAGE
# ============================================================

def students_page():

    st.title(
        "👨‍🎓 Student Management"
    )


    conn = get_connection()


    df = pd.read_sql_query("""

        SELECT

            id,

            name,

            username,

            email,

            COALESCE(course, 'BCA') AS course,

            created_at

        FROM users

        WHERE role = 'Student'

        ORDER BY id DESC

    """, conn)


    conn.close()


    if df.empty:

        st.info(
            "No students registered."
        )

        return


    st.metric(

        "Total Students",

        len(df)

    )


    st.dataframe(

        df,

        use_container_width=True

    )


# ============================================================
# QUIZ ANALYTICS PAGE
# ============================================================

def quiz_analytics_page():

    st.title(
        "📊 Quiz Analytics"
    )


    conn = get_connection()


    df = pd.read_sql_query("""

        SELECT

            subject,

            COUNT(*) AS attempts,

            AVG(percentage) AS average_score,

            MAX(percentage) AS highest_score,

            MIN(percentage) AS lowest_score

        FROM quiz_results

        GROUP BY subject

    """, conn)


    conn.close()


    if df.empty:

        st.info(
            "No quiz data available."
        )

        return


    st.dataframe(

        df,

        use_container_width=True

    )


    st.subheader(
        "📊 Average Performance"
    )


    st.bar_chart(

        df.set_index(
            "subject"
        )[
            "average_score"
        ]

    )


    st.subheader(
        "📝 Quiz Attempts"
    )


    st.bar_chart(

        df.set_index(
            "subject"
        )[
            "attempts"
        ]

    )


# ============================================================
# MAIN APPLICATION
# ============================================================

def main():

    if not st.session_state.logged_in:

        login_page()

        return


    page = sidebar()


    # ========================================================
    # STUDENT PAGES
    # ========================================================

    if st.session_state.role == "Student":


        if page == "Dashboard":

            student_dashboard()


        elif page == "AI Assistant":

            ai_assistant_page()


        elif page == "Quiz":

            quiz_page()


        elif page == "Notes":

            student_notes_page()


        elif page == "Performance":

            performance_page()


        elif page == "Recommendations":

            recommendations_page()


        elif page == "History":

            history_page()


    # ========================================================
    # TEACHER PAGES
    # ========================================================

    elif st.session_state.role == "Teacher":


        if page == "Dashboard":

            teacher_dashboard()


        elif page == "AI Assistant":

            ai_assistant_page()


        elif page == "Upload Notes":

            teacher_notes_page()


        elif page == "Students":

            students_page()


        elif page == "Quiz Analytics":

            quiz_analytics_page()


# ============================================================
# RUN APPLICATION
# ============================================================

if __name__ == "__main__":

    main()