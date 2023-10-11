# Car class
from typing import Union, Tuple
from numpy.random import normal
from random import choice
from numpy import sqrt, sign, exp

import pygame
pygame.mixer.init()
beeps = [pygame.mixer.Sound("media/beep"+str(i+1)+".wav") for i in range(10)]
V_MAX = 100 / 3.6  # 100 km/h
V_DESIRED = V_MAX * 1.2  # m/s
SIGMA = 2  # Standard deviation of the random initial velocities
GRINDSET = 0.1  # Standard dev. of random tick updates
GUSTAVO = 20  # Standard dev. of desired velocities (kph)
V_MIN = 60 / 3.6
CAR_LENGTH = 20
PIXEL_PER_M = 10


class Car:
    a_max = 1.44 
    b_max = 4.66 
    sqrt_ab = 2*sqrt(a_max*b_max)
    def __init__(self, x = 0,spawnframe=0):
        self.desiredvel: float = abs(normal(V_DESIRED, GUSTAVO/3.6))  # Absolute value necessary to avoid negatives
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
        self.neighbours = {'front': None, 'back': None, 'leftfront': None, 'leftback': None, 'rightfront': None, 'rightback': None}
    
    def update(self, dt: float):
        crash = False
        s = 5000

        # self.angerManagement(dt)
        self.checkPassing()

        infront = self.neighbours['front']
        if infront is not None:
            s = (infront.x - self.x - CAR_LENGTH)/PIXEL_PER_M  # s is in meters

            # Do we want to overtake?
            if self.wantToOvertake(infront, s):
                # Can we overtake?
                if self.canOvertake():
                    self.updateNeighboursOnOvertake()
                    return 1  # to let lane know we passed, to put self in another lane

        if self.canMerge():
            self.updateNeighboursOnMerge()
            return -1  # let lane know we merged, to put self in another lane

        crash = self.advancedSpeed(dt, infront)
        if crash:
            print(self.a, self.vel, self.x, self.s0)
            
        if self.vel < 0:
            self.vel = 0

        self.x += self.vel*dt*PIXEL_PER_M  # x is in pixels, vel is in m/s

        return 0

    def updateNeighboursOnOvertake(self):
        """Once we've overtaken, we need to update our neighbors"""
        self.neighbours['rightfront'] = self.neighbours['front']
        self.neighbours['rightback'] = self.neighbours['back']
        self.neighbours['front'] = self.neighbours['leftfront']
        self.neighbours['back'] = self.neighbours['leftback']

        # leftfront and leftback are more complicated!
        lf = self.neighbours['leftfront']
        if lf.neighbours['leftback'] is not None and lf.neighbours['leftback'].x > self.x:
            self.neighbours['leftfront'] = lf.neighbours['leftback']
        elif lf.neighbours['leftfront'] is not None:
            self.neighbours['leftfront'] = lf.neighbours['leftfront']
        else:
            self.neighbours['leftfront'] = None

        lb = self.neighbours['leftback']
        if lb.neighbours['leftfront'] is not None and lb.neighbours['leftfront'].x < self.x:
            self.neighbours['leftback'] = lb.neighbours['leftfront']
        elif lb.neighbours['leftback'] is not None:
            self.neighbours['leftback'] = lb.neighbours['leftback']
        else:
            self.neighbours['leftfront'] = None

    def updateNeighboursOnMerge(self):
        self.neighbours['leftfront'] = self.neighbours['front']
        self.neighbours['leftback'] = self.neighbours['back']
        self.neighbours['front'] = self.neighbours['rightfront']
        self.neighbours['back'] = self.neighbours['rightback']

        # Again, rightfront and rightback are more complicated
        # and I dont feel like typing it out rn :D

    def canOvertake(self):
        lf, lb = self.neighbours['leftfront'], self.neighbours['leftback']
        for othercar in [lf, lb]:
            if othercar is not None:
                if self.x > othercar.x:
                    delta_v = max(0, othercar.vel - self.vel)
                else:
                    delta_v = max(0, self.vel - othercar.vel)
                SafetyDist = 4 * delta_v * PIXEL_PER_M + 2 * PIXEL_PER_M
                if self.x - CAR_LENGTH - SafetyDist < othercar.x < self.x + CAR_LENGTH + SafetyDist:
                    return False
        if lb is not None and self.x - CAR_LENGTH - lb.x < 1.5 * lb.desiredDist(self) * PIXEL_PER_M:
            return False

        return True

    def canMerge(self):
        """Check whether we can merge depending on neighbours"""
        rf, rb = self.neighbours['leftfront'], self.neighbours['rightfront']
        for othercar in [rf, rb]:
            if othercar is not None:
                if self.x > othercar.x:
                    delta_v = max(0, othercar.vel - self.vel)
                else:
                    delta_v = max(0, self.vel - othercar.vel)
                SafetyDist = 4 * delta_v * PIXEL_PER_M + 2 * PIXEL_PER_M
                if self.x - CAR_LENGTH - SafetyDist < othercar.x < self.x + CAR_LENGTH + SafetyDist:
                    return False
        if rf is not None and rf.x - CAR_LENGTH - self.x < 1.5 * max(self.desiredDist(rf), 0) * PIXEL_PER_M:
            return False

        return True

    def checkPassing(self):
        """Check whether we've passed anyone and update neighbours"""
        # (should we then also check if someone passed us?, if so we might only
        # have to check every 2 lanes or something like that)
        if self.neighbours['leftfront'].x < self.x:
            # Others' new neighbours
            self.neighbours['leftfront'].neighbours['rightfront'] = self
            self.neighbours['leftfront'].neighbours['rightback'] = self.neighbours['back']

            # Our new neighbors:
            self.neighbours['leftback'] = self.neighbours['leftfront']
            self.neighbours['leftfront'] = self.neighbours['leftfront'].neighbours['front']  # could be None
        if self.neighbours['rightfront'].x < self.x:
            # Others' new neighbours
            self.neighbours['rightfront'].neighbours['leftfront'] = self
            self.neighbours['rightfront'].neighbours['leftback'] = self.neighbours['back']

            # Our new neighbors:
            self.neighbours['rightback'] = self.neighbours['rightfront']
            self.neighbours['rightfront'] = self.neighbours['rightfront'].neighbours['front']  # could be None

    def wantToOvertake(self, infront: 'Car', s: float):
        """Checks whether we are in the mood to pass this grandma in front"""
        return s < 1.2 * self.s0 and self.vel < self.desiredvel and self.desiredvel > infront.vel

    def angerManagement(self, dt):
        """On matters of getting angry or not"""
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
            In the limiting case delta_v <= 0, the desired distance is the jam distance.
            In the limiting case delta_v = self.vel, we find the distance scales quadratically with speed.
        '''
        delta_v = 0
        factor = 1
        if (infront is not None):
            delta_v = self.vel - infront.vel
            if (delta_v < 4):
                factor = exp(delta_v-4)  # when delta_v is small

        return 2 + (self.vel*1.6 + self.vel*delta_v/self.sqrt_ab)*factor
        # return max(2, 2 + self.vel*1.6 + self.vel*delta_v/self.sqrt_ab)  # linear correction (easier to explain)

    def updateSqrtAB(self):
        self.sqrt_ab = 2*sqrt(self.a_max, self.b_max)
            
    # Alexander's whimsical beeping            
    def beep(self,timestamp: float, infront: 'Car', windowspecs: Tuple[int,int] = (0,1)):
        """
        The function plays a random beep sound if the car in front is too slow and the car is on the screen.
        
        :param timestamp: The timestamp parameter is a float value representing the current second (frame*dt). It is
        used to determine when to trigger the beep sound
        :type timestamp: float
        :param windowspecs: The `windowspecs` parameter is a tuple that specifies the range of x-values
        within which the beep sound should be played. It has two elements: `windowspecs[0]` represents
        the lower bound of the range, and `windowspecs[1]` represents the upper bound.
        :type windowspecs: Tuple[int,int]
        """
        
        if (timestamp % 1 == 0 and infront.vel < 0.5*self.desiredvel and windowspecs[0] < self.x < windowspecs[1]):
                beep = choice(beeps)
                pygame.mixer.Sound.play(beep)
        return








