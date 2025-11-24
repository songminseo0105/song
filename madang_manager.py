import streamlit as st 
import pandas as pd
import sqlite3
import time

# ----------------------------------------------------
# 0. Streamlit 세션 상태 초기화
# ----------------------------------------------------
if 'new_customer_name' not in st.session_state:
    st.session_state.new_customer_name = ""

# ----------------------------------------------------
# 1. 데이터베이스 연결 및 커서 설정
# ----------------------------------------------------
try:
    conn = sqlite3.connect('madang.db')
    cursor = conn.cursor()

except Exception as e:
    st.error(f"데이터베이스 연결 오류: {e}")
    st.stop()


# 쿼리 실행 함수
def get_query_results(sql, params=()):
    cur = conn.cursor()
    cur.execute(sql, params)
    columns = [col[0] for col in cur.description]
    rows = cur.fetchall()
    return pd.DataFrame(rows, columns=columns)


# ----------------------------------------------------
# 2. 새로운 고객 등록
# ----------------------------------------------------
def insert_new_customer(conn, name, address, phone):
    name = name.strip()

    try:
        cur = conn.cursor()
        cur.execute("SELECT MAX(custid) FROM Customer")
        max_custid = cur.fetchone()[0]
        new_custid = (max_custid + 1) if max_custid else 1
    except Exception as e:
        st.error(f"❌ 최대 ID 조회 오류: {e}")
        return False

    try:
        cur.execute(
            "INSERT INTO Customer (custid, name, address, phone) VALUES (?, ?, ?, ?)",
            (new_custid, name, address, phone)
        )
        conn.commit()
        st.success(f"✅ 고객 '{name}'(ID: {new_custid}) 등록 완료!")

        st.session_state.new_customer_name = name
        return True
    except Exception as e:
        conn.rollback()
        st.error(f"❌ 고객 등록 오류: {e}")
        return False


# ----------------------------------------------------
# 3. Streamlit UI
# ----------------------------------------------------
st.title("📚 마당DB Streamlit 고객관리 시스템")

tab1, tab2, tab3 = st.tabs(["고객조회", "거래 입력", "고객 등록"])

# Book 목록 준비
book_df = get_query_results("SELECT bookid, bookname FROM Book")
books = [f"{row.bookid},{row.bookname}" for _, row in book_df.iterrows()]
books.insert(0, None)

initial_name = st.session_state.new_customer_name
name = ""
custid = None


# ---------------------- 고객 조회 ----------------------
with tab1:
    st.header("🔍 고객 조회 및 기존 거래 내역")

    name = st.text_input("고객명", value=initial_name)
    st.session_state.new_customer_name = ""

    if name.strip():
        lookup = name.strip()

        sql = """
            SELECT c.custid, c.name, b.bookname, o.orderdate, o.saleprice
            FROM Customer c
            JOIN Orders o ON c.custid = o.custid
            JOIN Book b ON o.bookid = b.bookid
            WHERE c.name = ?
        """

        df = get_query_results(sql, (lookup,))

        if not df.empty:
            st.success(f"'{lookup}' 고객의 거래 내역입니다.")
            st.dataframe(df)
            custid = df["custid"][0]

        else:
            single_sql = "SELECT custid, name FROM Customer WHERE name = ?"
            customer_df = get_query_results(single_sql, (lookup,))

            if not customer_df.empty:
                custid = customer_df["custid"][0]
                st.warning(f"거래 내역 없음 (ID: {custid})")
            else:
                st.error(f"'{lookup}' 고객이 존재하지 않습니다.")
                custid = None


# ---------------------- 거래 입력 ----------------------
with tab2:
    st.header("📝 새로운 거래 입력")

    if custid and name.strip():
        st.write(f"고객번호: {custid}")
        st.write(f"고객명: {name}")

        select_book = st.selectbox("구매 서적:", books)

        if select_book:
            bookid = int(select_book.split(",")[0])
            today = time.strftime("%Y-%m-%d")

            orderid_df = get_query_results("SELECT MAX(orderid) AS maxid FROM Orders")
            maxid = orderid_df["maxid"][0]
            new_orderid = (maxid + 1) if maxid else 1

            price = st.text_input("금액 입력")

            if st.button("거래 입력"):
                try:
                    cur = conn.cursor()
                    cur.execute(
                        "INSERT INTO Orders (orderid, custid, bookid, saleprice, orderdate) VALUES (?, ?, ?, ?, ?)",
                        (new_orderid, custid, bookid, price, today)
                    )
                    conn.commit()
                    st.success("거래가 입력되었습니다.")
                    st.rerun()
                except Exception as e:
                    conn.rollback()
                    st.error(f"거래 입력 오류: {e}")
    else:
        st.info("고객 조회 후 거래 입력이 가능합니다.")


# ---------------------- 고객 등록 ----------------------
with tab3:
    st.header("👤 새로운 고객 등록")

    new_name = st.text_input("고객 이름 (필수)")
    new_address = st.text_input("주소")
    new_phone = st.text_input("전화번호")

    if st.button("고객 등록"):
        if new_name.strip():
            if insert_new_customer(conn, new_name, new_address, new_phone):
                st.rerun()
        else:
            st.warning("이름은 필수입니다!")
