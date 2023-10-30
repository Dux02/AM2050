from typing import List
from .Lane import Lane, DataLane
from .Car import Car, CarData, DataCar, GRINDSET, PIXEL_PER_M
from .Output import AbstractOutput, FileOutput
from numpy import mean
import pygame
import pickle
import time

RENDER = True


def areSafeDist(main_car: 'Car', secondary_car: 'Car', overtaking=1):
    """Returns whether main_car can change into secondary_car's lane,
    based purely on difference in velocity, i.e. does not regard whether
    either car will have to brake hard once lane has been changed"""
    if main_car.x > secondary_car.x:
        delta_v = max(0, secondary_car.vel - main_car.vel)
    else:
        delta_v = max(0, main_car.vel - secondary_car.vel)

    scale = 2
    if overtaking == -1:
        scale = 1

    SafetyDist = scale * 3 * delta_v * PIXEL_PER_M + 2 * PIXEL_PER_M
    if main_car.inDist(SafetyDist,secondary_car):
        return False
    return True

def swapCarOnOvertake(car: Car, exitingLane: Lane, enteringLane: Lane, indices: List[int]):
    if (len(enteringLane.vehicles) == 0 or enteringLane.vehicles[0].x > car.x):
        enteringLane.vehicles.insert(0,car)
    elif(indices[1] == -1):
        enteringLane.vehicles.append(car)
    else:
        enteringLane.vehicles.insert(indices[1], car)

    car.multiplier = enteringLane.multiplier

    exitingLane.vehicles.remove(car)


def is_sorted(lane: Lane):
    return all(a.x <= b.x for a, b in zip(lane.vehicles, lane.vehicles[1:]))


