import matplotlib.pyplot as plt
import model_SIR as SIR
import numpy as np
import pandas as pd
from datetime import datetime as dt
from datetime import timedelta

# test SysID

# using csv files as sources
df_Landeskunde = pd.read_csv('../data_proc/Country_JHU_Info.csv',sep=';',index_col="country")
df_SIR_I = pd.read_csv('../data_proc/time_COVID19_SIR_I.csv',sep=';',index_col="date")
df_SIR_R = pd.read_csv('../data_proc/time_COVID19_SIR_R.csv',sep=';',index_col="date")

# setting the observation window
test_country = 'Austria'
# if test_country not in df_Landeskunde.index:
# 	print("Make sure the country name is one of those used in the JHU Dataset!")




population = df_Landeskunde.loc[test_country,'population']
#population = 100000


# print(list(df_SIR_I.columns))
startDate= "2020-03-20"
endDate="2020-04-15"
#endDate  = "2020-04-01"
obs_duration_days = (dt.strptime(endDate,'%Y-%m-%d')-dt.strptime(startDate,'%Y-%m-%d')).days + 1
#print(np.array(df_SIR_I.loc[startDate:endDate,test_country]))
df_country_IR_measured = pd.DataFrame({
    "SIR_I": np.array(df_SIR_I.loc[startDate:endDate,test_country]), # not to forget to convert the Pandas Series into an array!!!
	"SIR_R": np.array(df_SIR_R.loc[startDate:endDate,test_country])
}) # format as required by `df_IR_measured` in `SysID`

SIR_para_local_min = SIR.SysID(df_country_IR_measured, population)
beta, gamma, population_SIR = SIR_para_local_min
print(test_country, "having a population of", population, 
	"\n \t for the specified observation period {} to {}".format(startDate,endDate),
	"\n \t have the SIR parameters as follows:")
print("\t \t beta: {} [per day]".format(beta))
print("\t \t gamma: {} [per day]".format(gamma))
print("\t \t Reproductive No.: {} [-]".format(beta/gamma))
print("\t \t N: {} [man] (i.e. {} % of nominal population as of 2019 )".format(population_SIR, population_SIR/population*100))



# evaluate the fits graphically
Preview_Days = 14
t_obs = np.arange(obs_duration_days)
t_predict = np.arange(obs_duration_days-1, obs_duration_days+Preview_Days)
t_full = np.arange(obs_duration_days+Preview_Days)
fig,ax = plt.subplots();
ax.set(xlabel='time (Date)',ylabel='number of people',
		title='SIR Data of {} as derived by getData_JohnHopk and as smoothened by the SIR model'.format(test_country)
	)

endPreviewDateStr = (dt.strptime(endDate,'%Y-%m-%d')+timedelta(days=Preview_Days)).strftime('%Y-%m-%d')
ax.plot(t_full, df_SIR_I.loc[startDate : endPreviewDateStr, test_country], label="infected (measured)")

y_pred = SIR.gen_SIR_I(
			t_predict,
			*SIR_para_local_min, # 0.18, 0.003,
			# 140000, 
			df_SIR_I.loc[endDate,test_country], 
			df_SIR_R.loc[endDate,test_country] 
		)
ax.plot(t_predict,y_pred, linestyle="dashed", label="infected (SIR predicted)") # semilogy better


y_smooth_pred = SIR.gen_SIR_I(
			t_full,
			*SIR_para_local_min, # 0.18, 0.003,
			# 140000, 
			df_SIR_I.loc[startDate,test_country], 
			df_SIR_R.loc[startDate,test_country] 
		)
ax.plot(t_full,y_smooth_pred, linestyle="dashed", label="infected (SIR predicted from \ncontinuing smoothened value)") # semilogy better

plt.legend()
plt.show()