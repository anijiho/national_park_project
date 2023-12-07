import streamlit as st
import base64
import pandas as pd
from datetime import datetime, timedelta
import ee
import geemap
import os
import folium
from streamlit_folium import folium_static
import parks

def app():
    # 데이터프레임 생성
    national_parks = parks.get_parks()

    st.title("반달이의 눈 : 국립공원 변화탐지 플랫폼")

    st.write("")
    st.write("")

    # Markdown을 사용한 소제목
    st.markdown("##### 👍누구나 쉽게 클릭만으로, 위성 기반 전 국립공원의 자연 변화탐지")
    st.write("""
            **※화면 창을 최대 크기로 했을 때 최적의 서비스를 경험하실 수 있습니다.**
            """)


    #마크 다운바(분리 bar)
    st.markdown('<hr style="border:1px solid green;"/>', unsafe_allow_html=True)

    # #반달이의 눈 의미 소개글
        
    # auth = st.button('Authenticate')
    # if auth:
    #     ee.Authenticate()


    with st.expander("'반달이의 눈'의 의미"): # 비율로 컬럼 크기 지정
        st.write("""
                마스코트 '반달이'와 '하늘의 눈' 역할을 하는 위성 데이터를 더한 말로
                국립공원공단을 위해 성실히 자연 변화를 탐지하겠다는 저희의 포부를 담았습니다! :) 
                """)

    
    # '사용법 안내' 버튼 생성
    with st.expander("사용법 영상 보기"):
        col1,col2 = st.columns([3,1])  # 비율로 컬럼 크기 지정
        with col1:
            st.write("아래 영상을 시청하시면 더 빠르게 사용법 안내를 받으실 수 있습니다.")
            st.markdown(f"""
            <iframe width="600" height="315" src="https://www.youtube.com/embed/Efk0k0YhnZY" frameborder="0" allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture" allowfullscreen></iframe>
                
            """, unsafe_allow_html=True)

        with col2:
        # 두 번째 컬럼에 이미지 추가
            st.write("")
            st.write("")
            st.write("")
            st.image("./image/sunglass.png", width=200)  # 이미지 경로 변경

    # '사용법 글로 보기'(세 영역 나누기)
    # 1/이미지를 Base64 문자열로 인코딩하는 함수
    def get_image_base64(image_path):
        with open(image_path, "rb") as image_file:
            encoded_string = base64.b64encode(image_file.read()).decode()
        return "data:image/png;base64," + encoded_string

    # 2.이미지 파일을 Base64로 인코딩(그냥 경로 복붙은 작동 안됨)
    encoded_image1 = get_image_base64("./image/homepage.png")
    encoded_image2 = get_image_base64("./image/landcover_change.png")
    encoded_image3 = get_image_base64("./image/graph1.png")
    encoded_image4 = get_image_base64("./image/graph2.png")
    encoded_image5 = get_image_base64("./image/ex1.png")

    st.markdown("""
        <style>
        .custom-box {
            border: 1px solid #ccc;
            border-radius: 5px;
            width: 100%; 
            padding: 3px; #패딩 = 여백
            margin-bottom: 5px;
            align-items: center; /* 수직 방향 가운데 정렬 설정 */
            background-color: white;
        }
                

        </style>
        <div class="custom-box">
            <h4 style="margin:10; font-size: 14px;"> &nbsp;&nbsp;사용법 글로 보기</h4> 
        </div>
        """, unsafe_allow_html=True)
    #띄어쓰기 &nbsp;

    st.write("")
    st.write("")
    st.write("")

    #컨테이너(구분 박스) 생성
    with st.container():
        col1, col2, col3 = st.columns(3)  # 세 개의 컬럼(영역) 생성

        with col1:
            st.markdown("#####  &nbsp;페이지 사용법")  # 첫 번째 이미지 소제목
            st.markdown(f"<img src='{encoded_image1}' alt='Image1' style='width:100%'>", unsafe_allow_html=True)
            st.write("""
                    1. 사용설명서에서 사용법 영상과 글을 확인합니다.
                    2. 페이지 좌측 사이드바에서 원하는 메뉴를 선택합니다.
                    3. 페이지 접속 후, 관심 지역과 탐지 기간을 설정하면 변화 탐지가 시작됩니다.
                       만약 관심 지역 또는 탐지 기간 설정창이 없는 경우에는 입력하지 않아도 변화탐지가 가능한 것입니다. 
                    """)


        with col2:
            st.markdown("##### &nbsp;지형 & 식생지수 변화탐지")
            st.markdown(f"<img src='{encoded_image2}' alt='Image1' style='width:100%'>", unsafe_allow_html=True)
            st.write("""
                    관심 지역의 지형 변화를 확인할 수 있습니다.
                    1. 원하는 국립공원 선택 또는 geojson 파일 업로드로 관심 지역을 설정합니다.
                    2. 탐지 기간을 설정합니다.
                    3. 'submit' 버튼을 선택하면 지형 변화탐지 시작!
                    """)

            st.divider()


            st.markdown(f"<img src='{encoded_image3}' alt='Image1' style='width:100%'>", unsafe_allow_html=True)
            st.markdown(f"<img src='{encoded_image4}' alt='Image1' style='width:100%'>", unsafe_allow_html=True)
            st.write("""
                    1. 원하는 국립공원 선택 또는 geojson 파일 업로드로 관심 지역을 설정합니다.
                    2. 'submit' 버튼을 선택하면 식생지수 분석 시작!
                    3. 10년간의 식생지수를 분석하여 미래 식생지수를 예측하고, 식생지수 추이를 보여줍니다.
                    """)

        with col3:
            st.markdown("##### &nbsp;산사태 예측 지도")
            st.markdown(f"<img src='{encoded_image5}' alt='Image1' style='width:100%'>", unsafe_allow_html=True)
            st.write("""
                    1. 산사태 예측 지도 페이지 접속 시, 곧바로 예측이 시작됩니다.
                    2. 예측 후 지도를 클릭하면 해당 지역의 위도/경도를 확인할 수 있습니다.
                    3. 지도 하단의 위도/경도 입력창에 위도와 경도를 입력하면, 어떤 요소가 산사태에 영향을 미칠지 확인하실 수 있습니다.
                    """)



    #마크 다운바(분리 bar)
    st.markdown('<hr style="border:1px light gray;"/>', unsafe_allow_html=True)
    st.write('※ 사용에 불편한 점이 생기면 개발자(✉️ @gmail.com)에게 편히 연락주세요.')
    st.write('※❗화면 창을 최대 크기로 하였을 때 최적의 서비스를 경험하실 수 있습니다.')

    # st.markdown("""
    #     <style>
    #     /* Hide the link button */
    #     .stApp a:first-child {
    #         display: none;
    #     }
        
    #     .css-15zrgzn {display: none}
    #     .css-eczf16 {display: none}
    #     .css-jn99sy {display: none}
    #     </style>
    #     """, unsafe_allow_html=True)

    # add_selectbox = st.sidebar.selectbox("페이지 이동", ("홈화면", "지표면 변화 & 식생지수", "산사태 예측 지도"))

# launch
if __name__  == "__main__" :
    app()