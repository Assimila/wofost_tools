import pandas as pa
import numpy as np
import matplotlib.pyplot as plt
import datetime as dt
import glob
import pickle
import datetime as dt
import pcse
import copy
import yaml
import scipy.stats

from pcse.fileinput import CABOFileReader
from pcse.models import Wofost71_PP
from pcse.models import Wofost71_WLP_FD
from pcse.fileinput import CABOWeatherDataProvider
from pcse.base.parameter_providers import ParameterProvider
from pcse.util import WOFOST71SiteDataProvider
from pcse.fileinput import YAMLAgroManagementReader

class enwofost():
    
    """
    enwofost:
    
    Create n number of ensembles of WOFOST runs with random variations
    to given parameters. Variations are different each iteration.
    
    The module works by iterating through the ensemble runs and generating
    a new parameter for all the given parameters, inserting this into the 
    crop parameter file and then WOFOST is run with this new param set.
    
    The model is run and the outputs are appended to a list for future handing.
    There are multiple ways of handling the outputs, where the list can be 
    returned or more intuitive things can be done.
    
    Included Methods:
    
        - Generate_With_Dists_From_Scratch:
            Produce n ensembles from strings of file locations and a
            CSV describing the distributions.
            
        - Generate_With_Dists_From_Objects:
            Produce n ensembles from wofost objects and CSV describing
            the distributions.
            
        - Generate_With_MC_From_Objects:
            Produce n ensembles from wofost objects and Monte Carlo 
            parameter sets.
            
        - Extract_Params:
            Return a dictionary where the keys are the parameter. A
            2D array is in each branch. The dimension n ensembles *
            number of days.
            
        - Get_Outputs:
            Return the list of wofost outputs made in the ensembles.
            
        - PDF_Image:
            Produce a probability distribution image showing the 
            distributions of the ensembles.
    
    Example:
    
    # repo for allot of my data:
    woroot = '/media/DataShare/Alex/wofost/'
    
    # create an instance for 20 ensembles
    ensembles = enwofost(20,'/media/DataShare/Alex/wofost/scripts/par_prior.csv')
    
    # To generate them, you can either use raw data files on disk like this:
    ensembles.Generate_From_Scratch(woroot+'params/henan_crop_params.CAB',
                              woroot+'params/Hengshui.soil',
                              woroot+'cabo/henan_s01HB*',
                              woroot+'params/timer.amgt')
                              
    # Or you can generate ensembles from opened objects in python. This is important
    # as you often need to adjust these in an environment e.g. agromanager.
    
    # Once these are done, you can get the basic list of results
    list_results = ensembles.Get_Outputs()
    
    # or extract them nicely like this:
    dict_of_params = ensembles.Get_Params(['LAI', 'TSWO'])
    
    # to display the first ensemble
    plt.figure()
    plt.plot(ensembles.Time(),dict_of_params['LAI'][0])
    
    plt.figure()
    plt.plot(ensembles.Time(),dict_of_params['TWSO'][0])
    
    """
    
    def __init__(self, en_number,mode):
        
        self.en_number = en_number
        if mode not in ['potential', 'limited']:
            raise ValueError('mode must be "potential" or "limited"')
        
        if mode == 'potential':
            self.runner = Wofost71_PP
            
        if mode == 'limited':
            self.runner = Wofost71_WLP_FD

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
    
    
    
    def Generate_With_Dists_From_Objects(self, distribution_file, crop_object, soil_object, site_object, 
                              weather_object, agromanagement_object):
        
        self.repo = []
        self.param_files = []
        
        self.distribution_file = distribution_file
        
        try:
            self.params = pa.read_csv(distribution_file)
        except:
            raise NameError('Cant open the distribution file %s'%distribution_file)
            
        self.new_param_vals = {}
        
        for n,i in enumerate(self.params['Param'].iloc[:]):
            if np.isnan(self.params['Function_Value'].iloc[n]) == True:            
                self.new_param_vals[i] = []
            else:
                if i not in list(self.new_param_vals.keys()):
                    self.new_param_vals[i] = {}
                    self.new_param_vals[i][self.params['Function_Value'].iloc[n]] = []
                else:
                    self.new_param_vals[i][self.params['Function_Value'].iloc[n]] = []
        
        for i in range(self.en_number):
            
            # get a new copy of the parameters
            new = copy.deepcopy(crop_object)
            
            # loop through the parameters in the file
            for j in range(len(self.params)):
                
                # separate them out
                name,mu,min_val,max_val,sigma,func = self.params.iloc[j]
                
                # get the distributions                
                dist = scipy.stats.truncnorm((min_val - mu) / sigma,
                        (max_val - mu) / sigma, loc=mu, scale=sigma)            
    
                # get a new value
                new_val = dist.rvs(1)[0]
                
                # first, reasign the simple single parameters
                if np.isnan(func) == True:
                    new[name] = new_val
                    self.new_param_vals[name].append(new_val)
                    
                else:
                    # first check if there already is a function value in place already
                    prs_keys = np.array(new[name])[::2]
                    prs_vals = np.array(new[name])[1::2]
                    
                    # quickly add the val to the new _param_values
                    self.new_param_vals[name][func].append(new_val)
                    
                    # reasign the values if the function value is there
                    if func in prs_keys:
                        prs_vals[np.where(prs_keys == func)[0][0]] = new_val
                        new[name] = np.hstack(zip(prs_keys,prs_vals))
                        
                    # or put a new one in if it is not there already
                    else:
                        new_keys = np.concatenate([prs_keys,np.array([func])])                        
                        new_vals = np.concatenate([prs_vals,np.array([new_val])])
                        
                        sort_index = np.argsort(new_keys)
                        
                        new_keys = new_keys[sort_index]
                        new_vals = new_vals[sort_index]
                        
                        new[name] = np.hstack(zip(new_keys,new_vals))
                        
            self.param_files.append(new)
            new_parameter_object = ParameterProvider(new,soil_object,site_object)
            
            
            # instantiate the new version of wofost
            iter_wof = self.runner(new_parameter_object, 
                                   weather_object, 
                                   agromanagement_object)
                        
            # and run it
            iter_wof.run_till_terminate()
            
            # get the output
            output = iter_wof.get_output()
            
            # add it to the repo
            self.repo.append(output)  
            

    def Generate_With_Dists_From_Scratch(self, distribution_file,crop_file, soil_file,
                                         weather_point, timer_file):
        
        self.repo = []
        self.param_files = []
        
        self.distribution_file = distribution_file
        
        try:
            self.params = pa.read_csv(distribution_file)
        except:
            raise NameError('Cant open the distribution file %s'%distribution_file)
            
        self.new_param_vals = {}
        
        for n,i in enumerate(self.params['Param'].iloc[:]):
            if np.isnan(self.params['Function_Value'].iloc[n]) == True:            
                self.new_param_vals[i] = []
            else:
                if i not in list(self.new_param_vals.keys()):
                    self.new_param_vals[i] = {}
                    self.new_param_vals[i][self.params['Function_Value'].iloc[n]] = []
                else:
                    self.new_param_vals[i][self.params['Function_Value'].iloc[n]] = []
        
        # Read in the parameter files:
        crop = CABOFileReader(crop_file)
        soil = CABOFileReader(soil_file)

        # # the site parameters cover extra stuff not covered by the parameter files
        # # wav is the initial soil moisture content.
        site = WOFOST71SiteDataProvider(WAV=100, CO2=360)

        # # Read in the weather file
        weather = CABOWeatherDataProvider(weather_point)

        # get the agromanager
        agromanagement = YAMLAgroManagementReader(timer_file)
        
        for i in range(self.en_number):
            
            # get a clean version of the parameters
            new = copy.deepcopy(crop)
            
            # loop through the parameters in the file
            for j in range(len(self.params)):
                name,mu,min_val,max_val,sigma,func = self.params.iloc[j]
                
                # get the distributions                
                dist = scipy.stats.truncnorm((min_val - mu) / sigma,
                        (max_val - mu) / sigma, loc=mu, scale=sigma)            
    
                # get a new value
                new_val = dist.rvs(1)[0]
                
                
                # first, reasign the simple single parameters
                if np.isnan(func) == True:
                    new[name] = new_val
                    self.new_param_vals[name].append(new_val)
                    
                else:
                    # first check if there already is a function value in place already
                    prs_keys = np.array(new[name])[::2]
                    prs_vals = np.array(new[name])[1::2]
                    
                    # quickly add the val to the new _param_values
                    self.new_param_vals[name][func].append(new_val)
                    
                    # reasign the values if the function value is there
                    if func in prs_keys:
                        prs_vals[np.where(prs_keys == func)[0][0]] = new_val
                        new[name] = np.hstack(zip(prs_keys,prs_vals))
                        
                    # or put a new one in if it is not there already
                    else:
                        new_keys = np.concatenate([prs_keys,np.array([func])])                        
                        new_vals = np.concatenate([prs_vals,np.array([new_val])])
                        
                        sort_index = np.argsort(new_keys)
                        
                        new_keys = new_keys[sort_index]
                        new_vals = new_vals[sort_index]
                        
                        new[name] = np.hstack(zip(new_keys,new_vals))
            
            
            self.param_files.append(new)
            
            # put the new parameters in the parameter object
            parameters = ParameterProvider(new,soil,site)    

            # instatiate the new version
            iter_wof = self.runner(parameters,  weather, agromanagement)
            
            # run it
            iter_wof.run_till_terminate()
        
            output = iter_wof.get_output()
            
            self.repo.append(output)
            
    
    def Generate_With_MC_From_Objects(self,numpy_repo,crop_object, soil_object,
                     site_object, weather_object, agromanagement_object):
    
        self.repo = []
        
        # open the parameter repo
        distributions = np.load(numpy_repo)['retval'][0]

        # set up some usefull labels for each of the parameters
        pnames = ['LAIEM', 'RGRLAI', 'AMAXTB_01', 'AMAXTB_02', 'AMAXTB_03',\
              'AMAXTB_04', 'CVL', 'CVO', 'CVR', 'CVS', 'SLATB_01', 'SLATB_02',\
              'SLATB_04', 'SLATB_05', 'SLATB_06', 'SLATB_07', 'SLATB_08',\
              'SPAN', 'TBASE', 'TSUM1', 'TSUM2']

        # and there respective function keys
        pkeys = [np.nan,np.nan,0,1,1.3,2,np.nan,np.nan,np.nan,np.nan,\
                0,0.2,0.4,0.7,0.9,1.6,2,np.nan,np.nan,np.nan,np.nan]

        # iterate through the ensembles
        for i in range(self.en_number):

            # pull out some random index to sample
            selection = np.random.choice(range(len(distributions[0])))

            # and pull out that set of parameters
            param_select = distributions[:,selection]
            
            # get a clean version of the crop parameters
            new = copy.deepcopy(crop_object)

            # iterate through each parameter and place it in the new crop file
            for n,j in enumerate(param_select):
                
                inst_p = pnames[n]
                # find the key in the crop parameters
                if '_' in inst_p:
                    inst_p = inst_p.split('_')[0]

                # reassign the simple single parameters
                if type(new[inst_p]) != list:
                    new[inst_p] = j
                

                # then do the array parameters
                else:
                       
                    # find the function values assosiated with each parameter
                    func_vals = np.array(new[inst_p])[::2]

                    # reassign the new values if there is already a function value
                    if pkeys[n] in func_vals:
                        replace_index = np.where(func_vals == pkeys[n])[0]
                        new_param_vals = np.array(new[inst_p])[1::2]
                        new_param_vals[replace_index] = j
                        new_insert = np.hstack(zip(func_vals,new_param_vals))
                        new[inst_p] = list(new_insert)


                    # or insert the new function value and the parameter
                    else:

                        new_func_vals = np.concatenate([func_vals,np.array([pkeys[n]])])

                        sort_index = np.argsort(new_func_vals)

                        new_param_vals = np.array(new[inst_p][1::2])
                        new_param_vals = np.concatenate([new_param_vals,np.array([j])])

                        new_func_vals = new_func_vals[sort_index]
                        new_param_vals = new_param_vals[sort_index]
                        new_insert = np.hstack(zip(new_func_vals,new_param_vals))
                        new[inst_p] = list(new_insert)
                        
                  

         
            new_parameter_object = ParameterProvider(new,soil_object,site_object)

            # instantiate the new version of wofost
            iter_wof = self.runner(new_parameter_object, 
                                   weather_object, 
                                   agromanagement_object)

            iter_wof.run_till_terminate()

            output = iter_wof.get_output()

            self.repo.append(output)
            
    def Extract_Params(self,param_names):
               
        data = {}        
        
        for i in param_names:
            data[i] = np.zeros([self.en_number,len(self.repo[0])])            
            for n,j in enumerate(self.repo):
                data[i][n] = np.array([k[i] for k in j])
                
        return data
    
    def Get_Outputs(self):
        
        return self.repo
    
    def Get_Input_Values(self):
        
        return self.new_param_vals
    
    def Time(self):
        
        return np.array([i['day'] for i in self.repo[0]])
    
    def PDF_Image(self,param_name):
    
        # which output to display 
        lyr = self.Extract_Params([param_name])[param_name]

        # Number of pixels to have in the distribution picture
        pix = max(500, len(lyr[0]))

        x_ = np.linspace(0,len(self.Time())-1,pix,endpoint=True)
        y_ = np.linspace(0,np.nanmax(lyr),pix,endpoint=True)

        # create the y positions
        xp,yp = np.meshgrid(x_,y_)

        dists = {}

        # find the stats for the PDF at each x point
        for i in range(len(self.Time())):
            t = lyr[:,i]
            mu = np.mean(t)
            sigma = np.std(t)

            lower = min(t)
            upper = max(t)

            dists[i] = {}
            dists[i]['mu'] = mu
            dists[i]['sigma'] = sigma
            dists[i]['min/max'] = [lower,upper]

            im = np.zeros([pix,pix])*np.nan

        for n0,i in enumerate(xp[0]):
            vertical = yp[:,n0]

            in_x = i

            in_x_low = int(i)
            in_x_high = i + 1

            mu_l, sigma_l, lower_l, upper_l = dists[in_x_low]['mu'],dists[in_x_low]['sigma'],\
                                          dists[in_x_low]['min/max'][0],dists[in_x_low]['min/max'][1]

            # try/except is for the edges, where there is no data for the upper x
            try:
                mu_u, sigma_u, lower_u, upper_u = dists[in_x_high]['mu'],dists[in_x_high]['sigma'],\
                                          dists[in_x_high]['min/max'][0],dists[in_x_high]['min/max'][1]
            except:
                mu_u, sigma_u, lower_u, upper_u = dists[in_x_low]['mu'],dists[in_x_low]['sigma'],\
                                      dists[in_x_low]['min/max'][0],dists[in_x_low]['min/max'][1]


            y_l = None
            y_u = None

            y_l = scipy.stats.truncnorm.pdf(
                vertical, (lower_l - mu_l) / sigma_l, (upper_l - mu_l)\
                / sigma_l,loc=mu_l,scale=sigma_l) 

            y_u = scipy.stats.truncnorm.pdf(
                vertical, (lower_u - mu_u) / sigma_u, (upper_u - mu_u)\
                / sigma_u,loc=mu_u,scale=sigma_u)

            # interpolate between the lower and upper so the image is clearer
            if (y_l[0] != None) & (y_u[0] != None):

                xdif = in_x - in_x_low

                ydif = y_u - y_l

                yadd = ydif*xdif

                ynew = yadd+y_l

            # give it substribute values for 
            else:
                if y_l != None:
                    ynew = y_l
                else:
                    ynew = y_u

            ynew[ynew == 0] = np.nan

            im[:,n0] = ynew

        max_val = np.nanmean(im)*8

        im_cap = np.copy(im)

        capped = np.where(im_cap > max_val)

        im_cap[capped] = max_val
        
        xticks = np.linspace(0,len(self.Time())-1, 8, endpoint= True)
        xlabels = [self.Time()[int(i)] for i in xticks]
        xlabels = ['%s-%s-%s'%(i.year,i.month,i.day) for i in xlabels]

        plt.figure(figsize=(12,6))
        plt.contourf(xp,yp,im_cap,levels=np.linspace(0,np.nanmax(im_cap),100),cmap='nipy_spectral',)
      
        plt.xticks(xticks,xlabels)

        plt.ylabel(self._units(param_name))
        
        cbar = plt.colorbar()
        cbar.set_label('PDF',rotation = 270, labelpad = 15)