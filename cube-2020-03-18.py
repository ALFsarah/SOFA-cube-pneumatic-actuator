def createScene(rootNode):
	return rootNode

import Sofa
from stlib.visuals import ShowGrid
from stlib.physics.rigid import Floor
from stlib.scene import ContactHeader
import os
#Location of Meshes and objects
path = 'details/data/mesh/'

def createScene(rootNode):
	#Its helpful to be able to see the grid
	ShowGrid(rootNode)

	#Adding the Soft-Robotics Plugin and the SofaPython  plugin
	rootNode.createObject('RequiredPlugin', name='soft', pluginName='SoftRobots')
	rootNode.createObject('RequiredPlugin', name='SofaPython', pluginName='SofaPython')
	rootNode.createObject('RequiredPlugin', name='SofaSparseSolver', pluginName='SofaSparseSolver')


	#Gravity is automatically defined but we can redefine it
	rootNode.findData('gravity').value='0 0 -981'


	#It is nice to have the useful visualizatioin visible upon reloading the scene
	#you can find the options in the view tab in the GUI
	rootNode.createObject('VisualStyle', displayFlags='showForceFields showBehaviorModels')
	#Add BackgroundSetting in order not to have to reset it to white everytime you reload
	rootNode.createObject('BackgroundSetting', color='1 1 1')
	#Add the axis in the upper right corner automatically
	rootNode.createObject('OglSceneFrame', style="Arrows", alignment="TopRight")

	#The standard Global Bounding Box is very small  [-1,-1,-1,1,1,1]
	#in comparison to our object so we make it bigger
	rootNode.findData('bbox').value= '-200 -200 -200 200 200 200'


	#Let's add the Child node for the Mesh
	cube = rootNode.createChild('cube')
	#Adding the Mesh file and make sure it finds it in the location directed to by the path
	cube.createObject('MeshVTKLoader', name='loader', filename= path + 'mesh_cube20.vtk')
	#Now let's load the Mehs and make it a MechObj, which stores and is set to show the degrees of freedom of our box
	cube.createObject('Mesh', src='@loader', name='container')
	cube.createObject('MechanicalObject', name='tetras', template='Vec3d', showObject='true')	

	#Next we want to make the material soft so we add a forcefield 
	#We use TetrahedronFEMForceField in this case because of the nature of our mesh
	#Here we also determine the Young's Modulus and Poisson's ratio for the material
	#method is related to either small or large displacements

	cube.createObject('TetrahedronFEMForceField', template='Vec3d', name='FEM', method='large', poissonRatio='0.49', youngModulus='200')

	#Next we want to add the mass, since we want to uniformly distribute it we can either use
	#vertexMass which is the mass at each node, stored in the MevhanicalObject
	#or totalMass which is the total mass, which is then spread over the nodes. 
	#Beware these don't consider the geometry or topology of the system. More details, also on non-uniform masses: 
	#https://www.sofa-framework.org/community/doc/using-sofa/components/masses/uniformmass/

	cube.createObject('UniformMass', totalMass='0.01')

	#For initial try I will add a boundary condition for the bottom of the box
	#This will fix the box in place if I set the stifness of the springs rather high
	#As it creates springs between its initial and current position
	#In this case I placed the box in the xy-plane going from 0-100 and up to 10 along the z-axis

	#cube.createObject('BoxROI', name='boxROI', box='0 100 0 100 0 10', drawBoxes=True)
	#cube.createObject('RestShapeSpringsForceField', points='@boxROI.indices', stiffness='1e12', angularStiffness='1e12')

	#Now we add a time integration scene, allowing the system to be computed at each time step
	#We will use the EulerImplicit solver where the forces are based off of 
	#the information of the next time step. Although being slower than the Explicit solver, 
	#they are more stable and are needed for stiff differential equations
	cube.createObject('EulerImplicit', name='odesolver')


	#And following that we add a Matrix solver, this one is a direct solver based off of A=LDL^T
	#This one can be slow for very large systems but gives exact solutions
	cube.createObject('SparseLDLSolver', name='directSolver')

	#At this point it will deform a bit under gravity but not involve other dynamics
	#Lets add the pneumatic actuators

	#First let's create the cavity add the mesh and load it
	cavity = cube.createChild('cavity')
	cavity.createObject('MeshSTLLoader', name='loader', filename= path + 'mesh_cavity20.stl')
	cavity.createObject('Mesh', src='@loader', name='topo')
	#Now we must make the MechanicalObject of the surface mesh to store the degrees of freedom
	#along the surface that will cause deformations
	cavity.createObject('MechanicalObject', name='cavity')

	#Now we will add a SurfacePressureConstraint
	#This adds a constant pressure on a surface
	#Such that each point of the mesh receives the pressure of the elements it is a part of
	#You need to specify:
		#are you using triangles or quads
		#value
		#valueIndex (default is {0})
		#valueType; pressure or volumeGrowth
	#For more info: https://project.inria.fr/softrobot/documentation/constraint/surface-pressure-constraint/
	cavity.createObject('SurfacePressureConstraint', name='SurfacePressureConstraint', 
		template='Vec3d', value='0.0001', triangles='@topo.triangles', valueType='pressure')
	
	#Now we need to use a BarycentricMapping to map the deformation of the cavity onto our 3d Mesh
	cavity.createObject('BarycentricMapping', name='mapping')

	#Now as a first test we will use the prewritten controller program which uses +/- to inflate and deflate
	rootNode.createObject('PythonScriptController', filename='details/oscillationController.py', classname="controller")

	#Now we will add an animationloop, the easiest is to add the FreeMotionAnimationLoop
	rootNode.createObject('FreeMotionAnimationLoop')
	#Furthermore we will add to solvers to take various constraints into account
	rootNode.createObject('GenericConstraintSolver', maxIterations='10000', tolerance='1e-3')
	cube.createObject('LinearSolverConstraintCorrection', solverName='directSolver')

	#Let's add a visual model for the vube
	visualCube = cube.createChild('visualCube')
	visualCube.createObject('MeshSTLLoader', name='loader', filename= path + 'mesh_cube20.stl')
	visualCube.createObject('OglModel', src='@loader', template='ExtVec3d', color='0.4 0.9 0.9')
	visualCube.createObject('BarycentricMapping')

	#In order to visualize and export the scene we can use the monitor component
	#This is added to an indice of the component it is directly monitoring
	#cube.createObject('Monitor', name="monitor-39", indices="178 228 278 303 253 203", template="Vec3d",
	#	showPositions=True, PositionsColor="1 0 1 1", ExportPositions=False, 
	#	showVelocities=True, VelocitiesColor="0.5 0.5 1 1", ExportVelocities=False, 
	#	showForces=True, ForcesColor="0.8 0.2 0.2 1", ExportForces=False, 
	#	showTrajectories=False, TrajectoriesPrecision="0.1", TrajectoriesColor="0 1 1 1", sizeFactor="0.5")

	#Now let's add a floor on which the cube will rest. We will use a rigid, preset floor from SOFA for the floor
	#It is a preset with preset totalMass=1.0 and totalVolume=1.0. We will set it to be static.
	#Furthermore it already includes its own collisionmodel.
	#This includes the Mesh of the outer surface of the floor, A mapping between this mesh and that of the volume mesh of the floor
	#and it tells all triangles, lines and points how to interact upon collision. (By not moving)

	Floor(rootNode, translation=[0.0, 0.0, 0.0], rotation=[90.0, 0.0, 0.0], isAStaticObject=True, uniformScale=8.0)

	#Now let's add the collisionmodel to the cube
	collisionCube = cube.createChild("collisionCube")

	#First we will load and store the surface mesh of the cube, and turn it into a mechanicalObject
	#You could think about the translation of this object when wanting to add more cubes but for now it is not necessary
	collisionCube.createObject('MeshSTLLoader', name='loader', filename= path + 'mesh_cube20.stl')
	collisionCube.createObject('Mesh', src='@loader', name='topo')
	collisionCube.createObject('MechanicalObject', name='collisMech')

	#Now we add the behavior for the triangles, lines and points for the collision mesh
	collisionCube.createObject('Triangle', selfCollision=False)
	collisionCube.createObject('Line', selfCollision=False)
	collisionCube.createObject('Point', selfCollision=False)

	#Finally we add the mapping of this mesh to that of its parant node the cube
	collisionCube.createObject('BarycentricMapping')


	#We add the contactmodel and the corresponding friction coefficient
	ContactHeader(rootNode, alarmDistance=5, contactDistance=1, frictionCoef=0.0)






	




