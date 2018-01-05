import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from scipy.stats import norm

sigma_qty = []
sigma_price = []
x_values_qty_charging = []
x_values_qty_discharging = []
x_values_qty_neutral = []
x_values_price = []

#THIRTY PERCENTILE
#SIXTY PERCENTILE

with open('temp1.txt') as f:
	content = f.readlines()

for big_block in range(1):
	demand_train = pd.read_csv('Demand_Train.csv', header=None).as_matrix()[:600, :]
	demand_train_pred = pd.read_csv('Demand_Train_pred.csv', header=None).as_matrix()[:600, :]
	solar_train = pd.read_csv('Solar_Train.csv', header=None).as_matrix()[:600, :]
	solar_train_pred = pd.read_csv('Solar_Train_pred.csv', header=None).as_matrix()[:600, :]
	price_train = pd.read_csv('Price_Train.csv', header=None).as_matrix()[:600, :]
	price_train_pred = pd.read_csv('Price_Train_pred.csv', header=None).as_matrix()[:600, :]

	x_values = np.arange(-4, +4, 0.05)
	y_values = np.arange(-4, +4, 0.05)
	cost_charging = np.zeros((x_values.size, y_values.size))
	cost_discharging = np.zeros((x_values.size, y_values.size))
	cost_neutral = np.zeros((x_values.size, y_values.size))

	temp_qty_sigma = []
	temp_price_sigma = []
	temp_x_value_qty_charging = []
	temp_x_value_qty_discharging = []
	temp_x_value_qty_neutral = []
	temp_x_value_price = []

	for hour in range(24):

		effective_demand_train = demand_train[:, hour] - solar_train[:, hour]
		effective_demand_pred = demand_train_pred[:, hour] - solar_train_pred[:, hour]
		effective_price_train = price_train[:, hour]
		effective_price_pred = price_train_pred[:, hour]

		sorted_effective_demand_train = np.sort(effective_demand_train)
		sorted_effective_demand_pred = effective_demand_pred[np.argsort(effective_demand_train)]
		sorted_effective_price_train = effective_price_train[np.argsort(effective_demand_train)]
		sorted_effective_price_pred = effective_price_pred[np.argsort(effective_demand_train)]

		list_effective_demand_train = np.split(sorted_effective_demand_train, np.searchsorted(sorted_effective_demand_train, np.array([float(content[3*hour].split()[-1]), float(content[3*hour+1].split()[-1]), float(content[3*hour+2].split()[-1])]), side='right'))
		list_effective_demand_pred = np.split(sorted_effective_demand_pred, np.searchsorted(sorted_effective_demand_train, np.array([float(content[3*hour].split()[-1]), float(content[3*hour+1].split()[-1]), float(content[3*hour+2].split()[-1])]), side='right'))
		list_effective_price_train = np.split(sorted_effective_price_train, np.searchsorted(sorted_effective_demand_train, np.array([float(content[3*hour].split()[-1]), float(content[3*hour+1].split()[-1]), float(content[3*hour+2].split()[-1])]), side='right'))
		list_effective_price_pred = np.split(sorted_effective_price_pred, np.searchsorted(sorted_effective_demand_train, np.array([float(content[3*hour].split()[-1]), float(content[3*hour+1].split()[-1]), float(content[3*hour+2].split()[-1])]), side='right'))

		for block in range(4):
			error_data_quantity = list_effective_demand_train[block] - list_effective_demand_pred[block]
			error_data_price = list_effective_price_train[block] - list_effective_price_pred[block]

			(mu_error_quantity, sigma_error_quantity) = norm.fit(error_data_quantity)
			(mu_error_price, sigma_error_price) = norm.fit(error_data_price)

			print sigma_error_price, sigma_error_quantity

			for i in range(x_values.size):
				for j in range(y_values.size):
					my_bid_quantity_charging = (list_effective_demand_pred[block] + x_values[i]*sigma_error_quantity + 5).clip(min=0)
					my_bid_quantity_discharging = (list_effective_demand_pred[block] + x_values[i]*sigma_error_quantity - 4).clip(min=0)
					my_bid_quantity_neutral = (list_effective_demand_pred[block] + x_values[i]*sigma_error_quantity).clip(min=0)

					my_bid_price = list_effective_price_pred[block] + y_values[j] * sigma_error_price

					result_bidding = (my_bid_price >= list_effective_price_train[block]).astype(np.int)

					# EXCESS is positive CHARGING
					cost_if_won = result_bidding * (my_bid_quantity_charging * my_bid_price  + (list_effective_demand_train[block] - my_bid_quantity_charging).clip(min=0) * 7)
					cost_if_lost = (1 - result_bidding) * (7 * list_effective_demand_train[block])
					total_cost = np.sum(cost_if_won) + np.sum(cost_if_lost)
					cost_charging[i, j] = total_cost

					#DISCHARGING
					cost_if_won = result_bidding * (my_bid_quantity_discharging * my_bid_price  + (list_effective_demand_train[block] - my_bid_quantity_discharging).clip(min=0) * 7)
					cost_if_lost = (1 - result_bidding) * (7 * list_effective_demand_train[block])
					total_cost = np.sum(cost_if_won) + np.sum(cost_if_lost)
					cost_discharging[i, j] = total_cost

					#NEUTRAL
					cost_if_won = result_bidding * (my_bid_quantity_neutral * my_bid_price  + (list_effective_demand_train[block] - my_bid_quantity_neutral).clip(min=0) * 7)
					cost_if_lost = (1 - result_bidding) * (7 * list_effective_demand_train[block])
					total_cost = np.sum(cost_if_won) + np.sum(cost_if_lost)
					cost_neutral[i, j] = total_cost
			temp_qty_sigma.append(sigma_error_quantity)
			temp_price_sigma.append(sigma_error_price)
			temp_x_value_qty_charging.append(x_values[np.unravel_index(np.argmin(cost_charging), cost_charging.shape)[0]])
			temp_x_value_qty_discharging.append(x_values[np.unravel_index(np.argmin(cost_discharging), cost_discharging.shape)[0]])
			temp_x_value_qty_neutral.append(x_values[np.unravel_index(np.argmin(cost_neutral), cost_neutral.shape)[0]])
			temp_x_value_price.append(y_values[np.unravel_index(np.argmin(cost_charging), cost_charging.shape)[1]])
	sigma_qty.append(temp_qty_sigma)
	sigma_price.append(temp_price_sigma)
	x_values_qty_charging.append(temp_x_value_qty_charging)
	x_values_qty_discharging.append(temp_x_value_qty_discharging)
	x_values_qty_neutral.append(temp_x_value_qty_neutral)
	x_values_price.append(temp_x_value_price)

sigma_qty = np.mean(np.asarray(sigma_qty), axis=0)
sigma_price = np.mean(np.asarray(sigma_price), axis=0)
x_values_qty_charging = np.mean(np.asarray(x_values_qty_charging), axis=0)
x_values_qty_discharging = np.mean(np.asarray(x_values_qty_discharging), axis=0)
x_values_qty_neutral = np.mean(np.asarray(x_values_qty_neutral), axis=0)
x_values_price = np.mean(np.asarray(x_values_price), axis=0)

final = np.vstack((sigma_qty, sigma_price, x_values_qty_charging, x_values_qty_discharging, x_values_qty_neutral, x_values_price))

np.savetxt('test_600_4_block.txt', final, fmt='%.3e')