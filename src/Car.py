#Car class
from typing import Union
from numpy.random import normal
from numpy import sqrt, sign
V_MAX = 100 / 3.6 #100 km/h
V_DESIRED = V_MAX * 1.2
SIGMA = 2 #Standard deviation of the random initial velocities
GRINDSET = 0.1 #Standard dev. of random tick updates
GUSTAVO = 10 #Standard dev. of desired velocities
V_MIN = 60 / 3.6
CAR_LENGTH = 20
PIXEL_PER_M = 10


class Car:
    a_max = 1.44 
    b_max = 4.66 
    sqrt_ab = 2*sqrt(a_max*b_max)
    def __init__(self, x = 0,spawnframe=0):
        self.desiredvel: float = abs(normal(V_DESIRED, GUSTAVO/3.6))  # Absolute value necessary to avoid negatives (even if unlikely!)
        if (self.desiredvel < V_MIN):
            self.desiredvel = V_MIN
        self.vel: float = abs(normal(self.desiredvel,SIGMA))
        self.x: float = x
        self.a: float = 0
        self.overtaking = 0
        self.spawnframe = spawnframe
        self.s0 = 0
        self.waited = 0
        self.pissed = False
        self.prepissedvel = self.desiredvel
        self.debug = False
    
    def update(self,dt: float, infront: Union['Car', None] = None):
        crash = False
        
        s = 5000
        """
        # On matters of getting angry or not
        if (self.vel < self.desiredvel*0.8 and not self.pissed):
            self.waited += 0  # We're waiting
        elif (self.pissed):
            self.waited += 1  # Keep track of when our eruption was
            self.desiredvel += 0.5*dt  # I'm gonna accelerate until my grandma keels over

        if (self.waited*dt > 60 and not self.pissed):  # It's been too long, I've had enough
            self.waited = 0
            self.pissed = True
            self.desiredvel *= 1.5
            self.a_max *= 10  # With the power of pure rage we can survive at least a g-force
        elif (self.pissed and self.waited*dt > 10 and self.vel > (self.desiredvel / 1.5)):
            self.waited = 0
            self.pissed = False
            self.desiredvel = self.prepissedvel
            self.a_max /= 10
        """
        
        if (infront is not None):
            s = (infront.x - self.x - CAR_LENGTH)/PIXEL_PER_M  # s is in meters
            delta_v = self.vel - infront.vel
            # Do we want to overtake?
            # OVTF = 1.5, the factor time s0. Note this is similar to the previous code w/ a min. 3 second headway instead.
            if (s < 1.5 * self.s0 and self.vel < self.desiredvel and self.desiredvel > infront.vel):
                # Can we overtake?
                self.overtaking = 1
                
        
        # Do we want to merge?
        if (self.vel > 0.8*self.desiredvel):
            self.overtaking = -1
        
        crash = self.advancedSpeed(dt, infront)
        if (crash):
            print(self.a, self.vel, self.x, self.s0)
            
        if (self.vel < 0):
            self.vel = 0
        self.x += self.vel*dt*PIXEL_PER_M  # x is in pixels, vel is in m/s

    def normalSpeed(self,sigma: float):
        prev_vel = self.vel
        self.vel = normal(prev_vel, sigma)
        while(self.vel <= (60/3.6)):
            self.vel = normal(prev_vel, sigma)

    def advancedSpeed(self, dt: float, infront: Union['Car', None] = None) -> bool:
        ''' Calculate the new speed and acceleration of the car on the basis of the IDM model.
            Returns false if the car did not crash with the car infront, otherwise true.
            Uses distance between self and infront.
        '''
        s = 5000
        alpha = 0
        crashed = False
        if infront is not None:
            s = (infront.x - self.x - CAR_LENGTH)/PIXEL_PER_M  # s is in meters
            
            if s <= 0.1: # If they're too close, avoid division by 0!
                s = 10 # Must be bigger than the jam distance to avoid acceleration -> -inf!
                self.vel = 0
                crashed = True
        
        self.s0 = self.desiredDist(infront)
        alpha = self.s0 / s
        self.a = self.a_max * (1 - (self.vel/self.desiredvel)**4 - alpha**2)
        self.vel += self.a*dt
        if (self.a == float('-inf')): #Presumably, we've crashed
            print("Crisis dienst!!") #This should ideally *never* get triggered!
            crashed = True
            self.a = self.a_max
        return crashed
    
    def desiredDist(self, infront: Union['Car', None] = None) -> float:
        ''' Returns the desired distance of the car based on the car in front of it, in meters.
            This follows the Intelligent Driver Model (IDM), with a reaction time of 1.6 seconds,
            a jam distance of 2 meters, and a difference in speed dependent term.
            In the limiting case delta_v = 0, the desired distance is the safe braking distance.
            In the limiting case delta_v = self.vel, we find the distance scales quadratically with speed.
        '''
        delta_v = 0
        if (infront is not None):
            delta_v = self.vel - infront.vel
        
        return self.vel*1.6 + 2 + self.vel*delta_v/self.sqrt_ab 

    def updateSqrtAB(self):
        self.sqrt_ab = 2*sqrt(self.a_max, self.b_max)
            
       




