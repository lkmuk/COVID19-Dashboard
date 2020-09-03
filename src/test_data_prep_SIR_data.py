import matplotlib.pyplot as plt
from data_prep import getData_JohnHopk # technically, we can just use pandas and open the previously processed data
import pandas as pd
import numpy as np
from datetime import datetime

df_proc_list = getData_JohnHopk()
df_Landeskunden = pd.read_csv('../data_proc/Country_JHU_Info.csv',sep=';',
					index_col = 'country', dtype={'population':np.float64} #so that NaN can be encoded
				)# for normalization

#print(df_Landeskunden['population']) 
#print(type(df_Landeskunden['population']['Germany'])) 
	# turns out it's by default (without specifying the dtype) 
	# interpreted as a string (cause: some entries are missing)

print('\n \n ^^^^ Updates finishes ! ^^^^ \n \n ')
print('Country/ Group names on offer (as used in the JHU datasets:')
countries_full = df_proc_list['SIR_I'].columns
print(countries_full,sep='\t',end='\n')


filter_wo_population_data = np.isnan(df_Landeskunden['population'])
print("the following \"countries\" have no population data:")
print(list(df_Landeskunden.loc[filter_wo_population_data,:].index))



# =============== my test option =========================
showNormalization = False
showRecoveryPopulation = True
#countries_test=['Taiwan*','Japan','Austria','Germany','Australia','Magic']
countries_test=['Germany']
	#['Germany','France','Italy','Austria','Poland','Australia']#,'Spain','US','Brazil','Russia']


# =============== start processing the data and options ===========
t = np.array([datetime.strptime( eachOldStr,"%Y-%m-%d") 
		for eachOldStr in df_proc_list['SIR_I'].index]
	)

fig,ax = plt.subplots();
if showNormalization:
	yLabel = 'percentage of total poulation (as of 2019)'
else:
	yLabel = 'number of people'
ax.set(xlabel='time (Date)',ylabel=yLabel,
		title='SIR Data as derived by getData_JohnHopk'
)

print('\n\n====== Start preparing for the plot ====\n')
for country in countries_test:
	try:
		population_this_country = df_Landeskunden.loc[country,'population']
		print('population of {}: {}'.format(country,population_this_country))
		y_I = df_proc_list['SIR_I'].loc[:,country]	
		y_R = df_proc_list['SIR_R'].loc[:,country]
		if showNormalization:
			if np.isnan(population_this_country):
				print(' ... ... we regret to tell you we have no population that for {}'.format(country))
				print(' ... ... for that reason, we can neither give a predictive model, nor normalize the absolute numbers')
			else:
				y_I =y_I/population_this_country*100
				y_R = y_R/population_this_country*100

		if (not np.isnan(population_this_country) or not showNormalization):
			ax.plot(t,y_I, label="infected ({})".format(country))
			if showRecoveryPopulation:
			 	ax.plot(t,y_R, linestyle="dashed", label="'recovered'({})".format(country)) # semilogy better


	except KeyError:
		print('Sorry, no such country as {}'.format(country))
		print('please use only country (names) used in the JHU Data sets (see above).')


#ax.grid()
plt.legend()
plt.show()
