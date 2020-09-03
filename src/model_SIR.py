'''
on 28 Aug 2020, lkmuk wrote:
	This module is designed to maximize modularity, hence reusability.
	As such, all functions (except `SIR_countries`) pertine ONLY to a particular region/ country.
	Consequently, unit tests are more straightforward and simple, hence testability.

	Most basic functionalities are in form of wrapper of 
	standard scientific computing library functions.
	The parameters and return are very often a Pandas DataFrame/ Series.
'''


import numpy as np
import pandas as pd
import datetime
from scipy.integrate import odeint
from scipy.optimize import curve_fit

def SIR_countries(df_SIR_I_meas, df_SIR_R_meas, df_countryInfo, dates_ObsWin, countries_Full, silent=False, preWin_Duration_Days = 14):
	'''
	Effectively, the main wrapper function of this module.
	This module is designed to be invoked by
	callback `update_SIR` in `app_full.py`.

	That callback is triggered ONLY when the user changes 
	the settings on the observation window (cf. `dates_ObsWin`)
	for the SIR parameter identification.

	In other words, which countries are selected (to display) 
	in the dash/plotly figures of `app_full.py` is IRRELEVANT here.
	This function computes the returns FOR ALL COUNTRIES present
	in the given JHU dataset (cf. `df_SIR_I` and `df_SIR_R`).
	Moreover, whether to normalized the number of infected people
	(cf. `app_full.py`) is also IRRELEVANT here. It's the callback
	`update_SIR` 's responsibility to post-modify the returns of this function.

	The rationale behind is to improve responsiveness
	of `app_full.py` through eliminating ALL unnecessary (re)computations.
	Since there are too many possibilities in `dates_ObsWin` (cf. `dates_ObsWin`), 
	going to the extreme, i.e. further pre-computation 
	for ALL possible `dates_ObsWin` scenarios is not practical.

	parameters
	-----------
    df_SIR_I_meas:	DataFrame 
    	(raw) time series of the number of infected people for ALL countries of interest.
		"date" as index, in the format of "YYYY-MM-DD".
		column names as country names as appeared on the CSSE, JHU Dataset
		i.e.
		+--------------+------------+-----+
		| date (index) | Austria    | ... |
		+--------------+------------+-----+
		| "2020-01-22" | (float/int)| ... |
		| "2020-01-23" | ...        | ... |
		| ...          | ...        | ... |
		| (Yesterday)  | ...        | ... |
		+--------------+------------+-----+
	
	df_SIR_R_meas:	DataFrame 
    	(raw) time series of the number of recovered/removed/dead people for ALL countries of interest
		"date" as index, in the format of "YYYY-MM-DD".
		column names as country names as appeared on the CSSE, JHU Dataset
		(same structure as `df_SIR_I`)
	
	df_countryInfo:	DataFrame
		"country" as index, again, only those names as appeared on the CSSE, JHU dataset
		columns of interest here, are: 'population', (maybe more for future extension)
		+-----------------+------------+-----------------------------+-----+
        | Country (index) | population | date when first wave erupts | ... |
		+ ----------------+ -----------+ --------------------------- + ----+
		| Austria         | (int)      |  <"YYYY-MM-DD">             | ... |
		| ...             | ...        |  ...                        | ... |
        +-----------------+------------+-----------------------------+-----+
	
	dates_ObsWin:	2-tuple or list of date str
		dates of the beginning and the end of the observation window,
		where only the corresponding data will be used 
		for identifying the SIR parameters (if possible)
		example: ("2020-06-20","2020-07-20")
		assumptions:
		1. The second element has to be at least 10 date after the first element!!!
		   (cf. `preWin_Duration_Days`)
		2. Both elements must be in the ISO-norm (YYYY-MM-DD)
		While we can ensure from the GUI nature of `app.full.py`, assumption 2 is fulfilled,
		It can be clumpsy to verify assumption 1 at the application level,
		It might be BETTER to CHECK it here and print an warning message 
		to the server console (for the prototype stage) if appropriate.
	
	countries_Full: a tuple/ list of str of country names
		the countries that are to be considered for the data-driven SIR modeling
		(for the given observation period)

		make sure it complies with the naming used in the JHU Dataset!!!
		e.g. ["US","Cuba"]

	returns
	----------
    df_SIR_I_Smoothen_then_Pred: DataFrame
        the DataFrame of SMOOTHENED-THEN-PREDICTED time series of 
        the number of infected people for each countries
        using the respective identified SIR parameters.
        Below is an illustrative example:
        +--------------+------------+-----+
		| date (index) | Austria    | ... |
		+--------------+------------+-----+
		| "2020-06-12" | (float/int)| ... |   ^
		| "2020-06-13" | ...        | ... |   | smoothened "past"
		| ...          | ...        | ... |   | 
		| "2020-06-30" | ...        | ... |   v
		| "2020-07-01" | ...        | ... |   ^
		| "2020-07-02" | ...        | ... |   | predicted "future"
		| ...          | ...        | ... |   | 
		| "2020-08-09" | ...        | ... |   v
		+--------------+------------+-----+
        where 
        * "now" is defined as the END of the observation window 
          (in the example above, it is 30 June 2020),
        * the number of days to extrapolate after "now" is set (by me) 
          to be 40 [days] for COVID-19 !!! (as in the example above)
          Longer prediction horizon than 40 days is considered (by me) 
          as unrealistic.

	df_countryInfo_on_SIR: DataFrame
		includes the identified values of 
		the `beta`, `gamma`, reproductive number for each country
		might be joined to `df_countryInfo` in the `app_full.py`

	countries_wo_meaningful_SIR:	a list of string
		that reports to the user, which countries in `countries_Full`
		do NOT have a meaningful SIR parameters identified,
		e.g. gamma as absurdly low as 1/300 [per day], 
		which would mean the average time to recover is 300 days.
		Possible causes:
		* during that observation period, these countries are experiencing 
		  significant change in the spread dynamics
		* data integrity issues, delay or in general inaccuracy in reporting cases of 
		  confirmed deaths due to/ recovery from COVID-19 infections.

    More general remarks concerning the dataframe inputs    
    ----------------------------------------------------
    1. It is also assumed all DataFrames are sorted ascendingly by index,
       and the raw data ARE ALWAYS in regular time interval of 1 day. 
       (our friend from CSSE, JHU ensures this is the case;
       I am NOT going to verify this assumption in runtime!)
    2. the naming convention of countries/regions FOR all input DataFrame paramater 
      is expected to follow that of the CSSE, JHU dataset (e.g. "US" for USA)
	  (for the invocation by the GUI callback, this can be safely assumed to be valid)
	3. All the dataframe inputs are actually saved as csv-files in `../data_proc`.
	  However, `app_full.py` shall have those dataframes in its namespace regardless, 
	  reading those csv files is simply inferior to the API design that accepts dataframes.
    '''

    # ------------- Step 1 ----------------------
    # checking the dates, and the plausibility on `dates_ObsWin` --- observation window
	dates_raw_Data_str = list(df_SIR_I_meas.sort_index(ascending=True).index)
	date_raw_Data_Start = datetime.datetime.strptime(dates_raw_Data_str[0], "%Y-%m-%d")
	date_raw_Data_End = datetime.datetime.strptime(dates_raw_Data_str[-1],"%Y-%m-%d")
	date_ObsWin_Start = datetime.datetime.strptime(dates_ObsWin[0],"%Y-%m-%d")
	date_ObsWin_End = datetime.datetime.strptime(dates_ObsWin[1],"%Y-%m-%d")

	# fault mode: some dates in the specified observation window have no data!
	# (such faulty input is avoided by proper programming of the GUI's widget)
	if (date_ObsWin_Start < date_raw_Data_Start) or (date_ObsWin_End > date_raw_Data_End):
		raise ValueError(
    		"Make sure the observation window fall \
    		within the dates covered in the datasets!!!\
    		The obs. window can only start at earliest on" + dates_raw_Data_str[0]
    	    #"and end at latest on "+dates_raw_Data_str[-1]
    	    )

	# fault mode: observation window too short (less than 10 days in total)
    # also cover the case when the start is inadvertently swapped with the 
    # end date (not going to happen in the GUI app!)
	min_Obs_duration_days = 10
    # 10 is deemed by me to be sufficiently large to reduce uncertainty
    # more rigorous analysis might follow in the future.
	ObsWin_Duration_Days = (date_ObsWin_End - date_ObsWin_Start).days + 1
	if ObsWin_Duration_Days < min_Obs_duration_days:
		raise ValueError(
			"SIR Model not applicable! Please ensure \
    		observation period is at least 10 days\
    		including both the start and end dates"
    	)
    	
    # -------------- Step 2 -------------------
    # initializing the first DataFrame outputs
    # the time array and date array below span 
    # both the observation & predict windows!
	
	rel_days_full = range(ObsWin_Duration_Days + preWin_Duration_Days) 
	dates_full = [
		(date_ObsWin_Start+datetime.timedelta(days=day_offset)).strftime('%Y-%m-%d')
		for day_offset in rel_days_full
	]
	df_SIR_I_Smoothen_then_Pred = pd.DataFrame({"date":dates_full})

	# initializing the second DataFrame output
	# countries_Full = ["Germany","France"] # for testing
	# countries_Full = df_countryInfo.sort_index(ascending=True).index  # a bad idea, see below
	#  because we shall only compute the SIR parameters and signals FOR those having a similar timeline
	#  i.e. close to an(other) infection peak.
	# Obviously, this premise is generally invalid throughout the globe. 
	# Better just compute those parameters and signals for the (sensibily chosen) countries.
	df_countryInfo_on_SIR = pd.DataFrame({"country":countries_Full})
	df_countryInfo_on_SIR.set_index('country',inplace=True)
	df_countryInfo_on_SIR['beta'] = np.nan # unit: per day
	df_countryInfo_on_SIR['gamma'] = np.nan # unit: per day
	df_countryInfo_on_SIR['population_corr'] = np.nan # unit: per day

	# -------------- Step 3 ------------------
	# the core
	for country in countries_Full:
		if country in ['Diamond Princess', 'MS Zaandam']:
			continue # they are of no interest to us
		if not silent:
			print("\n\n -----------------\nProcessing the SIR model for "+country) 
		# gather country-specific information, e.g. "initial" numbers 
		# of Infected & Removed/Recovered people in this country
		# where "initial" refers to the start of the observation window
		population = df_countryInfo.loc[country,'population']
		I0 = df_SIR_I_meas.loc[dates_ObsWin[0],country]
		R0 = df_SIR_R_meas.loc[dates_ObsWin[0],country]
		
		# identify the parameters with `SysID`
		# --> store beta, gamma (for the given observation window) into `df_countryInfo_on_SIR`
		df_country_IR_measured = pd.DataFrame({
    		"SIR_I": df_SIR_I_meas.loc[dates_ObsWin[0]:dates_ObsWin[1],country],
    		"SIR_R": df_SIR_R_meas.loc[dates_ObsWin[0]:dates_ObsWin[1],country]
		}) # format as required by `df_IR_measured` in `SysID`
		try:
			beta_opt, gamma_opt, population_corrected = SysID(df_country_IR_measured.reset_index(),population,silent=silent) 
    		# pitfall with underexcited SIR system???
			df_countryInfo_on_SIR.loc[country,'beta'] = beta_opt
			df_countryInfo_on_SIR.loc[country,'gamma'] = gamma_opt
			df_countryInfo_on_SIR.loc[country,'population_corr'] = population_corrected

			# simulate with `gen_SIR_I` 
			# --> store the time series to `df_SIR_I_Smoothen_then_Pred`
			df_SIR_I_Smoothen_then_Pred[country] = gen_SIR_I(
					rel_days_full, 
					beta_opt, gamma_opt, 
					population_corrected, I0, R0
			)
		except ValueError: 
			# possible causes:
			# * when the observation window coincides with a prolonged period 
			#	in which no new (official) case is reported in the coutnry 
			continue
		except RuntimeError:
			# possible cause: immediate cause: cannot converge
			# * the spread has not started???? 
			# * or there is simply NO imminent wave of infections for that country??? 
			continue
	# ------------- Step 4 ------------------
	# finalize of dataframe indices & more dataframe manipulations
	df_SIR_I_Smoothen_then_Pred.set_index('date', inplace=True)
	df_countryInfo_on_SIR['contactNum'] =  df_countryInfo_on_SIR['beta'] / df_countryInfo_on_SIR['gamma'] #unit: dimensionless
	# this countries do not have a meaningful SIR parameter (for this observation window), 
	# hence unmeaningful SIR simulation signals as well.
	filter_unmeaningful = df_countryInfo_on_SIR['gamma'] <= 1/300
	countries_wo_meaningful_SIR = list(df_countryInfo_on_SIR.loc[filter_unmeaningful,:].index)

	return df_SIR_I_Smoothen_then_Pred, df_countryInfo_on_SIR, countries_wo_meaningful_SIR










