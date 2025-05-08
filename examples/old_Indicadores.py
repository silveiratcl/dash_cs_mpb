import streamlit as st
from sqlalchemy import create_engine, text
from urllib.parse import quote_plus

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib import lines
from matplotlib import patches
from matplotlib.patheffects import withStroke
import plotly.express as px

import folium
from streamlit_folium import st_folium
import ast
import datetime
from folium.plugins import MarkerCluster, Fullscreen
import requests
from branca.element import Template, MacroElement

# --- Page Configuration ---
st.set_page_config(page_title="Indicadores", page_icon="🗺️", layout="wide")
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

        indicator = st.radio("Indicadores", ["Transectos com Coral-sol", "Esforço de Monitoramento", "Detecções por ano", "Detecções vs. Massa Manejada"])
        show_transects_suncoral = indicator == "Transectos com Coral-sol"
        show_effort = indicator == "Esforço de Monitoramento"
        show_year = indicator == "Detecções por ano"
        show_year_managed_mass = indicator == "Detecções vs. Massa Manejada"

    return start_date, end_date, show_transects_suncoral, show_effort, show_year, show_year_managed_mass ###### 

# --- Legend Template ---

# Create the legend template as an HTML element
legend_transect = """
{% macro html(this, kwargs) %}
<div id='maplegend' class='maplegend' 
    style='position: absolute; z-index: 9999; background-color: rgba(255, 255, 255, 0.5);
     border-radius: 6px; padding: 10px; font-size: 10.5px; right: 20px; top: 20px;'>     
<div class='legend-scale'>
  <ul class='legend-labels'>
    <li><span style='background: red; opacity: 0.75;'></span>ALTO (>30)</li>
    <li><span style='background: orange; opacity: 0.75;'></span>MODERADO (15-30)</li>
    <li><span style='background: yellow; opacity: 0.75;'></span> BAIXO (5-15) </li>
    <li><span style='background: green; opacity: 0.75;'></span> AUSENTE </li>
  </ul>
</div>
</div> 
<style type='text/css'>
  .maplegend .legend-scale ul {margin: 0; padding: 0; color: #0f0f0f;}
  .maplegend .legend-scale ul li {list-style: none; line-height: 18px; margin-bottom: 1.5px;}
  .maplegend ul.legend-labels li span {float: left; height: 16px; width: 16px; margin-right: 4.5px;}
</style>
{% endmacro %}
"""

