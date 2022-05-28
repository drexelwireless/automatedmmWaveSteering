#!/usr/bin/python3
# This python code rotates the direction of the mmWave horn antenna
# to a specific angle given from the DoA estimation algorithm.

# Pseudocode
# 1. Creates socket server and set timeout
# 2. Listens for connections
# 3. On connection, change direction of motor (Arduino code)
# 4. Add print statement
# 5. Close connection

################################################
#################### PART 3 ####################
################################################
import time
import wiringpi
wiringpi.wiringPiSetupGpio()  # Set GPIO numbering scheme

# Define motor pins and variables
dirPin = 5 
stepPin = 6
stepsPerRevolution = 1036
degreesPerStep = 0.347490347
currAngle = 180.0
minAngle = 45.0
maxAngle = 315.0

wiringpi.pinMode(5,1)  # Sets GPIO 5 to output
wiringpi.pinMode(6,1)  # Sets GPIO 6 to output

def turn_mmWave(inputAngle):
	inputAngle = angle_constraint(inputAngle)
	turn_to_angle(inputAngle)
	time.sleep(0.2)

def angle_constraint(angle):
	if angle > maxAngle:
		angle = maxAngle
	elif angle < minAngle:
		angle = minAngle
	return angle

def turn_to_angle(angle):
	global currAngle
	angleDiff = angle - currAngle
	stepsToTake = convert_angle_to_steps(angleDiff)
	if stepsToTake < 0:
		step_ccw(-stepsToTake)
	else:
		step_cw(stepsToTake)
	currAngle = angle

def convert_angle_to_steps(angle):
	return round(angle/degreesPerStep)

def step_cw(steps):
	for i in range(steps-1):
		step_motor(True)

def step_ccw(steps):
	for i in range(steps-1):
		step_motor(False)	

def step_motor(dir):
	if dir == True:
		wiringpi.digitalWrite(dirPin, 1)
	else:
		wiringpi.digitalWrite(dirPin, 0)
	wiringpi.digitalWrite(stepPin, 1)
	time.sleep(0.005)
	wiringpi.digitalWrite(stepPin, 0) 
	time.sleep(0.005)


################################################
#################### PARTS 1,2,4 ####################
################################################
import socket
import threading

def run_connection_thread(conn):
	try:
		data = conn.recv(1024).decode() # receive data stream. it won't accept data packet greater than 1024 bytes 
		while len(data) > 0:
			print("Received:", data)
			turn_mmWave(int(data))
			conn.send(str("Done turning to: " + data).encode())
			data = conn.recv(1024).decode()
		conn.close() # close connection
	except ConnectionResetError:
		conn.close()


def server_socket():
	host = '' #socket.gethostbyname(socket.gethostname())
	port = 8082

	server_socket = socket.socket()  # get instance
	server_socket.bind((host, port))  # bind host address and port together
	#server_socket.settimeout(15)
	server_socket.listen(5) # configure how many client the server can listen simultaneously
	print("Started mmWave stepper control (%s, %d)" % (host, port))
	while True:
		#print("Waiting for another connection")
		conn, address = server_socket.accept()  # accept new connection
		print("Accepted a connection")
		new_thread = threading.Thread(target=run_connection_thread, args=(conn,))
		new_thread.start()

if __name__ == "__main__":
	server_socket()
 
