import streamlit as st
import pandas as pd
import json
import os
import time

st.set_page_config(page_title="Lumix OS Mobile", page_icon="🏍️", layout="centered")

# Helper functions for dynamic contacts
CONTACTS_FILE = "contacts.json"

def load_contacts():
    if os.path.exists(CONTACTS_FILE):
        with open(CONTACTS_FILE, "r") as f:
            return json.load(f)
    return {"emergency": {"name": "", "phone": ""}, "family": {"name": "", "phone": ""}}

def save_contacts(contacts_dict):
    with open(CONTACTS_FILE, "w") as f:
        json.dump(contacts_dict, f, indent=4)

contacts = load_contacts()

st.title("🏍️ LUMIX OS")
st.subheader("Smart Helmet Companion")
st.divider()

page = st.sidebar.radio("Navigation", ["Dashboard", "Emergency Alerts", "Settings"])

crash_data = None
if os.path.exists("alert_data.json"):
    try:
        with open("alert_data.json", "r", encoding="utf-8") as f:
            crash_data = json.load(f)
    except Exception:
        pass 

if page == "Dashboard":
    st.header("Helmet Status")
    col1, col2, col3 = st.columns(3)
    col1.metric("Battery", "85%", "-2%")
    col2.metric("Connection", "Paired", "Live")
    col3.metric("Vision System", "Active")
    st.divider()
    
    if crash_data:
        st.error("⚠️ CRASH EVENT DETECTED! Check Emergency Alerts Tab!")
    else:
        st.success("All systems nominal. Ride safe.")

elif page == "Emergency Alerts":
    st.header("🚨 Emergency Response System")
    
    if crash_data:
        st.error("**CRITICAL ALERT: SOS DISPATCHED**")
        st.write("Hardware damage suspected. Last Known Location sent to contacts.")
        
        col1, col2 = st.columns(2)
        with col1:
            st.write(f"**Date/Time:** {crash_data.get('timestamp', 'Unknown')}")
            st.write(f"**Impact:** {crash_data.get('impact', 'Unknown')}")
        with col2:
            st.write("**Dispatched To:**")
            # Dynamically reads the contacts!
            st.write(f"🚨 112 Emergency Services")
            if contacts['emergency']['name']:
                st.write(f"📞 {contacts['emergency']['name']} (Emergency)")
            if contacts['family']['name']:
                st.write(f"👨‍👩‍👧 {contacts['family']['name']} (Family)")

        st.divider()
        st.info(f"📍 **Address:** {crash_data.get('address', 'Calculating address...')}")
        
        lat = crash_data.get('lat', 18.4575)
        lon = crash_data.get('lon', 73.8677)
        map_data = pd.DataFrame({'lat': [lat], 'lon': [lon]})
        st.map(map_data, zoom=15, color="#ff0000", size=100)
        
        if st.button("Acknowledge & Clear Alert", type="primary"):
            try:
                os.remove("alert_data.json")
            except FileNotFoundError:
                pass
            st.rerun()
    else:
        st.success("✅ No active emergencies.")

elif page == "Settings":
    st.header("Contact Configuration")
    
    st.subheader("Level 1: Emergency Contact")
    em_name = st.text_input("Name", value=contacts['emergency']['name'], key="em_n")
    em_phone = st.text_input("Phone Number", value=contacts['emergency']['phone'], key="em_p")
    
    st.subheader("Level 2: Friends & Family")
    fam_name = st.text_input("Name", value=contacts['family']['name'], key="fam_n")
    fam_phone = st.text_input("Phone Number", value=contacts['family']['phone'], key="fam_p")
    
    if st.button("Save Contacts", type="primary"):
        new_contacts = {
            "emergency": {"name": em_name, "phone": em_phone},
            "family": {"name": fam_name, "phone": fam_phone}
        }
        save_contacts(new_contacts)
        st.success("Contacts securely saved to Lumix network.")

time.sleep(1)
st.rerun()