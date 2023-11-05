from numpy.random import f
from src.Simulation import Simulation, DataSimulation
from src.VisualSimulation import VisualSimulation
from src.Output import AbstractOutput, FileOutput
from src.Car import (GUSTAVO, SPEEDCAMERA, HEADWAYTIME, setHEADWAYTIME, MINIMUMDISTANCEFACTOR, DESIREDVELFACTOR,
                     VDESIREDEXPONENT, PERSONALFACTOR, XENOFACTOR, LANESTD, MERGEFACTOR, V_DESIRED, V_MIN)
from src.Lane import DYNAMIC, LANELENGTH, SPAWNSAFETYSECONDS
import numpy as np
import pickle
import random


def moving_average(a, n=3):
    ret = np.cumsum(a, dtype=float)
    ret[n:] = ret[n:] - ret[:-n]
    return ret[n - 1:] / n


ps, average_times = [], []
DT = 0.2
DURATION = 500
ITERS = 1

saving_data = []

for i in range(ITERS):
    output = AbstractOutput()
    LANES = 5
    PROB = 0.9
    sim = VisualSimulation(output, dt=DT, lanes=LANES, cars=np.ones(LANES, dtype=int)*1, pretty=False)
    if i == 0:
        VisualSimulation.renderer.kill()

    sim.manyCarsTimedPP(PROB, time=DURATION)

    key = dict()
    key["data"] = output.data
    key["carsgenerated"] = sim.carsgenerated
    key["gustavo"] = GUSTAVO
    key["duration"] = DURATION
    key["p"] = PROB
    key["iterations"] = ITERS
    key["lanes"] = LANES
    key["dt"] = DT
    key["headway"] = HEADWAYTIME
    key["dynamic"] = DYNAMIC
    key["speedcamera"] = SPEEDCAMERA
    key["lanelength"] = LANELENGTH
    key["minimumdistancefactor"] = MINIMUMDISTANCEFACTOR
    key["desiredvelfactor"] = DESIREDVELFACTOR
    key["vdesiredexponent"] = VDESIREDEXPONENT
    key["mergefactor"] = MERGEFACTOR
    key["xenofactor"] = XENOFACTOR
    key["personalfactor"] = PERSONALFACTOR
    key["vdesired"] = V_DESIRED
    key["vmin"] = V_MIN
    key["spawnsafetyseconds"] = SPAWNSAFETYSECONDS

    string = ("./data/iters" + str(ITERS) + ",p" + str(PROB) + ",lanes" + str(LANES) + ",dt" + str(DT) + ",dur" + str(DURATION) + " "
              + ''.join(random.choices("abcdefghijklmnopqrstuvwxyz1234567890", k=8)))

    f = open(string, 'wb')
    pickle.dump(key, f, protocol=pickle.HIGHEST_PROTOCOL)
    f.close()

    print("Finished", i+1)




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
