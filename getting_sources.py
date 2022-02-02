import csv
import sys
import numpy as np
import pandas as pd
import urllib, json, requests
from geopy.geocoders import Nominatim
from math import radians, cos, sin, asin, sqrt
from scipy.spatial import distance
import plotly.graph_objects as go
import plotly.offline as py

pd.set_option("display.max_rows", None, "display.max_columns", None)


# method that returns lists of evenly spaced latitude and longitude points on texas
def evenly_spaced_points(num):
    lat = np.linspace(25.83333333, 36.50000000, num)
    long = np.linspace(-93.51666667, -106.63333333, num)
    usablelat = []
    usablelong = []
    for latitude in lat:
        for longitude in long:
            geolocator = Nominatim(user_agent="test")
            try:
                loc = geolocator.reverse(str(latitude) + ', ' + str(longitude))
                dict = loc.raw['address']
                if dict.get('state', '') == 'Texas':
                    usablelat.append(latitude)
                    usablelong.append(longitude)
            finally:
                continue
    return usablelat, usablelong


# method that returns the carbon dioxide (in kg) produced by construction of a set turbines
def get_wind_carbon(turbines):
    ret = []
    carbon_output = 25326
    for turbine in turbines:
        ret.append(turbine * carbon_output)
    return ret


def minimize_wind(winds_vals, energy_consump):
    turbines = []
    for ind in range(len(energy_consump)):
        turbine = 0
        if winds_vals[ind] == 0:
            turbines.append(0)
            continue
        while get_wind_watthour(winds_vals[ind], turbine) < energy_consump[ind] * 1.5:
            turbine = turbine + .00005
        turbines.append(turbine)
    return turbines


# method that returns the watt hours produced by a set of wind speeds and their corresponding turbine counts
def get_wind_watthour(winds, turbines):
    wind_shear = .25
    efficiency_factor = 40
    radius = 82
    avg_air_density = 1.225
    speed = (8 ** wind_shear) * winds
    val = 24 * turbines * (np.pi / 2) * efficiency_factor * (radius ** 2) * (speed ** 3) * avg_air_density
    return val


# method that returns the watt hours produced by a set of solar radiations and their corresponding solar panel areas
def get_solar_watthour(irr, area):
    avg_yield = 27
    performance_ratio = .75
    val = irr * avg_yield * area * performance_ratio * 1000
    return val


def minimize_solar(irr_vals, energy_consump):
    areas = []
    for ind in range(len(energy_consump)):
        area = 0
        if irr_vals[ind] == 0:
            areas.append(0)
            continue
        while get_solar_watthour(irr_vals[ind], area) < energy_consump[ind] * 1.5:
            area = area + .005
        areas.append(area)
    return areas


# method that returns the carbon dioxide (in kg) produced construction of a set of areas of solar panels
def get_solar_carbon(area):
    ret = []
    carbon_output = 354.78
    for temp in area:
        ret.append(temp * carbon_output)
    return ret


def get_water_watthour(gage, discharge, distance, turbines):
    efficiency_factor = .9
    water_density = 997
    g = 9.806
    head = 300
    if gage / 2.0 < head:
        head = head / 2.0
    val = 24 * water_density * g * efficiency_factor * head * discharge * turbines
    val = val - val * (.06 ** (distance / 1000))
    return val


def minimize_water(gage_vals, discharge_vals, distance_vals, energy_consump):
    turbines = []
    for ind in range(len(energy_consump)):
        turbine = 0
        if gage_vals[ind] == 0 or discharge_vals[ind] == 0:
            turbines.append(0)
            continue
        while get_water_watthour(gage_vals[ind], discharge_vals[ind], distance_vals[ind], turbine) < energy_consump[
            ind] * 1.5:
            turbine = turbine + .005
        turbines.append(turbine)
    return turbines


# method that returns the carbon dioxide (in kg) produced by a set of flowrates and heads a
def get_water_carbon(gage_vals, discharge_vals, distance_vals, turbines):
    ret = []
    carbon_output = 18.5 / 10000000
    for turbine in range(len(turbines)):
        ret.append(get_water_watthour(gage_vals[turbine], discharge_vals[turbine], distance_vals[turbine],
                                      turbines[turbine]) * carbon_output)
    return ret


def get_coal_carbon(energy_consump):
    ret = []
    carbon_rate = .001002439
    for energy in energy_consump:
        ret.append(carbon_rate * energy * 1.5)
    return ret

#kg/watthour
def get_gas_carbon(energy_consump):
    ret = []
    carbon_rate = 0.0004127691
    for energy in energy_consump:
        ret.append(carbon_rate * energy * 1.5)
    return ret


