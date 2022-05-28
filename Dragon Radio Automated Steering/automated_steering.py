#!/usr/bin/env python3

import socket
import re
import time
from joblib import load
import numpy as np

TRAN_PI = "mmWavepi1"
RECV_PI = "mmWavepi2"

RALA_PORT = 8080
SP4T_PORT = 8081
MMWA_PORT = 8082

MMWA_CHAN = '1'
RALA_CHAN = '2'

ML_MODEL_FILE = "ML_models/forest_reg.joblib"

MMWAVE_BEAM_WIDTH = 10
MMWAVE_MIN = 40
MMWAVE_MAX = 320

NUM_RALA_STATES = 4

localradio = None

ml_model = None

# A list of all mmWave beam states as given by the parameters above
mmwave_states = [i * MMWAVE_BEAM_WIDTH for i in range(round(MMWAVE_MIN/MMWAVE_BEAM_WIDTH), round(MMWAVE_MAX/MMWAVE_BEAM_WIDTH))]
# The angles that correspond with the RALA states. Can be modified if the RALA positioning cannot be adjusted
mmWave_rala_angles_four_state = {1: (315, 45), 2: (45, 135), 3: (135, 225), 4: (225, 315)}

# This creates a dictionary of which RALA states correspond to which mmWave states. This should not be modified
mmwave_rala_map = {1: [], 2: [], 3: [], 4:[]}
for i in mmwave_states:
	for rala_state, angles in mmWave_rala_angles_four_state.items():
		if angles[0] > angles[1]:
			if i >= angles[0] or i < angles[1]:
				mmwave_rala_map[rala_state].append(i)
		else:
			if i >= angles[0] and i < angles[1]:
				mmwave_rala_map[rala_state].append(i)

# creates a basic internet socket
def create_socket(host, port):
	socket_conn = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	if re.search("\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}", host):
		ip_addr = host
	else:
		ip_addr = socket.gethostbyname(host)
	try:
		socket_conn.connect((ip_addr, port))
		return socket_conn
	except socket.error as err:
		print("Failed to establish socket connection")
	return None

# Encodes the string and sends it along the socket connection
def send_message(socket_conn, message):
	if(isinstance(message, str)):
		socket_conn.send(message.encode())
	else:
		socket_conn.send(str(message).encode())

# Rounds an angle to the closet valid mmWave state 
def get_closest_mmwave_angle(input_angle):
	global mmwave_states
	i = 0
	diff = abs(mmwave_states[i] - input_angle)
	prev_diff = 360
	while diff < prev_diff:
		i += 1
		prev_diff = diff
		diff = abs(mmwave_states[i] - input_angle)
	return (i, mmwave_states[i])	

# Used for the polar conversion
def get_quadrant(x,y):
	if x >= 0 and y >= 0:
		return 4
	elif x>= 0 and y <= 0:
		return 1
	elif x <= 0 and y <=0:
		return 2
	else:
		return 3
# Converts x/y output from the ML model to an angle
def to_polar(x_y):
	x = x_y[0]
	y = x_y[1]
	
	R = np.sqrt((x**2)+ (y**2))

	quadrant = get_quadrant(x,y)
	
	x = abs(x)
	y = abs(y)
	
	#print(quadrant)
	if quadrant == 1: 
		angle = np.rad2deg(np.arctan2(y,x))
	elif quadrant == 2: 
		angle = 180 - np.rad2deg(np.arctan2(y,x))
	elif quadrant == 3: 
		angle = 180 + np.rad2deg(np.arctan2(y,x))
	else: 
		angle = 360 - np.rad2deg(np.arctan2(y,x))
	
	#angle = np.arctan2(y,x)
	return R, angle

# loads the ML model from a file into a global variable
def load_ml_model(file_name):
	global ml_model
	ml_model = load(file_name)

# Get the estimated angle from the ML model given a list of RSSI values
def get_ml_aoa(input_rssi):
	global ml_model
	angle_arr = ml_model.predict([input_rssi])
	return to_polar(angle_arr[0])[1]

# Gets the current RSSI from DragonRadio
def get_rssi(node=1):
	return localradio.controller.send[node].long_rssi

# Gets an average RSSI measurement across multiple samples, each 1 second apart
def get_rssi_avg(node=1, samples=3):
	avg_rssi = 0
	for i in range(3):
		avg_rssi += localradio.controller.send[node].long_rssi
		time.sleep(1)
	return avg_rssi / samples;

# Gets the EVM/noise value from DragonRadio
def get_noise(node=1):
	return localradio.controller.send[node].long_evm

# Gets the RSSI of all the RALA states
def get_rala_rssi(socket_conn):
	rssi_vals = {}
	for i in range(1,NUM_RALA_STATES+1):
		send_message(socket_conn, i)
		time.sleep(1)
		rssi_vals[i] = get_rssi()
		print("State:", i, "-", rssi_vals[i])
	return rssi_vals