def dynamicsCT(sys_state, t, beta, gamma, population):
	''' Continuous-time (CT) dynamics of the SIR model

	Parameters
	----------
	sys_state: a 3-element array of floats/ int/ double
		i = 0 for S (number of subsceptibles in this country at that time)
		i = 1 for I (number of infected in this country at that time)
		i = 2 for R (number of recovered/deaths in this country at that time)
		as a matter of fact, this dynamics is a DAE, 
		we will reduce it to just 2 state variables I(t) and R(t)
		(given we know the total population, we can infer S(t) = N-I(t)-R(t)).
	t:	
		irrelevant for the (time-invariant) SIR model, 
		included only for satisfying the API of `scipy.integrate.odeint`
	beta: double
		a parameter of the SIR model [man / day] for the susceptible equation
	gamma: double 
		a parameter of the SIR model [man / day] for the recovery equation

	Returns
	----------
	dxdt:	a 3-element array of float/double
		`dxdt[i-1]` = the time derivative of the 
		i-th state variable (i.e. `sys_state[i-1]`) at current time
		as a function of the given `sys_state`.
		for this SIR model, `i` can assume the values of 0,1, or 2.


	See also
	-----------
	1. information about SIR model
	2. this function will be referenced by `gen_SIR_I`
	'''
	rate_population_S_to_I_per_day = beta/population*sys_state[0]*sys_state[1]
	rate_population_I_to_R_per_day = gamma*sys_state[1]
	dxdt = [ \
		-rate_population_S_to_I_per_day, \
		rate_population_S_to_I_per_day - rate_population_I_to_R_per_day, \
		rate_population_I_to_R_per_day \
	]
	return dxdt

