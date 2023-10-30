from numpy.random import f
from src.Simulation import Simulation, DataSimulation
from src.VisualSimulation import VisualSimulation
from src.Output import AbstractOutput, FileOutput
import numpy as np
import pandas as pd
import pickle


def moving_average(a, n=3):
    ret = np.cumsum(a, dtype=float)
    ret[n:] = ret[n:] - ret[:-n]
    return ret[n - 1:] / n


ps, average_times = [], []
DT = 0.3  # DT=0.2 gives crashes (at prob=1), even for one lane!
LANES = 5
CARCAP = 50000
ITERS = 20


saving_data = []
# plt.figure()
for i in range(ITERS):
    # Simulate
    # For data simulation
    #f = open('./data/'+str(np.datetime64('today'))+'-Lanes ' + str(i),'wb')
    #output = FileOutput(f)

    # For visualisation
    output = AbstractOutput()
    sim = VisualSimulation(output, dt=DT, lanes=LANES, cars=np.ones(LANES, dtype=int)*1)
    if (i == -1):
        VisualSimulation.renderer.kill()
    prob = 0.1 + i*0.1
    prob = 1
    sim.manyCarsPP(p=prob, carcap=CARCAP)

    # Data gathering
    saving_data.append(output.data)
    """
    ps.append(prob)
    average_times.append(np.mean(output.data[100:]))  # append av time and ignore first 100 cars
    """
    # plt.plot(moving_average(output.data, 50), label=str(i)+" lanes")
    # f.close()
    if (i % 1 == 0):
        print("I did loop", i)
"""
plt.legend()
plt.xlabel("Car Index")
plt.ylabel("Time taken")
plt.show()
"""
#print(saving_data)
f = open('./data/'+str(np.datetime64('today'))+'- p variation, carcap ' +str(CARCAP) + ', iters ' + str(ITERS), 'wb')
pickle.dump(saving_data,f)
f.close()
#df = pd.DataFrame(np.array(saving_data))
#df.to_csv('data.csv', index=False)

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