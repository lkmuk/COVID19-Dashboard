import os
import pandas as pd
import numpy as np
from datetime import datetime


def getData_JohnHopk():
	"""
	This is a subroutine that 
	1. updates the local copy of the time series of
	   confirmed (infected) coronavirus cases 
	   published by John Hopkins University via GITHUB,
	2. and then processes these data into the following table,  
		| date (as index) | Afghanistan | Albania | ... |
		| --------------- | ----------- | ------- | --- |
		| 2020-01-22      | ...         | ...     | ... | 
		| 2020-01-22      | ...         | ...     | ... | 
		| ...             | ...         | ...     | ... | 
		| (Today)         | ...         | ...     | ... | 
	3. finally saves the processed table as a csv file.
	
	Parameters
    ----------
	none

	Returns
    -------
    the DataFrame of the table above (cf. step 2)

	"""
	
	# -----------------------
	# Step 1: Updating data from the CSV File published by John Hopkins University

	os.system('sh updateRawJHU.sh' )
	df_raw = pd.read_csv('../data_raw/COVID-19/csse_covid_19_data/csse_covid_19_time_series/time_series_covid19_confirmed_global.csv')

	# -----------------------
	# Step 2: Processing Data

	# reformat the dates from the raw CSV to the ISO norm (yyyy-mm-dd) 
	# which permit easy sorting
	dateList =[datetime.strptime( eachOldStr,"%m/%d/%y") \
					for eachOldStr in df_raw.columns[4:]] 
	dateStrNew = [eachDate.strftime('%Y-%m-%d') for eachDate in dateList]

	# create the dataframe 
	df_proc = pd.DataFrame({'date':dateStrNew})
	df_proc.set_index('date', inplace=True)
	df_proc.sort_index(inplace=True) #Just in case
    
	# add a column for every country (in the raw CSV) to the new dataframe
	countries = df_raw['Country/Region'].unique() # returning a list
	# not recommended:  countries = set(df_raw['Country/Region'])  

	# to inform yourself how many countries are involved, run:
	# len(countries)

	for country in countries:
	    row_filter = df_raw['Country/Region']==country
	    df_proc[country]=np.array(df_raw[row_filter].iloc[:,4:].sum(axis=0))

	# -----------------------
	# Step 3: Outputing the (Processed) Data as CSV (semi-colon separated to be precise)

	df_proc.to_csv('../data_proc/COVID_TimeSeries_by_country.csv',sep=';')
	return df_proc

if __name__ == '__main__':
	df_covid_cases_series_latest = getData_JohnHopk()
	print(df_covid_cases_series_latest.tail())
	



