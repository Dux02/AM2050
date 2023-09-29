
from src.Simulation import Simulation
from src.Output import AbstractOutput
import matplotlib.pyplot as plt
import numpy as np

def moving_average(a, n=3):
    ret = np.cumsum(a, dtype=float)
    ret[n:] = ret[n:] - ret[:-n]
    return ret[n - 1:] / n

f = open('times.txt','a')
output = AbstractOutput()
DT=0.1
LANES = 5
for i in range(1):
    sim = Simulation(output, dt=DT,lanes=LANES, cars=np.ones(LANES,dtype=int)*1)
    sim.manyCarsPP(p=0.2,carcap=500)
    if ((i+1) % 1 == 0):
        print("I did loop",i+1)
    
print("I finished!")
#print(np.max(output.data))
#plt.plot(moving_average(output.data,10))
plt.hist(output.data,25,alpha=0.7)
plt.axvline(5000*3.6/120,color='r')
plt.xlabel("Time (s)")
plt.ylabel("Count")
plt.show()



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