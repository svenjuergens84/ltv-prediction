import streamlit as st
import numpy as np
import pandas as pd
from datetime import date
from scipy.optimize import curve_fit
import matplotlib.pyplot as plt


st.title("📈 LTV Prediction")

st.markdown('''
    **This dashboard will help you to figure out your users' Lifetime Value.**
    
    Just type in some numbers that you most likely got from your Google Play Store or Apple App Store.
    
    **How it works:**
    
    - the program tries to find a curve for the given points of your retention rate
    - please be gentle as there is no sanity check right now :)
    - e.g. your day 30 retention shouldn't be greater than your day 1 retention, etc.
    - then the program calculates many different scenarios and tries to find a point in time to satisfy your ROAS goal
    - e.g. ROAS goal of 120% would mean that you spend 1 USD and get back 1.20 USD
    - if the Break-Even Day variable is 0, that means that the algorithm couldn't find a point where you are running ROI positive with the given numbers  
    - this program is right now in an early version, so don't spend your entire marketing budget on these values :)
    - let me know if you have found a bug or have some feature requests ;)
    
    Made by Sven Jürgens
    
    https://www.linkedin.com/in/svenjuergens/  
    http://svenjuergens-consulting.com/
    
    ''')

col1, col2 = st.columns([1, 1])

with col1:
    st.header("Retention Rates")

    #day_1_retention = st.text_input('Type in your Day 1 retention %', '30.5')
    day_1_retention = st.number_input('Type in your Day 1 retention %', min_value = 0.0, max_value = 100.0, value = 30.5)
    #st.write('Day 1 Retention %: ', float(day_1_retention))
    
    #day_7_retention = st.text_input('Type in your Day 7 retention %', '10.1')
    day_7_retention = st.number_input('Type in your Day 7 retention %', min_value = 0.0, max_value = 100.0, value = 10.5)
    #st.write('Day 7 Retention %: ', float(day_7_retention))
    
    #day_30_retention = st.text_input('Type in your Day 30 retention %', '2.4')
    day_30_retention = st.number_input('Type in your Day 30 retention %', min_value = 0.0, max_value = 100.0, value = 3.5)
    #st.write('Day 30 Retention %: ', float(day_30_retention))


with col2:
    st.header("ARPDAU, CPI, ROAS")
    
    #arpdau = st.text_input('Type in your ARPDAU USD', '2.34')
    arpdau = st.number_input('Type in your ARPDAU USD', min_value = 0.0, max_value = 100.0, value = 0.5)
    arpdau = float(arpdau)
    #st.write('ARPDAU $: ', arpdau)
    
    #cpi = st.text_input('Type in your CPI USD', '4.89')
    cpi = st.number_input('Type in your CPI USD', min_value = 0.0, max_value = 100.0, value = 1.0)
    cpi = float(cpi)
    #st.write('CPI $: ', cpi)
    
    #roas = st.text_input('Type in your ROAS goal %', '120')
    roas = st.number_input('Type in your ROAS goal %', min_value = 0.0, max_value = 500.0, value = 120.0)
    roas = int(roas)
    #st.write('ROAS % Goal: ', roas)


st.header("Predicted Day in the future")
end_day = st.number_input('Type in the end day for your prediction, e.g. 30, 60, 360', min_value = 0, max_value = 360, value = 90)


# Read the CSV file into DataFrame
url_retention = "https://raw.githubusercontent.com/svenjuergens84/ltv-prediction/main/final_retention_clean_row_grouped.csv"
grouped_df = pd.read_csv(url_retention, usecols=['geo', 'day', 'genre_name', 'value'])
grouped_df = grouped_df.rename(columns={'value': 'retention_value'})

# Get unique genre and geo names
genre_names = grouped_df['genre_name'].unique()
geo_names = grouped_df['geo'].unique()

url_arpdau = "https://raw.githubusercontent.com/svenjuergens84/ltv-prediction/main/final_arpdau_clean_row_grouped.csv"
grouped_arpdau_df = pd.read_csv(url_arpdau, usecols=['metric', 'geo', 'genre_name', 'value'])
grouped_arpdau_df = grouped_arpdau_df.rename(columns={'value': 'arpdau_value'})



st.header("Game Retention Benchmarks")
st.write("❤️ The benchmarks are shared by the awesome folks at https://gameanalytics.com")
st.write("If you don't have a game, just leave it as default. This will not influence your LTV calculation")

# Streamlit UI components for selecting genre and geo
selected_genre = st.selectbox("Select your game genre:", genre_names)
selected_geo = st.selectbox("Select your main geo:", geo_names)


def filter_data(selected_genre, selected_geo):
    filtered_data = grouped_df[(grouped_df['genre_name'] == selected_genre) & 
                               (grouped_df['geo'] == selected_geo) & 
                               (grouped_df['day'].isin([1, 7, 28]))]
    return filtered_data.sort_values(by='day')

