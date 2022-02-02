import dataretrieval.nwis as nwis
from bs4 import BeautifulSoup
import requests as req
import csv

URL = 'https://waterdata.usgs.gov/nwis/annual?referred_module=sw&state_cd=tx&group_key=NONE&format=sitefile_output&sitefile_output_format=html_table&column_name=agency_cd&column_name=site_no&column_name=station_nm&list_of_search_criteria=state_cd%2Crealtime_parameter_selection'
page = req.get(URL)
soup = BeautifulSoup(page.content, 'lxml')
lists_data = soup.select('tr')
water_station_nums = []
water_station_coords = []
water_gage, water_discharge = [],[]
for data_tems in lists_data:
    try:
        site_num = data_tems.find('td', headers='site_no')
        water_station_nums.append(site_num.text)
        site = nwis.get_record(sites = site_num.text, service = 'site')
        water_station_coords.append([site.at[0,'dec_lat_va'],site.at[0,'dec_long_va']])
        link = site_num.find('a').get('href')
        nURL = 'https://waterdata.usgs.gov'+link
        stats_soup = BeautifulSoup(req.get(nURL).content, 'lxml')
        table = stats_soup.find(id='select_sites_data')
        table = table.find(id='stationTable')
        table = table.find('tbody')
        table = table.find_all(align = 'right')
        water_discharge.append(table[0].text)
        water_gage.append(table[1].text)
    except:
        continue
fields = ['Site Number', 'Latitude', 'Longitude', 'Gage Height (m)', 'Discharge (m^3/s)']
print(water_discharge)
records = []
for index in range(len(water_station_nums)):
    try:
        lis = [water_station_nums[index],water_station_coords[index][0],water_station_coords[index][1],water_gage[index],water_discharge[index]]
        if len(lis)==0:
            continue
        records.append(lis)
    except:
        continue
filename = 'water_stats_legit.csv'
with open(filename, 'w') as csvfile:
    csvwriter = csv.writer(csvfile)
    csvwriter.writerow(fields)
    csvwriter.writerows(records)
