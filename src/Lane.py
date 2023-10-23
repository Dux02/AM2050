from .Car import Car, DataCar, PIXEL_PER_M
from numpy import linspace, mean
from random import randint, random

SPAWNSAFETYDIST = 10 * PIXEL_PER_M

class Lane:
    def __init__(self, cars: int = 0):
        self.length = 5000 * PIXEL_PER_M  # 5 km
        xcoords = linspace(0, self.length, cars)
        self.vehicles: list[Car] = [Car(xcoords[i]) for i in range(cars)]
        self.finishedVehicles: list[Car] = []
        self.timeSinceLastCarGenerated = 0
        self.maxvel = 120 / 3.6

    def update(self, dt: float, frame: int) -> list[Car]:
        numOfCars = len(self.vehicles)
        if (numOfCars == 0):
            return
        carsToRemove: list[int] = []
        carsOvertaking: list[Car] = []
        for i in range(numOfCars):
            infront = None
            if (i < numOfCars-1):
                infront = self.vehicles[i+1]
            
            self.vehicles[i].update(dt, frame, infront)
                
            if (self.vehicles[i].overtaking != 0):
                    carsOvertaking.append(self.vehicles[i])
            if (self.vehicles[i].x > self.length):
                carsToRemove.append(i)
                
        carsToRemove.sort(reverse=True)
        for index in carsToRemove:
            self.finishedVehicles.append(self.vehicles.pop(index))
        return carsOvertaking

    def flushVehicles(self):
        '''Removes finished vehicles from memory'''
        self.finishedVehicles = []
    
    def getAvgSpeed(self) -> float:
        speeds = []
        for car in self.vehicles:
                speeds.append(car.vel)
        if len(speeds) == 0:
            speeds = [0]
        return mean(speeds)
    
    def getAvgDesiredSpeeds(self) -> float:
        speeds = []
        for car in self.vehicles:
                speeds.append(car.desiredvel)
        if len(speeds) == 0:
            speeds = [0]
        return mean(speeds)
    
    def findCarsAround(self,x): 
        # We're looking for the car in desiredLane to the left-back of car,
        # and we'll save its index @ desiredIndex
        checkList = self.vehicles
        if (len(checkList)==0):
            return [None, None]
        i = 0
        if (checkList[0].x > x):
            return [0,0]
        if (checkList[-1].x < x):
            return [-1,-1]
        while len(checkList) > 1:
            middleIndex = (len(checkList)-1) // 2  # Rounds down, but remember index starts @ 0
            if checkList[middleIndex].x < x < checkList[middleIndex+1].x:
                i += middleIndex
                # Done, found our car!
                break
            elif checkList[middleIndex].x > x:
                # Good we don't have to check above otherCar
                checkList = checkList[:middleIndex+1]
            else:
                i += middleIndex+1
                checkList = checkList[middleIndex+1:]
        return [i, i+1]
    
    def generateCarT(self,timestep:int,frame:int) -> bool:
        '''
        T STANDS FOR TIMESTAMP - FOR PROBABILISTIC GENERATION SEE generateCarP
        Generates a car between 1 and 2 timesteps since last car generated in the lane (wrt frame)
        If it successfully generates a car, it will return true, otherwise false.
        It will not spawn a car if there's not enough space to do so, regardless of the time since last spawn
        '''
        delta_i = frame - self.timeSinceLastCarGenerated
        if (delta_i < timestep):
            return False
        offset = randint(0,timestep-1)
        if ((delta_i % timestep == offset or delta_i >= 2*timestep)):
            #TODO: Make this more efficient? If we asssure index 0 is closest to start
            for car in self.vehicles:  
                if (car.x < SPAWNSAFETYDIST):
                    return False
            self.vehicles.insert(0,Car(spawnframe=frame))
            self.timeSinceLastCarGenerated = frame
            return True
        return False
    
    def generateCarP(self, p: float, frame: int) -> bool:
        '''
        P STANDS FOR PROBABILITY - FOR TIMED GENERATION SEE generateCarT
        Generates a car between 1 and 2 timesteps since last car generated in the lane (wrt frame)
        If it successfully generates a car, it will return true, otherwise false.
        It will not spawn a car if there's not enough space to do so, regardless of the time since last spawn
        '''
        if (random() < p):
            if len(self.vehicles) == 0:
                self.vehicles.insert(0, Car(spawnframe=frame))
                self.timeSinceLastCarGenerated = frame
                return True
            if self.vehicles[0].x < SPAWNSAFETYDIST:
                return False
            newCar = Car(spawnframe=frame)
            newCar.vel = self.vehicles[0].vel  # To avoid crashes, the cars come in with the same speed as the car in front
            self.vehicles.insert(0, newCar)
            self.timeSinceLastCarGenerated = frame
            return True
        return False


class DataLane(Lane):
    def __init__(self, cars: int = 0, y: int = 0):
        super().__init__(cars)
        self.y = y
        xcoords = linspace(0, self.length, cars)
        self.vehicles: list[DataCar] = [DataCar(xcoords[i],y) for i in range(cars)]
    
    def generateCarT(self, timestep: int, frame: int) -> bool:
        if super().generateCarT(timestep, frame):
            toReplace = self.vehicles[0]
            self.vehicles[0] = DataCar(toReplace.x,self.y,toReplace.spawnframe)
            return True
        return False
    def generateCarP(self, p: float, frame: int) -> bool:
        if super().generateCarP(p, frame):
            toReplace = self.vehicles[0]
            self.vehicles[0] = DataCar(toReplace.x,self.y,toReplace.spawnframe)
            return True
        return False