#Car class
from numpy.random import normal
V_MAX = 100 / 3.6 #100 km/h
SIGMA = 2 #Standard deviation of the random initial velocities
GRINDSET = 0.1 #Standard dev. of random tick updates

class Car:
    def __init__(self, x = 0):
        self.vel: float = abs(normal(V_MAX,SIGMA))  #random velocity protocol. Can be removed afterwards
                                                    #Absolute value necessary to avoid negatives (even if unlikely!)
        self.x: float = x

    
    #Rudimentary first update for moving cars
    def update(self,dt: float, infront = None, ):
        self.x += self.vel*dt
        if(infront is not None):
            if(infront.x - self.x < (2*self.vel)):
                self.vel -= 0.1
            else:
                self.normalSpeed(GRINDSET) #Comment out if need
        else:
            self.normalSpeed(GRINDSET)
        
    def normalSpeed(self,sigma: float):
        prev_vel = self.vel
        self.vel = normal(prev_vel, sigma)
        while(self.vel <= (60/3.6)):
            self.vel = normal(prev_vel, sigma)
            
       




