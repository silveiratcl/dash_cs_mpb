import streamlit as st
import folium
from streamlit_folium import st_folium
import os
import numpy as np
import matplotlib.pyplot as plt
import rasterio
from rasterio.plot import show
from tempfile import NamedTemporaryFile

# Set page configuration
st.set_page_config(layout="wide", page_title="Interactive MAP Sun Coral Modelling", page_icon="🌍")

# App title
st.title("🌍 Interactive MAP Sun Coral Modelling")

# Create sidebar for controls
with st.sidebar:
    st.header("Map Controls")
    default_location = st.selectbox(
        "Default Location",
        ["Brazil", "London", "Tokyo", "Custom"],
        index=0
    )
    
    if default_location == "Custom":
        lat = st.number_input("Latitude", value=-38.7785)
        lon = st.number_input("Longitude", value=-15.9930)
    else:
        locations = {
            "Brazil": (-38.7785, -15.9930),
            "London": (51.5074, -0.1278),
            "Tokyo": (35.6762, 139.6503)
        }
        lat, lon = locations[default_location]
    
    zoom_level = st.slider("Zoom Level", 1, 18, 11)
    
    # Add checkboxes for layer control
    st.markdown("### Layer Visibility")
    show_satellite = st.checkbox("Show Satellite Imagery", value=True)
    show_elevation = st.checkbox("Show Elevation", value=False)

# Data directory and layer configuration
DATA_DIR = "data"
LAYERS = {
    "Satellite Imagery": {
        "path": os.path.join(DATA_DIR, "EMwmeanByROC_reclass.tif"),
        "colormap": "viridis",
        "opacity": 0.8,
        "active": show_satellite
    },
    "Elevation": {
        "path": os.path.join(DATA_DIR, "EMwmeanByROC_reclass.tif"),
        "colormap": "terrain",
        "opacity": 0.7,
        "active": show_elevation
    }
}

def process_geotiff(geotiff_path, colormap_name='viridis'):
    """Process GeoTIFF and return image path and bounds"""
    with rasterio.open(geotiff_path) as src:
        # Read the data
        data = src.read(1)
        
        # Handle no-data values
        if src.nodata is not None:
            data[data == src.nodata] = np.nan
        
        # Normalize data
        vmin, vmax = np.nanpercentile(data, [2, 98])
        norm_data = (data - vmin) / (vmax - vmin)
        
        # Apply colormap
        cmap = plt.get_cmap(colormap_name)
        colored_data = cmap(norm_data)
        
        # Create temporary file
        with NamedTemporaryFile(suffix='.png', delete=False) as tmp:
            plt.imsave(tmp.name, colored_data, format='png')
            temp_image_path = tmp.name
        
        # Get bounds
        bounds = [
            [src.bounds.bottom, src.bounds.left],
            [src.bounds.top, src.bounds.right]
        ]
        
        return temp_image_path, bounds

def create_map():
    """Create Folium map with selected layers"""
    m = folium.Map(location=[lat, lon], zoom_start=zoom_level)
    temp_files = []  # To keep track of temporary files
    
    for layer_name, layer_config in LAYERS.items():
        if layer_config["active"]:
            try:
                # Process GeoTIFF
                image_path, bounds = process_geotiff(
                    layer_config["path"],
                    layer_config["colormap"]
                )
                temp_files.append(image_path)  # Store for cleanup
                
                # Add overlay to map
                folium.raster_layers.ImageOverlay(
                    image=image_path,
                    bounds=bounds,
                    name=layer_name,
                    opacity=layer_config["opacity"],
                    interactive=True,
                    cross_origin=True
                ).add_to(m)
            except Exception as e:
                st.error(f"Failed to load {layer_name}: {str(e)}")
                st.error(f"File path attempted: {layer_config['path']}")
    
    # Add layer control
    folium.LayerControl().add_to(m)
    return m, temp_files

# Display the map
st.subheader("Interactive Map")
map_obj, temp_files = create_map()
map_output = st_folium(
    map_obj,
    width=1200,
    height=700,
    returned_objects=["last_active_drawing", "bounds"]
)

# Clean up temporary files
for temp_file in temp_files:
    try:
        os.unlink(temp_file)
    except:
        pass

# Display feature information when clicked
if map_output.get("last_active_drawing"):
    st.subheader("Selected Feature Properties")
    feature_props = map_output["last_active_drawing"]["properties"]
    st.json(feature_props)

# Debugging information
with st.expander("Debug Information"):
    st.write("Current working directory:", os.getcwd())
    if os.path.exists(DATA_DIR):
        st.write("Data directory contents:", os.listdir(DATA_DIR))
    else:
        st.error(f"Data directory '{DATA_DIR}' does not exist")