# method that returns the wind speed and irradiance vals at a given list of latitude and longitudes
def get_wind_irradiance_vals(x, y):
    windspeeds = []
    irradiance = []
    for index in range(len(x)):
        print(str(index) + 'wind_irradiance')
        lat, lon, year = x[index], y[index], 2010
        api_key = 'ZoC2l2MbVxmtVElbmWILmDoa2MDlCAHJsKavpdBV'
        attributes = 'ghi,wind_speed'
        leap_year = 'false'
        interval = '60'
        utc = 'false'
        your_name = 'tharun'
        reason_for_use = 'beta+testing'
        your_affiliation = 'my+institution'
        your_email = 'tharun.tiruppali@gmail.com'
        mailing_list = 'false'
        url = 'https://developer.nrel.gov/api/solar/nsrdb_psm3_download.csv?wkt=POINT({lon}%20{lat})&names={' \
              'year}&leap_day={leap}&interval={interval}&utc={utc}&full_name={name}&email={email}&affiliation={' \
              'affiliation}&mailing_list={mailing_list}&reason={reason}&api_key={api}&attributes={attr}'.format(
            year=year, lat=lat, lon=lon, leap=leap_year, interval=interval, utc=utc, name=your_name, email=your_email,
            mailing_list=mailing_list, affiliation=your_affiliation, reason=reason_for_use, api=api_key,
            attr=attributes)
        info = pd.read_csv(url)
        if len(info) == 0:
            irradiance.append(0)
            windspeeds.append(0)
            continue
        sum_radiance = 0
        sum_wind = 0
        for i in range(len(info.index) - 2):
            sum_radiance = sum_radiance + int(info.at[i + 2, 'Latitude'])
            sum_wind = sum_wind + float(info.at[i + 2, 'Longitude'])
        irradiance.append(sum_radiance)
        avg_wind = sum_wind / (len(info.index) - 2)
        windspeeds.append(avg_wind)
    return windspeeds, irradiance


def get_water_vals(x, y):
    water_csv = pd.read_csv('water_stats_legit.csv')
    gage_vals = []
    discharge_vals = []
    distance_vals = []
    for ind in range(len(x)):
        dist = sys.float_info.max
        closest_coords = -1
        closest_index = -1
        for record in range(1, len(water_csv)):
            b = (water_csv.at[record, 'Latitude'], water_csv.at[record, 'Longitude'])
            temp = distance.euclidean((x[ind], y[ind]), b)
            if (temp < dist):
                dist = temp
                closest_index = record
                closest_coords = b
        gage_vals.append(water_csv.at[closest_index, 'Gage Height (m)'])
        discharge_vals.append(water_csv.at[closest_index, 'Discharge (m^3/s)'])
        distance_vals.append(get_distance(x[ind], closest_coords[0], y[ind], closest_coords[1]))
    return gage_vals, discharge_vals, distance_vals


def get_energy_consumption(x, y, area):
    daily_energy_consump_per_capita = 145949392.946 / 365
    daily_energy_consump = []
    pop_data = pd.read_csv('2019_txpopest_county.csv')
    for ind in range(len(x)):
        print(str(ind) + 'energy_consump')
        url2 = urllib.request.urlopen(
            "https://geo.fcc.gov/api/census/area?lat=" + str(x[ind]) + "&lon=" + str(y[ind]) + "&format=json")
        data = json.loads(url2.read().decode())
        if len(data['results']) == 0:
            daily_energy_consump.append(0)
            continue
        county = data['results'][0]['county_name']
        for i in range(len(pop_data)):
            if pop_data.at[i, 'county'] == county:
                pop_dens = float(str(pop_data.at[i, 'jan1_2020_pop_est']).replace(',', ''))
                county_area = pd.read_csv('county_area.csv')
                for area2 in range(len(county_area)):
                    if county_area.at[area2, 'Name'] == county:
                        pop_dens = float(pop_dens) / float(county_area.at[area2, 'Area'].replace(',', ''))
                daily_energy_consump.append(pop_dens * area * daily_energy_consump_per_capita)
    return daily_energy_consump


def get_distance(lat1, lat2, lon1, lon2):
    lon1 = radians(lon1)
    lon2 = radians(lon2)
    lat1 = radians(lat1)
    lat2 = radians(lat2)
    dlon = lon2 - lon1
    dlat = lat2 - lat1
    a = sin(dlat / 2) ** 2 + cos(lat1) * cos(lat2) * sin(dlon / 2) ** 2
    c = 2 * asin(sqrt(a))
    r = 6371
    return c * r


def write_coords(x, y):
    filename = 'coords.csv'
    records = []
    records.append(['x', 'y'])
    for ind in range(len(x)):
        row = [x[ind], y[ind]]
        records.append(row)
    with open(filename, 'w') as csvfile:
        csvwriter = csv.writer(csvfile)
        for row in records:
            csvwriter.writerow(row)


def write_vals(file_name, vals):
    records = []
    records.append(['val'])
    for ind in range(len(vals)):
        row = vals[ind]
        records.append([row])
    with open(file_name, 'w') as csvfile:
        csvwriter = csv.writer(csvfile)
        for row in records:
            csvwriter.writerow(row)

