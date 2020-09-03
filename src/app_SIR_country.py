import dash
import dash_core_components as dcc
import dash_html_components as html
import plotly.graph_objects as go
import dash_table
from dash.dependencies import Input, Output, State

import pandas as pd
from data_prep import getData_JohnHopk
from model_SIR import SIR_countries
from datetime import datetime as dt
from datetime import timedelta as td



# =========================================================================================
#     Update COVID-19 datasets with the GITHUB of CSSE, John Hopkins University (JHU):
#     We want primarily the timeseries of the 
#     accumulative confirmed cases, recovery & deaths of COVID-19 among different countries
# =========================================================================================
print("================================================================")
print(" Updating the Confirmed Cases and the files that depend on such data:")
dfs_timeseries = getData_JohnHopk(updateData=False)
print(" update completed/ bypassed")
country_list = list(dfs_timeseries['confirmed'].columns.unique())
country_list.remove("Diamond Princess") # they are of no interest to us
country_list.remove('MS Zaandam')
print("FYI, there are {} countries in the data set".format(len(country_list)))
dates_in_DataSets = list(dfs_timeseries['confirmed'].index)

# =========================================================================
#    More Application Variables for Initialization/ Callbacks to access
# =========================================================================
df_Landeskunde = pd.read_csv('../data_proc/Country_JHU_Info.csv',sep=';',index_col="country")
df_Landeskunde['100/population_nominal'] = 100/df_Landeskunde['population']

# Buffer, possibly also the respective initial values
GUI_buf={ # a quick dirty way to buffering some input widgets' attributes
		"obsWinStart": dt.strftime((dt.now()+td(days=-15)),"%Y-%m-%d"),#"2020-07-26",
		"obsWinEnd":   dt.strftime((dt.now()+td(days= -1)),"%Y-%m-%d"),#"2020-08-09",
		"countries_sel": ["Germany","France"], # belonging to the country multi-select drop-down,
		"Xaxis_Fit_SIR_Windows_n_clicks": 0, # an upcounter
		"is_first_call_update_SIR_calls": True, # intially False, just to get around the mechanism of omitting the System Identification computation
									# not sure if it would be benefitical to turn it into an up-counter
	}
# thoughts: how to ensure serialization? in case they will be overwritten by several callbacks???


# mainly, for scaling for X-axis of the plot of SIR, and trace's x-series
preWin_Duration_Days = 30 # potentially something the user can adjust 
			#(but seems uncertainty means this is the largest we can get)...
datesFull_str = list(dfs_timeseries['SIR_I'].index)



# Specifically for the SIR parameter DataTable
df_SIR_para_col_Name_4_dash=[
			'country',
			'population**',
			'COVID-19 Pandemic began on***',
			'Beta* [1/day]',   
			'Gamma* [1/day]', 
			'Contact Num.* [-]',
			'% Population in the SIR model*'
		]
df_SIR_para_Dtype_4_Dash = ["text","numeric","datetime","numeric","numeric","numeric","numeric"]

# specifically, global DataFrame necessitated by the conditional omission of SIR parameter identification
# (the execution of the expensive least square fitting wrapper `SIR_countries`)
df_SIR_I_Smoothen_then_Pred_was = []  # Dummy Initialization
df_countryInfo_on_SIR_was = [] # Dummy Initialization
countries_no_SIR_was =[] # Dummy Initialization


isDiagnoising = True










# =========================================================================
#    Preparing/ Initializing the Dash Application
# =========================================================================
print("\n================================================================")
print(" Loading the Dash Application ... \n \n")

external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']
# which will be overridden by ./assets/myEnhancement.css
my_bg_color = '#ffffee' #'rgb(250,230,230)'

app = dash.Dash(__name__, external_stylesheets=external_stylesheets)


