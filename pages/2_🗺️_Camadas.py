import streamlit as st
from sqlalchemy import create_engine, text
from urllib.parse import quote_plus
import pandas as pd
import folium
from streamlit_folium import st_folium
import ast
import datetime
from folium.plugins import MarkerCluster, Fullscreen
import requests
from branca.element import Template, MacroElement

# --- Page Configuration ---
st.set_page_config(page_title="Camadas", page_icon="🗺️", layout="wide")
st.logo('./assets/logo_horiz.png', size="large")


# --- Initialize Connection ---
@st.cache_resource
def init_connection():
    try:
        connection_details = st.secrets["connections"]["apibd"]
        encoded_password = quote_plus(connection_details["password"])
        connection_string = (
            f"{connection_details['dialect']}+{connection_details['driver']}://"
            f"{connection_details['username']}:{encoded_password}@"
            f"{connection_details['host']}:{connection_details['port']}/"
            f"{connection_details['database']}"
        )
        engine = create_engine(connection_string)
        # Test connection
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return engine
    except Exception as e:
        st.error(f"Database connection error: {e}")
        raise

engine = init_connection()

# --- Data Fetching Functions ---
@st.cache_data
@st.cache_data
def get_management_data(ttl=300):
    query = "SELECT management_id, management_coords, observer, managed_mass_kg, date FROM data_coralsol_management"
    with engine.begin() as connection:
        df = pd.read_sql(query, con=connection.connection)
    df.columns = map(str.lower, df.columns)
    return df

@st.cache_data
def get_locality_data(ttl=300):
    query = "SELECT locality_id, coords_local, name, date FROM data_coralsol_locality"
    with engine.begin() as connection:
        df = pd.read_sql(query, con=connection.connection)
    df.columns = map(str.lower, df.columns)
    return df

@st.cache_data
def get_occ_data(ttl=300):
    query = "SELECT Occurrence_id, Spot_coords, Date, Depth, Superficie_photo FROM data_coralsol_occurrence WHERE Superficie_photo IS NOT NULL LIMIT 10"
    with engine.begin() as connection:
        df = pd.read_sql(query, con=connection.connection)
    df.columns = map(str.lower, df.columns)
    return df

@st.cache_data
def get_dafor_data(ttl=300):
    query = "SELECT Dafor_id, Locality_id, Dafor_coords, Date, Horizontal_visibility, Bathymetric_zone, Method, Dafor_value FROM data_coralsol_dafor"
    with engine.begin() as connection:
        df = pd.read_sql(query, con=connection.connection)
    df.columns = map(str.lower, df.columns)
    return df


base_url = "https://api-bd.institutohorus.org.br/api"


# --- Sidebar Widgets ---
def render_sidebar():
    with st.sidebar:
        start_date = st.date_input('Data Inicial', datetime.date(2012, 1, 1))
        end_date = st.date_input('Data Final', datetime.date.today() + datetime.timedelta(days=1))

        layer = st.radio("Camadas", ["Manejos", "Localidades", "Ocorrências", "Monitoramento"])
        show_management = layer == "Manejos"
        show_locality = layer == "Localidades"
        show_occ = layer == "Ocorrências"
        show_dafor = layer == "Monitoramento"

    return start_date, end_date, show_management, show_locality, show_occ, show_dafor

# --- Persist Map State ---
def get_map():
    """Creates a folium map while preserving zoom and center."""
    if "map_center" not in st.session_state:
        st.session_state.map_center = [-27.281798, -48.366133]
    if "map_zoom" not in st.session_state:
        st.session_state.map_zoom = 13
    if "map_key" not in st.session_state:
        st.session_state.map_key = 0  # 🔥 Forces re-render when changed

    m = folium.Map(
        location=st.session_state.map_center,
        zoom_start=st.session_state.map_zoom,
        tiles="https://api.mapbox.com/v4/mapbox.satellite/{z}/{x}/{y}.png?access_token=pk.eyJ1Ijoic2lsdmVpcmF0Y2wiLCJhIjoiY202MTRrN3N5MGt3MDJqb2xhc3R0empqZCJ9.YfjBqq5HbnacUNw9Tyiaew",
        attr="Mapbox attribution",
        max_zoom=20,
        min_zoom=1
    )
    Fullscreen().add_to(m)

    return m