# Call the filter function to get filtered DataFrame
selected_data = filter_data(selected_genre, selected_geo)

def filter_arpdau_data(selected_genre, selected_geo):
    filtered_data = grouped_arpdau_df[(grouped_arpdau_df['genre_name'] == selected_genre) & 
                               (grouped_arpdau_df['geo'] == selected_geo)]
    return filtered_data

selected_arpdau_data = filter_arpdau_data(selected_genre, selected_geo)

benchmark_x = selected_data["day"]
benchmark_y = selected_data["retention_value"]/100
benchmark_arpdau = selected_arpdau_data[selected_arpdau_data['metric'] == 'arpdau']['arpdau_value'].values[0]


# Display the filtered DataFrame
st.write(selected_data)
st.write(selected_arpdau_data)

today = str(date.today()) #prepare the "today" variable with the US formatted date --> for writing it into the file name

x = [1, 7, 30] #days, e.g. 1, 7, 14, 30
y = [float(day_1_retention)/100,
     float(day_7_retention)/100,
     float(day_30_retention)/100]

currency = "$"


def PrintCurrentSettings(arpdau, cpi, roas, x_values, y_values):
    print("CURRENT SETTINGS:")
    print("ARPDAU $: " + str(arpdau))
    print("CPI $: " + str(cpi))
    print("ROAS Goal %: " + str(roas))
    print("RETENTION RATES: " + str(y_values))
    print("DAYS: " + str(x_values))
    print("----------")


def PowerLawFunction(x, a, b):
    return a * x** -b


def FindNewY(a, b, x):
    #y = ax^b
    new_y = a * x** -b
    return new_y


def GetLTV(arpdau, end_day, x_values, y_values):
    sum_list = []
    sum_list.append(1)
    for i in range(1, end_day):
        y_value = FindNewY(GetParametersOfCurveFit(x_values, y_values)[0], GetParametersOfCurveFit(x_values, y_values)[1], i)
        sum_list.append(y_value)
    ltv = sum(sum_list) * arpdau
    ltv = round(ltv, 3)
    return ltv


def GetStandardDayLTV(arpdau, x_values, y_values):
    ltv_dict = {}
    print("")
    print("LTV OVERVIEW:")
    day_list = [1, 3, 7, 14, 30, 60, 90, 360] #provide a list with days that should be printed out 
    sum_list = []
    sum_list.append(1)
    for day in range(1, 721): #provide a range that should be searched by to find the LTV per day (should be higher than max num of day_list)
        y_value = FindNewY(GetParametersOfCurveFit(x_values, y_values)[0], GetParametersOfCurveFit(x_values, y_values)[1], day)
        sum_list.append(y_value)
    for x in day_list:
        ltv_estimate = sum(sum_list[0:x+1]) * arpdau
        ltv_dict[x] = round(ltv_estimate, 2)
        print("LTV (D" + str(x) + ") $: " + str(round(ltv_estimate, 2)))
    print("----------")
    return ltv_dict


def GetDetailedDayLTV(arpdau, x_values, y_values, end_day_obj):
    ltv_dict = {}
    #print("")
    #print("LTV OVERVIEW:")
    #day_list = [1, 3, 7, 14, 30, 60, 90, 360] #provide a list with days that should be printed out 
    sum_list = []
    sum_list.append(1)
    for day in range(1, 721): #provide a range that should be searched by to find the LTV per day (should be higher than max num of day_list)
        y_value = FindNewY(GetParametersOfCurveFit(x_values, y_values)[0], GetParametersOfCurveFit(x_values, y_values)[1], day)
        sum_list.append(y_value)
    for x in range(end_day_obj):
        ltv_estimate = sum(sum_list[0:x+1]) * arpdau
        ltv_dict[x] = round(ltv_estimate, 2)
        #print("LTV (D" + str(x) + ") $: " + str(round(ltv_estimate, 2)))
    #print("----------")
    return ltv_dict


def GetLifetimeDays(end_day, x_values, y_values):
    sum_list = []
    for i in range(1, end_day):
        y_value = FindNewY(GetParametersOfCurveFit(x_values, y_values)[0], GetParametersOfCurveFit(x_values, y_values)[1], i)
        sum_list.append(y_value)
    sum_list.append(1)
    lifetime_days = sum(sum_list)
    lifetime_days = round(lifetime_days, 2)
    return lifetime_days


