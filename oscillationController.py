#!/usr/bin/env python
# -*- coding: utf-8 -*-
import Sofa
import math
import time

class controller(Sofa.PythonScriptController):





    def initGraph(self, node):

            self.node = node
            self.cube1Node=self.node.getChild('cube')
            self.pressureConstraint1Node = self.cube1Node.getChild('cavity')
            self.totalTime=0

    def onBeginAnimationStep(self, dt):
            self.dt = self.node.findData('dt').value
            start=time.time()
            self.totalTime = self.totalTime +dt
            print("The time is " + str(self.pressureConstraint1Node.findData('time')))
            #period
            B=2
            
            self.pressureConstraint1 = self.pressureConstraint1Node.getObject('SurfacePressureConstraint')
            
            if (math.sin(B*self.totalTime) >= 0):
                pressureValue = self.pressureConstraint1.findData('value').value[0][0] + 0.001
                if pressureValue > 1.5:
                    pressureValue = 1.5
               

            if (math.sin(B*self.totalTime) < 0):

                pressureValue = self.pressureConstraint1.findData('value').value[0][0] - 0.001
                if pressureValue < 0:
                    pressureValue = 0
            self.pressureConstraint1.findData('value').value = str(pressureValue)
            print("The value is " + str(self.pressureConstraint1.findData('value').value[0][0]))
            print("The volume is " + str((self.pressureConstraint1.findData('cavityVolume').value)))
                


