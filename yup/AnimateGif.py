from time import sleep
import pygame

class Animation: 
    def __init__(self, pathlist = [], datime = 1):
        self.pos = []
        self.images = []
        self.paths = []
        self.paths = pathlist
        self.width = []
        self.height = []
        self.framecount = len(self.paths)

    def setPaths(self, pathlist):
        self.framecount = len(pathlist)
        self.paths = pathlist

        while self.framecount > len(self.images):
            self.images.append(pygame.image.load(self.paths[0]))
        for i in range(self.framecount):
            self.images[i] = pygame.image.load(self.paths[i])

        while self.framecount > len(self.pos):
            self.pos.append((0, 0))
        while self.framecount > len(self.width):
            self.width.append(0)
            self.height.append(0)

    def getPaths(self, ShowAll = True, which = 0):
        if ShowAll == False:
            print (self.paths[which])
        else:
            for i in range(self.framecount):
                print(self.paths[i])

    def setSize(self, size = (0, 0), SetAll = True, which = 0):
        if SetAll == True:
            for i in range(self.framecount):
                self.width[i], self.height[i] = size
                self.images[i] = pygame.transform.scale(self.images[i], (self.width[i], self.height[i]))
        else:
            self.width[which], self.height[which] = size
            self.images[which] = pygame.transform.scale(self.images[which], (self.width[which], self.height[which]))

    def getSize(self, ShowAll = True, which = 0):
        if ShowAll == False:
            #print(self.width[which], self.height[i])
            return (self.width[which], self.height[which])
        else:
            for i in range(self.framecount):
                print("frame", i, " width:", self.width[i], " height:", self.height[i])

    def setPos(self, position = (0, 0), SetAll = True, which = 0):
        if SetAll == False:
            self.pos[which] = position
        else:
            for i in range(self.framecount):
                self.pos[i] = position

    def getPos(self, which):
        return(self.pos[which])

    def drawFrame(self, surface, which):
        surface.blit(self.images[which], self.pos[which])

    def drawAll(self, surface, time):
        for i in range(self.framecount):
            surface.blit(self.images[i], self.pos[i])
            pygame.display.flip()
            sleep(time/self.framecount)
