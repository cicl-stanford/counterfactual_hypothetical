# README: this script is an adaptation of the general model.py script
# for the hypothetical vs counterfactual experiment
# - Jingren Wang, Summer 2019 

import sys
import pygame
from pygame.locals import *
import pymunk
import pymunk.pygame_util
import itertools
import json
import numpy as np
import math
from pymunk import Vec2d
import collections #for keeping the order in which dictionaries were created
import time
import random

# WARNING: Pygame and Pymunk have reverse labeling conventions along the Y axis.
# For pymunk the top is higher values and for pygame the top is lower values
# be aware when interpreting coordinates

# Problem with empty pygame window: https://stackoverflow.com/questions/52718921/problems-getting-pygame-to-show-anything-but-a-blank-screen-on-macos-mojave
# pygame issue: https://github.com/pygame/pygame/issues/555

# A parameter that divides the number of steps of the simulation for faster viewings
# It correspondingly speeds up all bodies (balls and brick) so that their
# movement times change in accordance with the division
speed_multiplier = 1


class World():

	def __init__(self, gate=False, start_step=0, step_max=700/speed_multiplier):
		self.width = 800
		self.height = 600
		self.ball_size = 60
		self.box_size = (70,70)
		self.speed = 500*speed_multiplier # scales how fast balls are moving, default = 100
		self.step_size = 1/50.0
		self.step_max = step_max # step at which to stop the animation,i.e. max frame numbers
		self.step = start_step # used to record when events happen
		self.space = pymunk.Space()
		self.events = {'collisions': [], 'outcome': None} # used to record events
		# containers for bodies and shapes
		self.bodies = collections.OrderedDict()  # contain dict of ball names
		self.shapes = collections.OrderedDict()
		self.sprites = collections.OrderedDict()

		self.record_outcome = True
		self.cause_ball = 'A'
		self.target_ball = 'B'
		self.brick = None

		self.collision_types = {
			'static': 0,
			'dynamic': 1,
			'brick': 2,
			'brick_sensor': 3
		}

		# add walls
		self.add_wall(position = (400, 590), length = 800, height = 20, name = 'top_wall', space = self.space)
		self.add_wall(position = (400, 10), length = 800, height = 20, name = 'bottom_wall', space = self.space)
		self.add_wall(position = (10, 550), length = 20, height = 200, name = 'top_left_wall', space=self.space)
		self.add_wall(position = (10, 50), length = 20, height= 200, name = 'bottom_left_wall', space=self.space)



	###################### Simulation setup and running #######################
	def add_wall(self, position, length, height, name, space):
		body = pymunk.Body(body_type = pymunk.Body.STATIC)
		body.position = position
		body.name = name
		wall = pymunk.Poly.create_box(body, size = (length, height))
		wall.elasticity = 1
		# wall.name = name
		wall.collision_type = self.collision_types['static']
		space.add(wall)
		return wall

	def add_ball(self, position, velocity, size, name):
		mass = 1
		radius = size/2
		moment = pymunk.moment_for_circle(mass, 0, radius)
		body = pymunk.Body(mass, moment)
		body.position = position
		body.size = (size,size)
		body.angle = 0
		velocity = [x*self.speed for x in velocity]
		body.apply_impulse_at_local_point(velocity) #set velocity
		body.name = name
		shape = pymunk.Circle(body, radius)
		shape.elasticity = 1.0
		shape.friction = 0
		shape.collision_type = self.collision_types['dynamic']
		self.space.add(body, shape)
		self.bodies[name] = body
		self.shapes[name] = shape
		return body, shape

	def add_sensor(self, pos, name):
		body = pymunk.Body(body_type=pymunk.Body.STATIC)
		body.position = pos
		body.name = name
		body.size = (20, 20)
		body.angle = 0
		shape = pymunk.Poly.create_box(body=body, size=body.size)
		shape.collision_type = self.collision_types['brick_sensor']
		shape.sensor = True
		self.space.add(body, shape)
		self.bodies[body.name] = body
		self.shapes[body.name] = shape
		return body, shape

	def add_brick(self, name, ori, pos, vel, step):
		body = pymunk.Body(body_type=pymunk.Body.KINEMATIC)
		body.position = pos
		body.name = name
		body.size = (36, 100)
		body.angle = ori*(math.pi/180)
		shape = pymunk.Poly.create_box(body=body, size=body.size)
		shape.elasticity = 1.0
		shape.collision_type = self.collision_types['brick']
		self.space.add(body,shape)
		self.bodies[body.name] = body
		self.shapes[body.name] = shape
		self.brick = {'body': body, 'vel': vel, 'step': np.ceil(step/speed_multiplier)}
		return body, shape

	def flipy(self, y):
	    """Small hack to convert chipmunk physics to pygame coordinates"""
	    return -y+600

	def update_sprite(self,body,sprite,screen):
		p = body.position
		p = Vec2d(p.x, self.flipy(p.y))
		angle_degrees = math.degrees(body.angle)
		rotated_shape = pygame.transform.rotate(sprite, angle_degrees)
		offset = Vec2d(rotated_shape.get_size()) / 2.
		p = p - offset
		screen.blit(rotated_shape, p)

		# setup collision handlers
		
	def collision_setup(self):
		handler_dynamic = self.space.add_collision_handler(self.collision_types['dynamic'], self.collision_types['dynamic'])
		handler_dynamic.begin = self.collisions

		handler_brick_sensor = self.space.add_collision_handler(self.collision_types['brick'], self.collision_types['brick_sensor'])
		handler_brick_sensor.begin = self.brick_sensor_col

		handler_brick_wall = self.space.add_collision_handler(self.collision_types['brick'], self.collision_types['static'])
		handler_brick_wall.begin = self.brick_wall_col

		handler_brick_brick = self.space.add_collision_handler(self.collision_types['brick'], self.collision_types['brick'])
		handler_brick_brick.begin = self.brick_brick_col

	# handle dynamic events
	def collisions(self,arbiter,space,data):
		# print arbiter.is_first_contact #checks whether it was the first contact between the shapes
		event = {
			'objects': [arbiter.shapes[0].body.name,arbiter.shapes[1].body.name],
			'step': self.step,
			'type': 'collision'
		}
		self.events['collisions'].append(event)
		return True

	def brick_sensor_col(self, arbiter, space, data):
		brick = arbiter.shapes[0].body
		brick.velocity = (0,0)
		return True

	def brick_wall_col(self, arbiter, space, data):
		brick = arbiter.shapes[0].body
		brick.velocity = (0,0)
		return True

	def brick_brick_col(self, arbiter, space, data):
		b1 = arbiter.shapes[0].body
		b2 = arbiter.shapes[1].body
		b1.velocity = (0,0)
		b2.velocity = (0,0)
		return True

	# A method to check whether to end the simulation and record outcome info
	def end_clip(self):
		# If we have passed the max step
		if self.step > self.step_max:
			if self.target_ball in self.bodies:
				# if we want to record the outcome
				if self.record_outcome:
					# Save the outcome event at coarse and fine level
					#record whether ball B get into the gate or not
					b = self.bodies[self.target_ball]
					event = {
							'ball': self.target_ball,
							'step': self.step,
							'outcome_coarse': 0,
						}
					if b.position[0] > -self.ball_size/2:
						event['outcome_coarse'] = 0
					else:
						event['outcome_coarse'] = 1

					# event['outcome_fine'] = b.position
					self.events['outcome'] = event

			# quit pygame
			pygame.display.quit()
			return True
		else:
			return False

	def simulate(self, animate=False, track=True, ball_noise=1.5, collision_time=285, remove=False, save=False):

		self.collision_setup()
		if remove:
			self.remove(self.cause_ball, 0)

		done = False # pointer to say when animation is done

		# animation setup
		if animate:
			pygame.init()
			clock = pygame.time.Clock()
			screen = pygame.display.set_mode((self.width, self.height))
			pygame.display.set_caption("Animation")
			pic_count = 0 # used for saving images

			for bname in self.bodies:
				if 'sensor' not in bname:
					sprite = pygame.image.load('figures/' + bname + '.png')
					self.sprites[bname] = sprite

		while not done:
			# animation code
			if animate:
				# quit conditions
				for event in pygame.event.get():
					if event.type==QUIT:
						pygame.quit()
						sys.exit(0)
					elif event.type == KEYDOWN and event.key == K_ESCAPE:
						pygame.quit()
						sys.exit(0)

				# draw screen, background and bodies
				screen.fill((255,255,255)) #background

				# draw red gate
				pygame.draw.rect(screen, pygame.color.THECOLORS['red'], [0, 150, 20, 300])  # 0, 200, 20 ,200

				# draw sliding track if track == True
				if track==True:
					pygame.draw.line(screen, (125, 45, 30), (144, 105), (144, 300), 3)  # left track
					pygame.draw.line(screen, (125, 45, 30), (156, 105), (156, 300), 3)  # right track

					pygame.draw.circle(screen, (125, 45, 30), (144, 105), 3, 3)  # top-left dot
					pygame.draw.circle(screen, (125, 45, 30), (156, 105), 3, 3)  # top-right dot
					pygame.draw.circle(screen, (125, 45, 30), (144, 300), 3, 3)  # bottom-left dot
					pygame.draw.circle(screen, (125, 45, 30), (156, 300), 3, 3)  # bottom-left dot

				for body in self.bodies:
					if 'sensor' not in body:
						self.update_sprite(body = self.bodies.get(body), sprite = self.sprites.get(body),screen = screen)

					# pygame.draw.rect(screen, pygame.color.THECOLORS['red'], [0,200,20,200]) #goal
					pygame.draw.rect(screen, pygame.color.THECOLORS['black'], [0,0,800,20]) #top wall
					pygame.draw.rect(screen, pygame.color.THECOLORS['black'], [0,580,800,20]) #bottom wall
					pygame.draw.rect(screen, pygame.color.THECOLORS['black'], [0,0,20,150])
					pygame.draw.rect(screen, pygame.color.THECOLORS['black'], [0,450,20,200])


				# Update the screen
				pygame.display.flip()
				pygame.display.update()
				clock.tick(100)

				if save:
					pygame.image.save(screen, 'figures/frames/animation'+'{:03}'.format(pic_count)+'.png')
					pic_count += 1

			
			# Add noise to the ball if noise is positive
			# Skip the computation if it is not
			if ball_noise != 0:
				self.apply_noise(obj=self.target_ball,step=collision_time,noise=ball_noise)

			# If there is a brick and we've reached the starting step, move the brick
			if self.brick != None and self.step == self.brick['step']:	
				body = self.brick['body']
				body.velocity = [x * self.speed for x in self.brick['vel']]

			# check completion
			done = self.end_clip()

			# Update the world itself: frame by frame advancement
			self.space.step(self.step_size)
			self.step += 1

		# Double check collisions are in temporal order and return
		assert all([self.events['collisions'][i]['step'] <= self.events['collisions'][i+1]['step'] for i in range(len(self.events['collisions']) - 1)])
		return self.events


