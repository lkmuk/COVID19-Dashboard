# the dashboard code
# 	functionalities
#		* select the country of 
#		* indicate whether the SIR simulation model 
#			shall also be displayed
#			(subject to extension, if any)
#		* export the plot as png (as provided by plotly), 
#		   as well as the plot data as csv
# 	remarks:
#		to improve responsiveness,
#		much of the computation is computed ONLY once, 
#		and the corresponding csv file(s) is/are read
#		during callback.
#


import dash
import dash_core_components as dcc
import dash_html_components as html
import plotly.graph_objects as go
from dash.dependencies import Input, Output

import pandas as pd
from data_prep import getData_JohnHopk
# import model_SIR



# update data:
# confirmed cases data from John Hopkins University CSSE's GitHub
print("================================================================")
print("Updating the Confirmed Cases and the files that depend on such data:")
dfs_timeseries = getData_JohnHopk()
print("------  update complete -----")
country_list = dfs_timeseries['confirmed'].columns.unique() 
print("For your information, there are {} countries in the data set".format(len(country_list)))
	#hence more than 100 countries are available 
	# (note: some (small and/or special) countries (about 4 to 6 out of 188+) 
	# are not available for the SIR simulation due to lack of population data^)
	# ^ for the time being, I guess it's acceptable.
country_init = ['Germany','Spain'] #we can safely assume these 2 are in country_list

print(dfs_timeseries['confirmed'])
#dfs_timeseries['confirmed'].reset_index(inplace=True)




print("================================================================")
print("Loading the Dash Application ... \n \n")

external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']
# which will be overridden by ./assets/myEnhancement.css
my_bg_color = '#ffffee' #'rgb(250,230,230)'

app = dash.Dash(__name__, external_stylesheets=external_stylesheets)


# Dashboard HTML Layout/CSS Style 
# and Initialization of the widgets' state (except the plot fig)
figInfected = go.Figure()
app.layout = html.Div([
    html.H1("Cumulative Confirmed Cases of COVID-19"),
	html.P("The data are derived from:"),
    html.A("the GITHUB repository of CSSE, John Hopkins University (updated daily at 23:59 UTC)", 
        href="https://github.com/CSSEGISandData/COVID-19/blob/master/csse_covid_19_data/csse_covid_19_time_series/time_series_covid19_confirmed_global.csv",
        target="_blank"
    ),
    dcc.Markdown("> tips: You need to restart the server session to update the data."),        
    
    html.Label('Select the country(s) to display:',htmlFor='GUI_country_selected'),
    dcc.Dropdown(
        id='GUI_country_selected',
        options=[{'label':each,'value':each} for each in country_list],
        value=country_init, #initial value
        multi=True
    ),
    


    # tips about the simulation
    #html.Label('SIR filtering & forecast with posterior Least-Square Fitted Parameters?'),
    
    html.Div(
        dcc.Graph(id='GUI_plot_main',figure=figInfected),
        style={"textAlign": "center", "margin":"12px"}
    ),

    dcc.Markdown("""
        > Caution: The data above is **cumulative**,
        as suggested by the monotonically non-decreasing traces.
        > Therefore, it shall **NOT** be interpreted as 
        the number of infection at any time for a particualr country.
        > I personally believe the former is by itself of little practical use, 
        apart from bookkeeping and being handy to the the press.
        > For a more meaning data analysis, please run the `app_full.py` dashboard instead.
        """),
])

    
# reactive programming here
@app.callback(
        Output('GUI_plot_main', 'figure'), #is enclosing it with square braces so fatal? Yes....
        [Input('GUI_country_selected','value')]
    )
def update_figInfected(country_selected):
    '''
    Parameters
    ----------
    country_selected : list of strings
        as provided by the GUI multi-select dropdown menu
        hence no need to check the validity.

    Returns
    -------
    a dict of traces and plot layout to be taken effect
        to be digested by figInfected (dash graph) object

    '''
    traces = []
    for country in country_selected:
        trace_x = dfs_timeseries['confirmed'].index #dfs_timeseries['confirmed']['date']
        trace_y = dfs_timeseries['confirmed'][country] 
        #print(type(trace_x)) --- a Pandas series
        #print(type(trace_y)) --- a Pandas series
        traces.append(dict(
            x = trace_x,
            y = trace_y,
            mode = 'markers+lines',
            opacity = 0.9,
            name = country
          )
        )
    
    return {
        'data': traces,
        'layout': dict(
            #width = 1024,
            #height= 720,
            plot_bgcolor=my_bg_color,
            bgcolor=my_bg_color,
            xaxis={
                'title':'date'
            },
            yaxis={
                'type':"log",
                #'title':'Cumulated Confirmed Cases of Infected by COVID-19*'
            },
            title="Cumulated Confirmed Cases of COVID-19* by Country and Time"
        )
    }
    
if __name__ == '__main__':
    app.run_server(debug=True,use_reloader=False)