def gen_SIR_I(timestamps_from_init_in_days, beta, gamma, population,I0,R0): 
	'''
	generate the time series of infected people (of a given isolated region) 
	for the given initial state using the SIR model (including the given parameters)
	Use cases:
		1. as a function handle, for SysID (which dedicates the API of this func!)
		2. simulation for a given set of parameter and initial condition

	Parameters
	-----------
	timestamps_from_init_in_days:	(m+1)-numpy array
		$$ [t_0, t_1, ..., t_{m-1} ]$$
		where the interpretation of m depends on the use case,
		for use case 1, it is the number of oberservation
		while in use case 2, it is the number of simulated timestamp.
		Regardless of which use case, Its elements should be monotonically **non-decreasing**,
		i.e. t_0 > t_1 > ...
	population:	int  --- the population of the country/region
	I0, R0:	int --- the number of Infected and Recovered/Removed at time t_0 respectively
		note: S0 + I0 + R0 should equal the population
		remarks: This ugly API is due to the compatibility with scipy.optimize.curve_fit
		which is used for use case 1
	beta, gamma: float
		the SIR parameter

	Returns
	----------
	y_sim:	(m)-numpy array
		$$ [I(t_0), I(t_1), ... I(t_{m-1})] $$
		Remarks:
		Although y_sim(t_0), i.e. `y_sim[0]` is readily available as `state_init[1]`,
		it is more convenient to include it into the return!

	See also
	----------
		1. [`scipy.optimize.curve_fit`](https://docs.scipy.org/doc/scipy/reference/generated/scipy.optimize.curve_fit.html)
		   which is called `SysID` which calls this function (cf. use case 1)
		2. Forward Euler methods for numerical integration (for systems of first-order ODE)
		3. [`scipy.integrate.odeint`](https://docs.scipy.org/doc/scipy/reference/generated/scipy.integrate.odeint.html)
		   which this function uses
	'''
	#timestamps_from_init_in_days = np.array(range(days_to_simulate+1))
	state_init=(population-I0-R0, I0, R0)
	state_trajectory_sim = odeint(
			dynamicsCT, state_init, timestamps_from_init_in_days , (beta,gamma,population)
		)
	y_sim = state_trajectory_sim[:,1] # the simulated number of Infected
	return y_sim
	#print(beta,gamma)
	#print(type(state_trajectory_sim), state_trajectory_sim.shape, len(state_trajectory_sim))
	#return [state_trajectory_sim[i][1] for i in range(len(state_trajectory_sim))]
	