# Gets the strongest RALA state for the receiver
def get_strongest_rala_state(socket_conn):
	strongest = 0
	strongest_rssi = -90
	for i in range(1,NUM_RALA_STATES+1):
		send_message(socket_conn, i)
		time.sleep(1)
		state_rssi = get_rssi()
		print("State:", i, "-", state_rssi)
		if state_rssi > strongest_rssi:
			strongest = i
			strongest_rssi = state_rssi
	return strongest

# Gets the RSSI of all the mmWave states, exhaustively
def get_mmwave_rssi(socket_conn):
	rssi_vals = {}
	for i in mmwave_states:
		send_message(socket_conn, i)
		time.sleep(1)
		rssi_vals[i] = get_rssi()
	return rssi_vals

# Gets the strongest mmWave state for the receiver using an exhaustive search
def get_strongest_mmwave_state_exhaustive(socket_conn):
	strongest = 0
	strongest_rssi = -90
	delay = 8
	for i in mmwave_states:
		send_message(socket_conn, i)
		time.sleep(delay)
		delay = 1
		state_rssi = get_rssi()
		print("Angle:", i, "-", state_rssi)
		if state_rssi > strongest_rssi:
			strongest = i
			strongest_rssi = state_rssi
	return strongest

# Gets the strongest mmWave state for the receiver using a strongest-state search
def get_strongest_mmwave_state_baseline(socket_conn, strongest_rala):
	strongest = 0
	strongest_rssi = -90
	delay = 3
	for i in mmwave_rala_map[strongest_rala]:
		send_message(socket_conn, i)
		time.sleep(delay)
		delay = 1
		state_rssi = get_rssi()
		print("Angle:", i, "-", state_rssi)
		if(state_rssi > strongest_rssi):
			strongest = i
			strongest_rssi = state_rssi
	return strongest

# Gets the strongest mmWave state for the receiver using a DoA estimation search
def get_strongest_mmwave_state_informed(socket_conn, rala_rssi):
	global mmwave_states
	rala_rssi_list = list(rala_rssi.values())
	corrected_rssi_list = [i - 30 for i in rala_rssi_list]
	estimated_index, estimated_angle = get_closest_mmwave_angle(get_ml_aoa(corrected_rssi_list))
	send_message(socket_conn, estimated_angle)
	time.sleep(3)
	get_rssi()
	time.sleep(1)
	strongest_rssi = get_rssi()
	print("Estimated Angle:", estimated_angle, "-", strongest_rssi)
	for i in range(-1, 2, 2):
		side_angle = mmwave_states[estimated_index + i]
		send_message(socket_conn, side_angle)
		time.sleep(1)
		side_rssi = get_rssi()
		print("Angle", side_angle, "-", side_rssi)
		if side_rssi > strongest_rssi:
			j = 0
			while side_rssi > strongest_rssi:
				strongest_rssi = side_rssi
				strongest_angle = side_angle
				j += i
				side_angle = mmwave_states[estimated_index + i + j]
				send_message(socket_conn, side_angle)
				time.sleep(1)
				side_rssi = get_rssi()
				print("Angle", side_angle, "-", side_rssi)
			return strongest_angle
	return estimated_angle

# Keeps the mmWave antenna pointed at the strongest state until a 6 dB loss is measured
def maintain_connection(mmwa_sock, strong_state, delay=3):
	send_message(mmwa_sock, strong_state)
	time.sleep(delay)
	start_rssi = get_rssi()
	print("Connection RSSI =", start_rssi)
	prev_rssi = start_rssi
	print_counter = 0
	while(start_rssi - 6 < prev_rssi):
		prev_rssi = get_rssi()
		time.sleep(0.5)
		print_counter += 1
		if print_counter > 20:
			print("Current RSSI =", prev_rssi)
			print_counter = 0
	print("mmWave connection is broken")
	time.sleep(delay)

# Creates socket connections for all of the antenna controls
def create_antenna_sockets():
	rala_sock = create_socket(TRAN_PI, RALA_PORT)
	tran_sw_sock = create_socket(TRAN_PI, SP4T_PORT)
	recv_sw_sock = create_socket(RECV_PI, SP4T_PORT)
	mmwa_sock = create_socket(TRAN_PI, MMWA_PORT)

	return (rala_sock, tran_sw_sock, recv_sw_sock, mmwa_sock)

