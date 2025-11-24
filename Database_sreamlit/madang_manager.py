import streamlit as st 
import pymysql
import pandas as pd
import time
import sys

# ----------------------------------------------------
# 0. Streamlit 세션 상태 초기화
# ----------------------------------------------------
# 'new_customer_name' 변수를 초기화하여 등록된 고객 이름을 임시 저장합니다.
if 'new_customer_name' not in st.session_state:
    st.session_state.new_customer_name = ""

# ----------------------------------------------------
# 1. 데이터베이스 연결 및 커서 설정
# ----------------------------------------------------
try:
    # 데이터베이스 연결 정보 (사용자 설정 그대로)
    dbConn = pymysql.connect(user='root', passwd='hamo0526!', host='localhost', db='madang', charset='utf8')
    # DictCursor를 사용하여 쿼리 결과를 딕셔너리 형태로 받습니다.
    cursor = dbConn.cursor(pymysql.cursors.DictCursor)
except Exception as e:
    st.error(f"데이터베이스 연결 오류: {e}")
    st.stop() # 연결 실패 시 앱 실행 중지

# 쿼리 실행 함수: 딕셔너리 결과 반환
def get_query_results(sql):
    cursor.execute(sql)
    return cursor.fetchall()

# ----------------------------------------------------
# 2. 데이터 처리 함수
# ----------------------------------------------------

# 새로운 고객 정보를 Customer 테이블에 삽입하는 함수
def insert_new_customer(db_connection, name, address, phone):
    # 등록 시 이름의 양쪽 공백을 제거합니다. (데이터베이스 일관성 유지)
    name = name.strip() 
    
    try:
        # 1. 새 custid 결정: 현재 Customer 테이블의 최대 custid + 1
        cursor = db_connection.cursor()
        cursor.execute("SELECT MAX(custid) FROM Customer")
        max_custid = cursor.fetchone()[0] 
        new_custid = (max_custid + 1) if max_custid else 1 

    except Exception as e:
        st.error(f"❌ 최대 고객 ID 조회 중 오류 발생: {e}")
        return False

    # 2. 삽입 쿼리 준비
    insert_query = "INSERT INTO Customer (custid, name, address, phone) VALUES (%s, %s, %s, %s)"
    
    try:
        # 쿼리 실행 및 값 전달
        cursor.execute(insert_query, (new_custid, name, address, phone))
        db_connection.commit() 
        st.success(f"✅ 새 고객 '{name}' (CustID: {new_custid}) 등록 완료!")
        
        # 🚨 등록 성공 시 세션 상태에 고객명을 저장하여 조회 탭으로 전달
        st.session_state.new_customer_name = name
        
        return True
    except Exception as e:
        db_connection.rollback() 
        st.error(f"❌ 데이터 삽입 중 오류 발생: {e}")
        st.info("💡 custid 중복이나 Customer 테이블의 컬럼(custid, name, address, phone)을 확인하세요.")
        return False

# ----------------------------------------------------
# 3. Streamlit UI 구성
# ----------------------------------------------------

# Book 목록 데이터 준비 (콤보 박스용)
books = [None]
result = get_query_results("select concat(bookid, ',', bookname) as info from Book")
for res in result:
    books.append(res['info'])

# 탭 정의
tab1, tab2, tab3 = st.tabs(["고객조회", "거래 입력", "고객 등록"])

# 🚨 세션 상태를 사용하여 초기 고객명을 설정 (등록 직후에만 사용됨)
initial_name = st.session_state.new_customer_name
name = ""
custid = 999
result_df = pd.DataFrame()
select_book = ""


