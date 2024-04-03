import streamlit as st
import numpy as np
import pandas as pd
from datetime import date
import numpy as np
from scipy.optimize import curve_fit
import matplotlib.pyplot as plt

st.title("📈 LTV Prediction")
col1, col2 = st.columns([1, 1])



with col1:
    st.header("Retention Rates")

    day_1_retention = st.text_input('Type in your Day 1 retention %', '30.5')
    st.write('day_1_retention: ', float(day_1_retention))
    
    day_7_retention = st.text_input('Type in your Day 7 retention %', '10.1')
    st.write('day_7_retention: ', float(day_7_retention))
    
    day_30_retention = st.text_input('Type in your Day 30 retention %', '2.4')
    st.write('day_30_retention: ', float(day_30_retention))


with col2:
    st.header("ARPDAU, CPI, ROAS")
    
    arpdau = st.text_input('Type in your ARPDAU USD', '2.34')
    arpdau = float(arpdau)
    st.write('ARPDAU: ', arpdau)
    
    cpi = st.text_input('Type in your CPI USD', '4.89')
    cpi = float(cpi)
    st.write('CPI: ', cpi)
    
    roas = st.text_input('Type in your ROAS goal %', '120')
    roas = int(roas)
    st.write('ROAS % Goal: ', roas)



today = str(date.today()) #prepare the "today" variable with the US formatted date --> for writing it into the file name

#arpdau = 0.1 # the ARPDAU in USD, e.g. 0.3 = 30 Cents
end_day = 360 # provide the end day for your calculations. 360 is a good starting point
#cpi = 1 # the CPI in USD, e.g. 0.5 = 50 Cents

#x = [1, 7, 30] #days, e.g. 1, 7, 14, 30
#y = [0.40, 0.20, 0.07] #the corresponding retention rates as percentage, e.g. 0.30, 0.10

x = [1, 7, 30] #days, e.g. 1, 7, 14, 30
y = [float(day_1_retention)/100,
     float(day_7_retention)/100,
     float(day_30_retention)/100]

 #the corresponding retention rates as percentage, e.g. 0.30, 0.10


#ROAS = (Revenue / Spending) * 100
#defines the ROAS goal that a marketing campaign should reach.
#e.g. a ROAS of 200 means that the LTV is 2 times the CPI (LTV: 2$ vs. CPI: 1$)
#e.g. a ROAS of 50 means that the LTV is 50% of the CPI (LTV: 0.5$ vs. CPI: 1$)
#roas = 120  

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


def ShowPlot(x_num, y_num, ltv_num, arpdau_num):
    #Add the original data to the chart (data points of x and y)
    plt.scatter(x_num, y_num, label='actual data')
    #Add the curve_fit data to the chart (data points from powerfunction)
    plt.plot(x_num, GetPowerY(x_num, y_num), "r-", label="fit: a=%5.3f, b=%5.3f" % tuple(GetParametersOfCurveFit(x_num, y_num)))
    # add title and subtitle to the plot
    plt.title("LTV(Day "+ str(end_day)+"): " + str(ltv_num) + " " + currency)
    plt.suptitle("R-Squared: " + str(round(GetRSquared(x_num, y_num), 4)) + ", ARPDAU: " + str(round(arpdau_num, 4)) + " " + currency)
    plt.xlabel('x Days') #name the x axis of the plot
    plt.ylabel('y Retention %') #name the y axis of the plot
    plt.legend() #add a legend to the plot
    #plt.show()
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
    
    plt.title("LTV(Day "+ str(end_day)+"): " + str(ltv_num) + " " + currency)
    plt.suptitle("CPI: " + str(round(cpi_num, 4)) + " " + currency + " - " + "Breakeven Day: " + str(round(cpi_recoup_obj, 4)))
    plt.xlabel('x Days') #name the x axis of the plot
    plt.ylabel('y USD') #name the y axis of the plot
    plt.legend() #add a legend to the plot
    st.pyplot(plt)




PrintCurrentSettings(arpdau, cpi, roas, x, y)

ltv_end_day_float = GetLTV(arpdau, end_day, x, y)
ShowPlot(x, y, ltv_end_day_float, arpdau)

standard_ltv_dict = GetStandardDayLTV(arpdau, x, y)
detailed_ltv_dict = GetDetailedDayLTV(arpdau, x, y, end_day)


lifetime_days_float = GetLifetimeDays(end_day, x, y)

cpi_recoup_day = FindRecoupCPIDay(arpdau, cpi, roas, end_day, x, y)


ShowLTVCPIPlot(ltv_end_day_float, cpi, detailed_ltv_dict, cpi_recoup_day)