legend_effort = """
{% macro html(this, kwargs) %}
<div id='maplegend' class='maplegend' 
    style='position: absolute; z-index: 9999; background-color: rgba(255, 255, 255, 0.5);
     border-radius: 6px; padding: 10px; font-size: 10.5px; right: 20px; top: 20px;'>     
<div class='legend-scale'>
  <ul class='legend-labels'>
    <li><span style='background: red; opacity: 0.75;'></span>ALTO (>300 min.)</li>
    <li><span style='background: orange; opacity: 0.75;'></span>MODERADO (150-300 min.)</li>
    <li><span style='background: yellow; opacity: 0.75;'></span> BAIXO (50-150 min.) </li>
    <li><span style='background: green; opacity: 0.75;'></span> MUITO BAIXO (0-50 min.) </li>
  </ul>
</div>
</div> 
<style type='text/css'>
  .maplegend .legend-scale ul {margin: 0; padding: 0; color: #0f0f0f;}
  .maplegend .legend-scale ul li {list-style: none; line-height: 18px; margin-bottom: 1.5px;}
  .maplegend ul.legend-labels li span {float: left; height: 16px; width: 16px; margin-right: 4.5px;}
</style>
{% endmacro %}
"""


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
def render_map(m, start_date, end_date, show_transects_suncoral, show_effort):
    # Convert the start and end dates
    start_date_str = start_date.strftime('%Y-%m-%d')
    end_date_str = end_date.strftime('%Y-%m-%d')
    
    merged_data = pd.DataFrame()  # Initialize an empty DataFrame for merged_data
    merged_data_effort = pd.DataFrame()  # Initialize an empty DataFrame for merged_data_effort
   
    if show_transects_suncoral:
        layer = folium.FeatureGroup(name="Transectos com Coral-sol").add_to(m)

        locality_data = get_locality_data()
        locality_data['date'] = pd.to_datetime(locality_data['date'], errors='coerce', dayfirst=True)

        filtered_locality_data = locality_data[
            (locality_data['date'] >= pd.to_datetime(start_date_str, errors='coerce')) &
            (locality_data['date'] <= pd.to_datetime(end_date_str, errors='coerce'))
        ]

        dafor_data = get_dafor_data()
        dafor_data['date'] = pd.to_datetime(dafor_data['date'], errors='coerce', dayfirst=True)

        # Convert `dafor_value` to a list of numbers, handling errors
        dafor_data['dafor_value'] = dafor_data['dafor_value'].apply(lambda x: 
            [pd.to_numeric(i, errors='coerce') for i in str(x).split(',')]
        )

        dafor_data = dafor_data.explode('dafor_value')

        # Convert `dafor_value` column again to numeric
        dafor_data['dafor_value'] = pd.to_numeric(dafor_data['dafor_value'], errors='coerce')

        # Filter out NaN values after conversion
        filtered_dafor_data = dafor_data[
            (dafor_data['date'] >= pd.to_datetime(start_date_str, errors='coerce')) &
            (dafor_data['date'] <= pd.to_datetime(end_date_str, errors='coerce')) &
            (dafor_data['dafor_value'].notna())  # Remove NaNs
        ]

        dafor_counts = filtered_dafor_data[filtered_dafor_data['dafor_value'] > 0].groupby('locality_id').size().reset_index(name='dafor_count')

        # Merge filtered_locality_data with dafor_counts to include 'name' and other locality data
        merged_data = filtered_locality_data.merge(dafor_counts, on='locality_id', how='left').fillna({'dafor_count': 0})

        for _, row in merged_data.iterrows():
            try:
                coords_str = row['coords_local']
                try:
                    coords_local = ast.literal_eval(coords_str)
                except (ValueError, SyntaxError) as e:
                    st.error(f"Error parsing coordinates for Locality ID {row['locality_id']}: {e}")
                    continue

                if isinstance(coords_local, list) and len(coords_local) > 0:
                    dafor_count = row['dafor_count']
                    if dafor_count > 30:
                        color = 'red'
                    elif dafor_count > 15 < 29:
                        color = 'orange'
                    
                    elif dafor_count > 5 < 14:
                        color = 'yellow'    
                    else:
                        color = 'green'

                    folium.PolyLine(
                        coords_local,
                        color=color,
                        popup=(
                            f"<b>Locality:</b> {row['locality_id']}<br>"
                            f"<b>Name:</b> {row['name']}<br>"
                            f"<b>Date:</b> {row['date']}<br>"
                            f"<b>Dafor Count:</b> {dafor_count}"
                        ),
                        tooltip=f"Locality {row['locality_id']}"
                    ).add_to(layer)
                else:
                    st.error(f"Invalid coordinates for Locality ID {row['locality_id']}: {coords_local}")
            except Exception as e:
                st.error(f"Error adding line for Locality ID {row['locality_id']}: {e}")
        # Add the legend to the map
            macro = MacroElement()
            macro._template = Template(legend_transect)
            m.get_root().add_child(macro)
        

    if show_effort:
        layer = folium.FeatureGroup(name="Esforço de Monitoramento").add_to(m)

        locality_data = get_locality_data()
        locality_data['date'] = pd.to_datetime(locality_data['date'], errors='coerce', dayfirst=True)

        filtered_locality_data = locality_data[
            (locality_data['date'] >= pd.to_datetime(start_date_str, errors='coerce')) &
            (locality_data['date'] <= pd.to_datetime(end_date_str, errors='coerce'))
        ]

        dafor_data = get_dafor_data()
        dafor_data['date'] = pd.to_datetime(dafor_data['date'], errors='coerce', dayfirst=True)

        # Convert `dafor_value` to a list of numbers, handling errors
        dafor_data['dafor_value'] = dafor_data['dafor_value'].apply(lambda x: 
            [pd.to_numeric(i, errors='coerce') for i in str(x).split(',')]
        )

        dafor_data = dafor_data.explode('dafor_value')

        # Convert `dafor_value` column again to numeric
        dafor_data['dafor_value'] = pd.to_numeric(dafor_data['dafor_value'], errors='coerce')

        # Filter out NaN values after conversion
        filtered_dafor_data = dafor_data[
            (dafor_data['date'] >= pd.to_datetime(start_date_str, errors='coerce')) &
            (dafor_data['date'] <= pd.to_datetime(end_date_str, errors='coerce')) &
            (dafor_data['dafor_value'].notna())  # Remove NaNs
        ]

        dafor_counts_effort = filtered_dafor_data[filtered_dafor_data['dafor_value'] >= 0].groupby('locality_id').size().reset_index(name='dafor_count')

        # Merge filtered_locality_data with dafor_counts_effort to include 'name' and other locality data
        merged_data_effort = filtered_locality_data.merge(dafor_counts_effort, on='locality_id', how='left').fillna({'dafor_count': 0})

        for _, row in merged_data_effort.iterrows():
            try:
                coords_str = row['coords_local']
                try:
                    coords_local = ast.literal_eval(coords_str)
                except (ValueError, SyntaxError) as e:
                    st.error(f"Error parsing coordinates for Locality ID {row['locality_id']}: {e}")
                    continue

                if isinstance(coords_local, list) and len(coords_local) > 0:
                    dafor_count = row['dafor_count']
                    if dafor_count > 10:
                        color = 'red'
                    elif dafor_count > 5:
                        color = 'orange'
                    else:
                        color = 'green'

                    folium.PolyLine(
                        coords_local,
                        color=color,
                        popup=(
                            f"<b>Locality:</b> {row['locality_id']}<br>"
                            f"<b>Name:</b> {row['name']}<br>"
                            f"<b>Date:</b> {row['date']}<br>"
                            f"<b>Dafor Count:</b> {dafor_count}"
                        ),
                        tooltip=f"Locality {row['locality_id']}"
                    ).add_to(layer)
                else:
                    st.error(f"Invalid coordinates for Locality ID {row['locality_id']}: {coords_local}")
            except Exception as e:
                st.error(f"Error adding line for Locality ID {row['locality_id']}: {e}")

             # Add the legend to the map
            macro = MacroElement()
            macro._template = Template(legend_effort)
            m.get_root().add_child(macro)    


    return m, merged_data, merged_data_effort  # Return the map and merged_data

