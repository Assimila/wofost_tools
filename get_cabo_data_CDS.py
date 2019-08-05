import cdsapi
from calendar import monthrange
import os
import numpy as np
if os.path.isfile('era2cabo.py') == False:
    raise ValueError('Cant see the conversion tool era2cabo.py. Put this file in the current working environment.')
from era2cabo import do_conversion

##########################################################

# A module to create a CABO file for wofost for one year.


#-------------------User Inputs--------------------------#

# ------  Download parameters -------

# years to run the data though
years = [2016]

# These can be a list that corresponds with the data from sites_lons.
sites_lats = [52.604297,	 55.643042,	 55.09454399999999,	 55.367423,	 52.435302,	 52.824537,	 52.624841,	 52.705562,	 52.58516,	 52.373762,	 50.66232,	 52.691183,	 55.650254,	 52.70091899999999,	 52.512905,	 52.78634399999999,	 55.510891,	 52.284872,	 52.618849,	 52.816548,	 50.942536,	 52.245769,	 52.287672,	 52.205664,	 52.297085,	 52.234389,	 52.63113900000001,	 52.906365,	 52.92260400000001,	 52.787933,	 52.39514000000001,	 53.064522,	 53.189452,	 55.66184200000001,	 52.81675500000001,	 52.28592800000001,	 52.835382,	 55.660082,	 52.90961,	 52.22552,	 52.247011,	 52.712723,	 53.099222,	 52.484033,	 52.49905,	 52.378096,	 55.059173,	 52.770245,	 55.642451,	 52.86811,	 52.675812,	 52.728351,	 52.80983199999999,	 55.607424,	 53.099222,	 50.870394,	 53.093231]


sites_lons = [-1.01374,	 -2.2016472,	 -1.555092,	 -1.6700643,	 -0.02836817,	 -0.78178267,	 0.33810452,	 0.25348152,	 0.11435148,	 -0.89901716,	 -2.4895089,	 0.81258254,	 -2.4984842,	 0.96287033,	 1.0453037,	 1.0947833,	 -1.8957846,	 0.9925023,	 1.1698035,	 1.3200034,	 -2.8577901000000003,	 -0.60455419,	 -0.46028875,	 1.3912809,	 0.89261392,	 -0.23532358,	 -0.51448661,	 -0.7987294,	 0.51970627,	 -0.30334976,	 -0.37747987,	 -1.2105743999999998,	 -0.34329585,	 -2.0162977,	 1.319663,	 1.0004925,	 -0.72143149,	 -2.5310338,	 0.9459536,	 1.0170648000000002,	 0.89039425,	 0.15361923,	 -0.9758755,	 -0.37874689,	 1.4030024,	 0.35482841,	 -1.5193513,	 -1.3200763,	 -2.239948,	 0.025329801,	 0.25761543,	 0.13469158,	 0.13853343,	 -2.0577507,	 -0.9758755,	 -2.0793892,	 -0.83280709]

# A list that corresponds with sites lons. This names the cabo file prefix.
# OR leave run_handle_list as an empty list and use the run handle to call everything something similar.
run_handle_list = ['F01508_CF00500',	 'F01464_CF00502',	 'F01470_CF00503',	 'F01576_CF00504',	 'F01539_CF00510',	 'F01560_CF00511',	 'F01465_CF00516',	 'F01579_CF00524',	 'F01525_CF00525',	 'F01493_CF00527',	 'F01490_CF00528',	 'F01494_CF00534',	 'F01313_CF00540',	 'F01557_CF00542',	 'F01559_CF00547',	 'F01472_CF00548',	 'F01466_CF00553',	 'F01451_CF00555',	 'F01304_CF00558',	 'F01340_CF00562',	 'F01584_CF00566',	 'F01500_CF00574',	 'F01615_CF00575',	 'F00534_CF00577BASF',	 'F01602_CF00578BASF',	 'F01603_CF00589BASF',	 'F01581_CF00590BASF',	 'F01369_CF00592BASF',	 'F01598_CF00593BASF',	 'F01582_CF00594BASF',	 'F01288_CF00595BASF',	 'F01583_CF00599BASF',	 'F01631_CF00601BASF',	 'F01619_CF00603BASF',	 'F01340_CF00605BASF',	 'F01451_CF00610BASF',	 'F01560_CF00611BASF',	 'F01313_CF00613BASF',	 'F01346_CF00616BASF',	 'F01618_CF00624',	 'F01629_CF00635',	 'F01283_CF00637',	 'F01467_CF00639',	 'F01640_CF00642',	 'F01481_CF00643',	 'F01477_CF00647',	 'F01475_CF00652',	 'F01483_CF00658',	 'F01312_CF00660',	 'F01653_CF00661',	 'F01407_CF00675',	 'F01283_CF00679',	 'F01283_CF00680',	 'F01664_CF00685',	 'F01467_CF00691',	 'M0004_CF00709',	 'F01503_CF00710']

