import os
import pandas as pd
import numpy as np
from datetime import datetime

def getData_JohnHopk(updateData=True):
	"""
	This is a subroutine that 
	1. updates the local copy of the time series of
	   confirmed coronavirus cases, ...
	   published by John Hopkins University via GITHUB,
	2. and then processes these data (for each subject) into the following table,  
		| date (as index) | Afghanistan | Albania | ... |
		| --------------- | ----------- | ------- | --- |
		| 2020-01-22      | ...         | ...     | ... | 
		| 2020-01-22      | ...         | ...     | ... | 
		| ...             | ...         | ...     | ... | 
		| (Today)         | ...         | ...     | ... | 
	3. finally saves the processed table as a csv file.
	
	Parameters
    ----------
	updateData:	boolean
		(for testing, advantageous not to update)

	Returns
    ------------
    df_proc_list:
    	a dictionary of 5 times series panda frame,
        each frame takes the format of the table above

    File outputs
    -------------
	data_proc/COVID_time_COVID19_confirmed.csv
	data_proc/COVID_time_COVID19_deaths.csv
	data_proc/COVID_time_COVID19_recovered.csv
	data_proc/COVID_time_COVID19_SIR_I.csv (export not implemented)
	data_proc/COVID_time_COVID19_SIR_R.csv (export not implemented)
	data_proc/country_info.csv
	"""


	# =======================================================================
	# Subject 1: time series of cumulative sums of ... confirmed cases, deaths and recovered
	# -----------------------
	# Step 1: Updating local copies of the CSV Files that are published by John Hopkins University
	if updateData:
		try:
			os.system('sh updateRawJHU.sh' )
		except:
			print("Update script file not found! ")

	# -----------------------
	# Step 2: Processing Data from the 3 CSV files
	csv_inputs = ['confirmed','deaths','recovered']
	df_proc_list = dict()
	for subject in csv_inputs:
		input_csv_path = \
			'../data_raw/COVID-19/csse_covid_19_data/csse_covid_19_time_series/time_series_covid19_{}_global.csv'.format(subject)
		df_raw = pd.read_csv(input_csv_path)

		# reformat the dates from the raw CSV to the ISO norm (yyyy-mm-dd) 
		# which permit easy sorting & plotly operation on date objects (in app_<full/basic>.py)
		dateList =[datetime.strptime( eachOldStr,"%m/%d/%y") \
						for eachOldStr in df_raw.columns[4:]] 
		dateStrNew = [eachDate.strftime('%Y-%m-%d') for eachDate in dateList]
		# in theory, we do not have to repeat this for every subject, but just in case.
		print("The data set for {} has ...".format(subject)) 
		print("\t * {} days, in particular, from {} \t to {}.".format(len(dateStrNew),dateStrNew[0],dateStrNew[-1])) 
		    # it should be safe enough to assume the dates are the same across the three input csv files,
		    # if their numbers are the same

		# create the dataframe for the subject 
		df_proc = pd.DataFrame({'date':dateStrNew})
		df_proc.set_index('date', inplace=True) # not relevant for the CSV outputs
		df_proc.sort_index(inplace=True) #Just in case
    
		# add a column for every country (in the raw CSV) to the new dataframe
		countries = df_raw['Country/Region'].unique() # returning a list (in alphebetic order)
		# in theory, we do not have to repeat this for every subject, but just in case.
		print("\t * {} countries".format(len(countries)))
		    # it should be safe enough to assume the country is the same across the three input csv files,
		    # if their numbers are the same

		for country in countries:
		    row_filter = df_raw['Country/Region']==country
		    df_proc[country]=np.array(df_raw[row_filter].iloc[:,4:].sum(axis=0)) # aggregate function

		df_proc.sort_values('date',ascending=True, inplace=True) # just for safe    

		# -----------------------
		# Step 3: Outputing the (Processed) Data as CSV (semi-colon separated to be precise)
		df_proc.to_csv('../data_proc/time_COVID19_{}.csv'.format(subject),sep=';')
		df_proc_list[subject] = df_proc # for later manipulation

		print("")




	# =======================================================================
	# Subject 2: time series of SIR model 
	# ... Recover/removed/ death (i.e. the 'R' in SIR)
	# ... Infected (i.e. the 'I' in SIR)
	df_proc_list['SIR_R'] = df_proc_list['deaths'] + df_proc_list['recovered']
	df_proc_list['SIR_I'] = df_proc_list['confirmed'] - df_proc_list['SIR_R']
	#print(df_SIR_S.tail(60))
	for subject in ['SIR_I','SIR_R']:
		df_proc_list[subject].to_csv('../data_proc/time_COVID19_{}.csv'.format(subject),sep=';')



	# =======================================================================
	# Subject 3: update country info (relevant only if new countries emerge...)
	df_country_info = pd.DataFrame({'country':countries})
	# e.g. date of sufficiently cumulative confirmed case,
	dateStartPandemic = []
	threshold_as_critical = 20 # deemed (by me) as significant
	for country in countries: # there are better ways...
		row_filter = df_proc_list['confirmed'].loc[:,country] >= threshold_as_critical
		try:
			dateStartPandemic_country = df_proc_list['confirmed'].loc[row_filter,country].idxmin()
		except ValueError: #maybe this threshold has not been reached by this country
			dateStartPandemic_country = None
		dateStartPandemic.append(dateStartPandemic_country)
		#print("since {},\t {} has accumulatively reported at least {} cases".format(\
		#	dateStartPandemic_country, country, threshold_as_critical)
		#)
	df_country_info['date_pandemic_start']=dateStartPandemic

	# the population data is so far out-of-sync (population of 2019)
	df_country_pop_raw=pd.read_csv('../data_raw/Country-info.csv',sep=';')
	df_country_pop_raw.drop(['Country Name'],axis='columns', inplace=True) # dropping the country name as used by World Bank's data bank
	df_country_pop_raw.drop(['sources of pop data (if not from World Bank DB)'],axis='columns', inplace=True)
	df_country_pop_raw.rename(columns={'name_JHU':'country','Population in 2019 (WB DB)':'population'},inplace=True)
	df_country_pop_raw.set_index('country',inplace=True)

	# output to CSV
	df_country_info_new = df_country_info.set_index('country').join(df_country_pop_raw)
	df_country_info_new.to_csv('../data_proc/Country_JHU_Info.csv',sep=';')



	# ==================
	# (only relevant for Subjects 1 and 2)
	return df_proc_list

if __name__ == '__main__':
	#import matplotlib as plt
	df_proc_list = getData_JohnHopk()
	print(df_proc_list['confirmed'].tail())
	



