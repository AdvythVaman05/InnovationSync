import streamlit as st
from pymongo import MongoClient
from langchain.chains import RetrievalQA
from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_groq import ChatGroq

# --- MongoDB Setup ---
client = MongoClient("mongodb://localhost:27017")
db = client["synthetic_ehr"]
patient_login_col = db["patient_login"]
doctor_login_col = db["doctor_login"]
admin_login_col = db["admin_login"]
connections_col = db["patient_doctor_connections"]
patient_col = db["patient_records"]

# --- Load QA Chain ---
@st.cache_resource
def load_qa_chain():
    embeddings = HuggingFaceEmbeddings()
    vector_store = FAISS.load_local("faiss_index", embeddings, allow_dangerous_deserialization=True)
    llm = ChatGroq(model='llama3-70b-8192', temperature=0)
    return RetrievalQA.from_chain_type(llm=llm, retriever=vector_store.as_retriever())

qa_chain = load_qa_chain()

# --- App Header ---
def app_header():
    st.markdown("""
        <div style='text-align: center; margin-top: -50px;'>
            <h1 style='font-size: 60px; color: #4A90E2;'>🩺 MediQuest</h1>
            <h3 style='color: #777;'>Quest for Care, Simplified</h3>
            <hr style='border-top: 1px solid #ccc;' />
        </div>
    """, unsafe_allow_html=True)

# --- Login ---
def login():
    st.title("🔐 EHR Login")

    role = st.selectbox("Select your role", ["Doctor", "Admin"])
    user_id = st.text_input("User ID")
    password = st.text_input("Password", type="password")

    if st.button("Login"):
        if role == "Doctor":
            user = doctor_login_col.find_one({"doctor_id": user_id, "password": password})
        else:
            user = admin_login_col.find_one({"username": user_id, "password": password})

        if user:
            st.session_state.user_id = user_id
            st.session_state.role = role
            st.session_state.logged_in = True
            st.session_state.page = "Dashboard"
            st.success(f"Welcome, {role} {user_id}!")
            st.rerun()
        else:
            st.error("Invalid credentials")

# --- Doctor Dashboard ---
def doctor_dashboard():
    st.subheader("🩺 Doctor Dashboard")
    doctor_id = st.session_state.get("user_id")
    st.write(f"Logged in as: **Dr. {doctor_id}**")

    st.subheader("👥 Connected Patients")
    connections = list(connections_col.find({"doctor_id": doctor_id}))
    if not connections:
        st.info("No connected patients.")
        return

    for conn in connections:
        patient_id = conn["patient_id"]
        patient = patient_col.find_one({"patient_id": patient_id})
        if patient:
            st.markdown(f"### Patient: `{patient_id}`")
            st.json(patient)
        else:
            st.warning(f"No data found for patient `{patient_id}`")

    st.subheader("➕ Add New Patient")

    with st.form("add_patient_form"):
        new_patient_id = st.text_input("Patient ID", key="pat_id")
        new_patient_pw = st.text_input("Password", type="password", key="pat_pw")
        name = st.text_input("Name")
        age = st.number_input("Age", min_value=0, max_value=120)
        gender = st.selectbox("Gender", ["Male", "Female", "Other"])
        address = st.text_area("Address")
        contact = st.text_input("Contact")

        diabetes = st.selectbox("Diabetes", ["yes", "no"])
        blood_pressure = st.selectbox("Blood Pressure", ["yes", "no"])
        arthritis = st.selectbox("Arthritis", ["yes", "no"])
        asthma = st.selectbox("Asthma", ["yes", "no"])
        thyroid = st.selectbox("Thyroid", ["yes", "no"])

        submitted = st.form_submit_button("Add Patient")
        if submitted:
            if patient_login_col.find_one({"patient_id": new_patient_id}):
                st.error("Patient ID already exists.")
            else:
                patient_login_col.insert_one({
                    "patient_id": new_patient_id,
                    "password": new_patient_pw
                })
                patient_col.insert_one({
                    "patient_id": new_patient_id,
                    "name": name,
                    "age": age,
                    "gender": gender,
                    "address": address,
                    "contact": contact,
                    "diabetes": diabetes,
                    "blood_pressure": blood_pressure,
                    "arthritis": arthritis,
                    "asthma": asthma,
                    "thyroid": thyroid
                })
                st.success(f"Patient `{new_patient_id}` added successfully.")

# --- Admin Dashboard ---
def admin_dashboard():
    st.subheader("🧑‍💼 Admin Dashboard")
    st.write(f"Logged in as: **Admin {st.session_state.user_id}**")

    st.subheader("➕ Add New Doctor")
    with st.form("add_doctor_form"):
        new_doc_id = st.text_input("Doctor ID", key="doc_id")
        new_doc_pw = st.text_input("Password", type="password", key="doc_pw")
        submitted = st.form_submit_button("Add Doctor")
        if submitted:
            if doctor_login_col.find_one({"doctor_id": new_doc_id}):
                st.error("Doctor ID already exists.")
            else:
                doctor_login_col.insert_one({
                    "doctor_id": new_doc_id,
                    "password": new_doc_pw
                })
                st.success(f"Doctor `{new_doc_id}` added successfully.")

# --- Chat Assistant ---
def chat_assistant():
    st.subheader("🤖 EHR Chat Assistant")
    user_input = st.text_input("Ask something about patient data:")
    if user_input:
        with st.spinner("Thinking..."):
            response = qa_chain.run(user_input)
        st.success(response)

# --- Main Router ---
def main():
    app_header()

    if "logged_in" not in st.session_state or not st.session_state.get("logged_in"):
        login()
        return

    if "page" not in st.session_state:
        st.session_state.page = "Dashboard"

    st.sidebar.title("Navigation")
    st.sidebar.write(f"Logged in as: {st.session_state.user_id} ({st.session_state.role})")

    page = st.sidebar.radio("Go to", ["Dashboard", "Chat Assistant", "Logout"],
                            index=["Dashboard", "Chat Assistant", "Logout"].index(st.session_state.page))

    st.session_state.page = page  # Remember selection

    if page == "Dashboard":
        if st.session_state.role == "Doctor":
            doctor_dashboard()
        elif st.session_state.role == "Admin":
            admin_dashboard()
    elif page == "Chat Assistant":
        chat_assistant()
    elif page == "Logout":
        st.session_state.clear()
        st.rerun()

if __name__ == "__main__":
    main()
