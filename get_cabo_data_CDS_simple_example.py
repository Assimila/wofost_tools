import cdsapi
from calendar import monthrange
import os
import numpy as np
if os.path.isfile('era2cabo.py') == False:
    raise ValueError('Cant see the conversion tool era2cabo.py. Put this file in the current working environment.')
from era2cabo import do_conversion

##########################################################

# A module to create a CABO file for wofost for multiple years.


#-------------------User Inputs--------------------------#

# years to run the data though
years = [2017,2018]


# These can be a list that corresponds with the data from sites_lons.
sites_lats = [52.604297, 55.643042]

sites_lons = [-1.01374, -2.2016472]


# A list that corresponds with sites lons. This names the cabo file prefix.
# OR leave run_handle_list as an empty list and use the run handle to call everything something similar.
# each cabo file will be numbered and share the same prefix.
run_handle_list = []

# use this to call the era5 data something.
run_handle = 'uk_test_farms'
if len(run_handle_list) == 0:
    run_handle_list = ['%s_s%02d'%(run_handle,i) for i in range(len(sites_lats))]
    
# Location string for the timezone conversions.
# Full list is here https://stackoverflow.com/questions/13866926/is-there-a-list-of-pytz-timezones
location_tz = 'Europe/London'

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
malo = max(sites_lats)

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