import plotly.express as px

def render_chart(start_date, end_date, merged_data, show_year, show_year_managed_mass):
    if show_year:
        # Convert the start and end dates
        start_date_str = start_date.strftime('%Y-%m-%d')
        end_date_str = end_date.strftime('%Y-%m-%d')

        # Fetch the data
        locality_data = get_locality_data()
        dafor_data = get_dafor_data()

        # Convert 'date' columns to datetime
        locality_data['date'] = pd.to_datetime(locality_data['date'], errors='coerce', dayfirst=True)
        dafor_data['date'] = pd.to_datetime(dafor_data['date'], errors='coerce', dayfirst=True)

        # Process dafor_value - split into individual values and explode
        dafor_data['dafor_value'] = dafor_data['dafor_value'].apply(
            lambda x: [pd.to_numeric(i, errors='coerce') for i in str(x).split(',')]
        )
        dafor_data = dafor_data.explode('dafor_value')
        dafor_data['dafor_value'] = pd.to_numeric(dafor_data['dafor_value'], errors='coerce')

        # Filter data by date range and remove NaNs
        filtered_dafor_data = dafor_data[
            (dafor_data['date'] >= pd.to_datetime(start_date_str, errors='coerce')) &
            (dafor_data['date'] <= pd.to_datetime(end_date_str, errors='coerce')) &
            (dafor_data['dafor_value'].notna())
        ]

        # Merge with locality data
        merged_data = locality_data.merge(
            filtered_dafor_data, 
            left_on='locality_id', 
            right_on='locality_id', 
            how='inner'
        )

        # Extract year from date
        merged_data['year'] = merged_data['date_y'].dt.year

        # Calculate effort (count of values) and detections (values > 0)
        effort_data = merged_data.groupby(['name', 'year']).agg(
            total_effort=('dafor_value', 'count'),  # Each value = 1 minute of effort
            total_detections=('dafor_value', lambda x: (x > 0).sum())  # Count of values > 0
        ).reset_index()

        # Calculate detections per 60 minutes of effort
        effort_data['detections_per_60min'] = (effort_data['total_detections'] / 
                                             effort_data['total_effort']) * 60

        # Create Plotly line chart
        fig = px.line(
            effort_data,
            x='year',
            y='detections_per_60min',
            color='name',
            title='Detecções por 60 minutos de esforço por Ano',
            labels={
                'year': 'Ano',
                'detections_per_60min': 'Detecções por 60 minutos',
                'name': 'Localidade'
            },
            markers=True
        )

        # Customize layout
        fig.update_layout(
            xaxis_title='Ano',
            yaxis_title='Detecções por 60 minutos de esforço',
            legend_title='Localidade',
            hovermode='x unified',
            yaxis=dict(tickformat=".1f")  # Show 1 decimal place
        )

        # Add hover template
        fig.update_traces(
            hovertemplate=(
                "<b>%{x}</b><br>"
                "Localidade: %{fullData.name}<br>"
                "Detecções: %{customdata[0]}<br>"
                "Esforço: %{customdata[1]} min<br>"
                "Taxa: %{y:.1f} det/60min"
            ),
            customdata=effort_data[['total_detections', 'total_effort']].values
        )

        # Display the chart
        st.plotly_chart(fig)

        # Show data table
        st.write("Dados de Esforço e Detecções:")
        st.dataframe(effort_data)

    if show_year_managed_mass:
        # Convert the start and end dates
        start_date_str = start_date.strftime('%Y-%m-%d')
        end_date_str = end_date.strftime('%Y-%m-%d')

        # Fetch the data
        locality_data = get_locality_data()
        dafor_data = get_dafor_data()

        # Convert 'date' columns to datetime
        locality_data['date'] = pd.to_datetime(locality_data['date'], errors='coerce', dayfirst=True)
        dafor_data['date'] = pd.to_datetime(dafor_data['date'], errors='coerce', dayfirst=True)

        # Process dafor_value - split into individual values and explode
        dafor_data['dafor_value'] = dafor_data['dafor_value'].apply(
            lambda x: [pd.to_numeric(i, errors='coerce') for i in str(x).split(',')]
        )
        dafor_data = dafor_data.explode('dafor_value')
        dafor_data['dafor_value'] = pd.to_numeric(dafor_data['dafor_value'], errors='coerce')

        # Filter data by date range and remove NaNs
        filtered_dafor_data = dafor_data[
            (dafor_data['date'] >= pd.to_datetime(start_date_str, errors='coerce')) &
            (dafor_data['date'] <= pd.to_datetime(end_date_str, errors='coerce')) &
            (dafor_data['dafor_value'].notna())
        ]

        # Merge with locality data
        merged_data = locality_data.merge(
            filtered_dafor_data, 
            left_on='locality_id', 
            right_on='locality_id', 
            how='inner'
        )

        # Extract year from date
        merged_data['year'] = merged_data['date_y'].dt.year

        # Calculate effort (count of values) and detections (values > 0)
        effort_data = merged_data.groupby(['name', 'year']).agg(
            total_effort=('dafor_value', 'count'),  # Each value = 1 minute of effort
            total_detections=('dafor_value', lambda x: (x > 0).sum())  # Count of values > 0
        ).reset_index()

        # Calculate detections per 60 minutes of effort
        effort_data['detections_per_60min'] = (effort_data['total_detections'] / 
                                             effort_data['total_effort']) * 60

        # Create Plotly line chart
        fig = px.line(
            effort_data,
            x='year',
            y='detections_per_60min',
            color='name',
            title='Detecções por 60 minutos de esforço por Ano',
            labels={
                'year': 'Ano',
                'detections_per_60min': 'Detecções por 60 minutos',
                'name': 'Localidade'
            },
            markers=True
        )

        # Customize layout
        fig.update_layout(
            xaxis_title='Ano',
            yaxis_title='Detecções por 60 minutos de esforço',
            legend_title='Localidade',
            hovermode='x unified',
            yaxis=dict(tickformat=".1f")  # Show 1 decimal place
        )

        # Add hover template
        fig.update_traces(
            hovertemplate=(
                "<b>%{x}</b><br>"
                "Localidade: %{fullData.name}<br>"
                "Detecções: %{customdata[0]}<br>"
                "Esforço: %{customdata[1]} min<br>"
                "Taxa: %{y:.1f} det/60min"
            ),
            customdata=effort_data[['total_detections', 'total_effort']].values
        )

        # Display the chart
        st.plotly_chart(fig)

        # Show data table
        st.write("Dados de Esforço e Detecções:")
        st.dataframe(effort_data)


    return merged_data, show_year, show_year_managed_mass

