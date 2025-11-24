import streamlit as st

con1 = st.container(height=100, border=True)
con2 = st.container(height=50, border=True)
con1.subheader(' i am column1  subheader !! ')
con2.checkbox('this is checkbox2 in col2 ') 



