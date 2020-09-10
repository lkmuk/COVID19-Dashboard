# An Interactive COVID-19  Dashboard



## Functionalities
An interactive GUI based on Dash/ Plotly framework that:

* *before the dashboard application initializes*:
  automatically fetches (updates) & process[^1]  the raw data from the [COVID-19 Repo](https://github.com/CSSEGISandData/COVID-19/blob/master/csse_covid_19_data/csse_covid_19_time_series/) published by CSSE, John Hopkins University;

  [^1]:  specifically, aggregates the time series data by country, and perform some arithmetics to yield the empirical time series of the number of infected and "removed" people for each country)

* allows user to select those countries present in the dataset;

* for each selected countries:

  * in *part 1* of the dashboard: 
    plots the respective time series of the cumulative number of confirmed cases (in the *first* interactive figure);

  * in *part 2* of the dashboard: 
    
    * plots the *empirical* time series of the number of infected people (in the *second* interactive figure);
    * allows user to specify the *observation window*. The SIR parameters during that period is *identified* using Least-Square criterion 
      (in other words, a SIR model is "fitted" to the data recorded in this period);
    
    * simulates the time series & 
      plots it on the *second* interactive figure.
      The *predictive* segment is a 30-day period following the observation period;
    * presents those SIR parameters in an *interactive* table;
    * shows some diagnostic messages to the user.

A quick demo can be found in the first 3 minutes of [this video](https://youtu.be/1mKNixrBZDU):

> `app_basics` and `app_SIR_country` correspond to parts 1 and 2 of `app_full` respectively.



## Setting up the project

Below are the steps required for running the application (any one of `src/app_full.py`, `src/app_basics.py` or `src/app_SIR_country.py`)

0. Before beginning the setup, ensure your computer has *git* (for proper cloning of the repository & updating the raw csv data in form of *git submodule* dependency), *python 3* and  *pip3*.

1. Set up your local repository in your desired directory.
   
   ```bash
   $ git clone --recurse-submodules https://github.com/lkmuk/COVID19-Dashboard.git
   $ cd COVID19-Dashboard/data_raw/COVID-19
   $ git checkout master
   ```
   
2. Set up the virtual environment. (continued from above)
   
   ```bash
   $ cd ../..
   $ python3 -m venv venv
   $ source venv/bin/activate
   $ pip3 install -r dependencies.txt
   ```
   
3. Run any one of the three applications. This can be, for example: (continued from above)

   ```bash
   $ cd src
   $ python3 app_full.py
   ```
   note: because of the uses of **relative paths** inside the applications `app_<full/...>.py` for accessing both the raw and processed data, please call the application **only when** you are currently in the directory of `src`.

> If you also want to execute the test scripts in the source folder and the [notebooks](/notebooks), please also install also *matplotlib* and *jupyter notebook* respectively in the virtual environment.



## To-do/ Potential enhancements

This apparently, concerns only part 2.

* improve the numerical accuracy of the identification parameter/ more rigorous analysis into this issue
  * smooth the empirical SIR traces before any parameter identification?
  * more sophisticated version to `est_varying_BetaGamma`?
  * ways to compensate for measurement delay?
  * more advanced epidemic models than SIR?
* create more plausibility check rule, to guard against erroneous identified parameter.
* **more** memorization technique to reduce callback latency.
  So far, I've only eliminated the computationally expensive "refitting" when *only some* minor display options are changed, e.g. normalizing X-axis.  (see the console message of  `app_full.py`) 
  In the future, it is advantageous to refit only if 
  * the observation window is changed, OR
  * a **new** country is added to the selection.
    (now we "refit" the parameters *whenever* the selection list changes OR the obs. window spec. changes,)
* ...