############ Counterfactual manipulation procedures ###############
# define functions relevant for cf simulation
	
	# this function removes input object from pymunk physics world
	def remove(self,obj,step):
		if self.step == step:
			self.space.remove(self.shapes[obj]) #remove body from space 
			self.space.remove(self.bodies[obj]) #remove body from space 
			del self.bodies[obj] #remove body 
			del self.shapes[obj] #remove shape
			if obj in self.sprites:
				del self.sprites[obj] #remove sprite 

	############  apply noise to ball velocity vector ############  

	# use when there's a removed collision 
	# (represent uncertainty about where the ball would have gone)
	
	# This function generates step-wise velocity noise
	## apply gaussian noise to velocity at each step
	## step := which step do we start applying noise (the removed collision point)
	## arg noise := standard deviation of the angle of perturbation 
	## this function is recursive at each advancing step

	def apply_noise(self,obj,step,noise):
		if not noise == 0:
			b = self.bodies[obj]
			if self.step > step:
				x_vel = b.velocity[0]
				y_vel = b.velocity[1]
				# perturb = self.gaussian_noise()*noise
				perturb = np.random.normal(loc=0, scale=noise)
				cos_noise = np.cos(perturb*np.pi/180)
				sin_noise = np.sin(perturb*np.pi/180)
				x_vel_noise = x_vel * cos_noise - y_vel * sin_noise
				y_vel_noise = x_vel * sin_noise + y_vel * cos_noise
				b.velocity = x_vel_noise,y_vel_noise



	# This function returns a single noisy step of brick movement after applying gaussian noise
	## arg brick_noise is the spread of gaussian dist (in number of steps, e.g. brick_noise = 230
	## arg orig_step is the step of brick movement in actual world
	## arg collision_time is the step of ball collisions in actual world
	## arg step_max = 800 as per the World() setup
	## a valid noisy_step must be larger than step of collision & smaller than max_step = 800
	def noisy_step(self, brick_noise, collision_time, orig_step, step_max):  
	 	# bnoise = brick_noise
	 	noisy_step = orig_step + int(self.gaussian_noise()*brick_noise) 
	 	while True:
	 		noisy_step = orig_step + int(self.gaussian_noise()*brick_noise) 
	 		if noisy_step > collision_time: 
	 			break

	 	if noisy_step > step_max:
	 		noisy_step = step_max    # make sure the brick won't move 

	 	return noisy_step