# ====================================================
# 3-1. 고객 조회 탭 (tab1)
# ====================================================
with tab1:
    st.header("🔍 고객 조회 및 기존 거래 내역")
    
    # 등록 직후에는 initial_name(새 고객 이름)으로 필드가 자동 채워짐
    name = st.text_input("고객명", value=initial_name, key="customer_name_input")
    
    # 필드에 값이 들어갔으므로 세션 상태 초기화 (다음번 실행 시 빈 칸으로 시작)
    st.session_state.new_customer_name = "" 
    
    if len(name) > 0:
        # 입력된 이름의 양쪽 공백을 제거하고 조회합니다.
        lookup_name = name.strip()
        
        # 🚨🚨🚨 수정됨: CONVERT를 사용하여 문자열 비교의 인코딩 문제를 회피합니다.
        # name = '이름' 대신 CONVERT(name USING utf8) = '이름' 사용
        sql_with_orders = f"select c.custid, c.name, b.bookname, o.orderdate, o.saleprice from Customer c, Book b, Orders o where c.custid = o.custid and o.bookid = b.bookid and CONVERT(c.name USING utf8) = '{lookup_name}';"
        
        st.markdown("---")
        st.caption("실행된 SQL 쿼리:")
        st.code(sql_with_orders, language='sql') # 실행 쿼리 출력 (디버깅용)
        st.markdown("---")

        data = get_query_results(sql_with_orders)
        
        if data:
            st.success(f"✅ '{lookup_name}' 고객의 거래 내역을 찾았습니다.")
            result_df = pd.DataFrame(data)
            st.dataframe(result_df)
            custid = result_df['custid'][0] 
        else:
            # 거래 내역은 없지만 Customer 테이블에만 존재하는 고객 조회 (CONVERT 사용)
            single_cust_sql = f"select custid, name from Customer where CONVERT(name USING utf8) = '{lookup_name}';"
            single_cust_data = get_query_results(single_cust_sql)
            
            if single_cust_data:
                # 거래 내역은 없지만 고객 ID는 확보
                custid = single_cust_data[0]['custid']
                st.warning(f"'{lookup_name}' 고객의 기존 거래 내역을 찾을 수 없습니다. (고객 ID: {custid})")
                st.info("거래 입력 탭에서 새로운 거래를 입력할 수 있습니다.")
            else:
                 st.error(f"❌ '{lookup_name}' 고객이 데이터베이스에 존재하지 않습니다. '고객 등록' 탭에서 등록해 주세요.")
                 custid = 999


# ====================================================
# 3-2. 거래 입력 탭 (tab2)
# ====================================================
with tab2:
    st.header("📝 새로운 거래 입력")
    
    if custid != 999 and len(name) > 0: # 유효한 고객 ID와 이름이 있을 때만 실행
        st.write("고객번호: " + str(custid))
        st.write("고객명: " + name)
        
        select_book = st.selectbox("구매 서적:", books)

        if select_book is not None and select_book != "None":
            bookid = select_book.split(",")[0]
            dt = time.localtime()
            dt = time.strftime('%Y-%m-%d', dt)
            
            # orderid 생성 로직
            orderid_result = get_query_results("SELECT MAX(orderid) as max_orderid FROM orders;")
            orderid = (orderid_result[0]['max_orderid'] + 1) if orderid_result[0]['max_orderid'] is not None else 1
            
            price = st.text_input("금액")
            
            # SQL 쿼리 준비
            sql = f"insert into orders (orderid, custid, bookid, saleprice, orderdate) values ({orderid}, {custid}, {bookid}, {price}, '{dt}');"
            
            if st.button('거래 입력'):
                try:
                    cursor.execute(sql)
                    dbConn.commit()
                    st.success('거래가 입력되었습니다.')
                    st.rerun() # 앱 새로고침
                except Exception as e:
                    dbConn.rollback()
                    st.error(f"거래 입력 중 오류 발생: {e}")
        
    elif len(name) > 0 and custid == 999:
        st.warning(f"'{name}' 고객 정보가 DB에 존재하지 않아 거래를 입력할 수 없습니다. '고객 등록' 탭에서 먼저 등록해 주세요.")
    else:
        st.info("고객 조회 탭에서 고객명을 입력하고 조회하거나, '고객 등록' 탭에서 새로운 고객을 등록해 주세요.")

# ====================================================
# 3-3. 고객 등록 탭 (tab3)
# ====================================================
with tab3:
    st.header("👤 새로운 고객 정보 등록")
    
    new_name = st.text_input("새 고객 이름 (필수):")
    new_address = st.text_input("주소 (선택):")
    new_phone = st.text_input("전화번호 (선택):")
    
    st.markdown("---")
    
    if st.button("고객 정보 등록", key="register_customer", use_container_width=True):
        if new_name:
            success = insert_new_customer(dbConn, new_name, new_address, new_phone)
            if success:
                # 등록 성공 후 새로고침 (이때 세션 상태가 고객명을 들고 감)
                st.rerun() 
        else:
            st.warning("🚨 고객 이름을 반드시 입력해야 합니다.")