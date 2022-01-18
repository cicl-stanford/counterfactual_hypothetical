import model
import sys

"""
Takes in experiment and trial to generate a png of each video frame 
trial = trial index (remember 0 indexing)
"""

trial = int(sys.argv[1])
experiment = 'trialinfo/hyp_count_trials.json'

trials = model.load_trials(experiment)
tr = trials[trial]

# def create(exp, tr):
model.run_actual(tr, animate = True, save = True)	