def SysID(df_IR_measured, population, silent=False):
	'''
	parameter identification for the SIR model of a given region/ country.
	using least square criterion, optimization by Trust Reflexive Algorithm
	(guess solution, bounds and scaling which are vital to the numerical
	algorithm are enpowered by est_varying_BetaGamma)
	
	Parameters
	----------
	df_IR_measured:	a DataFrame Frame (of m entries 
	where m denotes the no. of observations)
		+-----------------+---------+--------+
		| day (the index) | SIR_I   | SIR_R  |
		+-----------------+---------+--------+
		|  0              | (float) | (float)|
		|  1              |  ...    | ...    |
		|  ...            |  ...    | ...    |
		|  m-1            |  ...    | ...    |
		+-----------------+---------+--------+
		Remarks:
		* This allows easy extension to fit a weighted MSE criteria of both I(t) and R(t)
		  At the moment, we only need `df_IR_measured['SIR_I']` and `df_IR_measured['SIR_R'][0]`.
		* The index should starts from 0
	population:	an int/float	
		For the SIR coupling, we need this information to derive the intial condition
		which is subsequently an input to `gen_SIR_I` which outputs 
		the simulated curve `y_sim`

	Return
	---------
	p_opt:	a tuple of three floats
		(beta_opt, gamma_opt, population_SIR_Most_Likely) --- the optimal parameters w.r.t. the given data & MSE

	See also
	----------
		1. Nonlinear Regression, or Nonlinear Least-square Curve-Fitting
		2. Trust Reflective  Region (the algorithm employed here)
		3. [`scipy.optimize.curve_fit`](https://docs.scipy.org/doc/scipy/reference/generated/scipy.optimize.curve_fit.html)
	'''
	
	# note all parameters (gamma and beta) should be bounded to be positive!!!


	timestamps_data_rel = np.array(df_IR_measured.index) #an argument to `gen_SIR_I`
	#print(df_IR_measured)
	I_init, R_init = df_IR_measured.loc[0,['SIR_I','SIR_R']]
	
	my_eps = 0.01 # for numerical reasons...
	Beta_Est_Time_Series, Gamma_Est_Time_Series = est_varying_BetaGamma(df_IR_measured,silent)
	Gamma_guess = Gamma_Est_Time_Series.quantile(0.5)
	Beta_guess = Beta_Est_Time_Series.quantile(0.5)
	bounds_4_gen_SIR_I = ( # order: beta, gamma, population, initial I val, initial R val
				[Beta_Est_Time_Series.min(), Gamma_Est_Time_Series.min(),  0,         I_init,     R_init],
				[max(Beta_Est_Time_Series.max(),0.0001), Gamma_Est_Time_Series.max(), population*0.2, I_init+my_eps, R_init+my_eps]
			)
	if not silent:
		print('Our guess on Beta: {} [per day] ; set to be within {} and {}.'.format(
			Beta_guess, bounds_4_gen_SIR_I[0][0],bounds_4_gen_SIR_I[1][0])
		)
		print('Our guess on Gamma: {} [per day] ; set to be within {} and {}.'.format(
			Gamma_guess, bounds_4_gen_SIR_I[0][1],bounds_4_gen_SIR_I[1][1])
		)

	pop_corr_factor = 0.25/100
	population_corrected = population*pop_corr_factor
	#print(Beta_guess, Gamma_guess, population_corrected,I_init,R_init) #testing
	p_opt_API, _ = curve_fit(
					gen_SIR_I, 
					timestamps_data_rel, np.array(df_IR_measured['SIR_I']),
					bounds=bounds_4_gen_SIR_I, method="trf", jac='3-point',
					p0=(Beta_guess,
						Gamma_guess,
						population_corrected,
						I_init,R_init
					),
					x_scale=np.array((Beta_guess, Gamma_guess, population_corrected,I_init,R_init)).clip(min=0.0001),
					#loss='soft_l1',
					#diff_step=0.01,
				)
	p_opt = p_opt_API[0:3]
	return p_opt