###################### Load and run trials #######################


# Procedure to load trials
def load_trials(path):
	with open(path) as f:
		data_str = f.read()

	return json.loads(data_str)


# run actual trial to get step of actual collision and outcome value
def run_actual(trial, animate=False, save=False):
	balls = trial['balls']

	# run the actual world to collect step of collision and outcome
	w = World()
	if 'bricks' in trial:
		for brick in trial['bricks']:
			w.add_brick(brick['name'], brick['orientation'], brick['position'], brick['velocity'], brick['step'])
			w.add_sensor(brick['sensor_pos'], 'brick_sensor')

	for ball in balls:
		 w.add_ball(tuple(ball['position']), tuple(ball['velocity']), w.ball_size, ball['name'])

	# return list of events in actual world
	actual_events = w.simulate(animate=animate,track=True, ball_noise=0, collision_time=0, remove=False, save=save)

	return actual_events


# Repeatedly sample a gate start time from a gaussian centered around the actual
# start until we find a sample that is within the range of collision time and 
# clip length
def sample_gate_start(brick_noise, trial_num, collision_time, max_time):

	# In trials 0 and 2 the gate starts moving at step 280.
	# In trials 4 and 6 the gate starts moving at step 290.
	# For hypothetical simulations we center the gaussian generating start points for
	# the brick on the time point where it starts in the actual world.
	# For the trials where the brick does not move we center the gaussian on
	# the point where the brick starts moving in the analagous world where the brick
	# does move (0 and 1, 2 and 3, 4 and 5, 6 and 7 are all analagous pairs)
	if trial_num < 4:
		start_time = 280
	else:
		start_time = 290

	start_time = start_time/speed_multiplier

	bnoise = brick_noise/speed_multiplier
	hypothetical_start = np.ceil(np.random.normal(loc=start_time, scale=bnoise))

	if hypothetical_start > collision_time and hypothetical_start < max_time:
		return hypothetical_start

	else:
		return sample_gate_start(brick_noise, trial_num, collision_time, max_time)



