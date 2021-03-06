
def do_conversion(data_file = None, rain_rad_file = None, in_lat_array = None, in_lon_array = None,
                 locality = None, file_handle_array = None):
    
    import numpy as np
    import datetime as dt
    import netCDF4 as nc
    from netCDF4 import num2date
    import pytz
    import pandas as pa
    
    def daily_stat(in_time = None, in_data = None, operation = None):
        
        # note to future alex:
        # the old daily_stat was crap as it looped throgh and found the days in the data
        # this method splits it up using panadas joojoo and agrigrates it
        # makes it way faster.
        
        dates_array = [d.date() for d in in_time]    
        df = pa.DataFrame({'dates': dates_array, 'data': in_data})
        grouped = df.groupby('dates',axis=0)
        aggrigated = grouped.aggregate(operation)

        return aggrigated['data'].values

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
    
    elevation = 50
    
    for site_num,(in_lat,in_lon) in enumerate(zip(in_lat_array,in_lon_array)):
        
        
        site_lat_ind = find_closest(in_lat,inst_data.variables['latitude'])[0][0][0]
        site_lon_ind = find_closest(in_lon,inst_data.variables['longitude'])[0][0][0]
        
        print ('Site %s - lat = %s, lon = %s,'%(site_num,in_lat,in_lon))
        print ('is is taking ERA5 data from pixel %s Lat, %s Lon.'%(
        inst_data.variables['latitude'][site_lat_ind],
        inst_data.variables['longitude'][site_lon_ind]))
        
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

            output_filename = file_handle_array[site_num]+'HB'+'.'+file_year

            with open(output_filename, 'w') as f:
                f.write(header) 
                for k,thisday in enumerate(doys+1):

                    thisline = '{:>7} {:>2} {:>4} {:>6.0f} {:>6.1f} {:>6.1f} {:>6.3f} {:>6.1f} {:>6.1f} \n'.format(
                        1, year_time[0].year, thisday, year_data[0][k], year_data[1][k], 
                        year_data[2][k], year_data[3][k], year_data[4][k], year_data[5][k])

                    f.write(thisline) # write the data to file
            f.close()
            print ("File: ", output_filename, "saved successfully.")
            print (' ')

            

def do_conversion_land(data_file = None, rain_rad_file = None, in_lat_array = None, in_lon_array = None,
                 locality = None, file_handle_array = None):
    
    import numpy as np
    import datetime as dt
    import netCDF4 as nc
    from netCDF4 import num2date
    import pytz
    import pandas as pa
    
    def daily_stat(in_time = None, in_data = None, operation = None):
        
        # note to future alex:
        # the old daily_stat was crap as it looped throgh and found the days in the data
        # this method splits it up using panadas joojoo and agrigrates it
        # makes it way faster.
        
        dates_array = [d.date() for d in in_time]    
        df = pa.DataFrame({'dates': dates_array, 'data': in_data})
        grouped = df.groupby('dates',axis=0)
        aggrigated = grouped.aggregate(operation)

        return aggrigated['data'].values

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
    
    elevation = 50
    
    for site_num,(in_lat,in_lon) in enumerate(zip(in_lat_array,in_lon_array)):
        
        
        site_lat_ind = find_closest(in_lat,inst_data.variables['latitude'])[0][0][0]
        site_lon_ind = find_closest(in_lon,inst_data.variables['longitude'])[0][0][0]
        
        print ('Site %s - lat = %s, lon = %s,'%(site_num,in_lat,in_lon))
        print ('is is taking ERA5 data from pixel %s Lat, %s Lon.'%(
        inst_data.variables['latitude'][site_lat_ind],
        inst_data.variables['longitude'][site_lon_ind]))
        
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
            
            # note to future alex - the land parameters are accumulated over 24 NOT since the last time step
            # thereofre, to get the daily sums of the accumulated parameters, use a custom function called 
            # get_last to find the last timestep in the day - the sum of the daily stats.
            
            def get_last(in_array):
                return np.array(in_array)[-1]
            
            a_operators = [get_last,np.min,np.max,get_last]   

            a_offsets = [0,-273.15,-273.15,0]
            a_scalers = [0.001,1,1,1000]

            # and loop through them for the accumulated data
            for n,i in enumerate(['ssrd','t2m','t2m', 'tp']):
        
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

            output_filename = file_handle_array[site_num]+'HB'+'.'+file_year

            with open(output_filename, 'w') as f:
                f.write(header) 
                for k,thisday in enumerate(doys+1):

                    thisline = '{:>7} {:>2} {:>4} {:>6.0f} {:>6.1f} {:>6.1f} {:>6.3f} {:>6.1f} {:>6.1f} \n'.format(
                        1, year_time[0].year, thisday, year_data[0][k], year_data[1][k], 
                        year_data[2][k], year_data[3][k], year_data[4][k], year_data[5][k])

                    f.write(thisline) # write the data to file
            f.close()
            print ("File: ", output_filename, "saved successfully.")
            print (' ')
            
