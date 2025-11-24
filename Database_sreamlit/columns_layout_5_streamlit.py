import streamlit as st

tab1, tab2 = st.tabs(["Tab1", "Tab2"])
tab1.write("this is tab1")
tab2.write("this is tab2")