def write_energy_source():
    # x, y = evenly_spaced_points(num=100)
    # write_coords(x,y)
    coords = pd.read_csv('coords.csv')
    x = []
    y = []
    for i in range(len(coords)):
        x.append(coords.at[i, 'x'])
        y.append(coords.at[i, 'y'])
    # write_coords(x,y)
    dy = (-93.51666667 + 106.63333333) / 198
    dx = (-25.83333333 + 36.50000000) / 198
    area = 2 * dx * 2 * dy
    # energy_consumption = get_energy_consumption(x=x, y=y, area=float(area))
    # print(energy_consumption)
    # write_vals('energy_consump.csv',energy_consumption)
    consump_csv = pd.read_csv('energy_consump.csv')
    energy_consumption = []
    for i in range(len(consump_csv)):
        energy_consumption.append(consump_csv.at[i, 'val'])

    # winds_vals, irradiance_vals = get_wind_irradiance_vals(x, y)
    # gage_vals, discharge_vals, distance_vals = get_water_vals(x, y)
    #
    # write_vals('gage.csv',gage_vals)
    # write_vals('discharge.csv',discharge_vals)
    # write_vals('wind_speed.csv', winds_vals)
    # write_vals('irradiance.csv', irradiance_vals)
    # write_vals('distance_vals.csv',distance_vals)

    winds_csv = pd.read_csv('wind_speed.csv')
    winds_vals = []
    for i in range(len(coords)):
        winds_vals.append(winds_csv.at[i, 'val'])

    gage_csv = pd.read_csv('gage.csv')
    gage_vals = []
    for i in range(len(coords)):
        gage_vals.append(gage_csv.at[i, 'val'])

    distance_csv = pd.read_csv('distance_vals.csv')
    distance_vals = []
    for i in range(len(coords)):
        distance_vals.append(distance_csv.at[i, 'val'])

    discharge_csv = pd.read_csv('discharge.csv')
    discharge_vals = []
    for i in range(len(coords)):
        discharge_vals.append(discharge_csv.at[i, 'val'])

    irradiance_csv = pd.read_csv('irradiance.csv')
    irradiance_vals = []
    for i in range(len(coords)):
        irradiance_vals.append(irradiance_csv.at[i, 'val'])

    solar_area = minimize_solar(irr_vals=irradiance_vals, energy_consump=energy_consumption)

    wind_turbines = minimize_wind(winds_vals=winds_vals, energy_consump=energy_consumption)

    water_turbines = minimize_water(gage_vals=gage_vals, discharge_vals=discharge_vals, distance_vals=distance_vals,
                                    energy_consump=energy_consumption)

    solar_carbon = get_solar_carbon(solar_area)
    wind_carbon = get_wind_carbon(wind_turbines)
    water_carbon = get_water_carbon(gage_vals, discharge_vals, distance_vals, water_turbines)
    coal_carbon = get_coal_carbon(energy_consump=energy_consumption)
    gas_carbon = get_gas_carbon(energy_consump=energy_consumption)

    # figure out which region is what source
    x_area_coords = []
    y_area_coords = []
    for i in range(len(water_carbon)):
        x_temp = [x[i] - dx, x[i] + dx]
        y_temp = [y[i] - dy, y[i] + dy]
        carbon = [wind_carbon[i], water_carbon[i], solar_carbon[i], coal_carbon[i], gas_carbon[i]]
        words = ['wind', 'water', 'solar', 'coal', 'gas']
        min = sys.float_info.max
        string_representation = ''
        for item in range(len(carbon)):
            if min > carbon[item]:
                min = carbon[item]
                string_representation = words[item]
        x_temp.append(string_representation)
        y_temp.append(string_representation)
        x_area_coords.append(x_temp)
        y_area_coords.append(y_temp)
    file_name = 'energy_source.csv'
    records = []
    records.append(['index', 'val'])
    for row in range(len(x_area_coords)):
        records.append([row, x_area_coords[row][2]])
    with open(file_name, 'w') as csvfile:
        csvwriter = csv.writer(csvfile)
        for row in records:
            csvwriter.writerow(row)
    #
    # x_map_coords = []
    # for rec in y_area_coords:
    #     x_map_coords.append(rec[0])
    #     x_map_coords.append(rec[1])
    #     x_map_coords.append(rec[1])
    #     x_map_coords.append(rec[0])
    #     x_map_coords.append(rec[0])
    #     x_map_coords.append(None)
    # y_map_coords = []
    # for rec in x_area_coords:
    #     y_map_coords.append(rec[0])
    #     y_map_coords.append(rec[0])
    #     y_map_coords.append(rec[1])
    #     y_map_coords.append(rec[1])
    #     y_map_coords.append(rec[0])
    #     y_map_coords.append(None)
    #
    # fig = go.Figure(go.Scattermapbox(
    #     fill="toself",
    #     lon=x_map_coords,
    #     lat=y_map_coords,
    #     marker={'size': 10, 'color': "orange"}))
    #
    # fig.update_layout(
    #     mapbox={
    #         'style': "stamen-terrain",
    #         'center': {'lon': -73, 'lat': 46},
    #         'zoom': 5},
    #     showlegend=False)
    #
    # py.plot(fig)