# --- Update Layers Without Resetting Map ---
# --- Update Layers Without Resetting Map ---
def render_map(m, start_date, end_date, show_management, show_locality, show_occ, show_dafor):
    # Convert start_date and end_date to datetime objects with dayfirst=True
    start_dt = pd.to_datetime(start_date, dayfirst=True)
    end_dt = pd.to_datetime(end_date, dayfirst=True)
    
    # Helper function for consistent date parsing
    def parse_dates(df):
        df['date'] = pd.to_datetime(df['date'], dayfirst=True, errors='coerce')
        return df.dropna(subset=['date'])  # Remove rows with invalid dates

    # --- Management Layer ---
    if show_management:
        management_layer = folium.FeatureGroup(name="Manejos").add_to(m)
        data = parse_dates(get_management_data())
        filtered_data = data[(data['date'] >= start_dt) & (data['date'] <= end_dt)]

        marker_cluster = MarkerCluster().add_to(m)
        for _, row in filtered_data.iterrows():
            try:
                coords = ast.literal_eval(row['management_coords'])
                if isinstance(coords, list) and len(coords) > 0:
                    folium.Marker(
                        [coords[0][0], coords[0][1]],  # lat, lon
                        popup=f"""
                        Observer: {row['observer']}<br>
                        Date: {row['date'].strftime('%d/%m/%Y')}<br>
                        Mass: {row['managed_mass_kg']} kg
                        """,
                        tooltip=f"Manejo {row['management_id']}"
                    ).add_to(marker_cluster)
            except Exception as e:
                st.error(f"Error adding management marker: {e}")

    # --- Locality Layer ---
    if show_locality:
        locality_layer = folium.FeatureGroup(name="Localidades").add_to(m)
        data = parse_dates(get_locality_data())
        filtered_data = data[(data['date'] >= start_dt) & (data['date'] <= end_dt)]

        for _, row in filtered_data.iterrows():
            try:
                coords = ast.literal_eval(row['coords_local'])
                if isinstance(coords, list) and len(coords) > 0:
                    folium.PolyLine(
                        coords,
                        popup=f"""
                        Locality: {row['name']}<br>
                        Date: {row['date'].strftime('%d/%m/%Y')}
                        """,
                        tooltip=f"Localidade {row['locality_id']}"
                    ).add_to(locality_layer)
            except Exception as e:
                st.error(f"Error adding locality {row['locality_id']}: {e}")

    # --- Occurrence Layer ---
    if show_occ:
        occ_cluster = MarkerCluster(disableClusteringAtZoom=5).add_to(m)
        data = parse_dates(get_occ_data())
        filtered_data = data[(data['date'] >= start_dt) & (data['date'] <= end_dt)]

        for _, row in filtered_data.iterrows():
            try:
                coords = ast.literal_eval(row['spot_coords'])
                if isinstance(coords, list) and len(coords) > 0:
                    photo_url = f"{base_url}/Upload/UploadImageCoralSol/{row['occurrence_id']}/{row['superficie_photo']}"
                    response = requests.get(photo_url)
                    
                    popup_html = f"""
                    <b>Date:</b> {row['date'].strftime('%d/%m/%Y')}<br>
                    <b>Depth:</b> {row['depth']} m<br>
                    """
                    
                    if response.status_code == 200:
                        popup_html += f'<img src="data:image/png;base64,{response.text}" width="300">'
                    else:
                        popup_html += f'<i>Photo unavailable (Error {response.status_code})</i>'
                    
                    folium.Marker(
                        [coords[0][0], coords[0][1]],
                        popup=folium.Popup(popup_html, max_width=300),
                        tooltip=f"Ocorrência {row['occurrence_id']}"
                    ).add_to(occ_cluster)
            except Exception as e:
                st.error(f"Error adding occurrence {row['occurrence_id']}: {e}")

    # --- Dafor Monitoring Layer ---
    if show_dafor:
        dafor_layer = folium.FeatureGroup(name="Monitoramento").add_to(m)
        data = parse_dates(get_dafor_data())
        filtered_data = data[(data['date'] >= start_dt) & (data['date'] <= end_dt)]

        for _, row in filtered_data.iterrows():
            try:
                coords = ast.literal_eval(row['dafor_coords'])
                if isinstance(coords, list) and len(coords) > 0:
                    folium.PolyLine(
                        coords,
                        popup=f"""
                        Locality: {row['locality_id']}<br>
                        Date: {row['date'].strftime('%d/%m/%Y')}
                        """,
                        tooltip=f"Monitoramento {row['dafor_id']}"
                    ).add_to(dafor_layer)
            except Exception as e:
                st.error(f"Error adding dafor monitoring {row['dafor_id']}: {e}")
    
    return m
# --- Main Logic ---
def main():
    start_date, end_date, show_management, show_locality, show_occ, show_dafor = render_sidebar()

    # --- Display Layer Titles ---
    if show_management:
        st.write("### Locais Manejados")
    
    if show_locality:
        st.write("### Localidades")
        
    if show_occ:
        st.write("### Ocorrências")
    
    if show_dafor:
        st.write("### Monitoramentos")

    # Load or create the map
    m = get_map()
    m = render_map(m, start_date, end_date, show_management, show_locality, show_occ, show_dafor)

    # Capture the previous zoom & center
    prev_zoom = st.session_state.map_zoom
    prev_center = st.session_state.map_center

    # ✅ Temporary storage for zoom & center
    if "temp_map_zoom" not in st.session_state:
        st.session_state.temp_map_zoom = st.session_state.map_zoom
    if "temp_map_center" not in st.session_state:
        st.session_state.temp_map_center = st.session_state.map_center

    # Display the map but DO NOT update zoom yet
    st_data = st_folium(
        m,
        width="100%",
        height=700,
        returned_objects=["center", "zoom"],
        key=st.session_state["map_key"],  # 🔥 Forces reloading when changed
    )

    # Debugging info
    #st.write(f"Debug: Before update -> Zoom: {prev_zoom}, Center: {prev_center}")
    #st.write(f"Debug: st_folium returned -> {st_data}")

    # Only store zoom & center TEMPORARILY
    if st_data:
        if "center" in st_data and st_data["center"]:
            st.session_state.temp_map_center = [st_data["center"]["lat"], st_data["center"]["lng"]]
        if "zoom" in st_data and st_data["zoom"]:
            st.session_state.temp_map_zoom = st_data["zoom"]

    # ✅ Add a button to apply zoom & center updates
    if st.button("Update Map View"):
        if (
            st.session_state.temp_map_zoom != prev_zoom or
            st.session_state.temp_map_center != prev_center
        ):
            st.session_state.map_zoom = st.session_state.temp_map_zoom
            st.session_state.map_center = st.session_state.temp_map_center
            st.session_state["map_key"] += 1  # 🔥 Forces full re-render
            st.write(f"Debug: Applied map updates, new key = {st.session_state['map_key']}")
    

if __name__ == "__main__":
    main()