import streamlit as st

col1,col2 = st.columns(2)
# 공간을 2개 컬럼 으로 분할하여 col1과 col2라는 이름을 가진 컬럼을 생성합니다.  

col1.subheader(' i am column1  subheader !! ')
col2.checkbox('this is checkbox2 in col2 ') 



