import streamlit as st
import ee
import pandas as pd 
import folium
from folium.plugins import Draw
from streamlit_folium import folium_static
import streamlit.components.v1 as components
import change, parks
import geemap.foliumap as geemap


def app():
    national_parks = parks.get_parks()
        
    # V-World 타일 서비스 URL (API 키 포함)
    vworld_satellite_url = "http://api.vworld.kr/req/wmts/1.0.0/{api_key}/Satellite/{z}/{y}/{x}.jpeg"
    vworld_hybrid_url = "http://api.vworld.kr/req/wmts/1.0.0/{api_key}/Hybrid/{z}/{y}/{x}.png"

    # API 키를 여기에 입력하세요
    api_key = "DCFAECAC-2343-3CB2-81AA-1FE195545C28"
    
    # 페이지 제목 설정
    st.title("산사태 예측 지도")

    #마크 다운바(분리 bar)
    st.markdown('<hr style="border:1px solid green;"/>', unsafe_allow_html=True)
        
    # folium 지도 객체에 Earth Engine 레이어 추가 메서드를 연결
    folium.Map.add_ee_layer = change.add_ee_layer
        
    ee.Initialize()
    ModelAverage = pd.read_pickle("ModelAverage토양수분2.pkl")
    Data = pd.read_pickle("Data_actuall토양수분2.pkl")

    # 임계값 설정
    threshold = 0.45

    # 임계값 이상의 값을 가지는 영역에 대한 그라데이션 적용
    # 임계값 미만의 값은 마스크 처리되어 표시되지 않음
    masked_image = ModelAverage.updateMask(ModelAverage.gt(threshold))

    # 최적 임계값을 기반으로 사용자 정의 이진 분포 지도화
    vis_params = {
        'min': threshold,  # 최소값을 임계값으로 설정
        'max': 1,          # 최대값
        'palette': ['#00FF00', '#FFFF00', '#FF0000'],
        'opacity' : 0.6,
        'transparent': True,}

    Map = geemap.Map()

    # # V-World 타일 레이어 추가
    folium.TileLayer(tiles=vworld_satellite_url.replace("{api_key}", api_key),
                    attr='V-World Satellite',
                    name='V-World Satellite', overlay = False).add_to(Map)
                    
    folium.TileLayer(tiles=vworld_hybrid_url.replace("{api_key}", api_key),
                    attr='V-World Hybrid',
                    name='V-World Hybrid', overlay = True).add_to(Map)
    
    Map.addLayer(masked_image, vis_params, 'Landslide vulnerability (Thresholded)')
    
    # 컬러바 추가
    Map.add_colorbar(vis_params, label="Landslide vulnerability", orientation="horizontal", layer_name="Landslide vulnerability (Thresholded)")
    
    # 산사태 발생지역 레이어 추가
    Map.addLayer(Data, {'color': 'orange'}, 'Presence')
    
    Map.centerObject(Data.geometry(), 7)

    Map.add_child(folium.LatLngPopup())
                                            
    # 지도에 레이어 컨트롤 추가
    Map.add_child(folium.LayerControl())

    # Draw 플러그인을 추가하여 사용자가 영역을 선택할 수 있도록 합니다.
    draw = Draw(
        export=True
    )
    draw.add_to(Map)

    # folium 지도 객체를 HTML 문자열로 변환하여 Streamlit에 표시합니다.
    map_html = Map._repr_html_()
    components.html(map_html, height=600)

    # change.display_map_with_draw(Map)
    
    
    lat = st.number_input("위도", value=35.95, format="%.5f")
    lon = st.number_input("경도", value=128.25, format="%.5f")

    # 사용자 입력에 따라 데이터 처리 및 결과 표시
    change.process_user_input(lat, lon)


# 변수 설명#################################################################################
    with st.container():
        col1, col2 = st.columns(2)

    with col1:
        st.markdown("""
        **변수 설명**
        - **Aspect (경사 방향)**: 지형의 경사면이 향하는 방향(동서남북)
        - **Crops (경작지)**: 경작지로 덮여있을 확률(0~1)
        - **Elevation (고도)**: 해수면으로부터의 높이를 m 단위로 측정
        - **Slope (경사도)**: 지표면의 기울기
        - **Water (수역)**: 수역으로 덮여있을 확률(0~1)
        """)

    with col2:
        st.markdown("""
        &nbsp;
        &nbsp;
        - **Susm (지하 토양 수분)**: mm 단위의 지하 토양 수분량
        - **Built (시가화지역)**: 주거·상업·공업지역으로 덮여있을 확률(0~1)
        - **VH (위성 신호 방향)**: Sentinel-1호(SAR) 위성에서 수직(V) 신호로 방출되고 지구 표면으로부터 수평(H) 신호로 수신되는 신호 방향으로, 지형의 구조적 변화와 불규칙한 형태를 감지하는데 효과적
        """)


    # feature_importance 이미지를 표시합니다.#########################################################
    st.image('./image/feature_importance.png', caption='Uploaded Image.', use_column_width=True)

if __name__ == "__main__":
    app()
