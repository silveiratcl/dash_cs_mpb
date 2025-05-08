import streamlit as st
from sqlalchemy import create_engine
import pandas as pd
import folium
from streamlit_folium import st_folium
import ast
import datetime
from folium.plugins import MarkerCluster, Fullscreen

# --- Page Configuration ---
st.set_page_config(page_title="Mapa", page_icon="🗺️", layout="wide")
st.logo('./assets/logo_horiz.png', size="large")

# --- Initialize Connection ---
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
    except Exception as e:
        st.error(f"Database connection error: {e}")
        raise

conn = init_connection()

# --- Data Fetching Functions ---
@st.cache_data
def get_management_data():
    query = "SELECT management_id, management_coords, observer, managed_mass_kg, date FROM data_coralsol_management"
    df = pd.read_sql(query, conn)
    df.columns = map(str.lower, df.columns)
    return df

# --- Sidebar Widgets ---
def render_sidebar():
    with st.sidebar:
        start_date = st.date_input('Data Inicial', datetime.date(2012, 1, 1))
        end_date = st.date_input('Data Final', datetime.date.today() + datetime.timedelta(days=1))

        with st.expander("Camadas", expanded=True):
            # ✅ Ensure session state is initialized BEFORE calling st.checkbox
            if "show_management" not in st.session_state:
                st.session_state.show_management = False  # Default state

            # ✅ Now, create the checkbox without modifying session state directly
            show_management = st.checkbox("Manejos", value=st.session_state.show_management, key="show_management")

    return start_date, end_date, show_management


# --- Persist Map State ---
def get_map():
    """Get or create a folium map with persisted state."""
    if "map_center" not in st.session_state:
        st.session_state.map_center = [-27.281798, -48.366133]
    if "map_zoom" not in st.session_state:
        st.session_state.map_zoom = 13

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
def render_map(m, start_date, end_date, show_management):  # ✅ Now correctly accepts 4 arguments
    start_date_str = start_date.strftime('%Y-%m-%d')
    end_date_str = end_date.strftime('%Y-%m-%d')

    # Add management layer dynamically
    if show_management:  # ✅ Use the correct parameter
        data = get_management_data()
        data['date'] = pd.to_datetime(data['date']).dt.strftime('%Y-%m-%d')
        filtered_data = data[(data['date'] >= start_date_str) & (data['date'] <= end_date_str)]

        marker_cluster = MarkerCluster().add_to(m)
        for _, row in filtered_data.iterrows():
            try:
                coords_str = row['management_coords']
                spot_coords = ast.literal_eval(coords_str)
                if isinstance(spot_coords, list) and len(spot_coords) > 0:
                    lat, lon = spot_coords[0]
                    folium.Marker(
                        [lat, lon],
                        popup=f"Observer: {row['observer']}, Date: {row['date']}, Mass(kg): {row['managed_mass_kg']}",
                        tooltip=f"Management {row['management_id']}"
                    ).add_to(marker_cluster)
            except Exception as e:
                st.error(f"Error adding marker: {e}")

    return m

# --- Main Logic ---
def main():
    start_date, end_date, show_management = render_sidebar()  # ✅ Expecting three values

    # Load or create the map
    m = get_map()
    m = render_map(m, start_date, end_date, show_management)  # Pass show_management

    # Display the map and capture new zoom/center if changed
    st_data = st_folium(m, width="100%", height=600, returned_objects=["center", "zoom"])

    # Update zoom and center only if changed
    if st_data:
        if "center" in st_data and st_data["center"]:
            st.session_state.map_center = [st_data["center"]["lat"], st_data["center"]["lng"]]
        if "zoom" in st_data and st_data["zoom"]:
            st.session_state.map_zoom = st_data["zoom"]

if __name__ == "__main__":
    main()
