# Car class
from typing import Union, Tuple
from numpy.random import normal
from random import choice
from numpy import sqrt, sign, exp
from numbers import Number

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

class Neighbours:
    def __init__(self):
        self.back: Union[Car, None] = None
        self.front: Union[Car, None] = None
        self.leftfront: Union[Car, None] = None
        self.rightfront: Union[Car, None] = None


def leastInFront(car: 'Car', start_iter: 'Car') -> 'Car':
    """Given a car, and another car whose x coordinate is larger than the first
        go down the chain of backs until we have the car who's behind is behind us, or None, and return it

    Args:
        car (Car): Car for which to reference our comparison
        start_iter (Car): Must satisfy start_iter.x > car.x. We start our iteration on this car

    Returns:
        Car: The car whose 'back' is behind the argument 'car', or None.
    """
    carToBe = start_iter
    despicable = False
    while (carToBe.x >= car.x and not despicable):
        if (carToBe.neighbours.back is None):
            despicable = True
        else:
            carToBe = carToBe.neighbours.back
    if (despicable):
        return carToBe
    else:
        return carToBe.neighbours.front

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
        self.neighbours = Neighbours()
    
    def update(self, dt: float):
        crash = False
        s = 5000

        # self.angerManagement(dt)
        self.validateNeighbours()

        infront = self.neighbours.front
        if infront is not None: # TODO: this should never be False, so we could remove this?
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
        self.neighbours.front.neighbours.back = self.neighbours.back # Our old front's back is our old back
        if (self.neighbours.back is not None):
            self.neighbours.back.neighbours.front = self.neighbours.front # And our old back's front is our old front
        self.neighbours.rightfront = self.neighbours.front # We went left (overtook) so our rf is our old front
        self.neighbours.front = self.neighbours.leftfront # And our front is our old lf
        self.neighbours.back = self.neighbours.front.neighbours.back # We pick up the back 
        self.neighbours.front.neighbours.back = self # And set the new back in
        if (self.neighbours.front.neighbours.leftfront is not None): # Last but not least, get our spanking new leftfront
            self.neighbours.leftfront = leastInFront(self,self.neighbours.front.neighbours.leftfront)
        else:
            self.neighbours.leftfront = None

    def updateNeighboursOnMerge(self):
        self.neighbours.front.neighbours.back = self.neighbours.back # Our old front's back is our old back
        if (self.neighbours.back is not None):
            self.neighbours.back.neighbours.front = self.neighbours.front # And our old back's front is our old front
        self.neighbours.leftfront = self.neighbours.front # We went right (merge) so our lf is our old front
        self.neighbours.front = self.neighbours.rightfront # And our front is our old rf
        self.neighbours.back = self.neighbours.front.neighbours.back # We pick up the back 
        self.neighbours.front.neighbours.back = self # And set the new back in
        if (self.neighbours.front.neighbours.rightfront is not None): # Last but not least, get our spanking new leftfront
            self.neighbours.rightfront = leastInFront(self,self.neighbours.front.neighbours.rightfront)
        else:
            self.neighbours.rightfront = None

    def canOvertake(self):
        lf = self.neighbours.leftfront
        if (lf is None): #There is no lane to our left
            return False
        delta_v = max(0,self.vel - lf.vel)
        SafetyDist = (4 * delta_v + 2) * PIXEL_PER_M
        if self.inDist(SafetyDist,lf):
            return False
        
        lb = lf.neighbours.back
        if (lb is None):
            return True
        delta_v = max(0,lb.vel - self.vel)
        SafetyDist = (4 * delta_v + 2) * PIXEL_PER_M
        if self.inDist(SafetyDist,lb) or self.inDist((1.5 * lb.desiredDist(self) * PIXEL_PER_M,0),lb):
            return False

        return True

    
    def canMerge(self):
        """Check whether we can merge depending on neighbours"""
        rf = self.neighbours.rightfront
        if (rf is None): #There is no lane to our left
            return False
        delta_v = max(0,self.vel - rf.vel)
        SafetyDist = (4 * delta_v + 2) * PIXEL_PER_M
        if self.inDist(SafetyDist,rf) or self.inDist((0,1.5*self.desiredDist(rf)*PIXEL_PER_M),rf):
            return False
        rb = rf.neighbours.back
        if (rb is None):
            return True
        delta_v = max(0,rb.vel - self.vel)
        SafetyDist = (4 * delta_v + 2) * PIXEL_PER_M
        if self.inDist(SafetyDist,rb):
            return False
        return True

    def validateNeighbours(self):
        """Check whether we've passed anyone and update neighbours"""
        # (should we then also check if someone passed us?, if so we might only
        # have to check every 2 lanes or something like that)
        if (self.neighbours.leftfront is not None):
            self.neighbours.leftfront = leastInFront(self,self.neighbours.leftfront)
        
        if (self.neighbours.rightfront is not None):
            self.neighbours.rightfront = leastInFront(self,self.neighbours.rightfront)
        
    def wantToOvertake(self, infront: 'Car', s: float):
        """Checks whether we are in the mood to pass this grandma in front"""
        return s < 1.2 * self.s0 and self.vel < self.desiredvel and self.desiredvel > infront.vel

    def endOfTheRoad(self,back:'Car'):
        """ When we reached the end of the road, we pretend we're far far away so any cars 
        linked to us by neighbourness can ignore us
        """
        self.x = float('inf')
        self.neighbours.back = back
            
    
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
        
    def inDist(self, dist: Union[float, Tuple[float,float]], othercar: 'Car') -> bool:
        """The function checks if another car is within a certain distance range from the current car.

        Args:
            dist (float | (float, float)): The parameter `dist` can be either a float or a tuple of two floats
                in which case dist[0] is the distance behind current car, and dist[1] in front
            othercar (Car): The car to check if it is in the distance range

        Returns:
            bool: True if in the distance range, False otherwise
        """ 
        if (isinstance(dist,Number)):
            return self.x - CAR_LENGTH - dist < othercar.x < self.x + CAR_LENGTH + dist
        else:
            return self.x - CAR_LENGTH - dist[0] < othercar.x < self.x + CAR_LENGTH + dist[1]

            
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
    
    def __eq__(self,p2: 'Car'):
        return (isinstance(p2,Car) and self.x == p2.x and self.desiredvel == p2.desiredvel and self.vel == p2.vel)