class Simulation:
    # dt given in seconds
    def __init__(self, output: AbstractOutput, dt:float = 1, lanes: int = 1, cars: list[int] = [1]):
        self.lanes: list[Lane] = [Lane(cars[i]) for i in range(lanes)]
        self.dt = dt
        self.output = output  # File to write interesting data to
        self.frames = 0
        if not RENDER:
            pygame.quit()
    
    def update(self):
        carsOvertaking =[]
        for lane in self.lanes:
            i = self.lanes.index(lane)
            carsOvertaking.append(lane.update(self.dt, self.frames))
            if (not is_sorted(lane)):
                print("Scooby dooby doo")
        
        for i in range(len(self.lanes)):
            if len(carsOvertaking[i]) == 0:
                continue
            for car in carsOvertaking[i]:
                self.overtakingLogic(car, i, self.lanes[i])
                car.overtaking = 0
            if (not is_sorted(self.lanes[i])):
                print("We're in the bonezone now!")
        
        self.frames += 1    
        if (self.frames % int(10/self.dt) == 0):
            print("Simulation time:", round(self.frames*self.dt))
        # print(self.getAvgSpeed()*3.6)

    def overtakingLogic(self, car: Car, laneno: int, lane: Lane) -> bool:
        if laneno - car.overtaking == -1 or laneno - car.overtaking >= len(self.lanes):
            # We cant merge out of the road or overtake into the grass
            car.overtaking = 0
            return False

        desiredLane: Lane = self.lanes[laneno-car.overtaking]
        canOvertake = True

        if (car.x > desiredLane.length):
            return False

        if len(desiredLane.vehicles) == 0:
            # We can always go into an empty lane :)
            desiredLane.vehicles.append(car)
            car.multiplier = desiredLane.multiplier
            lane.vehicles.remove(car)
            return True
        
        if len(desiredLane.vehicles) == 1:
            indices = [0, 0]
        else:
            indices = desiredLane.findCarsAround(car.x)
            if (indices[1] != -1 and desiredLane.vehicles[indices[1]].x < car.x):
                print("Hmmmmm My esteemed establishment dislikes this")

        for j in indices:
            otherCar = desiredLane.vehicles[j]
            if not areSafeDist(car, otherCar, car.overtaking):
                # If there is a car, check whether we can overtake it.
                canOvertake = False
                break
            elif otherCar.calcAccel(car) < -0.5 * (120/(3.6*car.desiredvel))**2:
                # Don't go if it will cause the car behind to hit his brakes hard
                canOvertake = False
                break
            elif car.calcAccel(otherCar) < -0.5 * ((3.6*car.desiredvel)/120)**2:
                # Prevents go if the car in front will cause us to hit our brakes hard
                canOvertake = False
                break
            # elif car.overtaking == 1 and car.inDist((1.5*120 / (3.6*car.desiredvel) *otherCar.desiredDist(car),0),otherCar):
            #     # Don't overtake if it will cause the car behind to hit his brakes hard
            #     canOvertake = False
            #     break
            # elif (car.overtaking == -1 and car.inDist((0,0.7 * (3.6*car.desiredvel)/120 *car.desiredDist(otherCar)),otherCar)):
            #     # Prevents merging when the car in front will cause us to hit our brakes hard
            #     canOvertake = False
            #     break
        
        if canOvertake:
            if (len(desiredLane.vehicles) > 1 and desiredLane.vehicles[indices[1]].x < car.x and indices[1] != -1):
                print("Someone's search function don't work")
            if (desiredLane.vehicles[indices[1]].x < car.x and indices[1] != -1 and len(desiredLane.vehicles) != 1) or (car.x < desiredLane.vehicles[indices[0]].x and indices[0] != 0):
                print("DEATH IS UPON THEE")
            if (len(desiredLane.vehicles) == 1):
                swapCarOnOvertake(car,lane,desiredLane,[1,1])
                if not is_sorted(desiredLane):
                    print("THE PROBLEM IS NOT WHAT IT SEEMS")
            else:
                swapCarOnOvertake(car, lane, desiredLane, indices)
                if not is_sorted(desiredLane):
                    print("The president has arrived")
            return True
        
        return False
    
    def getAvgSpeed(self) -> float:
        speeds: list[float] = []
        for lane in self.lanes:
            speeds.append(lane.getAvgSpeed())
        if len(speeds) == 0:
            speeds = [0]
        return mean(speeds)

    def getCars(self) -> int:
        cars = 0
        for lane in self.lanes:
            cars += len(lane.vehicles)
        return cars
        
    def normalSpeedSimUpdate(self) -> int:
        carsRemoved = 0
        for lane in self.lanes:
            for car in lane.vehicles:
                car.normalSpeed(GRINDSET,self.dt,self.frames)
                if (car.x > lane.length):
                    # print("CAR KILLED")
                    lane.vehicles.remove(car)
                    self.finishedCar(car)
                    carsRemoved += 1
        return carsRemoved
    
    def finishedCar(self,car:Car):
        # self.output.write(str((self.frames - car.spawnframe)*self.dt) + '\n')
        self.output.save((self.frames - car.spawnframe)*self.dt)
        return
    
    def runNormalSpeedSim(self):
        cars = sum([len(lane.vehicles) for lane in self.lanes])
        while (cars > 0):
            cars -= self.normalSpeedSimUpdate()
        
    def runNormalManyCarSim(self, carcap=10, timestep=20):
        carsgenerated = 0
        cars = sum([len(lane.vehicles) for lane in self.lanes])
        while (cars > 0 or carsgenerated < carcap):
            cars += self.normalSpeedSimUpdate()
                
            if (carsgenerated >= carcap):
                continue
            
            for lane in self.lanes:
                factor = 1  # len(self.lanes) - self.lanes.index(lane) # For dynamic lane generation
                if (lane.generateCarT(timestep*factor,self.frames)):
                    cars += 1
                    carsgenerated += 1
                    # self.output.save(lane.vehicles[0].desiredvel)
                    # print("CAR BIRTHED")
        return

    def manyCarsPP(self, p: float, carcap=10):
        """Run a complete simulation, generating carcap cars, with p the probability parameter"""
        carsgenerated = 0
        cars = self.getCars()
        while (cars > 0 or carsgenerated < carcap):
            data_bit = []  # list to gather data we want to save each frame
            # print(cars)
            self.update()
            # self.output.save(self.getAvgSpeed()*3.6)

            for lane in self.lanes:
                for car in lane.finishedVehicles:
                    self.finishedCar(car)  # time it took to get to the end
                    cars -= 1
                lane.flushVehicles()
                
                if (carsgenerated < carcap):
                    if (lane.generateCarP(p*self.dt,self.frames)):
                        cars += 1
                        carsgenerated += 1

            if len(data_bit) != 0:
                self.output.save(data_bit)

        return
    
    def readFromPickle(self): # TODO
        return

class DataSimulation(Simulation):
    def __init__(self, output: FileOutput, dt: float = 1, lanes: int = 1, cars: list[int] = [1]):
        self.lanes: list[DataLane] = [DataLane(cars[i],i) for i in range(lanes)]
        self.dt = dt
        self.output = output  # File to write interesting data to
        self.frames = 0
        self.carData: List[CarData] = []
    
    def overtakingLogic(self, car: Car, laneno: int, lane: Lane):
        if(super().overtakingLogic(car, laneno, lane)):
            car.y = laneno - car.overtaking # Change the y-coordinate of the goober
            return True
        return False
    
    def finishedCar(self, car: DataCar):
        super().finishedCar(car)
        self.carData.append(car.data.__dict__)
    
    def manyCarsPP(self, p: float, carcap=10):
        super().manyCarsPP(p, carcap)
        pickle.dump(self.carData,self.output.file)
    