# simulate ball B after ball A being removed for both cf and hp conditions

# There are two differing conditions in this experiment where we will want to do simulations with
# a removed cause ball

# In the counterfactual condition, we simulate as in other experiments.
# We remove the candidate cause and then apply noise to the movement of any ball that collided
# with the candidate, to represent the thinker's uncertainty in how the other ball would have
# moved after the collision.
# We model uncertainty as to exactly when the brick moves in the scenarios where the brick
# actually moves. In scenarios where the brick does not move, the model is certain that the
# brick would not have moved in the counterfactual.

# In the hypothetical condition, we simulate noise for the ball in the
# same way as we do in the counterfactual condition.
# Additionally, because the thinker did not view the gate's movement,
# we simulate uncertainty as to whether and when the gate will move. 
def run_removed(trial, animate=False, track=False, ball_noise=1.5, collision_time=0,
	brick_noise=0, cond='counterfactual', save=False, testing_output=False):       

	# world setup
	w = World()
	
	# args setup
	trial_num = trial['trial']
	balls = trial['balls']

	# add ball A and ball B
	for ball in balls:
		 w.add_ball(tuple(ball['position']), tuple(ball['velocity']), w.ball_size, ball['name'])


	for brick in trial['bricks']:
		w.add_brick(brick['name'], brick['orientation'], brick['position'], brick['velocity'], brick['step'])
		w.add_sensor(brick['sensor_pos'], 'brick_sensor')




	# If we are in the hypothetical condition, we need to account for the thinker's
	# uncertainty about if and when the brick would move. We modify the brick's starting
	# time in accordance with the procedure below
	if cond == 'hypothetical':

		# first determine whether or not the brick will move
		move = np.random.binomial(1, 0.5)

		# If the brick will not move, set the brick's movement time to after the clip finishes
		if not move:
			w.brick['step'] = w.step_max + 1

		# If the brick will move draw a random movement start time from a gaussian,
		# centered around the actual movement start time. Make sure that start time is 
		# after the collision of the balls and before the end of the clip
		# This reflects the thinker's uncertainty of when the brick would move given
		# that it would move
		else:
			hypothetical_start = sample_gate_start(brick_noise, trial_num, collision_time, w.step_max + 1)
			w.brick['step'] = hypothetical_start

	elif cond == 'counterfactual':
		# If we are in the counterfactual condition
		# check whether the gate moves in the actual world
		if w.brick['step'] < w.step_max:
			# If the gate moves in the actual world, add uncertainty to its start point
			# in the counterfactual just as we do in the hypothetical setting
			counterfactual_start = sample_gate_start(brick_noise, trial_num, collision_time, w.step_max + 1)
			w.brick['step'] = counterfactual_start

	else:
		raise Exception("Condition", cond, "not implemented")


	# Run the simulation with the cause removed and return the outcome
	events = w.simulate(animate=animate, track=track, ball_noise=ball_noise, collision_time=collision_time, remove=True, save=save)

	if not testing_output:
		return events['outcome']['outcome_coarse']

	elif cond == 'hypothetical':
		# Returns whether the block moved and it's starting time in addition to the outcome
		# Can use to test the distribution of movement and start times
		return {'outcome': events['outcome']['outcome_coarse'], 'movement': move, 'start_time': hypothetical_start if move else None}

	else:
		raise Exception('Condition must be hypothetical to return testing output')