# --- Main Logic ---
def main():
    # Render the sidebar and get the selected options
    start_date, end_date, show_transects_suncoral, show_effort, show_year, show_year_managed_mass  = render_sidebar()

    # If "Detecções por ano" is selected, render only the chart
    if show_year:
        # Call the render_chart function
        merged_data, show_year, _ = render_chart(start_date, end_date, None, show_year, False)
        return  # Exit the function early to skip the map and other components
    
    if show_year_managed_mass:
        # Call the render_chart function
        merged_data, _, show_year_managed_mass = render_chart(start_date, end_date, None, False, show_year_managed_mass)
        return  # Exit the function early to skip the map and other components

    # If "Detecções por ano" is not selected, render the map and other components
    # Load or create the map
    m = get_map()
    m, merged_data, merged_data_effort = render_map(m, start_date, end_date, show_transects_suncoral, show_effort)

    # Capture the previous zoom & center
    prev_zoom = st.session_state.map_zoom
    prev_center = st.session_state.map_center

    # Temporary storage for zoom & center
    if "temp_map_zoom" not in st.session_state:
        st.session_state.temp_map_zoom = st.session_state.map_zoom
    if "temp_map_center" not in st.session_state:
        st.session_state.temp_map_center = st.session_state.map_center

    # Create two columns
    col1, col2 = st.columns([2, 1], gap="medium")

    with col1:
        # Display the map but DO NOT update zoom yet
        st.write("### Indicadores do Monitoramento")
        st_data = st_folium(
            m,
            width="100%",
            height=700,
            returned_objects=["center", "zoom"],
            key=st.session_state["map_key"],  # Forces reloading when changed
        )

        # Only store zoom & center TEMPORARILY
        if st_data:
            if "center" in st_data and st_data["center"]:
                st.session_state.temp_map_center = [st_data["center"]["lat"], st_data["center"]["lng"]]
            if "zoom" in st_data and st_data["zoom"]:
                st.session_state.temp_map_zoom = st_data["zoom"]

        # Add a button to apply zoom & center updates
        if st.button("Update Map View"):
            if (
                st.session_state.temp_map_zoom != prev_zoom or
                st.session_state.temp_map_center != prev_center
            ):
                st.session_state.map_zoom = st.session_state.temp_map_zoom
                st.session_state.map_center = st.session_state.temp_map_center
                st.session_state["map_key"] += 1  # Forces full re-render
                st.write(f"Debug: Applied map updates, new key = {st.session_state['map_key']}")

    with col2:
        if show_transects_suncoral:
            # Sort merged_data by dafor_count in descending order and select 'name' and 'dafor_count' columns
            sorted_merged_data = merged_data[['name', 'dafor_count']].sort_values(by='dafor_count', ascending=False).rename(columns={'name': 'Localidade', 'dafor_count': 'N. Detecções'})
            # Add 'id' column name
            sorted_merged_data.index.name = 'id'

            # Display the sorted table
            st.write("### Número de Transectos com Coral-sol por Localidade")
            st.dataframe(sorted_merged_data)

        if show_effort:
            # Sort merged_data_effort by dafor_count in descending order and select 'name' and 'dafor_count' columns
            sorted_merged_data_effort = merged_data_effort[['name', 'dafor_count']].sort_values(by='dafor_count', ascending=False).rename(columns={'name': 'Localidade', 'dafor_count': 'Esforço (minutos)'})
            # Add 'id' column name
            sorted_merged_data_effort.index.name = 'id'

            # Display the sorted table
            st.write("### Esforço de Monitoramento")
            st.dataframe(sorted_merged_data_effort)

    # # Now add your conditional charts AFTER both column blocks
    # if show_transects_suncoral:
    #     st.write("### Gráfico de Transectos com Coral-sol")
    #     # Extract the data from the DataFrame
    #     sorted_merged_data = sorted_merged_data.sort_values(by='N. Detecções', ascending=True)
    #     names = sorted_merged_data['Localidade'].tolist()  # Convert the 'Localidade' column to a list
    #     counts = sorted_merged_data['N. Detecções'].tolist()  # Convert the 'N. Detecções' column to a list
    
    #     # The positions for the bars
    #     y = [i * 0.9 for i in range(len(names))]

    #     # The colors
    #     BLUE = "#076fa2"
    #     RED = "#E3120B"
    #     BLACK = "#202020"
    #     GREY = "#a2a2a2"

    #     # Create the plot
    #     fig, ax = plt.subplots(figsize=(12, 7))
    #     ax.barh(y, counts, height=0.55, align="edge", color=BLUE)

    #     # Set labels and title
    #     ax.xaxis.set_ticks([i * 5 for i in range(0, 12)])
    #     ax.xaxis.set_ticklabels([i * 5 for i in range(0, 12)], size=16, fontfamily="Econ Sans Cnd", fontweight=100)
    #     ax.xaxis.set_tick_params(labelbottom=False, labeltop=True, length=0)

    #     ax.set_xlim((0, 55.5)) # max in sorted merged data
    #     ax.set_ylim((0, len(names) * 0.9 - 0.2))

    #     # Set whether axis ticks and gridlines are above or below most artists.
    #     ax.set_axisbelow(True)
    #     ax.grid(axis = "x", color="#A8BAC4", lw=1.2)
    #     ax.spines["right"].set_visible(False)
    #     ax.spines["top"].set_visible(False)
    #     ax.spines["bottom"].set_visible(False)
    #     ax.spines["left"].set_lw(1.5)
    #     # This capstyle determines the lines don't go beyond the limit we specified
    #     # see: https://matplotlib.org/stable/api/_enums_api.html?highlight=capstyle#matplotlib._enums.CapStyle
    #     ax.spines["left"].set_capstyle("butt")

    #     # Hide y labels
    #     ax.yaxis.set_visible(False)

    #     PAD = 0.3
    #     for name, count, y_pos in zip(names, counts, y):
    #         x = 0
    #         color = "white"
    #         path_effects = None
    #         if count < 8:
    #             x = count
    #             color = BLUE    
    #             path_effects=[withStroke(linewidth=6, foreground="white")]
    
    #         ax.text(
    #         x + PAD, y_pos + 0.5 / 2, name, 
    #         color=color, fontfamily="Econ Sans Cnd", fontsize=18, va="center",
    #         path_effects=path_effects
    #     ) 

    #     # Display the plot in Streamlit
    #     st.pyplot(fig)

    #     # Clear the figure to avoid memory leaks
    #     plt.close(fig)

    # if show_effort: ## pending 
    #     st.write("### Gráfico de Esforço de Monitoramento")
    #     effort_data = pd.DataFrame(np.random.randn(20, 3), columns=["x", "y", "z"])
    #     st.line_chart(effort_data)


if __name__ == "__main__":
    main()