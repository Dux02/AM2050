from typing import Union
from .Simulation import Simulation
from .Output import AbstractOutput
from .Car import (V_MIN, V_DESIRED, GUSTAVO, PIXEL_PER_M, CAR_LENGTH, CAR_HEIGHT, LANE_HEIGHT, LINE_HEIGHT,
                  SPEEDCAMERALOCATION, SPEEDCAMERA)
import pygame
import numpy as np
import time

temp = max(V_MIN, V_DESIRED - 3*GUSTAVO/3.6)
# B is meters per second: A converts m/s to 0-255
A, B = (255-0)/(V_DESIRED + 3*GUSTAVO/3.6 - temp), -temp


class Renderer():
    image = pygame.image.load('media/auto.png')
    treeImages = [pygame.image.load('media/treebigger.png'), pygame.image.load('media/treebig.png'),
             pygame.image.load('media/treemedium.png'), pygame.image.load('media/treesmall.png')]

    RENDER = False  # NOT A HARDCODE OF IF WE RENDER OR NOT!!!
    
    WIDTH, HEIGHT = 1200, 600  # 1500, 720 blas computer
    red = (255, 0, 0)
    green = (0, 255, 0)
    blue = (0, 0, 255)
    white = (255, 255, 255)
    grey = (128, 128, 128)
    black = (0, 0, 0)
    window = None
    begin_draw = 0

    def __init__(self) -> None:
        if not Renderer.RENDER:
            Renderer.RENDER = True
            pygame.init()
            Renderer.window = pygame.display.set_mode((Renderer.WIDTH, Renderer.HEIGHT))
            Renderer.window.fill(Renderer.white)
            Renderer.font = pygame.font.Font("freesansbold.ttf",21)
            Renderer.font2 = pygame.font.Font("freesansbold.ttf",10)
    
    @staticmethod
    def kill():
        pygame.display.quit()
        pygame.quit()
        Renderer.RENDER = False


