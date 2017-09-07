#  Copyright CERFACS (http://cerfacs.fr/)
#  Apache License, Version 2.0 (http://www.apache.org/licenses/LICENSE-2.0)
#
#  Author: Natalia Tatarinova


import netcdftime
import pdb
import os
#from datetime import datetime
from netCDF4 import Dataset, MFDataset
import numpy
import sys

from ..icclim_exceptions import *

# unused function
def get_list_dates_from_nc(nc, type_dates):
    
    '''
    Returns list of dates from NetCDF dataset.
    
    :param nc: NetCDF dataset
    :type nc: netCDF4.Dataset
    :param type_dates: type of dates ('dt' for datetime objects, 'num' for float objects) 
    :type type_dates: str

    :rtype: list of datetime/float 
    
    '''
    
    var_time = nc.variables['time']
    time_units = var_time.units # str (ex.: 'days since 1850-01-01 00:00:00')
    try:
        time_calend = var_time.calendar # str (ex.: 'standard'/'gregorian'/...)
    except:
        time_calend = 'gregorian'
    
    if type_dates == 'num':
        arr_dt = var_time[:]
        list_dt = arr_dt.tolist() # numpy array -> list
        
    if type_dates == 'dt':
        t = netcdftime.utime(time_units, time_calend) 
        arr_dt = t.num2date(var_time[:]) 
        list_dt = arr_dt.tolist() # numpy array -> list
    del arr_dt
    
    return list_dt



def get_list_dates(ifile, type_dates):
    
    '''
    Returns list of dates from one file.
    
    :param ifile: NetCDF file
    :type ifile: str
    :param type_dates: type of dates ('dt' for datetime objects, 'num' for float objects) 
    :type type_dates: str

    :rtype: list of datetime/float 
    
    '''
    try:
        nc = Dataset(ifile, 'r')
    except RuntimeError:
        raise MissingIcclimInputError("Failed to access dataset: " + ifile)

    var_time = nc.variables['time']
    time_units = var_time.units # str (ex.: 'days since 1850-01-01 00:00:00')
    try:
        time_calend = var_time.calendar # str (ex.: 'standard'/'gregorian'/...)
    except:
        time_calend = 'gregorian'
    
    
    if type_dates == 'num':
        arr_dt = var_time[:]
        list_dt = arr_dt.tolist() # numpy array -> list
        
    if type_dates == 'dt':
        t = netcdftime.utime(time_units, time_calend) 
        arr_dt = t.num2date(var_time[:]) 
        list_dt = arr_dt.tolist() # numpy array -> list
    del arr_dt
    
    nc.close()
    
    return list_dt


def get_list_dates2(ifile_list, type_dates):
    
    '''
    Returns list of dates from a list of files.
    
    :param ifile_list: list of NetCDF files
    :type ifile: list of str
    :param type_dates: type of dates ('dt' for datetime objects, 'num' for float objects) 
    :type type_dates: str

    :rtype: list of datetime/float 
    
    '''
    
    list_dates_glob = []
    for filename in ifile_list:
        list_dates_current = get_list_dates(filename, type_dates)
        list_dates_glob = list_dates_glob + list_dates_current
    list_dates_glob.sort()
    
    return list_dates_glob


def date2num(dt, calend, units):   
    '''
    Converts datetime object to numerical date.    
    
    :param dt: datetime object
    :type dt: datetime.datetime object
    :param calend: calendar attribute of variable "time" in netCDF file
    :type calend: str
    :param units: units of variable "time" in netCDF file
    :type units: str
    
    :rtype: float
    '''
    t = netcdftime.utime(units, calend)
    dt_num = t.date2num(dt)
    
    return dt_num


def num2date(num, calend, units):
    '''
    Converts numerical date to datetime object.    
    
    :param num: numerical date
    :type num: float
    :param calend: calendar attribute of variable "time" in netCDF file
    :type calend: str
    :param units: units of variable "time" in netCDF file
    :type units: str
    
    :rtype: datetime.datetime object
    '''   
    t = netcdftime.utime(units, calend)    
    dt = t.num2date(num)

    return dt


def get_time_range(files, time_range=None, temporal_var_name='time'):
    
    '''
    If time_range is None, this function will get a time range from input files.
    Else, this function will adjust the time_range by setting hour value to datetime.datetime objects. 
    
    
    :param files: netCDF file(s) (including OPeNDAP URL(s))
    :type files: list of str
    
    :param time_range: time_range (default: None)
    :type time_range: list two datetime objects: [begin, end]  
     
    :param temporal_var_name: name of temporal variable from netCDF file (default: "time")
    :type temporal_var_name: str
    
    :rtype
    
    
    Returns a time range: a list two datetime objects: [begin, end], where "begin" is the first date, and "end" is the last.
    '''
    try:
        nc = Dataset(files[0],'r')
    except RuntimeError:
        raise MissingIcclimInputError("Failed to access dataset: " + files[0])

    time = nc.variables[temporal_var_name]
    
    try:
        calend = time.calendar
    except:
        calend = 'gregorian'

    units = time.units
    
    t = netcdftime.utime(units, calend)
    
    any_dt = t.num2date(time[0])
    nc.close()
    
    if time_range != None:        
        
        time_range = harmonize_hourly_timestamp(time_range, any_dt, calend, units)
        print(time_range[1])
    else:
        try:
            nc = MFDataset(files, 'r', aggdim='time')
        except RuntimeError:
            raise MissingIcclimInputError("Failed to access dataset: " + files)
        time_arr = nc.variables[temporal_var_name][:]
        nc.close()

        begin_num = min(time_arr)
        end_num = max(time_arr)

        begin_dt = num2date(begin_num, calend, units)
        end_dt = num2date(end_num, calend, units)
        
        time_range = [begin_dt, end_dt]

    return time_range