# Dashboard HTML Layout/CSS Style 
# and Initialization of most widgets' state
figSIR = go.Figure()
app.layout = html.Div([
	html.H1("Number of Infecteds of COVID-19",id="main header"),    
	html.Label('Select the country(s) to display:',htmlFor='GUI_countries_selected'),
	dcc.Dropdown(
        id='GUI_countries_selected',
        options=[{'label':each,'value':each} for each in country_list],
        value=GUI_buf["countries_sel"], #initial value
        multi=True
    ),

    # tips about the simulation
    #html.Label('SIR filtering & forecast with posterior Least-Square Fitted Parameters?'),
    
	html.Div(
		[
			html.Label('Please specify the observation window:',htmlFor='GUI_SIR_obs_DatesPicker'),
			dcc.DatePickerRange(
				id='GUI_SIR_obs_DatesPicker',
				start_date = GUI_buf['obsWinStart'],#dt.strptime(GUI_buf['obsWinStart'],"%Y-%m-%d").date(),
				end_date = GUI_buf['obsWinEnd'],#dt.strptime(GUI_buf['obsWinEnd'],"%Y-%m-%d").date(),
				min_date_allowed=dates_in_DataSets[0],#dt.strptime(dates_in_DataSets[0],"%Y-%m-%d"),
				max_date_allowed=dates_in_DataSets[-1],#dt.strptime(dates_in_DataSets[-1],"%Y-%m-%d"),
				minimum_nights = 6,
				display_format='MMM DD, YYYY',
			),

			html.Label('Display options:',htmlFor='GUI_SIR_show_opt_chkbox'),
		    dcc.Checklist(
				options=[
					{'label': "content: Show SIR simultation from observation start to prediction end", 'value': "showSmooth_then_Pred"},
					# {'label': "content: SIR prediction from observation end to prediction end", 'value': "showPredict_from_ObsEnd"},
					{'label': "Y axis: Show in percentage relative to nominal population", 'value':"showInPercent"},
					{'label': "X axis: Prevent auto resizing of X-axis", 'value':"stopAutoResizeX"}
				],
				id = "GUI_SIR_show_opt_chkbox",
				value=["showInPercent","showSmooth_then_Pred"], # plot only the measured values on reset
		    ),
		    html.Button(
		    	# button to resize X-axis plot to observation window + 20
		    	id="GUI_SIR_X_fit_to_windows",
		    	children="X axis: Resize it to fit the observation and prediction windows specified above",
		    	n_clicks=0
		    ),
			dcc.Graph(id='GUI_plot_SIR',figure=figSIR),
			dcc.Markdown("""
				Notes to different kinds of traces:

				^ simulated number of infecteds (or the percentage of which with respect to the country population) 
				  using the start of observation as *starting condition*
				  and the SIR parameters identified in the observation window (if possible)
				  up to the end of the prediction window.

				^^ predicted number of infected (or the percentage of which with respect to the country population)
				  using the end of the observation as *starting condition*
				  and the SIR parameters identified in the observation window (if possible)
				  up to the end of the prediction window.

				""", id = "GUI_info_plot_SIR"),

			dash_table.DataTable(
				id='GUI_tab_SIR_para',
				sort_action='native',
				style_table={
					'width': '1000px',  
					'overflowX': 'auto',
				},
				style_as_list_view=True,
				style_cell={
					'padding': '5px',
					'whiteSpace': 'normal',
					'height':  'auto',
					'lineHeight': '15px',
					'overflowX': 'auto',
					'font-family': 'Avenir Next, Open Sans, Roboto, Arial',
				},
				fixed_rows={'headers': True},
				style_header={
					#'backgroundColor': 'white',
					'fontWeight': 'bold',
					#'overflow': 'auto',
				},
				style_data_conditional=[ # alternating row bg colors
					{
						'if': {'row_index': 'odd'}, 
						'backgroundColor': 'rgb(248, 248, 248)'
					},
					{
						'if': {'filter_query': '{contactNum} > 15'}, 
						'column_id': 'contactNum',
						'color': 'tomato',
					}
				],
				# numb of digits
			),
			dcc.Markdown("""
				Note: * for the specified observation window; ** as of 2019, from various sources; *** the start of pandemic is defined to be the first time when
				the cumulative confirmed cases in this country exceeded the threshold of 20 (see `data_prep.py`)
				""",
				id = "GUI_info_table_SIR"),

			html.Div(
				children=[], 
				id='GUI_SIR_warning_txt',
				style={"MaxWidth": "500px", "BackgroundColor": "rgb(250,250,0)", "Padding": "30px"}
			),
			dcc.Markdown("""
				> Hint: Please make sure the observation window is reasonable for this country.\
				In particular, all countries selected shall be experiencing a rise in number of infecteds\
    		    and exhibit similar epidemic spread dynamics throughout the observation period.
    		    """, id="GUI_info_warning_SIR"),
        ],
        #style={"textAlign": "center", "margin":"12px"}
        id = "GUI_app_SIR"
    ),

])


















# =========================================================================
#    Callbacks of the Dash Application
# =========================================================================
    
# see also: reactive programming, and the guidelines on the official webpage

# organization of callbacks
''' 
-----------------------------------
1. update_confirm_cases_plot
	then update_countries_sel
2. update_SIR_data_and_displays	
	then update_countries_sel
3. update_subject
   Note, we have two subjects in this dashboard (a requirement of the assignment):
   a. confirmed cases (see callback 1)
   b. data-driven SIR analysis and prediction
   
   This callback does the following
   i. switches the h1 header content to the appropriate one, 
   ii. hides & shows the appropriate contents 
       (by toggling the CSS display state of the enclosing DIV: none or block)
'''


