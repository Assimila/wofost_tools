import pandas as pa
import numpy as np
import matplotlib.pyplot as plt
import datetime as dt
import glob
import pickle
import datetime as dt
import pandas as pa
import pcse
import copy
import yaml

from pcse.fileinput import CABOFileReader
from pcse.models import Wofost71_PP
from pcse.fileinput import CABOWeatherDataProvider
from pcse.base.parameter_providers import ParameterProvider
from pcse.util import WOFOST71SiteDataProvider
from pcse.fileinput import YAMLAgroManagementReader

class cofost():
    
    def __init__(self, weather_point, crop_file, soil_file, planting_date, upto_date):
        
        self.weather_point = weather_point
        self.crop_file = crop_file
        self.soil_file = soil_file
        self.planting_date = planting_date
        self.upto_date = upto_date
    
    def _units(self,param_name):
        
        labels = {'TWSO': 'Total Weight of Storage Organs ($kg\ ha^{-1}$)',
                 'RD':'Rooting Depth ($cm$)',
                 'LAI': 'Leaf Area Index ($cm\ cm^{-1}$)',
                 'TRA': 'Transpiration Rate ($cm\ day^{-1}$)',
                 'TWLV': 'Total Weight of Leaves ($kg\ ha^{-1}$)',
                 'TWRT': 'Total Weight of Roots ($kg\ ha^{-1}$)',
                 'TWST': 'Total Weight of Stems ($kg\ ha^{-1}$)',
                 'DVS': 'Vegetation Development Stage ($unitless$)',
                 'TAGP': 'Total Above Ground Production ($kg\ ha^{-1}$)'}
        
        return labels[param_name]
    
    def Process(self):
        
        # 1 - first we need to intialize the wofost components
        crop = CABOFileReader(self.crop_file)
        soil = CABOFileReader(self.soil_file)

        # # the site parameters cover extra stuff not covered by the parameter files
        # # wav is the initial soil moisture content.
        site = WOFOST71SiteDataProvider(WAV=100, CO2=360)

        # # and ciompile them into a single object.
        parameters = ParameterProvider(crop,soil,site)

        # # Read in the weather file
        weather = CABOWeatherDataProvider(self.weather_point)
        
        vanilla_timer = """Version: 1.0
AgroManagement:
- 2006-01-01:
    CropCalendar:
        crop_name: 'winter-wheat'
        variety_name: 'Shenzhou_wheat'
        crop_start_date: 2006-10-12
        crop_start_type: sowing
        crop_end_date: 2007-06-30
        crop_end_type: harvest
        max_duration: 300
    TimedEvents: null
    StateEvents: null"""
        
        agromanagement = yaml.load(vanilla_timer)['AgroManagement']
        
        # 2 - now we need to enter all the years as campaigns into the agromanager
        available_days = list(weather.store.keys())
        available_days = [i[0] for i in available_days]
        available_years = np.unique([i.year for i in available_days])
        
        # define the month and day to start and finish for each year
        start_month,start_day = self.planting_date.month,self.planting_date.day
        end_month,end_day = self.upto_date.month,self.upto_date.day
        
        # get the key into the original agromanager entry
        key = list(agromanagement[0].keys())[0]
        
        # loop through the years in the data
        for i in available_years:
            
            # define the years starting date
            crop_start = dt.date(i,start_month, start_day)
            
            # define the years end date
            if start_month > end_month:
                # add a year to the datetime if the upto crosses into the next year
                crop_end = dt.date(i+1,end_month,end_day)
            else:
                crop_end = dt.date(i,end_month,end_day)

            # copy the bulk of the campain so it can be edited
            new_campain = copy.deepcopy(agromanagement[0][key])
            
            # change the relivant bits
            new_campain['CropCalendar']['crop_start_date'] = crop_start
            new_campain['CropCalendar']['crop_end_date'] = crop_end
            
            # format it
            to_insert = {crop_start: new_campain}

            # delete the originals
            if i == available_years[-1]:
                del agromanagement[0]
            
            # dont add a campaign that is over the unto_datetime
            if crop_start > self.upto_date:
                continue
            
            # finally add that to the agromanager
            agromanagement.append(to_insert)
            
        # 3 - now we run WOFOST
        # instantiate a wofost instance
        wofost = Wofost71_PP(parameters,  weather, agromanagement)

        # # run
        wofost.run_till_terminate()    

        # # get the output
        self.output = wofost.get_output()
        
        # and save the agromanager
        self.agromanager = agromanagement
        
        # define all the starting and ending times for the campains is quick lists
        self.starts = [list(i.keys())[0] for i in self.agromanager]
        self.ends = [i[self.starts[n]]['CropCalendar']['crop_end_date'] for n,i in enumerate(self.agromanager)]
        
    def Display(self,param_name):
        
        # pull out the data from the output
        time = np.array([i['day'] for i in self.output])
        param = np.array([i[param_name] for i in self.output])
        
        # find the index of all data outside of out target year
        other_ind = np.where(((np.array(time) < self.planting_date) |
                                (np.array(time) > self.upto_date)) == True)[0]

        # find the index of the data inside out target year
        targets_ind = np.where(((np.array(time) >= self.planting_date) & 
                                (np.array(time) <= self.upto_date)) == True)[0]
        
        # pull out the actual data for our target year
        target_t = np.array(time)[targets_ind]
        target_p = np.array(param)[targets_ind]
        
        # nan out the data we have already plotted to avoil any weird trails
        plot_param = copy.deepcopy(np.array(param))
        plot_param[targets_ind] = np.nan
        
        # plot the data
        
        fig,axs = plt.subplots(2,1,figsize=(10,15))
        axs = np.ravel(axs)
        
        axs[0].plot(time,plot_param,c='k',alpha=0.4)
        axs[0].plot(target_t,target_p,c=[0,141./256,165./256],lw=2)
        axs[0].set_ylabel(self._units(param_name),fontsize=12)
        
        # now do the relative plots for days after sewing on the x axis
        
        # loop through each years campaigns
        for n,i in enumerate(self.starts):
            
            # find the index for this campaign
            between_ind = np.where((time >= i) & (time <= self.ends[n]))[0]
            
            # pull out the time and the data for that year
            between_time = time[between_ind]
            between_p = param[between_ind]
            
            # find the days after the sewing
            dos = np.array([(j - i).days for j in between_time])

            # color, width, alpha
            scheme = ['k', 0.8, 0.3]
            
            if between_time[0] == self.planting_date:
                scheme = [[0,141./256,165./256], 2,1]

            axs[1].plot(dos,between_p,c=scheme[0], lw=scheme[1], alpha=scheme[2])
            
            axs[1].set_xlabel('Days After Sewing')
            axs[1].set_ylabel(self._units(param_name),fontsize=12)
            
        axs[1].plot([], [], c=[0,141./256,165./256],
                        lw=2,label='Target Season:%s to %s'
                        %(self.planting_date,self.upto_date))
        axs[1].plot([], [], c='k', lw=0.8, alpha=0.3,
                    label='Previous Seasons:%s to %s'
                        %(self.starts[0].year,self.starts[-1].year))
        
        axs[1].legend()  
        
    def Export_Summary(self,export_savename):
        
        time = np.array([i['day'] for i in self.output])
        # find the indexes of all the years of data.
        year_segs = [np.where((time > i) & (time < self.ends[n]))[0] for n,i in enumerate(self.starts)]
        
        # setup a repo for the important stats
        stats = {'peak_lai': [],
        'dos_peak_lai': [],
        'current_twso': [],
        'current_twlv': [],
        'current_twrt': [],
        'current_twst': [],
        'current_dev_stage': [],
        'proportion_to_next_dev': [],
        'total_transpiration': []}
        
        # ... and repo to represent the years with strings
        indexes = []
    
        # loop through and chop out the data
        for n,i in enumerate(year_segs):
            
            # slice the year out
            year_data = np.array(self.output)[i]

            param_keys = ['DVS', 'LAI', 'TWSO', 'TWLV', 'TWRT', 'TWST', 'RD', 'TRA', 'day']
            
            # get each parameter of the data out
            yd = {}
            for j in param_keys:
                yd[j] = [k[j] for k in year_data]
            
            # get all the statistics out and add them to the dictionary for the year.
            stats['peak_lai'].append(np.max(yd['LAI']))
            stats['dos_peak_lai'].append(np.argmax(np.array(yd['LAI'])))

            stats['current_twso'].append(yd['TWSO'][-1])
            stats['current_twlv'].append(yd['TWLV'][-1])
            stats['current_twrt'].append(yd['TWRT'][-1])
            stats['current_twst'].append(yd['TWST'][-1])
            
            # get a string to represent the DVS
            c_dvs = yd['DVS'][-1]
            if c_dvs < 1:
                dvs_label = 'juvinille'
            if (c_dvs >= 1) & (c_dvs < 2):
                dvs_label = 'anthesis'
            if c_dvs >= 2:
                dvs_label = 'mature'

            stats['current_dev_stage'].append(dvs_label)

            stats['proportion_to_next_dev'].append((1 - (int(c_dvs)+1 - c_dvs))*100)
            
            stats['total_transpiration'].append(np.sum(yd['TRA']))

            indexes.append('%s - %s'%(self.starts[n],self.ends[n]))
        
        # round the data
        for i in list(stats.keys()):
            try:
                stats[i] = np.round(stats[i],3)
            except:
                pass

        df = pa.DataFrame(stats,index=indexes)
        
        df.to_csv(export_savename)