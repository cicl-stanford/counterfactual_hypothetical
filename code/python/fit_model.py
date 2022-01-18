import model
import numpy as np
import pandas as pd
import time

# A procedure to generate model predictions for a given parameter setting
# Returns the model as a 8x2 np array. Hypotheticals on the left, Counterfactuals on the right
def generate_model_predictions(num_samples, uncertainty_noise, brick_noise, save=False, save_file='../R/data/model_predictions.csv'):

	trials = model.load_trials('trialinfo/hyp_count_trials.json')
	# Don't consider the practice trials
	trials = trials[:8]

	predictions = np.zeros((len(trials), 2))

	for i in range(len(trials)):
		tr = trials[i]

		hyp_estimate = model.model_judgement(tr, condition='hypothetical', ball_noise=uncertainty_noise,
			brick_noise=brick_noise, num_samples=num_samples)
		cf_estimate = model.model_judgement(tr, condition='counterfactual', ball_noise=uncertainty_noise,
			brick_noise=brick_noise, num_samples=num_samples)

		predictions[i,:] = [hyp_estimate, cf_estimate]

	if save:
		df_predictions = pd.DataFrame(data=predictions, columns=['hypothetical', 'counterfactual'])
		df_predictions.to_csv(save_file)

	return predictions


# Calculate the squared error loss for a given model prediction against
# the human data
def calculate_loss(model_predictions, human_data): return np.sum((model_predictions - human_data)**2)

# Run a grid search for a given set of uncertainty noise and brick noise parameters
# Generate model predictions for each parameter setting and compute loss value
# Against a given human data response set.
# Human data and number of samples is fixed for the full search.
# Option to save the output search if desired. Defaults to save
# Prints the progress of the outer loop as well as runtime upon completion
def grid_search(human_data, num_samples, unoise_range, bnoise_range, save=True, save_file='data/new_file.csv'):
	# output = np.zeros((len(unoise_range), len(bnoise_range)))
	# loss_values = []
	loss_values = np.zeros((len(unoise_range)*len(bnoise_range), 3))

	t_start = time.time()
	for i in range(len(unoise_range)):
		print(i + 1, 'out of', len(unoise_range))
		unoise = unoise_range[i]
		for j in range(len(bnoise_range)):
			bnoise = bnoise_range[j]

			model_predictions = generate_model_predictions(num_samples, unoise, bnoise)
			loss_val = calculate_loss(model_predictions, human_data)

			# output[i,j] = loss_val
			row_index = i*len(bnoise_range) + j
			loss_values[row_index, :] = [unoise, bnoise, loss_val]

	t_end = time.time()
	print()
	print('time:', t_end - t_start)
	print()

	df_grid_search = pd.DataFrame(data=loss_values, columns=['unoise', 'bnoise', 'loss'])
	if save:
		df_grid_search.to_csv(save_file)

	return df_grid_search

# Procedure to draw a contour graph displaying the loss landscape
# discovered by a grid search.
# Takes the output of a grid search, either just produced or reloaded
# If using conda, must run with pythonw
def visualize_loss_landscape(grid_search_output):

	import matplotlib.pyplot as plt

	loss_values = grid_search_output['loss']
	unoise_range = grid_search_output['unoise'].unique()
	bnoise_range = grid_search_output['bnoise'].unique()

	 # evaluation of the function on the grid
	loss_grid = np.zeros((len(unoise_range), len(bnoise_range)))
	for i in range(len(unoise_range)):
		for j in range(len(bnoise_range)):
			row_index = i*len(bnoise_range) + j
			loss = loss_values[row_index]
			loss_grid[i,j] = loss


	plt.contourf(bnoise_range, unoise_range, loss_grid, 20, cmap='RdGy')
	plt.colorbar()
	plt.show()

# *** Human data needs to be divided in order to be on the same scale as model predictions ***
# human_data = np.array(pd.read_csv('data/hpcf_means.csv')[['human_hp', 'human_cf']])/100
# unoise_range = np.arange(0, 1.3, 0.1)
# bnoise_range = np.arange(0, 275, 25)

# Uncomment to run the grid search
# output = grid_search(human_data, 1000, unoise_range, bnoise_range, save_file='data/grid_search.csv')

# Uncomment to load the output of a prior gridsearch
# output = pd.read_csv('data/grid_search.csv')

# Uncomment to visualize the results of a grid search
# visualize_loss_landscape(output)

# Set seed  and generate predictions from optimal output
# Uncomment to reproduce results after loading loss values from above
# To reproduce results, must load grid_search.csv
# np.random.seed(123)

# opt_model_predictions = generate_model_predictions(num_samples=1000, uncertainty_noise=0.9, brick_noise=0, save=True, save_file='../R/data/model_predictions_ball_only.csv')