@app.callback(
        [ # the reactive outputs
        	Output('GUI_plot_SIR', 'figure'),
        	Output('GUI_tab_SIR_para', 'columns'),
        	Output('GUI_tab_SIR_para', 'data'),
        	Output('GUI_SIR_warning_txt','children'),
        ],
        [ # the stimulative inputs
        	Input('GUI_countries_selected','value'),
        	Input('GUI_SIR_obs_DatesPicker','start_date'),
        	Input('GUI_SIR_obs_DatesPicker','end_date'),
        	Input('GUI_SIR_show_opt_chkbox','value'),
        	Input('GUI_SIR_X_fit_to_windows','n_clicks'),
        	#Input('GUI_SIR_show_R_raw','value'),
        ],
        [   State('GUI_plot_SIR', 'figure')]
    )
def update_SIR_data_and_displays(countries_sel,dateObsStart,dateObsEnd,showOpts,resizeXAxisReq,prevPlotObj):
	''' the callback actions for the SIR output widgets AND/OR related data:
	1. compute SIR_countries [comutationally expensive!] 
		(ONLY if the country selection^ and/or observation window changes)
		^ optimization is possible when the observation window do not change, (not implemented)
		in which we only compute the NEWLY ADDED country's SIR parameters and signals
		(assuming memory mgmt being not critical, there is no benefit of dropping 
		NEWLY UNSELECTED entries as long as the observation window does not change!)
	2. update the plot of SIR, the country info table, and the warning text for the SIR model
		(always redo when this callback is invoked)
	3. update all key-value pairs in the `GUI_buf` (race condition? repeated execution for update_confirmed_cases??? )
	'''

	print("\n ------------------\n callback 'update_SIR_data_and_displays' triggered ... ") 

	# ==========================
	# step 1: recompute SIR parameters & signals 
	# (recompute  CONDITIONALLY to speed up the computation, see the function descriptions above)
	# step 1a: to determine if there is a need to recompute
	#           & update GUI_buf appropriately
	if (dateObsStart == GUI_buf['obsWinStart']) and (dateObsEnd == GUI_buf['obsWinEnd']):
		change_in_ObsWin_spec = False
	else:
		change_in_ObsWin_spec = True
		GUI_buf['obsWinStart'] = dateObsStart # update the buffer
		GUI_buf['obsWinEnd'] = dateObsEnd # update the buffer

	if countries_sel == GUI_buf['countries_sel']:
		change_in_country_sel = False
	else:
		change_in_country_sel = True
		GUI_buf['countries_sel'] = countries_sel # update the buffer

	isNewFit = change_in_ObsWin_spec or change_in_country_sel or GUI_buf["is_first_call_update_SIR_calls"]
	if isDiagnoising:
		print(" Change in Observation Window Specification?\t",change_in_ObsWin_spec)
		print(" Change in the selection of countries?\t", change_in_country_sel)

	# step 1b: proceed to compute ONLY if needed (at least to some extent)
	global df_SIR_I_Smoothen_then_Pred_was
	global df_countryInfo_on_SIR_was
	global countries_no_SIR_was
	if isNewFit:
		print("\n  ------------------\n  Refitting in progress.... (might take a while)")
		df_SIR_I_Smoothen_then_Pred, df_countryInfo_on_SIR, countries_no_SIR = SIR_countries(
			dfs_timeseries['SIR_I'], dfs_timeseries['SIR_R'],
			df_Landeskunde,
			(dateObsStart, dateObsEnd),
			countries_sel,
			preWin_Duration_Days=preWin_Duration_Days, # potentially something, the user can adjust...
			silent=True,
		)
		print("  Refitting completes! \n ------------------")

		# just to keep GLOBAL reference to those data frame, so that they can survive across 
		#  callbacks that omitts the recomputation
		df_SIR_I_Smoothen_then_Pred_was = df_SIR_I_Smoothen_then_Pred
		df_countryInfo_on_SIR_was = df_countryInfo_on_SIR
		countries_no_SIR_was = countries_no_SIR
	else:
		print("\n ------------------") 
		print(" Refitting omitted in this callback instance. ;) \n ------------------")
		# just to use the latched GLOBAL reference, so that the following code can still run
		df_SIR_I_Smoothen_then_Pred = df_SIR_I_Smoothen_then_Pred_was
		df_countryInfo_on_SIR = df_countryInfo_on_SIR_was
		countries_no_SIR = countries_no_SIR_was

	# step 1c: Housekeeping	
	GUI_buf["is_first_call_update_SIR_calls"] = False

	# ==========================
	# step 2: update figure

	# ---------------------------
	# 2a: miscellaneous specifications of the range of the X-axis
	# dateObsStart_dt = dt.strptime(dateObsStart,'%Y-%m-%d')
	# obsWinDur = (dateObsEnd_dt-dateObsStart_dt).days + 1 # duration of observation window [days]
	datesUltimateEnd_str = (dt.strptime(dateObsEnd,'%Y-%m-%d') + td(days=preWin_Duration_Days)).strftime('%Y-%m-%d') 

	# spaghetti overriding logic for the next xaxis range 
	# case 1 (no button event, nor lock enabled):
	datesAxisRange = [datesFull_str[0],datesUltimateEnd_str] 
		# which can also be achieved by the "autoscale" in the plotly toolbar on the top right
	# case 2 (second priority):
	if ("stopAutoResizeX" in showOpts):
		datesAxisRange = prevPlotObj['layout']['xaxis']['range'] # latching, fail back solution: GUI_buf
	# case 3 (highest priority): triggered when new Button Request is detected, (conceptually) triggered by changes in n_clicks (seems we can't change it within a session) ...
	if (GUI_buf['Xaxis_Fit_SIR_Windows_n_clicks'] < resizeXAxisReq):
		datesAxisRange = [dateObsStart, datesUltimateEnd_str]
		GUI_buf['Xaxis_Fit_SIR_Windows_n_clicks']=resizeXAxisReq # update the buffer
	if isDiagnoising:
		print("\n the X-axis will be updated to: {} to {}\n".format(datesAxisRange[0],datesAxisRange[-1]))
	

	# ---------------------------
	# Step 2b: repacking the traces
	traces = []
	for country in countries_sel:
		if "showInPercent" in showOpts:
			factor_switch = df_Landeskunde.loc[country,"100/population_nominal"]
		else:
			factor_switch = 1

		# the measured SIR_I trace
		traces.append(dict(
			x = datesFull_str, # the dates
			y = dfs_timeseries['SIR_I'][country]*factor_switch,
			mode = 'lines', line={"width":3}, opacity = 0.9,
			name = country + " (measured)"
		))

		# BEGIN of adding SIR signals for this country
		# if country in countries_no_SIR:
		# 	continue

		if "showSmooth_then_Pred" in showOpts:
			traces.append(dict(
				x = df_SIR_I_Smoothen_then_Pred.index, # the dates
				y = df_SIR_I_Smoothen_then_Pred[country]*factor_switch,
				mode = 'lines',
				line=dict(width=2, dash='dot'), 
				opacity = 0.7,
				name = country + " (SIR^)"
			))
		# END of adding SIR signals for this country

	# =======================
	# step 3: update the SIR parameter table
	# rounding the contactNum
	df_countryInfo_on_SIR['contactNum']=df_countryInfo_on_SIR['contactNum'].round(3) # to facilitate formatting
	# creating a new column
	df_countryInfo_on_SIR['population_corr'] = (df_countryInfo_on_SIR['population_corr']/df_Landeskunde['population']*100).dropna(axis="index")
	# adding more columns from the Precalculated Landeskunden (which is independent of the observation window specifications)
	df_SIR_para = df_countryInfo_on_SIR.join(
			df_Landeskunde.loc[:,['population','date_pandemic_start']]
		).dropna(axis="index",how="any") # required for compatibility with DataTable

	# rearrange the position of the columns
	df_SIR_para = df_SIR_para[['population','date_pandemic_start','beta','gamma','contactNum','population_corr']]
	df_SIR_para.reset_index(inplace=True)
	
	# ======================
	# step 4: update the warning text
	if len(countries_no_SIR) is 0:
		warnTxt = "No warning."
	else:
		warnTxt = "Warning!!! Unfortunately, the following countries do not seem to a reasonable SIR fit: "
		warnTxt += ", ".join(countries_no_SIR)

	return [
		{
		    'data': traces,
		    'layout': dict(
		        #width = 1024,
		        #height= 720,\
		        paper_bgcolor =my_bg_color,
		        plot_bgcolor=my_bg_color,
		        bgcolor=my_bg_color,
		        xaxis={
		        	'type': 'date',
		            'title':'Date',
		            'range': datesAxisRange,
		        },
		        yaxis={
		            'type':"linear",
		            'title': ("Percent of country population (%)" 
		            	if "showInPercent" in showOpts else "Number of People"),
		            'autorange': True,
		        },
		        title="Trend of the number of infecteds of COVID-19 by Country"
		    )
		},
		[
			{"id": i, "name": name,  "type": dtype} 
			for i, name, dtype in zip(df_SIR_para.columns, df_SIR_para_col_Name_4_dash, df_SIR_para_Dtype_4_Dash)
		],
		df_SIR_para.to_dict('records'),
		warnTxt,
	]















if __name__ == '__main__':
	app.run_server(debug=True,use_reloader=False)

# def genListDateStr(start_date_str,days_tot_inclusive):
# 	''' returns a contingous list of upcounting date strings
# 	'''
# 	start_date_dt = dt.strptime(start_date,'%Y-%m-%d')
# 	return [(start_date_dt+datetime.timedelta(days=each)).strftime('%Y-%m-%d') for each in range(days_tot_inclusive)]