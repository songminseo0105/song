
import streamlit as st
import pandas as pd
import sqlite3
import time

# ============================================
# 0. DB 연결
# ============================================
def get_conn():
    return sqlite3.connect('madang.db')

conn = get_conn()


# ============================================
# 1. 공용 함수
# ============================================
def run_query(sql, params=()):
    cur = conn.cursor()
    cur.execute(sql, params)
    rows = cur.fetchall()
    cols = [col[0] for col in cur.description]
    return pd.DataFrame(rows, columns=cols)

def run_execute(sql, params=()):
    cur = conn.cursor()
    cur.execute(sql, params)
    conn.commit()


# ============================================
# 2. 세션 초기화
# ============================================
if "new_customer_name" not in st.session_state:
    st.session_state.new_customer_name = ""


# ============================================
# 3. UI
# ============================================
st.title("📚 마당DB 고객 관리 시스템")

tab1, tab2, tab3 = st.tabs(["고객조회", "거래 입력", "고객 등록"])


# ============================================
# Book 목록 로드
# ============================================
book_df = run_query("SELECT bookid, bookname FROM Book")
book_list = [None] + [f"{row.bookid},{row.bookname}" for _, row in book_df.iterrows()]


# ============================================
# TAB 1: 고객 조회
# ============================================
with tab1:
    st.header("🔍 고객 조회 및 거래 내역")

    initial_name = st.session_state.new_customer_name
    name = st.text_input("고객명 입력", value=initial_name)
    st.session_state.new_customer_name = ""  # 초기화

    custid = None

    if name.strip():
        sql = """
            SELECT c.custid, c.name, b.bookname, o.orderdate, o.saleprice
            FROM Customer c
            JOIN Orders o ON c.custid = o.custid
            JOIN Book b ON o.bookid = b.bookid
            WHERE c.name = ?
        """
        df = run_query(sql, (name.strip(),))

        if not df.empty:
            st.success(f"'{name}' 고객의 거래 내역")
            st.dataframe(df)
            custid = df["custid"][0]
        else:
            df2 = run_query("SELECT custid, name FROM Customer WHERE name = ?", (name.strip(),))
            if not df2.empty:
                custid = df2["custid"][0]
                st.warning("거래 내역은 없지만 고객은 존재합니다.")
            else:
                st.error("고객이 존재하지 않습니다.")
                custid = None


# ============================================
# TAB 2: 거래 입력
# ============================================
with tab2:
    st.header("📝 새로운 거래 입력")

    if custid and name.strip():

        st.write(f"고객번호: {custid}")
        st.write(f"고객명: {name}")

        select_book = st.selectbox("구매 서적 선택", book_list)

        if select_book:
            bookid = int(select_book.split(",")[0])
            today = time.strftime("%Y-%m-%d")

            # orderid 생성
            max_df = run_query("SELECT MAX(orderid) AS maxid FROM Orders")
            maxid = max_df["maxid"].iloc[0]

            if pd.isna(maxid):
                new_orderid = 1
            else:
                new_orderid = int(maxid) + 1

            price = st.text_input("금액 입력")

            if st.button("거래 입력"):
                try:
                    run_execute(
                        "INSERT INTO Orders (orderid, custid, bookid, saleprice, orderdate) VALUES (?, ?, ?, ?, ?)",
                        (new_orderid, custid, bookid, price, today)
                    )
                    st.success("거래가 성공적으로 입력되었습니다.")
                    st.rerun()
                except Exception as e:
                    st.error(f"거래 입력 오류: {e}")

    else:
        st.info("고객을 먼저 조회하거나 등록해주세요.")


# ============================================
# TAB 3: 고객 등록
# ============================================
with tab3:
    st.header("👤 고객 등록")

    new_name = st.text_input("이름 (필수)")
    new_address = st.text_input("주소")
    new_phone = st.text_input("전화번호")

    if st.button("고객 등록"):
        if not new_name.strip():
            st.warning("이름은 필수입니다.")
        else:
            # 새로운 custid 생성
            df = run_query("SELECT MAX(custid) AS maxid FROM Customer")
            maxid = df["maxid"].iloc[0]

            if pd.isna(maxid):
                new_custid = 1
            else:
                new_custid = int(maxid) + 1

            try:
                run_execute(
                    "INSERT INTO Customer (custid, name, address, phone) VALUES (?, ?, ?, ?)",
                    (new_custid, new_name.strip(), new_address, new_phone)
                )
                st.success("고객 등록 완료!")
                st.session_state.new_customer_name = new_name.strip()
                st.rerun()
            except Exception as e:
                st.error(f"등록 오류: {e}")
