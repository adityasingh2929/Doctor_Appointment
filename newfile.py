import streamlit as st  
import pandas as pd  
import numpy as np  
import joblib  
from sklearn.preprocessing import LabelEncoder  
from io import BytesIO  

# ✅ Load trained model  
model = joblib.load('random_forest_model.pkl')  

# ✅ Set Page Configuration and Styling  
st.set_page_config(  
    page_title="Doctor Engagement Predictor",  
    page_icon="🩺",  
    layout="wide"  
)  

# ➡️ Custom CSS for background and styling  
st.markdown("""  
    <style>  
        body {  
            background-color: #F5F5F5;  
            font-family: Arial, sans-serif;  
        }  
        .main-title {  
            color: #2E3B55;  
            font-size: 36px;  
            font-weight: bold;  
            text-align: center;  
            padding-bottom: 20px;  
        }  
        .sidebar-title {  
            color: #2E3B55;  
            font-size: 22px;  
            font-weight: bold;  
            text-align: center;  
            padding-bottom: 10px;  
        }  
        .stDownloadButton > button {  
            background-color: #2E3B55;  
            color: white;  
            font-weight: bold;  
            border-radius: 8px;  
        }  
        .stDownloadButton > button:hover {  
            background-color: #1C2833;  
        }  
        .dataframe th {  
            background-color: #2E3B55;  
            color: #FFFFFF;  
            text-align: center;  
        }  
    </style>  
""", unsafe_allow_html=True)  

# ✅ Title  
st.markdown('<div class="main-title">Doctor Survey Engagement Predictor 🩺</div>', unsafe_allow_html=True)  

# ✅ Load dataset  
file_path = r"C:\Users\Dell\OneDrive\Desktop\Intership project\dummy_npi_data (1).xlsx"  
df = pd.read_excel(file_path)  

# ✅ Create Time-Based Features  
df['Login hour'] = df['Login Time'].dt.hour  
df['Logout hour'] = df['Logout Time'].dt.hour  
df['Session Duration'] = (df['Logout Time'] - df['Login Time']).dt.total_seconds() / 60  

# ✅ Extract time from datetime  
df['Login Time'] = df['Login Time'].dt.time  
df['Logout Time'] = df['Logout Time'].dt.time  

# ✅ Create Time Slot Column  
df['Time Slot'] = df['Login Time'].astype(str) + " - " + df['Logout Time'].astype(str)  

# ✅ Encode categorical features  
speciality_encoder = LabelEncoder()  
region_encoder = LabelEncoder()  
state_encoder = LabelEncoder()  

# ✅ Fit encoders and create mapping  
df['Speciality'] = speciality_encoder.fit_transform(df['Speciality'])  
speciality_mapping = dict(zip(speciality_encoder.classes_, speciality_encoder.transform(speciality_encoder.classes_)))  

df['Region'] = region_encoder.fit_transform(df['Region'])  
region_mapping = dict(zip(region_encoder.classes_, region_encoder.transform(region_encoder.classes_)))  

df['State'] = state_encoder.fit_transform(df['State'])  
state_mapping = dict(zip(state_encoder.classes_, state_encoder.transform(state_encoder.classes_)))  

# ✅ Predict Engagement  
X = df[['State', 'Region', 'Speciality', 'Login hour', 'Logout hour', 'Session Duration', 'Usage Time (mins)', 'Count of Survey Attempts']]  
df['Engaged'] = model.predict(X)  

# ✅ Sidebar for Input  
with st.sidebar:  
    st.markdown('<div class="sidebar-title">📅 Select Time Slot</div>', unsafe_allow_html=True)  
    
    # ✅ User Input for Time Slot (24-hour format)  
    start_time = st.time_input("Select Start Time", value=pd.to_datetime("06:00").time())  
    end_time = st.time_input("Select End Time", value=pd.to_datetime("23:59").time())  
    
    # 🔍 Filter Options  
    st.markdown("---")  
    st.markdown("### 📌 Filter by:")  
    
    # ✅ Speciality Options  
    specialities = ["All"] + list(speciality_mapping.keys())  
    selected_speciality = st.selectbox("Speciality", specialities)  
    
    # ✅ Region Options  
    regions = ["All"] + list(region_mapping.keys())  
    selected_region = st.selectbox("Region", regions)  
    
    # ✅ State Options  
    states = ["All"] + list(state_mapping.keys())  
    selected_state = st.selectbox("State", states)  

# ✅ Strict Time Slot Logic  
df['Available'] = df.apply(  
    lambda x: (x['Login Time'] >= start_time and x['Logout Time'] <= end_time),  
    axis=1  
)  

# ✅ Fix for 'All' Issue  
selected_speciality_encoded = speciality_mapping.get(selected_speciality) if selected_speciality != "All" else None  
selected_region_encoded = region_mapping.get(selected_region) if selected_region != "All" else None  
selected_state_encoded = state_mapping.get(selected_state) if selected_state != "All" else None  

# ✅ Filtering Logic  
filtered_doctors = df.loc[  
    (df['Available'] == True) &  
    ((selected_speciality_encoded is None) | (df['Speciality'] == selected_speciality_encoded)) &  
    ((selected_region_encoded is None) | (df['Region'] == selected_region_encoded)) &  
    ((selected_state_encoded is None) | (df['State'] == selected_state_encoded)),  
    ['NPI', 'State', 'Region', 'Speciality', 'Usage Time (mins)', 'Count of Survey Attempts', 'Time Slot']  
]  

# ✅ Map back encoded values to original categories  
filtered_doctors['State'] = filtered_doctors['State'].map({v: k for k, v in state_mapping.items()})  
filtered_doctors['Speciality'] = filtered_doctors['Speciality'].map({v: k for k, v in speciality_mapping.items()})  
filtered_doctors['Region'] = filtered_doctors['Region'].map({v: k for k, v in region_mapping.items()})  

# ✅ Sort by Start Time  
filtered_doctors['Start Time'] = pd.to_datetime(filtered_doctors['Time Slot'].str.split(' - ').str[0])  
filtered_doctors = filtered_doctors.sort_values(by='Start Time').drop(columns=['Start Time'])  

# ✅ Display Results  
st.markdown("### 👨‍⚕️ Available and Engaged Doctors:")  
if not filtered_doctors.empty:  
    st.dataframe(filtered_doctors, height=400)  
else:  
    st.write("⚠️ No available doctors found in the selected time slot.")  

# ✅ Export to Excel  
def to_excel(df):  
    output = BytesIO()  
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:  
        df.to_excel(writer, index=False, sheet_name='Available Doctors')  
        writer.close()  
    processed_data = output.getvalue()  
    return processed_data  

# ✅ Download Button for Excel  
if not filtered_doctors.empty:  
    st.download_button(  
        label="📥 Download Available Doctors (Excel)",  
        data=to_excel(filtered_doctors),  
        file_name=f"available_doctors_{start_time.strftime('%H_%M')}_to_{end_time.strftime('%H_%M')}.xlsx",  
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"  
    )  

# ✅ Footer  
st.markdown("---")  
st.markdown(  
    "💡 **Tip:** You can refine the model using more time-based features or by including historical patterns."  
)  
