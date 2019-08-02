import cdsapi
from calendar import monthrange
import os
import numpy as np
if os.path.isfile('era2cabo.py') == False:
    raise ValueError('Cant see the conversion tool era2cabo.py. Put this file in the current working environment.')
from era2cabo import do_conversion_land

##########################################################

# A module to create a CABO file for wofost for one year.


#-------------------User Inputs--------------------------#

# ------  Download parameters -------

# years to run the data though
years = [2016,2017,2018]

# These can be a list that corresponds with the data from sites_lons.
sites_lats =  [52.604296999999995,	 55.643042,	 55.09454399999999,	 55.367422999999995,	 52.435302,	 52.824537,	 52.624841,	 52.705562,	 52.585159999999995,	 52.373762,	 50.66232,	 52.691182999999995,	 55.650254000000004,	 52.70091899999999,	 52.512905,	 52.78634399999999,	 55.510891,	 52.284872,	 52.618849,	 52.816548,	 50.942536,	 52.245769,	 52.287672,	 52.205664,	 52.297084999999996,	 52.234389,	 52.631139000000005,	 52.906365,	 52.92260400000001,	 52.787932999999995,	 52.395140000000005,	 53.064522,	 53.189452,	 55.66184200000001,	 52.81675500000001,	 52.285928000000006,	 52.835381999999996,	 55.660081999999996,	 52.90961,	 52.22552,	 52.247011,	 52.712723,	 53.099222,	 52.484033,	 52.49905,	 52.378096,	 55.059173,	 52.770244999999996,	 55.642451,	 52.868109999999994,	 52.675812,	 52.728351,	 52.80983199999999,	 55.607424,	 53.099222,	 50.870394,	 53.093231,	 52.444409,	 52.785157999999996,	 52.50390600000001,	 55.647873,	 52.692037,	 52.248940999999995,	 52.920145,	 52.602416000000005,	 53.051435,	 52.620169999999995,	 52.78900600000001,	 52.683324,	 55.056394999999995,	 52.795683999999994,	 52.869663,	 53.168902,	 53.134710999999996,	 52.707462,	 53.038353,	 53.193142,	 53.201262,	 52.261125,	 52.644534,	 50.940619,	 51.130066,	 52.644558999999994,	 52.701641,	 52.7576,	 55.106747999999996,	 55.367879,	 55.716145,	 53.106063,	 52.483166000000004,	 52.486424,	 52.747772,	 52.968049,	 55.528180000000006,	 51.101692,	 52.370754999999996,	 53.180388,	 52.294191,	 52.626987,	 52.191712,	 52.214073,	 52.840334,	 52.31219,	 55.643912,	 55.647873,	 55.666228000000004,	 52.88524399999999,	 51.029427,	 52.8087,	 52.784317,	 52.263047,	 52.199606,	 52.89673199999999,	 52.259519,	 52.240856,	 52.788855000000005,	 52.360356,	 52.871451,	 52.398359,	 52.760369999999995,	 55.729002,	 50.834590000000006,	 52.607890000000005,	 52.267765999999995,	 52.629505,	 52.61963000000001,	 55.660081999999996]


sites_lons = [-1.0137399999999999,	 -2.2016472,	 -1.555092,	 -1.6700643,	 -0.02836817,	 -0.78178267,	 0.33810452,	 0.25348152,	 0.11435148,	 -0.89901716,	 -2.4895089,	 0.81258254,	 -2.4984842,	 0.96287033,	 1.0453037,	 1.0947833,	 -1.8957846,	 0.9925023000000001,	 1.1698035,	 1.3200034,	 -2.8577901000000003,	 -0.60455419,	 -0.46028875,	 1.3912809,	 0.89261392,	 -0.23532358,	 -0.51448661,	 -0.7987294,	 0.51970627,	 -0.30334976,	 -0.37747987,	 -1.2105743999999998,	 -0.34329585,	 -2.0162977,	 1.319663,	 1.0004925,	 -0.72143149,	 -2.5310338,	 0.9459536000000001,	 1.0170648000000002,	 0.89039425,	 0.15361923,	 -0.9758754999999999,	 -0.37874689,	 1.4030023999999999,	 0.35482841,	 -1.5193513,	 -1.3200763,	 -2.239948,	 0.025329801000000002,	 0.25761543,	 0.13469158,	 0.13853343,	 -2.0577506999999997,	 -0.9758754999999999,	 -2.0793892,	 -0.83280709,	 0.055617207,	 -1.27299,	 1.4123685,	 -2.4895717,	 0.25544855,	 -0.2128895,	 -0.33888303,	 0.092528846,	 -0.015903556,	 1.1942812,	 0.15160122,	 0.25499948,	 -1.5144848,	 0.14525589,	 -0.91690166,	 -0.98783069,	 -0.92872414,	 0.96982843,	 -0.66469576,	 -0.34683597,	 -0.34767632,	 0.93396214,	 0.73522422,	 -2.8628644,	 -1.5980357,	 0.29306459999999995,	 0.25165128,	 -1.017735,	 -1.5505364,	 -1.6692243000000002,	 -2.0316805000000002,	 -0.89639368,	 -0.37452276,	 -0.38067667,	 1.3640773000000002,	 -0.8199214,	 -2.6427417,	 -1.5840424,	 -0.46768366,	 -0.38373514,	 0.99279343,	 -0.52465923,	 1.1879963,	 1.1318813,	 -0.73212415,	 0.89895491,	 -2.2462642999999995,	 -2.4895717,	 -2.0035345,	 0.69609928,	 -2.51346,	 0.2851057,	 -0.33368087,	 -0.6150310999999999,	 1.3914779,	 0.93948829,	 -0.12898706,	 -0.49656229999999996,	 0.31940855,	 1.2433934,	 0.031354667999999995,	 -0.37620061,	 1.3221002,	 -2.2989933999999996,	 -2.12099,	 0.03951,	 -1.4425413,	 0.33114241,	 0.9198799999999999,	 -2.5310338]


