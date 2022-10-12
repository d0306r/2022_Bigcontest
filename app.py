# app.py
# author daye.jung

import streamlit as st
import pandas as pd
import decimal
from decimal import Decimal, getcontext
import numpy as np

def main() :

    st.title('제주 여행 탄소발자국 계산기🌴')
    st.text('여행 전체 인원 사용량 기준으로 답변해주세요.')
    st.subheader("1. 숙박🏨")

    #주소별 온실가스 배출량 불러오기
    df = pd.read_csv('TB_ECO_BUILDING_GHG_GIS_JEJU_1920.csv', thousands=',', encoding='euc-kr')

    #sum 배출량만 남기고 제거
    df_new = df
    for i in range(16) :
        df_2 = df_new.drop(df_new.columns[[2]], axis = 1)
        df_new = df_2
    df_new = df_new.drop('LTNO_ADDR', axis=1)

    #2022년 숙박 자료만 남기고 제거
    df_3 = pd.read_csv('JT_MT_ACCTO_TRRSRT_SCCNT_LIST.csv', thousands=',', encoding='cp949')
    df_3_drop = df_3[df_3['BASE_YEAR'] ==2021].index
    df_3.drop(df_3_drop, inplace=True)
    df_3_drop_2 = df_3[df_3['CL_CD'] != 'c3'].index
    df_3.drop(df_3_drop_2, inplace=True)

    #필요없는 컬럼 제거
    df_accomodation = df_3
    for i in range(13) :
        df_3 = df_accomodation.drop(df_accomodation.columns[[4]], axis = 1)
        df_accomodation = df_3

    #두 데이터프레임 머지
    df_new.rename(columns={'ROAD_NM_ADDR':'ADDR'}, inplace='True')
    df_INNER_JOIN = pd.merge(df_accomodation, df_new, left_on = 'ADDR', right_on='ADDR', how='outer')

    #숙박 명이 동일한 것들의 배출 평균 구하기
    df_meadian = df_INNER_JOIN.groupby('AREA_NM')['SUM_GRGS_DSAMT'].mean()

    #숙박 업소 명으로 데이티프레임 합치기
    df_resort = pd.merge(df_meadian, df_INNER_JOIN, left_on = 'AREA_NM', right_on='AREA_NM', how='inner')
    df_resort = df_resort.drop(df_resort.columns[[2,3,5,6]], axis=1)
    df_resort = df_resort.drop_duplicates()
    df_resort.rename(columns={'SUM_GRGS_DSAMT_x':'SUM_CO2'}, inplace='True')

    #SUM_CO2 값이 NaN인 항목들 채워주기
    resort_replaced = df_resort.replace(np.nan, 0.2727)
    resort_replaced = resort_replaced.set_index('AREA_NM')

    #표출될 데이티프레임 설정
    show_list = resort_replaced.drop('SUM_CO2', axis=1)
    st.write(show_list)

    #사용자에게 값 입력받기
    use_accomodation = st.number_input("몇 개의 숙소를 이용했나요? ", 1, 3)
    sum_accomo = 0
    for j in range(1, use_accomodation+1):

        resort_name_list = ['BK호텔제주', '그랜드 조선 제주', '꿈꾸는 노마드', '더블루제주', '메종글래드 제주']
        if resort_name_list[j] not in st.session_state:
            st.session_state[resort_name_list[j]] = resort_name_list[j]

        accomodation = st.text_input("%d번째로 이용한 숙소 명을 정확히 입력하세요 " % j, key = resort_name_list[j], help='현재 입력된 숙소 명은 예시입니다.')
        cnt_rooms_total = st.number_input("%d번째로 이용한 숙소의 총 객실 수를 입력하세요 " % j, 1, 500, help='https://kr.trip.com/ 링크를 참고하세요.')
        cnt_rooms = st.number_input("%d번째로 이용한 숙소에서 사용하는 방의 개수를 입력하세요 " % j, 1, 500)

        if resort_replaced.loc[accomodation]['SUM_CO2'] == 0.272700 :
            resort_co2 = resort_replaced.loc[accomodation]['SUM_CO2']
            co2_accomodation = Decimal(0.272700) * Decimal(cnt_rooms)
            sum_accomo = Decimal(sum_accomo) + Decimal(co2_accomodation)
            sum_accomo = round(sum_accomo, 4)
            sum_accomo = Decimal(sum_accomo)
        else :
            resort_co2 = resort_replaced.loc[accomodation]['SUM_CO2']
            co2_accomodation = Decimal(resort_co2) / Decimal(cnt_rooms_total) * Decimal(cnt_rooms)
            sum_accomo = Decimal(sum_accomo) + Decimal(co2_accomodation)
            sum_accomo = round(sum_accomo, 4)
            sum_accomo = Decimal(sum_accomo)
        

    #항공
    sum_airplane = Decimal('0.128') * 2 * 459


    #이동수단 
    st.subheader("2. 이동수단🚌")
    sum_trans = 0
    co2_trans = 0
    sum_car = 0

    if 'y_or_n' not in st.session_state:
        st.session_state['y_or_n'] = "Y"

    use_car = st.text_input ("렌트카를 이용했나요? (Y 또는 N을 입력해주세요.) ", key = 'y_or_n')
    if use_car == 'Y' :
        car = st.selectbox("이용 차량의 연료 구분을 선택하세요", ['가솔린/디젤', '하이브리드', '전기자동차'])
        distance_car = st.number_input ("이동 거리를 입력하세요(km) ", 0.0, 100.0)
        if car == '가솔린/디젤' :
            sum_car = Decimal(0.2293) * Decimal(distance_car)
        elif car == '하이브리드' :
            sum_car = Decimal(0.1563) * Decimal(distance_car)
        else :
            sum_car = Decimal(0.1219) * Decimal(distance_car)

    else :
        use_trans = st.number_input ("여행 전체에서 교통수단을 몇 번 이용했나요? ", 1, 100)

        for i in range (1,use_trans+1) :     
            transport = st.selectbox ("%d번째로 이용한 교통수단을 선택하세요 " %i, ['버스', '택시', '배', '전동킥보드', '자전거'])
            distance = st.number_input ("%d번째 교통수단의 이동 거리를 입력하세요(km) " %i, 0.0, 100.0)
                
            if transport == '버스' :
                kind_bus = st.text_input ("%d번째로 탑승한 버스가 시외/고속버스인가요? (Y 또는 N을 입력해주세요.) " %i)
                if kind_bus == 'Y' :
                    co2_trans = Decimal(distance) * Decimal('0.03')
                else :
                    co2_trans = Decimal(distance) * Decimal('0.04')

            elif transport == '택시' :
                co2_trans = Decimal(distance) * Decimal('0.19')
            elif transport == '배' :
                co2_trans = Decimal(distance) * Decimal('0.38')
            elif transport == '전동킥보드' :
                co2_trans = Decimal(distance) * Decimal('0.004')
            elif transport == '자전거' :
                co2_trans == 0
            else :
                co2_trans == 0
            
            sum_trans = Decimal(Decimal(sum_trans) + Decimal(co2_trans))


    #휴대폰 사용
    st.subheader("3. 휴대폰 사용📱")
    sum_mobile = 0
    co2_mobile = 0
    use_data = st.number_input("사용한 데이터는 총 몇 MB인가요? ", 0, 1000000)
    co2_mobile = Decimal('0.011') * Decimal(use_data)
    sum_mobile = Decimal(Decimal(sum_mobile) + Decimal(co2_mobile))

    use_call = st.number_input("통화 시간은 총 몇 분인가요? ", 0 ,100)
    co2_mobile = Decimal('0.0036') * Decimal(use_call)
    sum_mobile = Decimal(Decimal(sum_mobile) + Decimal(co2_mobile))


    #식사 및 카페
    st.subheader("4. 식당 및 카페🍽️")
    cnt_meat = st.number_input("여행 중 육류 메뉴에 지출한 금액을 입력하세요 ", 0, 1000000)
    cnt_grain = st.number_input("여행 중 곡류 메뉴에 지출한 금액을 입력하세요 ", 0 ,1000000)
    cnt_seafood = st.number_input("여행 중 해산물/생선류 메뉴에 지출한 금액을 입력하세요 ", 0, 1000000)
    cnt_milk = st.number_input("여행 중 우유, 유제품류 메뉴에 지출한 금액을 입력하세요 ", 0, 1000000)
    cnt_vegi = st.number_input("여행 중 과채류 메뉴에 지출한 금액을 입력하세요 ", 0, 1000000)

    eur_change_meat = Decimal(cnt_meat) * Decimal('0.00072')
    eur_change_grain = Decimal(cnt_grain) * Decimal('0.00072')
    eur_change_seafood = Decimal(cnt_seafood) * Decimal('0.00072')
    eur_change_milk = Decimal(cnt_milk) * Decimal('0.00072')
    eur_change_vegi = Decimal(cnt_vegi) * Decimal('0.00072')

    sum_meal = 0
    co2_meat = Decimal('0.785') * Decimal(eur_change_meat)
    co2_grain = Decimal('0.073') * Decimal(eur_change_grain)
    co2_seafood = Decimal('0.177') * Decimal(eur_change_seafood) 
    co2_milk = Decimal('0.204') * Decimal(eur_change_milk)
    co2_vegi = Decimal('0.061') * Decimal(eur_change_vegi)


    cafe_or_drink = st.text_input("여행 중 카페에 방문하거나 음주를 했나요? (Y 또는 N을 입력해주세요.) ")
    if cafe_or_drink == 'Y' :
        cnt_drinks = st.number_input("여행 중 음료(커피/차/주스)에 지출한 금액을 입력하세요 ", 0, 1000000)
        cnt_dessert = st.number_input("여행 중 디저트 메뉴에 지출한 금액을 입력하세요 ", 0, 1000000)
        cnt_liquid = st.number_input("여행 중 주류에 지출한 금액을 입력하세요 ", 0, 1000000)

        eur_change_drinks = Decimal(cnt_drinks) * Decimal('0.00072')
        eur_change_dessert = Decimal(cnt_dessert) * Decimal('0.00072')
        eur_change_liquid = Decimal(cnt_liquid) * Decimal('0.00072')


        co2_drinks = Decimal('0.275') * Decimal(eur_change_drinks)
        co2_dessert = Decimal('0.31') * Decimal(eur_change_dessert)
        co2_liquid = Decimal('0.051') * Decimal(eur_change_liquid)
        sum_meal = Decimal(co2_meat + co2_grain + co2_seafood + co2_milk + co2_vegi + co2_drinks + co2_dessert + co2_liquid)
    else :
        sum_meal = Decimal(co2_meat + co2_grain + co2_seafood + co2_milk + co2_vegi)
        
    
    sum_jeju_co2 = Decimal(sum_accomo + sum_airplane + sum_trans + sum_car + sum_mobile + sum_meal)
    sum_jeju_co2 = round(sum_jeju_co2, 2)

    st.header("여행에서 발생한 탄소발자국의 총 합계👣")
    st.text("항공, 숙박, 이동수단, 휴대폰 사용, 식품 섭취에서 발생한 탄소발자국의 합입니다.(kg/CO2)")
    st.info(sum_jeju_co2) 

if __name__ == '__main__' :	
    main()