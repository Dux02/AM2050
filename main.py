
from src.Simulation import Simulation
from src.Output import AbstractOutput
import matplotlib.pyplot as plt

f = open('times.txt','a')
output = AbstractOutput()

for i in range(10):
    sim = Simulation(output, dt=0.05, cars=[1])
    sim.runNormalManyCarSim(carcap=100,timestep=1000)
    if ((i+1) % 1 == 0):
        print("I did loop",i+1)
    
print("I finished!")
plt.hist(output.data,25,alpha=0.7)
plt.axvline(180,color='r')
plt.xlabel("Time (s)")
plt.ylabel("Frequency")
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