# A list that corresponds with sites lons. This names the cabo file prefix.
# OR leave run_handle_list as an empty list and use the run handle to call everything something similar.
run_handle_list = ['F01508_CF00500',	 'F01464_CF00502',	 'F01470_CF00503',	 'F01576_CF00504',	 'F01539_CF00510',	 'F01560_CF00511',	 'F01465_CF00516',	 'F01579_CF00524',	 'F01525_CF00525',	 'F01493_CF00527',	 'F01490_CF00528',	 'F01494_CF00534',	 'F01313_CF00540',	 'F01557_CF00542',	 'F01559_CF00547',	 'F01472_CF00548',	 'F01466_CF00553',	 'F01451_CF00555',	 'F01304_CF00558',	 'F01340_CF00562',	 'F01584_CF00566',	 'F01500_CF00574',	 'F01615_CF00575',	 'F00534_CF00577BASF',	 'F01602_CF00578BASF',	 'F01603_CF00589BASF',	 'F01581_CF00590BASF',	 'F01369_CF00592BASF',	 'F01598_CF00593BASF',	 'F01582_CF00594BASF',	 'F01288_CF00595BASF',	 'F01583_CF00599BASF',	 'F01631_CF00601BASF',	 'F01619_CF00603BASF',	 'F01340_CF00605BASF',	 'F01451_CF00610BASF',	 'F01560_CF00611BASF',	 'F01313_CF00613BASF',	 'F01346_CF00616BASF',	 'F01618_CF00624',	 'F01629_CF00635',	 'F01283_CF00637',	 'F01467_CF00639',	 'F01640_CF00642',	 'F01481_CF00643',	 'F01477_CF00647',	 'F01475_CF00652',	 'F01483_CF00658',	 'F01312_CF00660',	 'F01653_CF00661',	 'F01407_CF00675',	 'F01283_CF00679',	 'F01283_CF00680',	 'F01664_CF00685',	 'F01467_CF00691',	 'M0004_CF00709',	 'F01503_CF00710',	 'F01690_CF00800',	 'F01483_CF00804',	 'F01481_CF00805',	 'F01313_CF00811',	 'F01407_CF00814AFS',	 'F01731_CF00815',	 'F01572_CF00817',	 'F01525_CF00826',	 'F01283_CF00827FS',	 'F01304_CF00831',	 'F01283_CF00833',	 'F01407_CF00814BFS',	 'F01475_CF00835',	 'F01283_CF00844FS',	 'F01740_CF00846',	 'F01741_CF00847',	 'F01467_CF00856',	 'F01557_CF00858',	 'F01631_CF00862A',	 'F01631_CF00862B',	 'F01631_CF00862C',	 'F01323_CF00868',	 'F01753_CF00870',	 'F01584_CF00876T',	 'F01757_CF00877',	 'F01579_CF00881FS',	 'F01579_CF00882',	 'F01761_CF00884',	 'F01473_CF00886',	 'F01576_CF00887',	 'F01464_CF00888FS',	 'F01503_CF00889',	 'F01640_CF00891',	 'F01640_CF00892FS',	 'F01040_CF00895',	 'F00503_CF00898',	 'F01600_CF00899',	 'F01759_CF00901',	 'F01569_CF00907',	 'F01631_CF00909FS',	 'F01323_CF00910FS',	 'F01581_CF00911FS',	 'F01321_CF00912FS',	 'F01510_CF00914FS',	 'F01560_CF00916FS',	 'F01602_CF00923FS',	 'F01312_CF00932',	 'F01313_CF00939FS',	 'F01619_CF00945FS',	 'F01598_CF00948FS',	 'F01596_CF00949FS',	 'F01600_CF00950FS',	 'F01582_CF00952FS',	 'F01500_CF00953FS',	 'F00534_CF00958FS',	 'F01346_CF00959FS',	 'F01462_CF00968',	 'F00502_CF00971',	 'F01343_CF00975FS',	 'F01767_CF00982',	 'F01319_CF00983T',	 'F01288_CF01002FS',	 'F01769_CF01006',	 'F01608_CF01007FS',	 'F01820_CF01011',	 'F01555_CF01018',	 'F01400_CF01023FS',	 'F01465_CF01025',	 'F00509_CF01031FS',	 'F01313_CF01039FS']


# run_handle_list = []

# Location string for the timezone conversions.
# Full list is here https://stackoverflow.com/questions/13866926/is-there-a-list-of-pytz-timezones
location_tz = 'Europe/London'

# use this to call 
run_handle = 'uk_3year_land9km'
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
                        ['2m_temperature',
                        'surface_solar_radiation_downwards',
                        'total_precipitation']]

        for n0,v in enumerate(variable_list):

            if os.path.isfile(file_handles[n0]%(year)) == False:

                c = cdsapi.Client()
                c.retrieve("reanalysis-era5-land",
                {
                "variable": v,
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

    do_conversion_land(data_file,rain_rad_file,sites_lats,sites_lons,location_tz,run_handle_list)

