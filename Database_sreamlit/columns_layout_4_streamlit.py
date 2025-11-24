import streamlit as st

st.sidebar.write("This lives in the side")
c = st.sidebar.button("Clicked me")
st.write(c)