# run_handle_list = []

# Location string for the timezone conversions.
# Full list is here https://stackoverflow.com/questions/13866926/is-there-a-list-of-pytz-timezones
location_tz = 'Europe/London'

# use this to call 
run_handle = 'uk_allfarms'
if len(run_handle_list) == 0:
    run_handle_list = ['%s_s%02d'%(run_handle,i) for i in range(len(sites_lats))]

# If you already have the era data downloaded somewhere.

# Leave None if you want to download era data.
# If you want, put the data file with wind in first, 
# then the radiation/precip file.
manual_data_point = None

##########################################################
# Checks:
        
if location_tz == None:
    raise ValueError('No TZ info given.')
    
if type(run_handle) != str:
    raise ValueError('run_handle must be a string')
    
if len(sites_lons) != len(sites_lats):
    raise ValueError('site lat and lon lengths dont add up')
##########################################################


def find_closest(element = None, search_array = None):
    """
    Function to find the element in the search array that is closest to the element.
    Returns a tuple, containing the index of the closest array position to the element,
    and also the actual value closest to it.
    """
    import numpy as np
    
    long_element = np.repeat(element,len(search_array))
    difs = abs(long_element - np.array(search_array))
    
    index = np.where((difs == min(difs)) == True)
    return(index,np.array(search_array)[index])

mila = min(sites_lats)
milo = min(sites_lons)

mala = max(sites_lats)
malo = max(sites_lons)

bl_lon = find_closest(milo, [int(milo) + (np.sign(milo)*i) for i in [0,0.25,0.5,0.75,1]])[1][0]
bl_lat = find_closest(mila, [int(mila) + (np.sign(mila)*i) for i in [0,0.25,0.5,0.75,1]])[1][0]

tr_lon = find_closest(malo, [int(malo) + (np.sign(malo)*i) for i in [0,0.25,0.5,0.75,1]])[1][0]
tr_lat = find_closest(mala, [int(mala) + (np.sign(mala)*i) for i in [0,0.25,0.5,0.75,1]])[1][0]

for year in years:

    if manual_data_point == None:

        file_handles = [run_handle+'_era5_cabo_instantaneous_%s.nc',
                        run_handle+'_era5_cabo_accumulated_%s.nc']

        variable_list = [['10m_u_component_of_wind','10m_v_component_of_wind',"2m_dewpoint_temperature"],
                        ['maximum_2m_temperature_since_previous_post_processing',
                        'minimum_2m_temperature_since_previous_post_processing',
                        'surface_solar_radiation_downwards',
                        'total_precipitation']]

        for n0,v in enumerate(variable_list):

            if os.path.isfile(file_handles[n0]%(year)) == False:

                c = cdsapi.Client()
                c.retrieve("reanalysis-era5-single-levels",
                {
                "variable": v,
                "product_type": "reanalysis",
                "year": "%s"%year,
                "time": ["%02d:00"%j for j in range(24)],
                "area": [bl_lat,bl_lon,tr_lat,tr_lon],
                "format": "netcdf"
                },
                file_handles[n0]%(year))

    else:
        print ('Using existing data %s'%manual_data_point)

    if manual_data_point == None:
        data_file = file_handles[0]%(year)
        rain_rad_file = file_handles[1]%(year)
    else:
        data_file = manual_data_point[0]
        rain_rad_file = manual_data_point[1]

    do_conversion(data_file,rain_rad_file,sites_lats,sites_lons,location_tz,run_handle_list)