def do_conversion_single(data_file, in_lat_array, in_lon_array,
                 locality, file_handle_array):
    
     
    def daily_stat(in_time = None, in_data = None, operation = None):
        
        # note to future alex:
        # the old daily_stat was crap as it looped throgh and found the days in the data
        # this method splits it up using panadas joojoo and agrigrates it
        # makes it way faster.
        
        dates_array = [d.date() for d in in_time]    
        df = pa.DataFrame({'dates': dates_array, 'data': in_data})
        grouped = df.groupby('dates',axis=0)
        aggrigated = grouped.aggregate(operation)

        return aggrigated['data'].values

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
    
     # open the data process time
    data  = nc.Dataset(data_file)
    time_utc = nc.num2date(data.variables['time'][:], data.variables['time'].units)

    time_local = np.array([pytz.timezone('utc').localize(i).astimezone(
            pytz.timezone(locality)) for i in time_utc])
    
    elevation = 50
    
    # get the years in the data
    years = np.unique([i.year for i in time_local])
    
    for site_num,(in_lat,in_lon) in enumerate(zip(in_lat_array,in_lon_array)):
        
        site_lat_ind = find_closest(in_lat,data.variables['latitude'])[0][0][0]
        site_lon_ind = find_closest(in_lon,data.variables['longitude'])[0][0][0]
        
        
        print ('Site %s - lat = %s, lon = %s,'%(site_num,in_lat,in_lon))
        print ('is is taking ERA5 data from pixel %s Lat, %s Lon.'%(
        data.variables['latitude'][site_lat_ind],
        data.variables['longitude'][site_lon_ind]))
        
        header = '*---------------------------------------------------------------------------*\n*Station name: '+str(in_lat)+' '+str(in_lon)+'\n* Column  Daily value\n* 1       station number\n* 2       year\n* 3       day\n* 4       irradiation                   (kJ m-2 d-1)\n* 5       minimum temperature           (degrees Celsius)\n* 6       maximum temperature           (degrees Celsius)\n* 7       early morning vapour pressure (kPa)\n* 8       mean wind speed (height: 2 m) (m s-1)\n* 9       precipitation                 (mm d-1)\n*\n* '+'era5'+'\n* Created by era2cabo, by Alex \n* File created: ' + str(dt.datetime.today()) +'\n** WCCFORMAT=2\n*---------------------------------------------------------------------------*\n'+'%s'%in_lon+'  '+'%s'%in_lat+'  '+'{:>2.6f}'.format(elevation)+'  -0.180000  -0.550000 \n'
        
        # loop through each year and make a cabo file for that year
        for y in years:
           
            # find a slice of time that fits in the year
            year_slice = np.where((time_local >= pytz.timezone(locality).
                               localize(dt.datetime(y,1,1,0,0))) & 
                              (time_local < pytz.timezone(locality).
                               localize(dt.datetime(y+1,1,1,0,0))))[0]
            # slice the time
            year_time = time_local[year_slice]

            if len(year_time) < 24:
                print ('Data from file %s covers less than 24 hours for year %s. Annual CABO file ommited for that year.'%(data_file,y))
                continue
        
            # slice the time
            year_time = time_local[year_slice]

            if len(year_time) < 24:
                print ('Data from file %s covers less than 24 hours for year %s. Annual CABO file ommited for that year.'%(data_file,y))
                continue
                
             # find the DoYs of the data
            doys = np.unique([(i - pytz.timezone(locality).
                               localize(dt.datetime(y,1,1))).days for i in year_time])
            
            
            
            # set up an empty repo for the data
            year_data = np.zeros([6,len(doys)])
            
            variables = ['ssrd', 'mn2t', 'mx2t', 'd2m', \
                         ['u10', 'v10'], 'tp']
            
            offsets = [0,-273.15,-273.15, -273.15, 0, 0]
            scalers = [0.001,1,1,0.1,1,1000]
            operators = [np.sum,np.min,np.max,np.mean,np.mean,np.sum]
            
            for n,i in enumerate(variables):
                
                if type(i) == list:
                    
                    for j in i:
                        if j == 'u10':
                            u_wind = data.variables[j][year_slice,site_lat_ind,site_lon_ind]
                        if j == 'v10':
                            v_wind = data.variables[j][year_slice,site_lat_ind,site_lon_ind]
                    
                    ws_hourly = calc_wspeed(u_wind,v_wind)
                    
                    param_daily = daily_stat(year_time,ws_hourly,operators[n])
                    
                elif i == 'd2m':
                    
                    d2m_hourly = data[i][year_slice,site_lat_ind,site_lon_ind] + offsets[n]
                    
                    vp_hourly = calc_es(d2m_hourly)*scalers[n]
                    
                    param_daily = daily_stat(year_time, vp_hourly, operators[n])
                    
                else:
                    
                    
                    var_hourly = data[i][year_slice,site_lat_ind,site_lon_ind]*scalers[n] + offsets[n]
                    
                    param_daily = daily_stat(year_time,var_hourly,operators[n])
                    
                year_data[n] = param_daily
                
             # put all the data into a cabo file
            file_year = str(year_time[0].year)[1:]

            output_filename = file_handle_array[site_num]+'HB.'+file_year

            with open(output_filename, 'w') as f:
                f.write(header) 
                for k,thisday in enumerate(doys+1):

                    thisline = '{:>7} {:>2} {:>4} {:>6.0f} {:>6.1f} {:>6.1f} {:>6.3f} {:>6.1f} {:>6.1f} \n'.format(
                        1, year_time[0].year, thisday, year_data[0][k], year_data[1][k], 
                        year_data[2][k], year_data[3][k], year_data[4][k], year_data[5][k])

                    f.write(thisline) # write the data to file
            f.close()
            print ("File: ", output_filename, "saved successfully.")
            print (' ')