class VisualSimulation(Simulation):
    renderer: Union[None, Renderer] = None
    
    def initRenderer(self):
        if (VisualSimulation.renderer is None):
            VisualSimulation.renderer = Renderer()
        return
    
    def __init__(self, output: AbstractOutput, dt: float = 1, lanes: int = 1, cars: list[int] = [1], pretty=False):
        super().__init__(output, dt, lanes, cars)
        self.initRenderer()
        self.rendering = VisualSimulation.renderer.RENDER
        self.avspeeds, self.avdesspeeds = 0, 0
        self.pretty = pretty

        # Tree locations
        numTrees = 50
        rdr = VisualSimulation.renderer
        self.trees = []

        roadWidth = PIXEL_PER_M*(LANE_HEIGHT*len(self.lanes) + LINE_HEIGHT*(len(self.lanes)-1))
        top = (rdr.HEIGHT - roadWidth)/2

        miny1, maxy1 = 0, top
        miny2, maxy2 = top+roadWidth, rdr.HEIGHT
        for i in range(numTrees):
            x = np.random.randint(self.lanes[0].length-140)

            coin = np.random.choice(["heads", "tails"])
            if coin == "heads":
                y = np.random.randint(miny1, maxy1-168)
            else:
                y = np.random.randint(miny2, maxy2-168)

            image = np.random.choice(rdr.treeImages)
            self.trees.append([x, y, image])

    def update(self):
        super().update()
        if not VisualSimulation.renderer.RENDER:
            self.rendering = False
        if self.rendering:
            self.render()
    
    def render(self):
        rdr: Renderer = VisualSimulation.renderer
        rdr.window.fill(rdr.white)
        if not self.pretty:
            if ((self.frames-1)*self.dt % 1 == 0):
                # Update statistics
                self.avdesspeeds = str([round(lane.getAvgDesiredSpeeds()*3.6) for lane in self.lanes])
                self.avspeeds = str([round(lane.getAvgSpeed() * 3.6) for lane in self.lanes])
            # Draw statistics
            pygame.draw.rect(rdr.window, rdr.white, pygame.Rect(0, 0, rdr.WIDTH, 90))
            avd_text = rdr.font.render("Avg desired speeds: " + self.avdesspeeds + " km/h",
                                        True, rdr.black,rdr.white)
            av_text = rdr.font.render("Avg speeds: " + self.avspeeds + " km/h",
                                        True, rdr.black, rdr.white)
            # av_text = font.render("No. of cars: "+ str(self.getCars()) + " cars",True,black,white)
            rdr.window.blit(avd_text, (0, 0))
            rdr.window.blit(av_text, (0, 30))

            text = "Speed limits: " + str([round(lane.speedlimit) for lane in self.lanes])
            limits = rdr.font.render(text, True, rdr.black, rdr.white)
            rdr.window.blit(limits, (int(rdr.WIDTH/2), 0))

            text = "p = " + str(round(self.p, 2))
            p = rdr.font.render(text, True, rdr.black, rdr.white)
            rdr.window.blit(p, (int(rdr.WIDTH/2), 30))

            clock = rdr.font.render("T+" + str(round(self.frames*self.dt)) + " s", True, rdr.black, rdr.white)
            rdr.window.blit(clock, (0, 60))

        if self.pretty:
            # Draw trees
            for (x, y, image) in self.trees:
                if 0 < x - rdr.begin_draw < rdr.WIDTH:
                    rdr.window.blit(image, (x - rdr.begin_draw, y))

        # Draw lanes
        n = len(self.lanes)
        lh, lw = int(LANE_HEIGHT*PIXEL_PER_M), int(LINE_HEIGHT*PIXEL_PER_M)
        empty_space_above = (rdr.HEIGHT - (lh*n+lw*(n-1)))/2
        pygame.draw.rect(rdr.window, rdr.grey, pygame.Rect(0, empty_space_above, rdr.WIDTH, lh*n+lw*(n-1)))
        for i in range(n-1):
            y = empty_space_above + lh + (lh+lw)*i
            pygame.draw.rect(rdr.window, rdr.black, pygame.Rect(0, y, rdr.WIDTH, lw))

        # Draw finish
        if 0 < self.lanes[0].length - rdr.begin_draw < rdr.WIDTH:
            pygame

        # Draw speed camera
        if SPEEDCAMERA:
            x = SPEEDCAMERALOCATION * PIXEL_PER_M
            if 0 < x - rdr.begin_draw < rdr.WIDTH:
                pygame.draw.rect(rdr.window, rdr.grey, pygame.Rect(x - rdr.begin_draw, empty_space_above-30, 1, 30))
                pygame.draw.rect(rdr.window, rdr.grey, pygame.Rect(x - rdr.begin_draw-5, empty_space_above-30-10, 10, 10))
                pygame.draw.circle(rdr.window, rdr.black, (x - rdr.begin_draw, empty_space_above-30-5), 2)

        # Draw cars
        ch, cl = CAR_HEIGHT*PIXEL_PER_M, CAR_LENGTH*PIXEL_PER_M
        for lane in self.lanes:
            lane_num = self.lanes.index(lane)
            for i in range(len(lane.vehicles)):
                car = lane.vehicles[i]
                if car.debug:
                    rdr.begin_draw = car.x - rdr.WIDTH/2.5
                if (0 < car.x - rdr.begin_draw < rdr.WIDTH):
                    if (i < len(lane.vehicles) - 1 and self.pretty):
                        car.beep(self.frames*self.dt, lane.vehicles[i+1],
                                 (rdr.begin_draw, rdr.begin_draw + rdr.WIDTH))
                    draw_x = car.x - rdr.begin_draw
                    draw_y = empty_space_above + (lh+lw) * lane_num + int((lh-ch)/2)

                    x = A * (car.multiplier*car.desiredvel + B)
                    color = (x, 0, 255 - x)
                    if color[0] >= 255:
                        color = (255, 0, 0)
                    elif color[0] <= 0:
                        color = (0, 0, 255)

                    if car.debug:
                        color = (0, 255, 0)

                    in_front_dist = car.s0

                    pygame.draw.rect(rdr.window, color, pygame.Rect(draw_x, draw_y, cl, ch))
                    # rdr.window.blit(rdr.image, (draw_x, draw_y))

                    if not self.pretty:
                        acc_text = rdr.font2.render(str(round(3.6*car.vel)), True, rdr.white, color)
                        rdr.window.blit(acc_text, (draw_x, draw_y))
                        pygame.draw.rect(rdr.window, color, pygame.Rect(draw_x + cl, draw_y + int(ch / 2), in_front_dist, 1))

        # Draw buttons and check if there being hovered over
        pygame.draw.rect(rdr.window, rdr.red, pygame.Rect(0, rdr.HEIGHT-40, 40, 40))
        pygame.draw.rect(rdr.window, rdr.green, pygame.Rect(50, rdr.HEIGHT-40, 40, 40))
        mouse = pygame.mouse.get_pos()
        if 0 < mouse[0] < 40 and rdr.HEIGHT-40 < mouse[1] < rdr.HEIGHT:
            rdr.begin_draw -= 150*self.dt*PIXEL_PER_M
        if 50 < mouse[0] < 90 and rdr.HEIGHT-40 < mouse[1] < rdr.HEIGHT:
            rdr.begin_draw += 150*self.dt*PIXEL_PER_M
        window_pos = rdr.font.render(str(round(rdr.begin_draw/PIXEL_PER_M)) + " m", True, rdr.black, rdr.white)
        pygame.draw.rect(rdr.window, rdr.white, pygame.Rect(90,rdr.HEIGHT-40,100,40))
        rdr.window.blit(window_pos, (100, rdr.HEIGHT-20))
        
        pygame.display.update()
        events = pygame.event.get()
        for event in events:
            if event.type == pygame.QUIT:
                rdr.window.fill(rdr.white)
                text = rdr.font.render("Awaiting termination... See console", True, rdr.black, rdr.white)
                rdr.window.blit(text,(0,0))
                print("Awaiting Renderer.kill or next VisualSimulation call to delete pygamewindow...")
                pygame.display.update()
                self.rendering = False
            if event.type == pygame.WINDOWEXPOSED:
                # print("OK")
                pass
    