def get_year_list(dt_arr):
    '''
    Just to get a list of all years containing the time steps vector (dt_arr).
    '''

    year_list = []
    for dt in dt_arr:
        year_list.append(dt.year)
        
    year_list = list(set(year_list))
    
    return year_list


def harmonize_hourly_timestamp(time_range, dt, calend, units):
    '''
    Adjust the ``time_range`` by setting hour value to datetime.datetime objects.
    
    :param time_range: time range selected by user   
    :type time_range: list of two datetime.datetime objects
    
    :param dt: any datetime step of input datetime vector
    :type dt: datetime.datetime object

    :param calend: calendar attribute of variable "time" in netCDF file
    :type calend: str

    :param units: units of variable "time" in netCDF file
    :type units: str
    
    :rtype: list of two datetime.datetime objects
    
    WHY:
    if input time steps vector is from 1990-01-01 12:00 to 2000-12-31 12:00,
    and user's time_range is [datetime.datetime(1900, 1, 1), datetime.datetime(1905, 12, 31)],
    i.e. [datetime.datetime(1900, 1, 1, 0, 0), datetime.datetime(1905, 12, 31, 0, 0)],
    it will be not included in the input time steps (there will be the error message "The time range is not included in the input time steps array.").
    Thus, this function will adjust the hour of the user's time_range: [datetime.datetime(1900, 1, 1, 12, 0), datetime.datetime(1905, 12, 31, 12, 0)]

    '''

#     time_range_begin = datetime(time_range[0].year, time_range[0].month, time_range[0].day, dt.hour)
#     time_range_end = datetime(time_range[1].year, time_range[1].month, time_range[1].day, dt.hour)

    if calend == 'noleap' or calend == '365_day':
        time_range_begin = netcdftime._netcdftime.DatetimeNoLeap(time_range[0].year, time_range[0].month, time_range[0].day, dt.hour)
        time_range_end = netcdftime._netcdftime.DatetimeNoLeap(time_range[1].year, time_range[1].month, time_range[1].day, dt.hour)
    elif calend == '360_day':
        time_range_begin = netcdftime._netcdftime.Datetime360Day(time_range[0].year, time_range[0].month, time_range[0].day, dt.hour)
        time_range_end = netcdftime._netcdftime.Datetime360Day(time_range[1].year, time_range[1].month, time_range[1].day, dt.hour)
    elif calend == 'gregorian':
        time_range_begin = netcdftime._netcdftime.DatetimeGregorian(time_range[0].year, time_range[0].month, time_range[0].day, dt.hour)
        time_range_end = netcdftime._netcdftime.DatetimeGregorian(time_range[1].year, time_range[1].month, time_range[1].day, dt.hour)
    elif calend == 'proleptic_gregorian':
        time_range_begin = netcdftime._netcdftime.DatetimeProlepticGregorian(time_range[0].year, time_range[0].month, time_range[0].day, dt.hour)
        time_range_end = netcdftime._netcdftime.DatetimeProlepticGregorian(time_range[1].year, time_range[1].month, time_range[1].day, dt.hour)
    elif calend == 'julian':
        time_range_begin = netcdftime._netcdftime.DatetimeJulian(time_range[0].year, time_range[0].month, time_range[0].day, dt.hour)
        time_range_end = netcdftime._netcdftime.DatetimeJulian(time_range[1].year, time_range[1].month, time_range[1].day, dt.hour)
    elif calend == 'all_leap' or calend == '366_day':
        time_range_begin = netcdftime._netcdftime.DatetimeAllLeap(time_range[0].year, time_range[0].month, time_range[0].day, dt.hour)
        time_range_end = netcdftime._netcdftime.DatetimeAllLeap(time_range[1].year, time_range[1].month, time_range[1].day, dt.hour)
    else:
        time_range_begin = netcdftime.datetime(time_range[0].year, time_range[0].month, time_range[0].day, dt.hour)
        time_range_end = netcdftime.datetime(time_range[1].year, time_range[1].month, time_range[1].day, dt.hour)

    return [time_range_begin, time_range_end]


def get_indices_subset(dt_arr, time_range):
    '''
    Returns indices for time subset.
    
    :param dt_arr: time steps vector
    :type dt_arr: numpy.ndarray of datetime objects
    :param time_range: time range
    :type time_range: [datetime1, datetime2]
    
    '''

    dt1 = time_range[0]
    dt2 = time_range[1]

    if dt1 >= dt_arr[0] and dt2 <= dt_arr[-1]:

        mask_dt_arr = numpy.logical_or(dt_arr<dt1, dt_arr>dt2)
        
        indices_non_masked = numpy.where(mask_dt_arr==False)[0]
       
        return indices_non_masked
        
    else: 
        error_msg = ""
        if dt1 < dt_arr[0]:
            error_msg = "Lower limit input to time array is earlier than available time steps, dt1 < dt_arr[0]: " + str(dt1) + " < " + str(dt_arr[0]) + "\n"
        if dt2 > dt_arr[-1]:
            error_msg = error_msg + "Upper time limit specified is later than available time steps, dt2 > dt_arr[-1]: " + str(dt2) + " < " + str(dt_arr[-1])
    raise ValueError(error_msg)

def get_intersecting_years(time_range1, time_range2):
    year_begin_tr1 = time_range1[0].year
    year_end_tr1 = time_range1[1].year
    
    year_begin_tr2 = time_range2[0].year
    year_end_tr2 = time_range2[1].year
    
    list_years_tr1 = range(year_begin_tr1, year_end_tr1+1)
    list_years_tr2 = range(year_begin_tr2, year_end_tr2+1)
    
    intersection = list( set(list_years_tr1).intersection(list_years_tr2) )
    
    return intersection
