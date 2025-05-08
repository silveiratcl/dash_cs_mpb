import streamlit as st
from sqlalchemy import create_engine
import pandas as pd
import folium
from streamlit_folium import folium_static
import ast
import datetime
from folium.plugins import MarkerCluster, Fullscreen
import requests

# --- Page Configuration ---
st.set_page_config(page_title="Mapa", page_icon="🗺️", layout="wide")
st.logo('./assets/logo_horiz.png', size="large")

# --- Initialize DB Connection ---
@st.cache_resource
def init_connection():
    try:
        connection_details = st.secrets["connections"]["apibd06"]
        connection_string = (
            f"{connection_details['dialect']}+{connection_details['driver']}://"
            f"{connection_details['username']}:{connection_details['password']}@"
            f"{connection_details['host']}:{connection_details['port']}/"
            f"{connection_details['database']}"
        )
        engine = create_engine(connection_string)
        return engine.connect()
    except KeyError as e:
        st.error(f"KeyError: {e}. Check your secrets.toml structure or Streamlit Cloud settings.")
        raise
    except Exception as e:
        st.error(f"An error occurred while connecting to the database: {e}")
        raise

conn = init_connection()

# --- Data Fetching Functions ---
@st.cache_data
def get_management_data():
    query = "SELECT management_id, Management_coords, Observer, Managed_mass_kg, Date FROM data_coralsol_management"
    df = pd.read_sql(query, conn)
    df.columns = map(str.lower, df.columns)
    return df

@st.cache_data
def get_locality_data():
    query = "SELECT locality_id, coords_local, name, date FROM data_coralsol_locality"
    df = pd.read_sql(query, conn)
    df.columns = map(str.lower, df.columns)
    return df

@st.cache_data
def get_occ_data():
    query = "SELECT Occurrence_id, Spot_coords, Date, Depth, Superficie_photo FROM data_coralsol_occurrence WHERE Superficie_photo IS NOT NULL LIMIT 10"
    df = pd.read_sql(query, conn)
    df.columns = map(str.lower, df.columns)
    return df

@st.cache_data
def get_dafor_data():
    query = "SELECT Dafor_id, Locality_id, Dafor_coords, Date, Horizontal_visibility, Bathymetric_zone, Method, Dafor_value FROM data_coralsol_dafor"
    df = pd.read_sql(query, conn)
    df.columns = map(str.lower, df.columns)
    return df

# --- Base URL test DB ---
base_url = "http://coralsol-api.kinghost.net/api"

# --- Sidebar Widgets ---
def render_sidebar():
    with st.sidebar:
        today = datetime.date.today()
        tomorrow = today + datetime.timedelta(days=1)
        start_date = st.date_input('Data Inicial', datetime.date(2012, 1, 1))
        end_date = st.date_input('Data Final', tomorrow)
        if start_date < end_date:
            st.success(f'Start date: {start_date} \nEnd date: {end_date}')
        else:
            st.error('Error: Data Final deve ser após a Data inicial.')

        with st.expander("Indicadores", expanded=True):
            show_transects_suncoral = st.checkbox("Transectos com Coral-sol", value=True)

        with st.expander("Camadas", expanded=False):
            show_management = st.checkbox("Manejos", value=False)
            show_locality = st.checkbox("Localidades", value=False)
            show_occ = st.checkbox("Ocorrências", value=False)
            show_dafor = st.checkbox("Monitoramento", value=False)

    return start_date, end_date, show_management, show_locality

def create_map():
    if 'map' not in st.session_state or st.session_state.map is None:
        # Initialize the map
        m = folium.Map(
            location=[-27.281798, -48.366133],  # Default center
            zoom_start=13,  # Default zoom
            tiles="https://api.mapbox.com/v4/mapbox.satellite/{z}/{x}/{y}.png?access_token=pk.eyJ1Ijoic2lsdmVpcmF0Y2wiLCJhIjoiY202MTRrN3N5MGt3MDJqb2xhc3R0empqZCJ9.YfjBqq5HbnacUNw9Tyiaew",
            attr="Mapbox attribution",
            max_zoom=20,
            min_zoom=1
        )

        def render_map(start_date, end_date, show_management, show_locality):
            start_date_str = start_date.strftime('%d/%m/%Y')
            end_date_str = end_date.strftime('%d/%m/%Y')
            m = create_map()  # Get or create the map

            if show_management:
                if 'Manejos' in st.session_state.layers:
                    m._children.pop(st.session_state.layers['Manejos']._name, None)
                layer = MarkerCluster().add_to(m)
                st.session_state.layers['Manejos'] = layer

                data = get_management_data()
                data['date'] = pd.to_datetime(data['date'], format='%d/%m/%Y')  # Convert to datetime
                filtered_data = data[
                (data['date'] >= pd.to_datetime(start_date_str, format='%d/%m/%Y')) &
                (data['date'] <= pd.to_datetime(end_date_str, format='%d/%m/%Y'))
                ]
                for index, row in filtered_data.iterrows():
                    try:
                        coords_str = row['management_coords']
                        spot_coords = ast.literal_eval(coords_str)
                        if isinstance(spot_coords, list) and len(spot_coords) > 0:
                            lat, lon = spot_coords[0]
                            folium.Marker(
                                [lat, lon],
                                popup=f"Observer: {row['observer']}, Date: {row['date']}, Mass(kg): {row['managed_mass_kg']}",
                                tooltip=f"Management {row['management_id']}"
                            ).add_to(layer)
                    except Exception as e:
                        st.error(f"Error adding marker for Management ID {row['management_id']}: {e}")
            else:
                if 'Manejos' in st.session_state.layers:
                    m._children.pop(st.session_state.layers['Manejos']._name, None)
                    del st.session_state.layers['Manejos']

            # Display locality if selected
            if show_locality:
                if 'Localidades' in st.session_state.layers:
                    m._children.pop(st.session_state.layers['Localidades']._name, None)
                    layer = folium.FeatureGroup(name="Localidades").add_to(m)
                    st.session_state.layers['Localidades'] = layer

                data = get_locality_data()
                data['date'] = pd.to_datetime(data['date'], format='%d/%m/%Y')  # Convert to datetime
                filtered_data = data[
                    (data['date'] >= pd.to_datetime(start_date_str, format='%d/%m/%Y')) &
                    (data['date'] <= pd.to_datetime(end_date_str, format='%d/%m/%Y'))
                ]
                for index, row in filtered_data.iterrows():
                    try:
                        coords_str = row['coords_local']
                        locality_coords = ast.literal_eval(coords_str)
                        if isinstance(locality_coords, list) and len(locality_coords) > 0:
                            folium.PolyLine(
                                locality_coords,
                                popup=f"Locality: {row['name']}, Date: {row['date']}",
                                tooltip=f"Locality {row['locality_id']}"
                            ).add_to(layer)
                        else:
                            st.error(f"Invalid coordinates for Locality ID {row['locality_id']}: {locality_coords}")
                    except Exception as e:
                        st.error(f"Error adding line for Locality ID {row['locality_id']}: {e}")
            else:
                if 'Localidades' in st.session_state.layers:
                    m._children.pop(st.session_state.layers['Localidades']._name, None)
                    del st.session_state.layers['Localidades']

        Fullscreen().add_to(m)
        st.session_state.map = m  # Save the map in the session state
        st.session_state.layers = {}

    return st.session_state.map
        

def show_map():
    m = create_map()  # Get or create the map
    folium_static(m, width=1300, height=600) # Create responsieve map

show_map()

