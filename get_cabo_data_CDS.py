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


years = [2017,2018]

# These can be a list that corresponds with the data from sites_lons.
sites_lats = [52.444409, 52.785157999999996, 52.50390600000001, 55.647873, 52.692037, 52.248940999999995, 52.920145, 52.602416000000005, 53.051435, 52.620169999999995, 52.78900600000001, 52.683324, 55.056394999999995, 52.795683999999994, 52.869663, 53.168902, 53.134710999999996, 52.707462, 53.038353, 53.193142, 53.201262, 52.261125, 52.644534, 50.940619, 51.130066, 52.644558999999994, 52.701641, 52.7576, 55.106747999999996, 55.367879, 55.716145, 53.106063, 52.483166000000004, 52.486424, 52.747772, 52.968049, 55.528180000000006, 51.101692, 52.370754999999996, 53.180388, 52.294191, 52.626987, 52.191712, 52.214073, 52.840334, 52.31219, 55.643912, 55.647873, 55.666228000000004, 52.88524399999999, 51.029427, 52.8087, 52.784317, 52.263047, 52.199606, 52.89673199999999, 52.259519, 52.240856, 52.788855000000005, 52.360356, 52.871451, 52.398359, 52.760369999999995, 55.729002, 50.834590000000006, 52.607890000000005, 52.267765999999995, 52.629505, 52.61963000000001, 55.660081999999996]

sites_lons = [0.055617207, -1.27299, 1.4123685, -2.4895717, 0.25544855, -0.2128895, -0.33888303, 0.092528846, -0.015903556, 1.1942812, 0.15160122, 0.25499948, -1.5144848, 0.14525589, -0.91690166, -0.98783069, -0.92872414, 0.96982843, -0.66469576, -0.34683597, -0.34767632, 0.93396214, 0.73522422, -2.8628644, -1.5980357, 0.29306459999999995, 0.25165128, -1.017735, -1.5505364, -1.6692243000000002, -2.0316805000000002, -0.89639368, -0.37452276, -0.38067667, 1.3640773000000002, -0.8199214, -2.6427417, -1.5840424, -0.46768366, -0.38373514, 0.99279343, -0.52465923, 1.1879963, 1.1318813, -0.73212415, 0.89895491, -2.2462642999999995, -2.4895717, -2.0035345, 0.69609928, -2.51346, 0.2851057, -0.33368087, -0.6150310999999999, 1.3914779, 0.93948829, -0.12898706, -0.49656229999999996, 0.31940855, 1.2433934, 0.031354667999999995, -0.37620061, 1.3221002, -2.2989933999999996, -2.12099, 0.03951, -1.4425413, 0.33114241, 0.9198799999999999, -2.5310338]


# Location string for the timezone conversions.
# Full list is here https://stackoverflow.com/questions/13866926/is-there-a-list-of-pytz-timezones
location_tz = 'Europe/London'

# what to call the data and results
run_handle = 'uk'

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

