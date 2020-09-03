#import matplotlib.pyplot as plt
import model_SIR as SIR
#import numpy as np
import pandas as pd
#from datetime import datetime as dt
#from datetime import timedelta

# test SIR_countries

# using csv files as sources
df_Landeskunde = pd.read_csv('../data_proc/Country_JHU_Info.csv',sep=';',index_col="country")
df_SIR_I = pd.read_csv('../data_proc/time_COVID19_SIR_I.csv',sep=';',index_col="date")
df_SIR_R = pd.read_csv('../data_proc/time_COVID19_SIR_R.csv',sep=';',index_col="date")

obsWindow = ("2020-06-12","2020-06-30")
countries=('Germany','France','Belgium','Austria','Switzerland')
df_SIR_I_Smoothen_then_Pred, df_countryInfo_on_SIR, countries_no_SIR = SIR.SIR_countries(
		df_SIR_I, df_SIR_R,
		df_Landeskunde,
		obsWindow,
		countries
	)

print(df_countryInfo_on_SIR)

print(df_SIR_I_Smoothen_then_Pred)

print("\n\nThe countries below should have their SIR parameters and simulation disregarded!")
print("Make sure the observation window you select is sensible for these countries!")
print(countries_no_SIR)
