from typing import List
from .Lane import Lane, DataLane, TRAFFICSPEEDLIMIT, DYNAMIC
from .Car import (Car, CarData, DataCar, GRINDSET, PIXEL_PER_M, PERSONALFACTOR, XENOFACTOR, DESIREDVELFACTOR,
                  MINIMUMDISTANCEFACTOR)
from .Output import AbstractOutput, FileOutput
import numpy as np
import pygame
import pickle
import time
import matplotlib.pyplot as plt

RENDER = True

np.random.seed(5)
PS = [1]
for i in range(1, 100000):
    x = PS[-1] + np.random.choice([0.1, -0.1])
    if x > 1:
        x = 1
    elif x < 0:
        x = 0
    for j in range(150):
        PS.append(x)


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

    SafetyDist = scale * delta_v * PIXEL_PER_M + PIXEL_PER_M
    if main_car.inDist(SafetyDist, secondary_car):
        return False
    return True


def swapCarOnOvertake(car: Car, exitingLane: Lane, enteringLane: Lane, indices: List[int]):
    if (len(enteringLane.vehicles) == 0 or enteringLane.vehicles[0].x > car.x):
        enteringLane.vehicles.insert(0, car)
    elif(indices[1] == -1):
        enteringLane.vehicles.append(car)
    else:
        enteringLane.vehicles.insert(indices[1], car)

    car.adaptToSpeedLimit(enteringLane.speedlimit)

    exitingLane.vehicles.remove(car)


def is_sorted(lane: Lane):
    return all(a.x <= b.x for a, b in zip(lane.vehicles, lane.vehicles[1:]))


