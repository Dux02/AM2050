from src.Simulation import Simulation
from src.Output import AbstractOutput
import numpy as np
import pandas as pd


def moving_average(a, n=3):
    ret = np.cumsum(a, dtype=float)
    ret[n:] = ret[n:] - ret[:-n]
    return ret[n - 1:] / n


ps, average_times = [], []
f = open('times.txt', 'a')
DT = 0.005  # DT=0.2 gives crashes (at prob=1), even for one lane!
LANES = 3


saving_data = []
# plt.figure()
for i in range(1, LANES+1):
    # Simulate
    output = AbstractOutput()
    sim = Simulation(output, dt=DT, lanes=LANES, cars=np.ones(LANES, dtype=int)*0)
    prob = 10
    sim.manyCarsPP(p=prob, carcap=2000)

    # Data gathering
    saving_data.append(output.data)
    """
    ps.append(prob)
    average_times.append(np.mean(output.data[100:]))  # append av time and ignore first 100 cars
    """
    # plt.plot(moving_average(output.data, 50), label=str(i)+" lanes")

    if (i % 1 == 0):
        print("I did loop", i)
"""
plt.legend()
plt.xlabel("Car Index")
plt.ylabel("Time taken")
plt.show()
"""
print(saving_data)
df = pd.DataFrame(np.array(saving_data))
df.to_csv('data.csv', index=False)

print('hij denk hij is la primo maar hij heeft')
"""
print("I finished!")
#print(np.max(output.data))
if (len(average_times) == 1 and False):
    plt.plot(output.data[100:])
else:
    plt.plot(ps, average_times)
plt.show()


plt.plot(moving_average(output.data, 10))
#plt.hist(output.data,25,alpha=0.7)
plt.axvline(5000*3.6/120,color='r')
plt.xlabel("Time (s)")
plt.ylabel("Count")
plt.show()
"""

'''
=========================================================
PSEUDOCODE BELOW
=========================================================
class Car:
    def __init__(self):
        self.weight = 0 #Measure of how good it can accelerate/brake
        self.vel = 0
        self.x, self.y = 0 #y is "basically only which rijstrook
       
    def braking(weight, infront):
       
    def accel(infront?):
        self.vel =      
    
    def update(self):
        if noCarInFront:
            #vroom
        elif inhaalMogelijk:
            inhaal
        else:
            brakeTill2SecRule

class Lane:
    def __init__(self):
        self.maxspeed = 100/3.6
        self.spits = False
        self.tunnel = False
        #Angle of incline somehow?
    
    


#Road conditions? - e.g. wet
class Simulation:
    def __init__(self):
        self.lanes = []
        
'''