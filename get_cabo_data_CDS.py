import cdsapi
from calendar import monthrange
import os
if os.path.isfile('era2cabo.py') == False:
    raise ValueError('Cant see the conversion tool era2cabo.py. Put this file in the current working environment.')
from era2cabo import do_conversion

##########################################################

# A module to create a CABO file for wofost for one year.


#-------------------User Inputs--------------------------#

# ------  Download parameters -------


years = [2006]

# These can be a list that corresponds with the data from sites_lons.
sites_lats = [35.135916]
sites_lons = [113.763737]


# Location string for the timezone conversions.
# Full list is here https://stackoverflow.com/questions/13866926/is-there-a-list-of-pytz-timezones
location_tz = 'Asia/Shanghai'

# what to call the data and results
run_handle = 'henan'

# If you already have the era data downloaded somewhere.

# Leave None if you want to download era data.

# If you want, put the data file with wind in first, 
# then the radiation/precip file.
manual_data_point = None

##########################################################
# Checks:
        
if location_tz == None:
    raise ValueError('No TZ info given.')
    
if run_handle == None:
    raise ValueError('Must provide a run handle')
    
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


bl_lon = find_closest(min(sites_lons), [int(min(sites_lons)) + i for i in [0,0.25,0.5,0.75,1]])[1][0]
bl_lat = find_closest(min(sites_lats), [int(min(sites_lats)) + i for i in [0,0.25,0.5,0.75,1]])[1][0]

tr_lon = find_closest(max(sites_lons), [int(max(sites_lons)) + i for i in [0,0.25,0.5,0.75,1]])[1][0]
tr_lat = find_closest(max(sites_lats), [int(max(sites_lats)) + i for i in [0,0.25,0.5,0.75,1]])[1][0]

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

    for n,i in enumerate(sites_lats):
        start = '%s0101'%year
        end = '%s1230'%year
        lat = i
        lon = sites_lons[n]
        elev = 50.
        stno = n
        file_num = "s%02d"%(n+1)
        target_dir = run_handle

        if manual_data_point == None:
            data_file = file_handles[0]%(year)
            rain_rad_file = file_handles[1]%(year)
        else:
            data_file = manual_data_point[0]
            rain_rad_file = manual_data_point[1]

        do_conversion(data_file, rain_rad_file, i, sites_lons[n],location_tz, stno, elev, file_num,run_handle)