class Simulation:
    # dt given in seconds
    def __init__(self, output: AbstractOutput, dt: float = 1, lanes: int = 1, cars: list[int] = [1]):
        self.lanes: list[Lane] = [Lane(cars[i]) for i in range(lanes)]
        self.dt = dt
        self.output = output  # File to write interesting data to
        self.frames = 0
        self.p = np.random.random()
        if not RENDER:
            pygame.quit()
    
    def update(self):
        carsOvertaking = []
        replace = True
        for lane in self.lanes:
            i = self.lanes.index(lane)
            carsOvertaking.append(lane.update(self.dt, self.frames))

            if DYNAMIC:  # and self.frames*self.dt % 10 == 0
                if 0 < lane.getAvgSpeed()*3.6 <= TRAFFICSPEEDLIMIT:
                    replace = False  # as soon as we have one slow lane, all lanes get slowed
                    for elene in self.lanes:
                        elene.speedlimit = TRAFFICSPEEDLIMIT + 15
                        for car in elene.vehicles:
                            car.adaptToSpeedLimit(elene.speedlimit)  # when cars check to merge and such they currently use the wrong desiredvel

        if DYNAMIC and replace:
            for lane in self.lanes:
                lane.speedlimit = 120
                for car in lane.vehicles:
                    car.multiplier = 1
        
        for i in range(len(self.lanes)):
            if len(carsOvertaking[i]) == 0:
                continue
            for car in carsOvertaking[i]:
                self.overtakingLogic(car, i, self.lanes[i])
                car.overtaking = 0
        
        self.frames += 1    
        if self.frames % int(100/self.dt) == 0:
            print("Avg speeds:", [round(3.6*lane.getAvgSpeed()) for lane in self.lanes])
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
            swapCarOnOvertake(car, lane, desiredLane, [0, 0])

            # desiredLane.vehicles.append(car)
            # lane.vehicles.remove(car)
            #
            # car.adaptToSpeedLimit(desiredLane.speedlimit)

            return True
        
        if len(desiredLane.vehicles) == 1:
            indices = [0, 0]
        else:
            indices = desiredLane.findCarsAround(car.x)
            if (indices[1] != -1 and desiredLane.vehicles[indices[1]].x < car.x):
                print("Hmmmmm My esteemed establishment dislikes this")

        for j in indices:
            otherCar = desiredLane.vehicles[j]
            k = indices.index(j)

            if not areSafeDist(car, otherCar, car.overtaking):
                # Check whether if we overtake, we would do so into another car
                canOvertake = False
                break
            elif k == 0 and otherCar.calcAccel(car) < car.xenofactor * (120 / (3.6 * car.multiplier * car.desiredvel))**2:
                # Don't go if it will cause the car behind to hit his brakes hard
                canOvertake = False
                break
            elif k == 1 and car.calcAccel(otherCar) < car.personalfactor * ((3.6 * car.multiplier * car.desiredvel) / 120)**2:
                # Don't go if the car in front will cause us to hit our brakes hard
                canOvertake = False
                break
            elif (car.overtaking == -1 and k == 1
                  and otherCar.vel <= DESIREDVELFACTOR*car.multiplier*car.desiredvel*(desiredLane.speedlimit/120)
                  and otherCar.x - car.x < 5*car.vel*PIXEL_PER_M):
                # Don't go if we will want to overtake as soon as we've merged,
                # unless the other car is more than 5 seconds away
                canOvertake = False
                break
            # elif (car.overtaking == 1 and k == 1
            #       and car.vel > otherCar.vel):
            #     # If we're overtaking, we should also not go if our lane is going faster
            #     canOvertake = False
            #     break

            # elif car.overtaking == 1 and car.inDist((1.5*120 / (3.6*car.desiredvel) *otherCar.desiredDist(car),0),otherCar):
            #     # Don't overtake if it will cause the car behind to hit his brakes hard
            #     canOvertake = False
            #     break
            # elif (car.overtaking == -1 and car.inDist((0,0.7 * (3.6*car.desiredvel)/120 *car.desiredDist(otherCar)),otherCar)):
            #     # Prevents merging when the car in front will cause us to hit our brakes hard
            #     canOvertake = False
            #     break
        
        if canOvertake:
            # if (len(desiredLane.vehicles) > 1 and desiredLane.vehicles[indices[1]].x < car.x and indices[1] != -1):
            #     print("Someone's search function don't work")
            # if (desiredLane.vehicles[indices[1]].x < car.x and indices[1] != -1 and len(desiredLane.vehicles) != 1) or (car.x < desiredLane.vehicles[indices[0]].x and indices[0] != 0):
            #     print("DEATH IS UPON THEE")
            if (len(desiredLane.vehicles) == 1):
                swapCarOnOvertake(car, lane, desiredLane, [1, 1])
            else:
                swapCarOnOvertake(car, lane, desiredLane, indices)
            return True
        
        return False
    
    def getAvgSpeed(self) -> float:
        speeds: list[float] = []
        for lane in self.lanes:
            speeds.append(lane.getAvgSpeed())
        if len(speeds) == 0:
            speeds = [0]
        return np.mean(speeds)

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
    
    def finishedCar(self, car: Car):
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
        self.p = p
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
                    # Note 1 - p = chance that no car is spawned in one second
                    # if q is the chance of spawning a car in one frame (there are 1/dt frames in a second)
                    # We find 1 - p = (1 - q)^(1/dt)
                    # Rearranging for q gives formula below
                    probPerFrame = 1 - np.power((1-p), self.dt)
                    if lane.generateCarP(probPerFrame, self.frames):
                        cars += 1
                        carsgenerated += 1

            if len(data_bit) != 0:
                self.output.save(data_bit)

        return

    def manyCarsRP(self, carcap=10):
        """Run a complete simulation, generating carcap cars with
         a probability spawning system, but p does a random walk."""

        carsgenerated = 0
        cars = self.getCars()
        while (cars > 0 or carsgenerated < carcap):
            data_bit = []  # list to gather data we want to save each frame
            # print(cars)

            self.p = PS[self.frames]

            self.update()
            # self.output.save(self.getAvgSpeed()*3.6)

            data_bit.append(self.p)

            # if self.frames*self.dt % 5 == 0:
            #     if np.random.random() < 0.5:
            #         self.p += 0.1
            #     else:
            #         self.p -= 0.1
            #
            # if self.p < 0:
            #     self.p = 0
            # elif self.p > 1:
            #     self.p = 1

            for lane in self.lanes:
                lanespeed = lane.getAvgSpeed()
                if lanespeed != 0:
                    data_bit.append(lanespeed)
                else:
                    data_bit.append(self.output.data[-1][self.lanes.index(lane)+1])

                for car in lane.finishedVehicles:
                    # self.finishedCar(car)
                    # data_bit.append((self.frames - car.spawnframe)*self.dt)  # time it took to get to the end
                    cars -= 1
                lane.flushVehicles()

                if (carsgenerated < carcap):
                    # Note 1 - p = chance that no car is spawned in one second
                    # if q is the chance of spawning a car in one frame (there are 1/dt frames in a second)
                    # We find 1 - p = (1 - q)^(1/dt)
                    # Rearranging for q gives formula below
                    probPerFrame = 1 - np.power((1 - self.p), self.dt)
                    if lane.generateCarP(probPerFrame, self.frames):
                        cars += 1
                        carsgenerated += 1

            if len(data_bit) != 0:
                self.output.save(data_bit)

        return

    def manyCarsTimedRP(self, time=100):
        """Run a complete simulation for time simulated seconds with random walk p"""
        cars = self.getCars()
        do = False
        while self.dt*self.frames < time:
            data_bit = []  # list to gather data we want to save each frame
            # print(cars)

            if do:
                for lane in self.lanes:
                    for car in lane.vehicles:
                        if car.desiredvel*3.6 > 140 and self.frames*self.dt > 25:
                            car.debug = True
                            do = False
                            break
                    if not do:
                        break

            self.p = PS[self.frames]

            self.update()
            # self.output.save(self.getAvgSpeed()*3.6)

            data_bit.append(self.p)

            # if self.frames*self.dt % 5 == 0:
            #     if np.random.random() < 0.5:
            #         self.p += 0.1
            #     else:
            #         self.p -= 0.1
            #
            # if self.p < 0:
            #     self.p = 0
            # elif self.p > 1:
            #     self.p = 1

            for lane in self.lanes:
                lanespeed = lane.getAvgSpeed()
                if lanespeed != 0:
                    data_bit.append(lanespeed)
                else:
                    data_bit.append(self.output.data[-1][self.lanes.index(lane)+1])

                for car in lane.finishedVehicles:
                    # self.finishedCar(car)
                    # data_bit.append((self.frames - car.spawnframe)*self.dt)  # time it took to get to the end
                    cars -= 1
                lane.flushVehicles()

                # Note 1 - p = chance that no car is spawned in one second
                # if q is the chance of spawning a car in one frame (there are 1/kdt frames in 1/k second)
                # We find 1 - p = (1 - q)^(1/kdt)
                # Rearranging for q gives formula below (with k=1)
                probPerFrame = 1 - np.power((1 - self.p), self.dt)
                if lane.generateCarP(probPerFrame, self.frames):
                    cars += 1

            for lane in self.lanes:
                data_bit.append(len(lane.vehicles))

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

    def manyCarsRP(self, carcap=10):
        super().manyCarsRP(carcap)
        pickle.dump(self.carData,self.output.file)
    