# Executes a strongest state search but does not maintain a conection
def run_simple_sweep(radio, loops=3):
	global localradio
	rala_sock, tran_sw_sock, recv_sw_sock, mmwa_sock = create_antenna_sockets()
	localradio = radio
	for i in range(loops):
		send_message(tran_sw_sock, RALA_CHAN)
		send_message(recv_sw_sock, RALA_CHAN)
		get_rssi() # clear the rolling average RSSI
		strong_state = get_strongest_rala_state(rala_sock)
		print("Strongest RALA State =", strong_state)
		send_message(tran_sw_sock, MMWA_CHAN)
		send_message(recv_sw_sock, MMWA_CHAN)
		time.sleep(1)
		get_rssi() # clear the rolling average RSSI
		strong_state = get_strongest_mmwave_state_baseline(mmwa_sock, strong_state)
		print("Strongest mmWave State =", strong_state)
		time.sleep(1)

# Executes a exhaustive search but does not maintain a conection
def run_exhaustive_sweep(radio, loops=3):
	global localradio
	rala_sock, tran_sw_sock, recv_sw_sock, mmwa_sock = create_antenna_sockets()
	localradio = radio
	for i in range(loops):
		send_message(tran_sw_sock, MMWA_CHAN)
		send_message(recv_sw_sock, MMWA_CHAN)
		get_rssi() # clear the rolling average RSSI
		strong_state = get_strongest_mmwave_state_exhaustive(mmwa_sock)
		print("Strongest mmWave State =", strong_state)
		time.sleep(1)

# Executes a DoA informed search but does not maintain a conection
def run_ml_sweep(radio, loops=3):
	global localradio
	rala_sock, tran_sw_sock, recv_sw_sock, mmwa_sock = create_antenna_sockets()
	localradio = radio
	load_ml_model(ML_MODEL_FILE)
	for i in range(loops):
		send_message(tran_sw_sock, RALA_CHAN)
		send_message(recv_sw_sock, RALA_CHAN)
		get_rssi() # clear the rolling average RSSI
		rala_rssi = get_rala_rssi(rala_sock)
		send_message(tran_sw_sock, MMWA_CHAN)
		send_message(recv_sw_sock, MMWA_CHAN)
		time.sleep(1)
		get_rssi() # clear the rolling average RSSI
		strong_state = get_strongest_mmwave_state_informed(mmwa_sock, rala_rssi)
		print("Strongest mmWave Angle =", strong_state)
		time.sleep(1)

# Executes a strongest state search and maintains the conection
def run_simple_connection(radio):
	global localradio
	rala_sock, tran_sw_sock, recv_sw_sock, mmwa_sock = create_antenna_sockets()
	localradio = radio
	while True:
		send_message(tran_sw_sock, RALA_CHAN)
		send_message(recv_sw_sock, RALA_CHAN)
		get_rssi() # clear the rolling average RSSI
		strong_state = get_strongest_rala_state(rala_sock)
		print("Strongest RALA State =", strong_state)
		send_message(tran_sw_sock, MMWA_CHAN)
		send_message(recv_sw_sock, MMWA_CHAN)
		time.sleep(1)
		get_rssi() # clear the rolling average RSSI
		strong_state = get_strongest_mmwave_state_baseline(mmwa_sock, strong_state)
		print("Strongest mmWave State =", strong_state)
		maintain_connection(mmwa_sock, strong_state)

# Executes a strongest state search and maintains the conection
def run_exhaustive_connection(radio):
	global localradio
	rala_sock, tran_sw_sock, recv_sw_sock, mmwa_sock = create_antenna_sockets()
	localradio = radio
	while True:
		send_message(tran_sw_sock, MMWA_CHAN)
		send_message(recv_sw_sock, MMWA_CHAN)
		get_rssi() # clear the rolling average RSSI
		strong_state = get_strongest_mmwave_state_exhaustive(mmwa_sock)
		print("Strongest mmWave State =", strong_state)
		maintain_connection(mmwa_sock, strong_state, 8)

# Executes a strongest state search and maintains the conection
def run_ml_connection(radio):
	global localradio
	rala_sock, tran_sw_sock, recv_sw_sock, mmwa_sock = create_antenna_sockets()
	localradio = radio
	load_ml_model(ML_MODEL_FILE)
	while True:
		send_message(tran_sw_sock, RALA_CHAN)
		send_message(recv_sw_sock, RALA_CHAN)
		get_rssi() # clear the rolling average RSSI
		rala_rssi = get_rala_rssi(rala_sock)
		send_message(tran_sw_sock, MMWA_CHAN)
		send_message(recv_sw_sock, MMWA_CHAN)
		time.sleep(1)
		get_rssi() # clear the rolling average RSSI
		strong_state = get_strongest_mmwave_state_informed(mmwa_sock, rala_rssi)
		print("Strongest mmWave Angle =", strong_state)
		maintain_connection(mmwa_sock, strong_state)

if __name__ == "__main__":
	print("This should not be executed standalone. This should be imported into the python interactive console within DragonRadio")