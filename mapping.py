import plotly.graph_objects as go
import plotly.offline as py
import pandas as pd
import plotly.express as px
import json
from getting_sources import *


def write_geojson():
    coords = pd.read_csv('coords.csv')
    x_vals = []
    y_vals = []
    x_area_coords = []
    y_area_coords = []
    dy = (-93.51666667 + 106.63333333) / 198
    dx = (-25.83333333 + 36.50000000) / 198
    for item in range(len(coords)):
        x_vals.append(coords.at[item, 'x'])
        y_vals.append(coords.at[item, 'y'])
        x_area_coords.append([coords.at[item, 'x'] - dx, coords.at[item, 'x'] + dx])
        y_area_coords.append([coords.at[item, 'y'] - dy, coords.at[item, 'y'] + dy])
    x_map_coords = []
    for rec in y_area_coords:
        xvals = []
        xvals.append(rec[0])
        xvals.append(rec[1])
        xvals.append(rec[1])
        xvals.append(rec[0])
        # xvals.append(rec[0])
        x_map_coords.append(xvals)
    y_map_coords = []
    for rec in x_area_coords:
        xvals = []
        xvals.append(rec[0])
        xvals.append(rec[0])
        xvals.append(rec[1])
        xvals.append(rec[1])
        # xvals.append(rec[0])
        y_map_coords.append(xvals)
    features = []
    for ind in range(len(y_map_coords)):
        poly_coords_x = x_map_coords[ind]
        poly_coords_y = y_map_coords[ind]
        total_poly_coords = []
        for i in range(len(poly_coords_y)):
            total_poly_coords.append((poly_coords_x[i], poly_coords_y[i]))
        dict = {'type': 'Polygon',
                'coordinates': [total_poly_coords]}
        feature = {'type': 'Feature',
                   'geometry': dict,
                   'id': ind}
        features.append(feature)
    feature_collection = {"type": "FeatureCollection",
                          "features": features}
    with open("sample.json", "w") as outfile:
        json.dump(feature_collection, outfile)


def choropleth_map():
    energy_source = pd.read_csv('energy_source.csv')
    fig = px.choropleth_mapbox(energy_source, geojson=json.load(open('sample.json')), locations='index', color='val',
                               color_continuous_scale="Viridis",
                               range_color=(3, 9),
                               mapbox_style="carto-positron",
                               zoom=5, center={"lat": 30.0902, "lon": -95.7129},
                               opacity=0.75,
                               )
    fig.update_layout(margin={"r": 0, "t": 0, "l": 0, "b": 0})
    py.plot(fig)


# write_energy_source()
write_geojson()
choropleth_map()
