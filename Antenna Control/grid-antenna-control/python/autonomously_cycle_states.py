import socket, sys, time
import wiringpi


def get_state():
    wiringpi.wiringPiSetupGpio()  # Set GPIO numbering scheme

    # Define rala pins and states
    rala_pins = [26, 20, 19, 16]
    rala_states = [[1, 1, 1, 1],  # Omnidirectional
                   [1, 0, 0, 0],  # Direction 1
                   [0, 1, 0, 0],  # Direction 2
                   [0, 0, 1, 0],  # Direction 3
                   [0, 0, 0, 1],  # Direction 4
                   [0, 0, 0, 0]]  # Off]

    # Define RFSwitch pins and states
    rfswitch_pins = [17, 27]
    rfswitch_states = [[0, 0],  # RFPort 1
                       [1, 0],  # RFPort 2
                       [0, 1],  # RFPort 3
                       [1, 1]]  # RFPort 4

    # Get state for RALA
    gpio = [wiringpi.digitalRead(pin) for pin in rala_pins]
    for i in range(len(rala_states)):
        if rala_states[i] == gpio:
            print("RALA state: " + str(i))

    # Get state for RFSwitch
    gpio = [wiringpi.digitalRead(pin) for pin in rfswitch_pins]
    for i in range(len(rfswitch_states)):
        if rfswitch_states[i] == gpio:
            print("RFSwitch state: " + str(i + 1))

#def switch_states():


# Error check input arguments, if none assume localhost testing
if len(sys.argv) == 1:
    destinationIP = "localhost"
    port = 8080
    state = '0' # By default send omni configuration
elif len(sys.argv) == 4:
    destinationIP = sys.argv[1]
    port = int(sys.argv[2])
    state = sys.argv[3]
else:
    print("USAGE: 'python3 file.py destinationIP port message'")
    print("ERROR not enough input arguments.")
    exit()
# Send the socket command
while True:
    try:
        clientsocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        clientsocket.connect((destinationIP, port))
        for i in range(5):
            state = i
            clientsocket.send(str(state).encode())
            time.sleep(1)
            get_state()
            time.sleep(10)
        #state = input("Desired state? [0 -4]: ")
    except KeyboardInterrupt:
        print("\nAdios")
        exit()
