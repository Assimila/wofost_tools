def do_conversion(data_file = None, rain_rad_file = None, in_lat = None, in_lon = None,
                 locality = None, station_number = None, elevation = None,
                 file_number = None, file_handle = None):
    
    import numpy as np
    import datetime as dt
    import netCDF4 as nc
    from netCDF4 import num2date
    import pytz
    
    def daily_stat(in_time = None, in_data = None, operation = None):
        fd = in_time[0]
        fd = fd - dt.timedelta(hours=fd.hour)
        ld = in_time[-1]
        ld = ld - dt.timedelta(hours=ld.hour)
        # find difference in last and first day
        dif = (ld -fd).days
        ret = []
        # loop through and get daily data
        for i in range(dif+1):
            # find the index between each daya
            within = np.where((in_time >= fd+dt.timedelta(hours=24*i)) & (in_time < fd+dt.timedelta(hours=(24*i) + 24)))[0]
            # index out the data
            sec = in_data[within]
            ret.append(operation(sec))
        # return daily statistic
        return np.array(ret)

    def calc_wspeed(u, v):
        wspd = np.sqrt(u*u + v*v)
        return wspd

    def find_closest(element = None, search_array = None):
        long_element = np.repeat(element,len(search_array))
        difs = abs(long_element - np.array(search_array))

        index = np.where((difs == min(difs)) == True)
        return(index,np.array(search_array)[index])

    def calc_es(tempc):
        #using equations from NOAA NWS page at http://www.srh.noaa.gov/epz/?n=wxcalc
        #es = 6.11*10**((7.5*tempc)/(237.3+tempc)) #calculate saturation vapour pressure 
        #es = 6.112*np.exp(17.67*(temp-273.15)/(temp-29.65))  # temp in K      
        # from Rogers and Yau : A Short Course in Cloud Physics 
        es = 6.112*np.exp(17.67*tempc/(tempc+243.5))
        return es
    
    def find_closest_pixel(l):
        int_ = int(l)
        dec = np.array([0.,0.25,0.5,0.75])
        closest_decimal = dec[np.argmin(abs(dec - (l-int_)))]
        return closest_decimal+int_

    # open the data process time
    inst_data  = nc.Dataset(data_file)
    inst_time_utc = nc.num2date(inst_data.variables['time'][:], inst_data.variables['time'].units)

    inst_time_local = np.array([pytz.timezone('utc').localize(i).astimezone(
            pytz.timezone(locality)) for i in inst_time_utc])

    accum_data = nc.Dataset(rain_rad_file)
    accum_time_utc = nc.num2date(accum_data.variables['time'][:], accum_data.variables['time'].units)

    accum_time_local = np.array([pytz.timezone('utc').localize(i).astimezone(
            pytz.timezone(locality)) for i in accum_time_utc])

    # get the years in the data
    years = np.unique([i.year for i in accum_time_local])

    # find the indexes of the site in the data
    era_lat = find_closest_pixel(in_lat)
    era_lon = find_closest_pixel(in_lon)
    
    
    site_lat_ind = find_closest(era_lat,inst_data.variables['latitude'])[0][0][0]
    site_lon_ind = find_closest(era_lon,inst_data.variables['longitude'])[0][0][0]

    print (site_lon_ind)
    print (site_lat_ind)
    
    
    # give the header of the CABO file
    header = '*---------------------------------------------------------------------------*\n*Station name: '+str(in_lat)+' '+str(in_lon)+'\n* Column  Daily value\n* 1       station number\n* 2       year\n* 3       day\n* 4       irradiation                   (kJ m-2 d-1)\n* 5       minimum temperature           (degrees Celsius)\n* 6       maximum temperature           (degrees Celsius)\n* 7       early morning vapour pressure (kPa)\n* 8       mean wind speed (height: 2 m) (m s-1)\n* 9       precipitation                 (mm d-1)\n*\n* '+'era5'+'\n* Created by era2cabo, by Alex \n* File created: ' + str(dt.datetime.today()) +'\n** WCCFORMAT=2\n*---------------------------------------------------------------------------*\n'+'%s'%in_lon+'  '+'%s'%in_lat+'  '+'{:>2.6f}'.format(elevation)+'  -0.180000  -0.550000 \n'

    # loop through each year and make a cabo file for that year
    for y in years:

        # find a slice of time that fits in the year
        year_slice = np.where((inst_time_local >= pytz.timezone(locality).
                           localize(dt.datetime(y,1,1,0,0))) & 
                          (inst_time_local < pytz.timezone(locality).
                           localize(dt.datetime(y+1,1,1,0,0))))[0]

        # slice the time
        year_time = inst_time_local[year_slice]
        
        if len(year_time) < 24:
            print ('Data from file %s covers less than 24 hours for year %s. Annual CABO file ommited for that year.'%(data_file,y))
            continue

        # find the DoYs of the data
        doys = np.unique([(i - pytz.timezone(locality).
                           localize(dt.datetime(y,1,1))).days for i in year_time])

        # set up an empty repo for the data
        year_data = np.zeros([6,len(doys)])
    
        # establish indexes, offsets and scaler for each variable...
        a_inds = [0,1,2,5]
        a_operators = [np.sum,np.min,np.max,np.sum]   

        a_offsets = [0,-273.15,-273.15,0]
        a_scalers = [0.001,1,1,1000]
        
        # and loop through them for the accumulated data
        for n,i in enumerate(['ssrd','mn2t','mx2t', 'tp']):
            
            # get the data
            param_hourly = accum_data.variables[i][year_slice,site_lat_ind,site_lon_ind]

            # compress into daily statistics
            param_daily = daily_stat(year_time,param_hourly,a_operators[n])  
            
            # and add it to the data array
            year_data[a_inds[n],:] = (param_daily*a_scalers[n]) + a_offsets[n]

        # do the same for the instantaneos data
        i_inds = [3,4]
        i_operators = [np.mean,np.mean]   

        i_offsets = [-273.15,0]
        i_scalers = [0.1,1]

        for n,i in enumerate(['d2m',['u10','v10']]):

            if type(i) == str:

                param_hourly = calc_es(inst_data.variables[i][year_slice,site_lat_ind,site_lon_ind] + i_offsets[n])*i_scalers[n]

                param_daily = daily_stat(year_time,param_hourly,i_operators[n])  

                year_data[i_inds[n],:] = param_daily

            else:

                param_hourly = []

                for j in i:

                    param_hourly.append(inst_data.variables[j][year_slice,site_lat_ind,site_lon_ind])

                param_daily = daily_stat(year_time,
                                         calc_wspeed(param_hourly[0],param_hourly[1]),i_operators[n])

                year_data[i_inds[n],:] = (param_daily*i_scalers[n]) + i_offsets[n] 
    
        # put all the data into a cabo file
        file_year = str(year_time[0].year)[1:]

        output_filename = file_handle+'_'+str(file_number)+'HB'+'.'+file_year

        with open(output_filename, 'w') as f:
            f.write(header) 
            for k,thisday in enumerate(doys+1):

                thisline = '{:>7} {:>2} {:>4} {:>6.0f} {:>6.1f} {:>6.1f} {:>6.3f} {:>6.1f} {:>6.1f} \n'.format(
                    station_number, year_time[0].year, thisday, year_data[0][k], year_data[1][k], 
                    year_data[2][k], year_data[3][k], year_data[4][k], year_data[5][k])

                f.write(thisline) # write the data to file
        f.close()
        print ("File: ", output_filename, "saved successfully.")