# Produce a model judgement on a given trial using either hypothetical or counterfactual simulation
# Model returns the number of samples that went through the gate divided by total samples
def model_judgement(trial, condition, ball_noise=0.6, brick_noise=175, num_samples=100,
	track=False, animate=False):

	if condition not in {'counterfactual', 'hypothetical'}:
		raise Exception('Condition', condition, 'not implemented')

	events_actual = run_actual(trial, animate=animate)
	collision_time = events_actual['collisions'][0]['step']
	outcome = events_actual['outcome']['outcome_coarse']

	went_through = 0

	for _ in range(num_samples):

		sim_outcome = run_removed(trial, animate=animate, track=track, ball_noise=ball_noise, collision_time=collision_time, brick_noise=brick_noise, cond=condition, save=False, testing_output=False)

		went_through += sim_outcome

	return went_through/num_samples



# A simple test to check whether the binomial distribution comes out looking roughly right
def test_hypothetical_binomial_dist(trial):

	events = run_actual(trial, animate=False)
	col1_time = events['collisions'][0]['step']

	binomial_dist = {'move': 0, 'no move': 0}

	for i in range(10000):
		test = run_removed(trial, animate=False, track=True, ball_noise=1.5, collision_time=col1_time, brick_noise=0, cond='hypothetical', save=False, testing_output=True)
		move = test['movement']

		if move:
			binomial_dist['move'] += 1
		else:
			binomial_dist['no move'] += 1

	return binomial_dist


# A simple test to check whether the start time distribution looks roughly right
def test_hypothetical_normal_dist(trial, brick_noise=175):

	import matplotlib.pyplot as plt
	import seaborn as sns
	sns.set()

	events = run_actual(trial, animate=False)
	col1_time = events['collisions'][0]['step']

	start_samples = []
	num_successful = 0

	for i in range(10000):
		test = run_removed(trial, animate=False, track=True, ball_noise=1.5, collision_time=col1_time, brick_noise=brick_noise, cond='hypothetical', save=False, testing_output=True)
		samp = test['start_time']

		if samp != None:
			start_samples.append(samp)
			num_successful += 1

	print("Number of Moves:", num_successful)
	print("Samples:")
	print(start_samples)

	sns.distplot(start_samples)
	plt.show()