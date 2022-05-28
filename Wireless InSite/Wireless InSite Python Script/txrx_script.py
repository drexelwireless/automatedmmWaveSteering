import random
import os
import math

path = r'C:\Users\kevin\Documents\mmWave Simulation'

if os.path.exists(path) == False:
    os.mkdir(path)

txrx_path = os.path.join(path, 'test.txrx')

z = 2.000000000000000
tx_x = 0.0
tx_y = 0.0

format_z = "{:.15f}".format(z)

with open(txrx_path, "r") as f:
    contents = f.readlines()

def dist(x1, x2, y1, y2):
    return math.sqrt(math.pow((x2 - x1), 2) + math.pow((y2 - y1), 2))

for i in range(6000):
    x = random.uniform(-6.0, 6.0)
    y = random.uniform(-6.0, 6.0)
    z = float(2.000000000000000)
    
    for j in range(i):
        if abs(dist(tx_x, x, tx_y, y)) < 1.0:
            x = random.uniform(-6.0, 6.0)
            y = random.uniform(-6.0, 6.0)
            
        if abs(dist(tx_x, x, tx_y, y)) > 6.0:
            x = random.uniform(-6.0, 6.0)
            y = random.uniform(-6.0, 6.0)
    
    #print(str(x) + ' ' + str(y) + ' ' + str(z))
    contents.insert(24 + i, str(x) + ' ' + str(y) + ' ' + format_z + '\n')

with open(txrx_path, "w") as f:
    contents = "".join(contents)
    f.write(contents)