def est_varying_BetaGamma(df_IR_measured, silent=False):
	'''
	one step look-back for the given I and R time series MEASUREMENT,
	We infer analytically the time-varying parameters of beta and gamma
	(again unit time chosen as day).

	assumption
	-----------------
	the population is predominantly susceptible (i.e. S/N ~ 1) for the given observation period 
	(i.e. before thresholding, aka peaking of I(t))

	Parameters
	----------
		see `SysID`

	returns
	----------
		time series of the estimated beta and gamma (both per day)

	'''
	I_smoothened_avg_previous = (df_IR_measured['SIR_I'].shift(-1) + df_IR_measured['SIR_I'])/2
	gammas_est = df_IR_measured['SIR_R'].diff()/I_smoothened_avg_previous # shift or no shift?
	betas_est = df_IR_measured['SIR_I'].diff()/I_smoothened_avg_previous + gammas_est
	#beta_est = betas_est.quantile(0.5) # for the period

	if not silent:
		print("for the given observation period (presumably before peaking):")
		for para, para_des in zip([betas_est, gammas_est],["Beta","Gamma"]):
			print(" {} ranges from \t {} to\t {}\t \n\t (mean: {}, std dev: {}) ".format(
					para_des,
					para.min(), para.max(),
					para.mean(), para.std(),
				))
	return betas_est, gammas_est


# if __name__ == '__main__':
	# #from data_prep import getData_JohnHopk
	# #df_proc_list = getData_JohnHopk()
	# df_SIR_I = pd.read_csv('../data_proc/time_COVID19_SIR_I.csv',sep=';')
	# df_SIR_R = pd.read_csv('../data_proc/time_COVID19_SIR_I.csv',sep=';')
	# # corner case, e.g. Taiwan, Holy See... about 4 to 5 of them in total not tested
	# countries=['Germany','Spain'] # test cases
	# df_plot = SIR_batch_posterior(df_SIR_I, df_SIR_R, countries, days_to_forecast = 5)
	# print(df_plot)