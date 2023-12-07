import streamlit as st
import folium
from streamlit_folium import folium_static
import geemap
import ee
import pandas as pd
import branca.colormap as cm
import matplotlib.pyplot as plt
import numpy as np
import pprint
from folium.plugins import Draw
import geopandas as gpd
from shapely.geometry import shape, Polygon
import json
import hydralit_components as hc
from datetime import datetime, timedelta


import change, parks
import matplotlib.font_manager as fm

font_path = 'c:/USERS/ASUS/APPDATA/LOCAL/MICROSOFT/WINDOWS/FONTS/NANUMGOTHIC.TTF'
# 폰트 프로퍼티 설정
font_prop = fm.FontProperties(fname=font_path, size=14)
# matplotlib의 폰트를 설정
plt.rcParams['font.family'] = font_prop.get_name()

def app():

    # 페이지 제목 설정
    st.title("토양 분석 그래프")

    #마크 다운바(분리 bar)
    st.markdown('<hr style="border:1px solid green;"/>', unsafe_allow_html=True)

    # Initialize the Earth Engine module.
    ee.Initialize()

    national_parks = parks.get_parks()

    tab1, tab2 = st.tabs(['국립공원 선택', 'GeoJson 파일 업로드'])

    with tab1:
        with st.form("selected_park"):
            col1, buff, col2 = st.columns([1, 0.3, 1])
            with col1:
                # 사용자로부터 시작 날짜를 입력 받습니다.
                start_date = st.date_input('관측 시작 날짜를 선택해 주세요.', 
                                        min_value=datetime(2014, 1, 1).date(), 
                                        value=datetime(2023, 11, 20).date())
            # 현재 날짜를 한 번만 계산합니다.
            current_date = datetime.now().date()
            # # 종료 날짜의 최대 값을 계산합니다.
            # max_end_date = min(start_date + timedelta(days=270), current_date)
            with col2:
                # 사용자로부터 종료 날짜를 입력 받습니다.
                end_date = st.date_input('관측 종료 날짜를 선택해 주세요.', 
                                        value=current_date, 
                                        min_value=start_date, 
                                        )
            # # 날짜 간격이 9개월을 초과하는지 확인합니다.
            # if start_date < end_date and (end_date - start_date).days > 270:
            #     st.error('선택한 기간이 9개월을 초과합니다. 날짜를 다시 선택해 주세요.')
                
            if start_date >= end_date:
                st.error('종료 날짜는 시작 날짜 이후여야 합니다.')
            # GEE에서 사용할 날짜 형식으로 변환합니다.
            start_date_str = start_date.strftime('%Y-%m-%d')
            end_date_str = end_date.strftime('%Y-%m-%d')
            
            selected_park = st.selectbox("국립공원을 선택해 주세요.", national_parks['park_ko'])
            uploaded_file = None
            # Every form must have a submit button.
            submitted = st.form_submit_button("Submit")
        if submitted:
            ee.Initialize()
        
            loc = change.get_aoi(selected_park, uploaded_file)
            geo_loc = loc.geometry()
            location = geo_loc.centroid().coordinates().getInfo()[::-1]
            # 분석에 사용할 투영의 명목상의 해상도 [단위: 미터].
            scale = 1000
            # Add Earth Engine drawing method to folium.
            folium.Map.add_ee_layer = change.add_ee_layer
            # 데이터가 있는 토양 깊이 [cm].
            olm_depths = [0, 10, 30, 60, 100, 200]
            # 참조 깊이와 연결된 밴드 이름.
            olm_bands = ["b" + str(sd) for sd in olm_depths]
            # 모래 함량과 관련된 이미지.
            sand = change.get_soil_prop("sand")
            # 점토 함량과 관련된 이미지.
            clay = change.get_soil_prop("clay")
            # 유기 탄소 함량과 관련된 이미지.
            orgc = change.get_soil_prop("orgc")
            # 유기 탄소 함량을 유기물 함량으로 변환.
            orgm = orgc.multiply(1.724)
            col1, buff, col2 = st.columns([1, 0.2, 1])
            with col1:
                # 함수를 적용하여 모래 함량 프로필을 얻습니다.
                profile_sand = change.local_profile(sand, loc, scale, olm_bands)
                
                # 점토 및 유기 탄소 함량 프로필.
                profile_clay = change.local_profile(clay, loc, scale, olm_bands)
                profile_orgc = change.local_profile(orgc, loc, scale, olm_bands)
                            
                # 막대 그래프 형태의 데이터 시각화.
                fig, ax = plt.subplots(figsize=(15, 6))
                ax.axes.get_yaxis().set_visible(False)
                # 라벨 위치 정의.
                x = np.arange(len(olm_bands))
                # 막대 너비 정의.
                width = 0.25
                # 모래 함량 프로필을 나타내는 막대 그래프.
                rect1 = ax.bar(
                    x - width,
                    [round(100 * profile_sand[b], 2) for b in olm_bands],
                    width,
                    label="모래",
                    color="#ecebbd",
                )
                # 점토 함량 프로필을 나타내는 막대 그래프.
                rect2 = ax.bar(
                    x,
                    [round(100 * profile_clay[b], 2) for b in olm_bands],
                    width,
                    label="흙",
                    color="#6f6c5d",
                )
                # 유기 탄소 함량 프로필을 나타내는 막대 그래프.
                rect3 = ax.bar(
                    x + width,
                    [round(100 * profile_orgc[b], 2) for b in olm_bands],
                    width,
                    label="유기 탄소",
                    color="black",
                    alpha=0.75,
                )
                # 각 막대 그래프에 함수 적용.
                change.autolabel_soil_prop(rect1, ax)
                change.autolabel_soil_prop(rect2, ax)
                change.autolabel_soil_prop(rect3, ax)
                # 그래프 제목 설정.
                ax.set_title("깊이에 따른 토양 성분 (함량)", fontsize=14)
                # x/y 라벨 및 눈금 속성 설정.
                ax.set_xticks(x)
                x_labels = [str(d) + " cm" for d in olm_depths]
                ax.set_xticklabels(x_labels, rotation=45, fontsize=10)
                ax.spines["left"].set_visible(False)
                ax.spines["right"].set_visible(False)
                ax.spines["top"].set_visible(False)
                
                # 현재 축의 높이를 아래쪽으로 10% 축소.
                box = ax.get_position()
                ax.set_position([box.x0, box.y0 + box.height * 0.1, box.width, box.height * 0.9])
                
                # 현재 축 아래에 범례 추가.
                ax.legend(
                    loc="upper center", bbox_to_anchor=(0.5, -0.15), fancybox=True, shadow=True, ncol=3
                )
                st.pyplot(fig)
                    
            with col2:
                # 시들음점과 토양의 최대 수분용량을 위한 두 개의 상수 이미지 초기화.
                wilting_point = ee.Image(0)
                field_capacity = ee.Image(0)
                # 각 표준 깊이에 대한 계산을 루프를 사용하여 수행.
                for key in olm_bands:
                    # 적절한 깊이에서 모래, 점토, 유기물 얻기.
                    si = sand.select(key)
                    ci = clay.select(key)
                    oi = orgm.select(key)
                    # 시들음점 계산.
                    # 주어진 깊이에 필요한 theta_1500t 매개변수.
                    theta_1500ti = (
                        ee.Image(0)
                        .expression(
                            "-0.024 * S + 0.487 * C + 0.006 * OM + 0.005 * (S * OM)\
                            - 0.013 * (C * OM) + 0.068 * (S * C) + 0.031",
                            {
                                "S": si,
                                "C": ci,
                                "OM": oi,
                            },
                        )
                        .rename("T1500ti")
                    )
                    # 시들음점을 위한 최종 식.
                    wpi = theta_1500ti.expression(
                        "T1500ti + (0.14 * T1500ti - 0.002)", {"T1500ti": theta_1500ti}
                    ).rename("wpi")
                    # 전체 시들음점을 ee.Image에 새 밴드로 추가.
                    wilting_point = wilting_point.addBands(wpi.rename(key).float())
                    # 최대 수분용량 계산을 위한 동일한 과정.
                    # 주어진 깊이에 필요한 theta_33t 매개변수.
                    theta_33ti = (
                        ee.Image(0)
                        .expression(
                            "-0.251 * S + 0.195 * C + 0.011 * OM +\
                            0.006 * (S * OM) - 0.027 * (C * OM)+\
                            0.452 * (S * C) + 0.299",
                            {
                                "S": si,
                                "C": ci,
                                "OM": oi,
                            },
                        )
                        .rename("T33ti")
                    )
                    # 토양의 최대 수분용량을 위한 최종 식.
                    fci = theta_33ti.expression(
                        "T33ti + (1.283 * T33ti * T33ti - 0.374 * T33ti - 0.015)",
                        {"T33ti": theta_33ti.select("T33ti")},
                    )
                    # 전체 최대 수분용량을 ee.Image에 새 밴드로 추가.
                    field_capacity = field_capacity.addBands(fci.rename(key).float())
                profile_wp = change.local_profile(wilting_point, loc, scale, olm_bands)
                profile_fc = change.local_profile(field_capacity, loc, scale, olm_bands)
                fig, ax = plt.subplots(figsize=(15, 6))
                ax.axes.get_yaxis().set_visible(False)
                
                # 라벨 위치 정의.
                x = np.arange(len(olm_bands))
                
                # 막대 그래프의 너비 정의.
                width = 0.25
                
                # 시듦점에서의 물 함량과 관련된 막대 그래프.
                rect1 = ax.bar(
                    x - width / 2,
                    [round(profile_wp[b] * 100, 2) for b in olm_bands],
                    width,
                    label="시들음 시점의 토양 수분 함량",
                    color="red",
                    alpha=0.5,
                )
                
                # 수분용량에서의 물 함량과 관련된 막대 그래프.
                rect2 = ax.bar(
                    x + width / 2,
                    [round(profile_fc[b] * 100, 2) for b in olm_bands],
                    width,
                    label="토양 최대 수분용량",
                    color="blue",
                    alpha=0.5,
                )
                
                # 각 막대 위에 라벨 추가.
                change.autolabel_soil_prop(rect1, ax)
                change.autolabel_soil_prop(rect2, ax)
                
                # 그래프 제목 설정.
                ax.set_title("깊이에 따른 토양 수분 특성", fontsize=14)
                
                # x/y 라벨 및 눈금 속성 설정.
                ax.set_xticks(x)
                x_labels = [str(d) + " cm" for d in olm_depths]
                ax.set_xticklabels(x_labels, rotation=45, fontsize=10)
                ax.spines["left"].set_visible(False)
                ax.spines["right"].set_visible(False)
                ax.spines["top"].set_visible(False)
                
                # 현재 축의 높이를 아래쪽으로 10% 축소.
                box = ax.get_position()
                ax.set_position([box.x0, box.y0 + box.height * 0.1, box.width, box.height * 0.9])
                
                # 현재 축 아래에 범례 추가.
                ax.legend(
                    loc="upper center", bbox_to_anchor=(0.5, -0.15), fancybox=True, shadow=True, ncol=2
                )
                st.pyplot(fig)
    with tab2:
        with st.form("uploaded_file"):
            col1, buff, col2 = st.columns([1, 0.3, 1])
            with col1:
                # 사용자로부터 시작 날짜를 입력 받습니다.
                start_date = st.date_input('관측 시작 날짜를 선택해 주세요.', 
                                        min_value=datetime(2014, 1, 1).date(), 
                                        value=datetime(2023, 11, 20).date())
            # 현재 날짜를 한 번만 계산합니다.
            current_date = datetime.now().date()
            # # 종료 날짜의 최대 값을 계산합니다.
            # max_end_date = min(start_date + timedelta(days=270), current_date)
            with col2:
                # 사용자로부터 종료 날짜를 입력 받습니다.
                end_date = st.date_input('관측 종료 날짜를 선택해 주세요.', 
                                        value=current_date, 
                                        min_value=start_date, 
                                        )
            # # 날짜 간격이 9개월을 초과하는지 확인합니다.
            # if start_date < end_date and (end_date - start_date).days > 270:
            #     st.error('선택한 기간이 9개월을 초과합니다. 날짜를 다시 선택해 주세요.')
                
            if start_date >= end_date:
                st.error('종료 날짜는 시작 날짜 이후여야 합니다.')
            # GEE에서 사용할 날짜 형식으로 변환합니다.
            start_date_str = start_date.strftime('%Y-%m-%d')
            end_date_str = end_date.strftime('%Y-%m-%d')
            
            # 사용자로부터 GeoJSON 파일 업로드 받기
            uploaded_file = st.file_uploader("GeoJSON 파일을 업로드 해주세요.", type=['geojson'])
            selected_park = None

            # Every form must have a submit button.
            submitted = st.form_submit_button("Submit")
            
        if submitted:
            ee.Initialize()
        
            loc = change.get_aoi(selected_park, uploaded_file)
            geo_loc = loc.geometry()
            location = geo_loc.centroid().coordinates().getInfo()[::-1]
            # 분석에 사용할 투영의 명목상의 해상도 [단위: 미터].
            scale = 1000
            # Add Earth Engine drawing method to folium.
            folium.Map.add_ee_layer = change.add_ee_layer
            # 데이터가 있는 토양 깊이 [cm].
            olm_depths = [0, 10, 30, 60, 100, 200]
            # 참조 깊이와 연결된 밴드 이름.
            olm_bands = ["b" + str(sd) for sd in olm_depths]
            # 모래 함량과 관련된 이미지.
            sand = change.get_soil_prop("sand")
            # 점토 함량과 관련된 이미지.
            clay = change.get_soil_prop("clay")
            # 유기 탄소 함량과 관련된 이미지.
            orgc = change.get_soil_prop("orgc")
            # 유기 탄소 함량을 유기물 함량으로 변환.
            orgm = orgc.multiply(1.724)
            col1, buff, col2 = st.columns([1, 0.2, 1])

            with col1:
                # 함수를 적용하여 모래 함량 프로필을 얻습니다.
                profile_sand = change.local_profile(sand, loc, scale, olm_bands)
                
                # 점토 및 유기 탄소 함량 프로필.
                profile_clay = change.local_profile(clay, loc, scale, olm_bands)
                profile_orgc = change.local_profile(orgc, loc, scale, olm_bands)
                            
                # 막대 그래프 형태의 데이터 시각화.
                fig, ax = plt.subplots(figsize=(15, 6))
                ax.axes.get_yaxis().set_visible(False)
                # 라벨 위치 정의.
                x = np.arange(len(olm_bands))
                # 막대 너비 정의.
                width = 0.25
                # 모래 함량 프로필을 나타내는 막대 그래프.
                rect1 = ax.bar(
                    x - width,
                    [round(100 * profile_sand[b], 2) for b in olm_bands],
                    width,
                    label="모래",
                    color="#ecebbd",
                )
                # 점토 함량 프로필을 나타내는 막대 그래프.
                rect2 = ax.bar(
                    x,
                    [round(100 * profile_clay[b], 2) for b in olm_bands],
                    width,
                    label="흙",
                    color="#6f6c5d",
                )
                # 유기 탄소 함량 프로필을 나타내는 막대 그래프.
                rect3 = ax.bar(
                    x + width,
                    [round(100 * profile_orgc[b], 2) for b in olm_bands],
                    width,
                    label="유기 탄소",
                    color="black",
                    alpha=0.75,
                )
                # 각 막대 그래프에 함수 적용.
                change.autolabel_soil_prop(rect1, ax)
                change.autolabel_soil_prop(rect2, ax)
                change.autolabel_soil_prop(rect3, ax)
                # 그래프 제목 설정.
                ax.set_title("깊이에 따른 토양 성분 (함량)", fontsize=14)
                # x/y 라벨 및 눈금 속성 설정.
                ax.set_xticks(x)
                x_labels = [str(d) + " cm" for d in olm_depths]
                ax.set_xticklabels(x_labels, rotation=45, fontsize=10)
                ax.spines["left"].set_visible(False)
                ax.spines["right"].set_visible(False)
                ax.spines["top"].set_visible(False)
                
                # 현재 축의 높이를 아래쪽으로 10% 축소.
                box = ax.get_position()
                ax.set_position([box.x0, box.y0 + box.height * 0.1, box.width, box.height * 0.9])
                
                # 현재 축 아래에 범례 추가.
                ax.legend(
                    loc="upper center", bbox_to_anchor=(0.5, -0.15), fancybox=True, shadow=True, ncol=3
                )
                st.pyplot(fig)
                    
            with col2:
                # 시들음점과 토양의 최대 수분용량을 위한 두 개의 상수 이미지 초기화.
                wilting_point = ee.Image(0)
                field_capacity = ee.Image(0)
                # 각 표준 깊이에 대한 계산을 루프를 사용하여 수행.
                for key in olm_bands:
                    # 적절한 깊이에서 모래, 점토, 유기물 얻기.
                    si = sand.select(key)
                    ci = clay.select(key)
                    oi = orgm.select(key)
                    # 시들음점 계산.
                    # 주어진 깊이에 필요한 theta_1500t 매개변수.
                    theta_1500ti = (
                        ee.Image(0)
                        .expression(
                            "-0.024 * S + 0.487 * C + 0.006 * OM + 0.005 * (S * OM)\
                            - 0.013 * (C * OM) + 0.068 * (S * C) + 0.031",
                            {
                                "S": si,
                                "C": ci,
                                "OM": oi,
                            },
                        )
                        .rename("T1500ti")
                    )
                    # 시들음점을 위한 최종 식.
                    wpi = theta_1500ti.expression(
                        "T1500ti + (0.14 * T1500ti - 0.002)", {"T1500ti": theta_1500ti}
                    ).rename("wpi")
                    # 전체 시들음점을 ee.Image에 새 밴드로 추가.
                    wilting_point = wilting_point.addBands(wpi.rename(key).float())
                    # 최대 수분용량 계산을 위한 동일한 과정.
                    # 주어진 깊이에 필요한 theta_33t 매개변수.
                    theta_33ti = (
                        ee.Image(0)
                        .expression(
                            "-0.251 * S + 0.195 * C + 0.011 * OM +\
                            0.006 * (S * OM) - 0.027 * (C * OM)+\
                            0.452 * (S * C) + 0.299",
                            {
                                "S": si,
                                "C": ci,
                                "OM": oi,
                            },
                        )
                        .rename("T33ti")
                    )
                    # 토양의 최대 수분용량을 위한 최종 식.
                    fci = theta_33ti.expression(
                        "T33ti + (1.283 * T33ti * T33ti - 0.374 * T33ti - 0.015)",
                        {"T33ti": theta_33ti.select("T33ti")},
                    )
                    # 전체 최대 수분용량을 ee.Image에 새 밴드로 추가.
                    field_capacity = field_capacity.addBands(fci.rename(key).float())
                profile_wp = change.local_profile(wilting_point, loc, scale, olm_bands)
                profile_fc = change.local_profile(field_capacity, loc, scale, olm_bands)
                fig, ax = plt.subplots(figsize=(15, 6))
                ax.axes.get_yaxis().set_visible(False)
                # 라벨 위치 정의.
                x = np.arange(len(olm_bands))
                
                # 막대 그래프의 너비 정의.
                width = 0.25
                
                # 시듦점에서의 물 함량과 관련된 막대 그래프.
                rect1 = ax.bar(
                    x - width / 2,
                    [round(profile_wp[b] * 100, 2) for b in olm_bands],
                    width,
                    label="시들음 시점의 토양 수분 함량",
                    color="red",
                    alpha=0.5,
                )
                
                # 수분용량에서의 물 함량과 관련된 막대 그래프.
                rect2 = ax.bar(
                    x + width / 2,
                    [round(profile_fc[b] * 100, 2) for b in olm_bands],
                    width,
                    label="토양 최대 수분용량",
                    color="blue",
                    alpha=0.5,
                )
                
                # 각 막대 위에 라벨 추가.
                change.autolabel_soil_prop(rect1, ax)
                change.autolabel_soil_prop(rect2, ax)
                
                # 그래프 제목 설정.
                ax.set_title("깊이에 따른 토양 수분 특성", fontsize=14)
                
                # x/y 라벨 및 눈금 속성 설정.
                ax.set_xticks(x)
                x_labels = [str(d) + " cm" for d in olm_depths]
                ax.set_xticklabels(x_labels, rotation=45, fontsize=10)
                ax.spines["left"].set_visible(False)
                ax.spines["right"].set_visible(False)
                ax.spines["top"].set_visible(False)
                
                # 현재 축의 높이를 아래쪽으로 10% 축소.
                box = ax.get_position()
                ax.set_position([box.x0, box.y0 + box.height * 0.1, box.width, box.height * 0.9])
                
                # 현재 축 아래에 범례 추가.
                ax.legend(
                    loc="upper center", bbox_to_anchor=(0.5, -0.15), fancybox=True, shadow=True, ncol=2
                )
                st.pyplot(fig)

    # with st.form("change_detection"):
    #     tab1, tab2 = st.tabs(['국립공원 선택', 'GeoJson 파일 업로드'])

    #     with tab1:
    #         col1, buff, col2 = st.columns([1, 0.3, 1])
    #         with col1:
    #             # 사용자로부터 시작 날짜를 입력 받습니다.
    #             start_date = st.date_input('관측 시작 날짜를 선택해 주세요.', 
    #                                     min_value=datetime(2014, 1, 1).date(), 
    #                                     value=datetime(2023, 11, 20).date())

    #         # 현재 날짜를 한 번만 계산합니다.
    #         current_date = datetime.now().date()

    #         # 종료 날짜의 최대 값을 계산합니다.
    #         max_end_date = min(start_date + timedelta(days=270), current_date)

    #         with col2:
    #             # 사용자로부터 종료 날짜를 입력 받습니다.
    #             end_date = st.date_input('관측 종료 날짜를 선택해 주세요.', 
    #                                     value=max_end_date, 
    #                                     min_value=start_date, 
    #                                     max_value=max_end_date
    #                                     )

    #         # 날짜 간격이 9개월을 초과하는지 확인합니다.
    #         if start_date < end_date and (end_date - start_date).days > 270:
    #             st.error('선택한 기간이 9개월을 초과합니다. 날짜를 다시 선택해 주세요.')
                
    #         elif start_date >= end_date:
    #             st.error('종료 날짜는 시작 날짜 이후여야 합니다.')

    #         # GEE에서 사용할 날짜 형식으로 변환합니다.
    #         start_date_str = start_date.strftime('%Y-%m-%d')
    #         end_date_str = end_date.strftime('%Y-%m-%d')
            
    #         # 사용자로부터 GeoJSON 파일 업로드 받기
    #         uploaded_file = st.file_uploader("GeoJSON 파일을 업로드 해주세요.", type=['geojson'])

    #     with tab2:
    #         col1, buff, col2 = st.columns([1, 0.3, 1])

    #         with col1:
    #             # 사용자로부터 시작 날짜를 입력 받습니다.
    #             start_date = st.date_input('관측 시작 날짜를 선택해 주세요.', 
    #                                     min_value=datetime(2014, 1, 1).date(), 
    #                                     value=datetime(2023, 11, 20).date())

    #         # 현재 날짜를 한 번만 계산합니다.
    #         current_date = datetime.now().date()

    #         # 종료 날짜의 최대 값을 계산합니다.
    #         max_end_date = min(start_date + timedelta(days=270), current_date)

    #         with col2:
    #             # 사용자로부터 종료 날짜를 입력 받습니다.
    #             end_date = st.date_input('관측 종료 날짜를 선택해 주세요.', 
    #                                     value=max_end_date, 
    #                                     min_value=start_date, 
    #                                     max_value=max_end_date
    #                                     )

    #         # 날짜 간격이 9개월을 초과하는지 확인합니다.
    #         if start_date < end_date and (end_date - start_date).days > 270:
    #             st.error('선택한 기간이 9개월을 초과합니다. 날짜를 다시 선택해 주세요.')
                
    #         elif start_date >= end_date:
    #             st.error('종료 날짜는 시작 날짜 이후여야 합니다.')

    #         # GEE에서 사용할 날짜 형식으로 변환합니다.
    #         start_date_str = start_date.strftime('%Y-%m-%d')
    #         end_date_str = end_date.strftime('%Y-%m-%d')

            
    #         selected_park = st.selectbox("국립공원을 선택해 주세요.", national_parks['park_ko'])

    #     # Every form must have a submit button.
    #     submitted = st.form_submit_button("Submit")


    # if submitted:
    #     ee.Initialize()
    
    #     loc = change.get_aoi(selected_park, uploaded_file)
    #     geo_loc = loc.geometry()
    #     location = geo_loc.centroid().coordinates().getInfo()[::-1]

    #     # 분석에 사용할 투영의 명목상의 해상도 [단위: 미터].
    #     scale = 1000

    #     # Add Earth Engine drawing method to folium.
    #     folium.Map.add_ee_layer = change.add_ee_layer

    #     # 데이터가 있는 토양 깊이 [cm].
    #     olm_depths = [0, 10, 30, 60, 100, 200]

    #     # 참조 깊이와 연결된 밴드 이름.
    #     olm_bands = ["b" + str(sd) for sd in olm_depths]

    #     # 모래 함량과 관련된 이미지.
    #     sand = change.get_soil_prop("sand")

    #     # 점토 함량과 관련된 이미지.
    #     clay = change.get_soil_prop("clay")

    #     # 유기 탄소 함량과 관련된 이미지.
    #     orgc = change.get_soil_prop("orgc")

    #     # 유기 탄소 함량을 유기물 함량으로 변환.
    #     orgm = orgc.multiply(1.724)

    #     col1, buff, col2 = st.columns([1, 0.2, 1])

    #     with col1:

    #         # 함수를 적용하여 모래 함량 프로필을 얻습니다.
    #         profile_sand = change.local_profile(sand, loc, scale, olm_bands)
            
    #         # 점토 및 유기 탄소 함량 프로필.
    #         profile_clay = change.local_profile(clay, loc, scale, olm_bands)
    #         profile_orgc = change.local_profile(orgc, loc, scale, olm_bands)
                        
    #         # 막대 그래프 형태의 데이터 시각화.
    #         fig, ax = plt.subplots(figsize=(15, 6))
    #         ax.axes.get_yaxis().set_visible(False)

    #         # 라벨 위치 정의.
    #         x = np.arange(len(olm_bands))

    #         # 막대 너비 정의.
    #         width = 0.25

    #         # 모래 함량 프로필을 나타내는 막대 그래프.
    #         rect1 = ax.bar(
    #             x - width,
    #             [round(100 * profile_sand[b], 2) for b in olm_bands],
    #             width,
    #             label="모래",
    #             color="#ecebbd",
    #         )

    #         # 점토 함량 프로필을 나타내는 막대 그래프.
    #         rect2 = ax.bar(
    #             x,
    #             [round(100 * profile_clay[b], 2) for b in olm_bands],
    #             width,
    #             label="흙",
    #             color="#6f6c5d",
    #         )

    #         # 유기 탄소 함량 프로필을 나타내는 막대 그래프.
    #         rect3 = ax.bar(
    #             x + width,
    #             [round(100 * profile_orgc[b], 2) for b in olm_bands],
    #             width,
    #             label="유기 탄소",
    #             color="black",
    #             alpha=0.75,
    #         )

    #         # 각 막대 그래프에 함수 적용.
    #         change.autolabel_soil_prop(rect1, ax)
    #         change.autolabel_soil_prop(rect2, ax)
    #         change.autolabel_soil_prop(rect3, ax)

    #         # 그래프 제목 설정.
    #         ax.set_title("깊이에 따른 토양 성분 (함량)", fontsize=14)

    #         # x/y 라벨 및 눈금 속성 설정.
    #         ax.set_xticks(x)
    #         x_labels = [str(d) + " cm" for d in olm_depths]
    #         ax.set_xticklabels(x_labels, rotation=45, fontsize=10)

    #         ax.spines["left"].set_visible(False)
    #         ax.spines["right"].set_visible(False)
    #         ax.spines["top"].set_visible(False)
            
    #         # 현재 축의 높이를 아래쪽으로 10% 축소.
    #         box = ax.get_position()
    #         ax.set_position([box.x0, box.y0 + box.height * 0.1, box.width, box.height * 0.9])
            
    #         # 현재 축 아래에 범례 추가.
    #         ax.legend(
    #             loc="upper center", bbox_to_anchor=(0.5, -0.15), fancybox=True, shadow=True, ncol=3
    #         )
    #         st.pyplot(fig)
                
    #     with col2:

    #         # 시들음점과 토양의 최대 수분용량을 위한 두 개의 상수 이미지 초기화.
    #         wilting_point = ee.Image(0)
    #         field_capacity = ee.Image(0)

    #         # 각 표준 깊이에 대한 계산을 루프를 사용하여 수행.
    #         for key in olm_bands:

    #             # 적절한 깊이에서 모래, 점토, 유기물 얻기.
    #             si = sand.select(key)
    #             ci = clay.select(key)
    #             oi = orgm.select(key)

    #             # 시들음점 계산.
    #             # 주어진 깊이에 필요한 theta_1500t 매개변수.
    #             theta_1500ti = (
    #                 ee.Image(0)
    #                 .expression(
    #                     "-0.024 * S + 0.487 * C + 0.006 * OM + 0.005 * (S * OM)\
    #                     - 0.013 * (C * OM) + 0.068 * (S * C) + 0.031",
    #                     {
    #                         "S": si,
    #                         "C": ci,
    #                         "OM": oi,
    #                     },
    #                 )
    #                 .rename("T1500ti")
    #             )

    #             # 시들음점을 위한 최종 식.
    #             wpi = theta_1500ti.expression(
    #                 "T1500ti + (0.14 * T1500ti - 0.002)", {"T1500ti": theta_1500ti}
    #             ).rename("wpi")

    #             # 전체 시들음점을 ee.Image에 새 밴드로 추가.
    #             wilting_point = wilting_point.addBands(wpi.rename(key).float())

    #             # 최대 수분용량 계산을 위한 동일한 과정.
    #             # 주어진 깊이에 필요한 theta_33t 매개변수.
    #             theta_33ti = (
    #                 ee.Image(0)
    #                 .expression(
    #                     "-0.251 * S + 0.195 * C + 0.011 * OM +\
    #                     0.006 * (S * OM) - 0.027 * (C * OM)+\
    #                     0.452 * (S * C) + 0.299",
    #                     {
    #                         "S": si,
    #                         "C": ci,
    #                         "OM": oi,
    #                     },
    #                 )
    #                 .rename("T33ti")
    #             )

    #             # 토양의 최대 수분용량을 위한 최종 식.
    #             fci = theta_33ti.expression(
    #                 "T33ti + (1.283 * T33ti * T33ti - 0.374 * T33ti - 0.015)",
    #                 {"T33ti": theta_33ti.select("T33ti")},
    #             )

    #             # 전체 최대 수분용량을 ee.Image에 새 밴드로 추가.
    #             field_capacity = field_capacity.addBands(fci.rename(key).float())

    #         profile_wp = change.local_profile(wilting_point, loc, scale, olm_bands)
    #         profile_fc = change.local_profile(field_capacity, loc, scale, olm_bands)

    #         fig, ax = plt.subplots(figsize=(15, 6))
    #         ax.axes.get_yaxis().set_visible(False)

    #         # 라벨 위치 정의.
    #         x = np.arange(len(olm_bands))
            
    #         # 막대 그래프의 너비 정의.
    #         width = 0.25
            
    #         # 시듦점에서의 물 함량과 관련된 막대 그래프.
    #         rect1 = ax.bar(
    #             x - width / 2,
    #             [round(profile_wp[b] * 100, 2) for b in olm_bands],
    #             width,
    #             label="시들음 시점의 토양 수분 함량",
    #             color="red",
    #             alpha=0.5,
    #         )
            
    #         # 수분용량에서의 물 함량과 관련된 막대 그래프.
    #         rect2 = ax.bar(
    #             x + width / 2,
    #             [round(profile_fc[b] * 100, 2) for b in olm_bands],
    #             width,
    #             label="토양 최대 수분용량",
    #             color="blue",
    #             alpha=0.5,
    #         )
            
    #         # 각 막대 위에 라벨 추가.
    #         change.autolabel_soil_prop(rect1, ax)
    #         change.autolabel_soil_prop(rect2, ax)
            
    #         # 그래프 제목 설정.
    #         ax.set_title("깊이에 따른 토양 수분 특성", fontsize=14)
            
    #         # x/y 라벨 및 눈금 속성 설정.
    #         ax.set_xticks(x)
    #         x_labels = [str(d) + " cm" for d in olm_depths]
    #         ax.set_xticklabels(x_labels, rotation=45, fontsize=10)

    #         ax.spines["left"].set_visible(False)
    #         ax.spines["right"].set_visible(False)
    #         ax.spines["top"].set_visible(False)
            
    #         # 현재 축의 높이를 아래쪽으로 10% 축소.
    #         box = ax.get_position()
    #         ax.set_position([box.x0, box.y0 + box.height * 0.1, box.width, box.height * 0.9])
            
    #         # 현재 축 아래에 범례 추가.
    #         ax.legend(
    #             loc="upper center", bbox_to_anchor=(0.5, -0.15), fancybox=True, shadow=True, ncol=2
    #         )
    #         st.pyplot(fig)
                

if __name__ == "__main__":
    app()