def FindRecoupCPIDay(arpdau_value, cpi_value, roas_goal, end_day, x_values, y_values):
    sum_list = []
    sum_list.append(1)
    print("")
    print("CPI RECOUPING OVERVIEW:")
    print("ARPDAU: " + str(arpdau_value))
    print("CPI: " + str(cpi_value))
    print("ROAS Goal: " + str(roas_goal))
    print("End Day: " + str(end_day))
    print("X Values: " + str(x_values))
    print("Y Values: " + str(y_values))
    exp_ltv = roas_goal / 100 * cpi_value
    print("Expected LTV: " + str(exp_ltv))

    for day in range(1, end_day):
        y_value = FindNewY(GetParametersOfCurveFit(x_values, y_values)[0], GetParametersOfCurveFit(x_values, y_values)[1], day)
        sum_list.append(y_value)
        current_ltv = sum(sum_list) * arpdau_value
        current_roas = (current_ltv / cpi_value) * 100
        if current_roas > roas_goal: #we do find a value within the given timeframe, aka. the CPI will recoup
            print("")
            print("Days needed to recoup CPI: " + str(day))
            print("LTV (D" + str(day) +  ") $: " + str(round(current_ltv, 2)))
            print("Observed ROAS(D" + str(day) +  ") %: " + str(round(current_roas, 2)))
            print("")
            print("----------")
            return day
        
    print("You will not recoup the CPI with the given settings")
    day = 0
    return day
            

def GetParametersOfCurveFit(x_values, y_values):
    popt, pcov = curve_fit(PowerLawFunction,  x_values,  y_values)
    #How to use the return in other functions
    #a_param = popt[0]
    #b_param = popt[1]
    #power_y = popt[0]*x**-popt[1]
    return popt


def GetPowerY(x_values, y_values):
    popt = GetParametersOfCurveFit(x_values, y_values)
    power_y = popt[0]*x_values**-popt[1]
    return power_y


def GetRSquared(x_num, y_num):
    xdata = np.array(x_num)
    ydata = np.array(y_num)
    residuals = ydata - PowerLawFunction(xdata, * GetParametersOfCurveFit(x_num, y_num))
    ss_res = np.sum(residuals**2)
    ss_tot = np.sum((ydata-np.mean(ydata))**2)
    r_squared = 1 - (ss_res / ss_tot)
    r_squared = round(r_squared, 3)
    return r_squared


def ShowPlot(user_input_x, user_input_y, benchmark_x, benchmark_y, ltv_num, arpdau_num):
    # Add the original data to the chart (data points of x and y)
    plt.scatter(user_input_x, user_input_y, label='User Input Data')
    # Add the curve_fit data to the chart (data points from powerfunction)
    plt.plot(user_input_x, GetPowerY(user_input_x, user_input_y), "r-", label="User Input Fit: a=%5.3f, b=%5.3f" % tuple(GetParametersOfCurveFit(user_input_x, user_input_y)))
    
    # Add benchmark data to the chart
    plt.scatter(benchmark_x, benchmark_y, label='Benchmark Data')
    plt.plot(benchmark_x, GetPowerY(benchmark_x, benchmark_y), "g-", label="Benchmark Fit: a=%5.3f, b=%5.3f" % tuple(GetParametersOfCurveFit(benchmark_x, benchmark_y)))
    
    # Add title and subtitle to the plot
    plt.suptitle("Retention Plot")
    plt.title("R-Squared (your input): " + str(round(GetRSquared(user_input_x, user_input_y), 4)))
    plt.xlabel('x Days') # Name the x axis of the plot
    plt.ylabel('y Retention %') # Name the y axis of the plot
    plt.legend() # Add a legend to the plot
    st.pyplot(plt)


def ShowLTVCPIPlot(ltv_num, cpi_num, ltv_dict_obj, cpi_recoup_obj):
    plt.clf()
    #unpack and sort the dict of LTV values
    plt.plot(*zip(*sorted(ltv_dict_obj.items())), label="LTV over time")
    # add the CPI value as horizontal line
    plt.axhline(y=cpi_num, color='r', linestyle='-', label="CPI (constant)")
    
    if cpi_recoup_obj != 0:
        plt.annotate(f'ROAS Goal {roas}% Recoup Day: {cpi_recoup_obj}', xy=(cpi_recoup_obj, cpi_num),
                     xytext=(cpi_recoup_obj + 5, cpi_num + 0.1),
                     arrowprops=dict(facecolor='black', arrowstyle='->'),
                     fontsize=8)
    
    plt.suptitle("LTV Plot (your input): LTV(Day "+ str(end_day)+"): " + str(ltv_num) + " " + currency)
    plt.title("CPI: " + str(round(cpi_num, 4)) + " " + currency + " - " + "Breakeven Day (ROAS Goal): " + str(round(cpi_recoup_obj, 4)))
    plt.xlabel('x Days') #name the x axis of the plot
    plt.ylabel('y USD') #name the y axis of the plot
    plt.legend() #add a legend to the plot
    st.pyplot(plt)



ltv_end_day_float = GetLTV(arpdau, end_day, x, y) #user ltv
ShowPlot(x, y,benchmark_x,benchmark_y, ltv_end_day_float, arpdau)
detailed_ltv_dict = GetDetailedDayLTV(arpdau, x, y, end_day) #LTV dict user
cpi_recoup_day = FindRecoupCPIDay(arpdau, cpi, roas, end_day, x, y)
ShowLTVCPIPlot(ltv_end_day_float, cpi, detailed_ltv_dict, cpi_recoup_day)



