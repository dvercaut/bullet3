import os
import inspect
import time
currentdir = os.path.dirname(os.path.abspath(
    inspect.getfile(inspect.currentframe())))
parentdir = os.path.dirname(os.path.dirname(currentdir))
os.sys.path.insert(0, parentdir)

import pybullet as p
import numpy as np
import math
import pybullet_data

class Baxter:
    """
    This class will only use the right arm of the Baxter robot
    """

    def __init__(self, urdfRootPath=pybullet_data.getDataPath(), timeStep=0.01, useBlock=True, use2D=False):
        self.urdfRootPath = urdfRootPath
        self.timeStep = timeStep
        self.maxVelocity = .35
        self.maxForce = 5000.
        self.baxterEndEffectorIndex = 26  # or 25
        self.baxterGripperIndex = 20  # or 26
        self.baxterHeadCameraIndex = 9
        self.useBlock = useBlock
        self.use2d = use2D
        self.torusScale = 1.
        self.torusRad = 0.23 * self.torusScale
        self.margin = 0.#0.06
        self.maxIter = 40
        # First semi-circle
        #   self.llSpace = [0.8333, -0.5, 0.64]
        #   self.ulSpace = [1.1, -0.2, 1.22]
        # Second semi-circle
        #   self.llSpace = [0.5666, -0.65, 0.35]
        #   self.ulSpace = [1.1, -0.05, 1.51]
        # Third semi-circle
        self.llSpace = [0.3, -0.8, 0.06]  # x,y,z
        self.ulSpace = [1.1, 0.1, 1.8]  # x,y,z

        if self.use2d:
            self.llSpace[2] = 1.
            self.ulSpace[2] = 1.

        self.setup()

    def setup(self):
        self.baxterUid = p.loadURDF(os.path.join(
            self.urdfRootPath, "baxter_common/baxter.urdf"), [0, 0, 0.62], useFixedBase=True, flags=p.URDF_USE_SELF_COLLISION_EXCLUDE_PARENT)
        self.numJoints = p.getNumJoints(self.baxterUid)  # 42

        p.loadURDF(os.path.join(
            self.urdfRootPath, "plane.urdf"), [0, 0, -0.3], useFixedBase=True)

        # Load in torus
        orn = p.getQuaternionFromEuler([0, 0, math.pi / 2.])

        ypos = -.1 + 0.05 * np.random.random()
        if self.use2d:
            zpos = 1.
        else:
            zpos = 1. + 0.05 * np.random.random()
        self.torus_coord = [1.1, ypos, zpos]
        # ang = 3.1415925438 * random.random() --> TODO maybe randomize angle as dom randomization
        # orn = p.getQuaternionFromEuler([0, 0, ang])

        self.torusUid = p.loadURDF(os.path.join(
            self.urdfRootPath, "torus/torus.urdf"), self.torus_coord,
            orn, useFixedBase=True, globalScaling=self.torusScale)

        if self.useBlock:
            # Compute coordinates of block
            coord1 = p.getLinkState(self.baxterUid, 28)[0]
            coord2 = p.getLinkState(self.baxterUid, 30)[0]
            block_coord = [(x[0] + x[1]) / 2. for x in zip(coord1, coord2)]
            orn = p.getLinkState(self.baxterUid, 23)[1]  # Get orn from link 23
            # Joint 30 (orthagonal), joint 25 (orthagonal)

            self.blockUid = p.loadURDF(os.path.join(
                self.urdfRootPath, "block_rot.urdf"), block_coord)

            p.resetBasePositionAndOrientation(self.blockUid, block_coord, orn)
            self.cid_base = p.createConstraint(self.baxterUid, self.baxterEndEffectorIndex, self.blockUid, -1,
                                               jointType=p.JOINT_FIXED, jointAxis=[1, 0, 0],
                                               parentFramePosition=[0, 0, 0], childFramePosition=[0, 0, 0],
                                               parentFrameOrientation=p.getQuaternionFromEuler([0, math.pi / 2., 0]))

        # Create line for reward function
        orn = np.array(p.getEulerFromQuaternion(p.getBasePositionAndOrientation(self.torusUid)[1]))
        orn[2] = orn[2] + math.pi / 2.  # Rotate within plane perpendicular to torus
        line_coord = self.torus_coord
        # This needs to be made more general if torus orn changes so multiply by dir vector from reward function
        #dir = vdot(dir_vector, np.array([0, 0, -0.2]))
        #line_coord += dir
        line_coord[0] -= 0.2
        self.torusLineUid = p.loadURDF(os.path.join(self.urdfRootPath, "block_line.urdf"),
                                       self.torus_coord, p.getQuaternionFromEuler(orn), useFixedBase=True)

        self.motorNames = []
        self.motorIndices = [12, 13, 14, 15, 16, 18, 19]

        for i in self.motorIndices:
            jointInfo = p.getJointInfo(self.baxterUid, i)
            qIndex = jointInfo[3]
            if qIndex > -1:
                # print "motorname", jointInfo[1]
                self.motorNames.append(str(jointInfo[1]))

    def reset(self):
        # reset joint state of baxter
        base_pos = [0 for x in range(len(self.motorIndices))]
        for i in range(len(self.motorIndices)):
            p.resetJointState(self.baxterUid, self.motorIndices[i], base_pos[i])

        # re-randomize torus position
        ypos = -.1 + 0.05 * np.random.random()
        if self.use2d:
            zpos = 1.
        else:
            zpos = 1. + 0.05 * np.random.random()
        self.torus_coord = np.array([1.1, ypos, zpos])
        orn = p.getQuaternionFromEuler([0, 0, math.pi / 2.])
        p.resetBasePositionAndOrientation(self.torusUid, self.torus_coord, orn)

        # Reset torusLine
        orn = np.array(p.getEulerFromQuaternion(p.getBasePositionAndOrientation(self.torusUid)[1]))
        orn[2] = orn[2] + math.pi / 2.  # Rotate within plane perpendicular to torus
        line_coord = self.torus_coord
        p.resetBasePositionAndOrientation(self.torusLineUid, self.torus_coord, p.getQuaternionFromEuler(orn))

    def setExplorationSpace(self, space):
        if space == 0:
            # Spawn in font of torus
            self.llSpace = [0.97, self.torus_coord[1] - self.torusRad*1/5., self.torus_coord[2] - self.torusRad*1/5.]
            self.ulSpace = [1.0, self.torus_coord[1] + self.torusRad*1/5., self.torus_coord[2] + self.torusRad*1/5.]
        elif space == 1:
            # Extended spawn in front of torus
            self.llSpace = [0.94, self.torus_coord[1] - self.torusRad*1/3., self.torus_coord[2] - self.torusRad*1/3.]
            self.ulSpace = [1.0, self.torus_coord[1] + self.torusRad*1/3., self.torus_coord[2] - self.torusRad*1/3.]
        elif space == 2:
            # Extended spawn in front of torus
            self.llSpace = [0.9, self.torus_coord[1] - self.torusRad*3/5., self.torus_coord[2] - self.torusRad*3/5.]
            self.ulSpace = [1.0, self.torus_coord[1] + self.torusRad*3/5., self.torus_coord[2] - self.torusRad*3/5.]
        elif space == 3:
            # Extended spawn in front of torus
            # Added
            self.llSpace = [0.87, self.torus_coord[1] - self.torusRad*4/5., self.torus_coord[2] - self.torusRad*4/5.]
            self.ulSpace = [1.0, self.torus_coord[1] + self.torusRad*4/5., self.torus_coord[2] - self.torusRad*4/5.]
        elif space == 4:
            # Added
            self.llSpace = [0.86, -0.30, 0.77]
            self.ulSpace = [1.0, -0.13, 1.19]
        elif space == 5:
            # Added
            self.llSpace = [0.85, -0.32, 0.72]
            self.ulSpace = [1.0, -0.165, 1.2]
        elif space == 6:
            # Added
            self.llSpace = [0.84, -0.35, 0.68]
            self.ulSpace = [1.0, -0.2, 1.21]
        elif space == 7:
            # Added
            self.llSpace = [0.836, -0.4, 0.66]
            self.ulSpace = [1.05, -0.2, 1.215]
        elif space == 8:
            # First semi-circle
            self.llSpace = [0.8333, -0.5, 0.64]
            self.ulSpace = [1.1, -0.2, 1.22]
        elif space == 9:
            self.llSpace = [0.69, -0.55, 0.46]
            self.ulSpace = [1.1, -0.1, 1.36]
        elif space == 10:
            # Second semi-circle
            self.llSpace = [0.5666, -0.65, 0.35]
            self.ulSpace = [1.1, -0.05, 1.51]
        else:
            # Third semi-circle
            self.llSpace = [0.3, -0.8, 0.06]  # x,y,z
            self.ulSpace = [1.1, 0.1, 1.8]  # x,y,z

        if self.use2d:
            self.llSpace[2] = 1.
            self.ulSpace[2] = 1.

    def getActionDimension(self):
        return len(self.motorIndices)

    def getObservationDimension(self):
        return len(self.getObservation())

    def getObservation(self):
        # Extend this to give information from all joints in self.motorIndices
        observation = []
        state = p.getLinkState(self.baxterUid, self.baxterGripperIndex)
        pos = state[0]
        orn = state[1]
        euler = p.getEulerFromQuaternion(orn)

        observation.extend(list(pos))
        observation.extend(list(euler))

        return observation

    def printJointInfo(self):
        joint_name2joint_index = {}
        for joint_nr in range(p.getNumJoints(self.baxterUid)):
            joint_info = p.getJointInfo(self.baxterUid, joint_nr)
            # print joint_info[0], joint_info[1]
            joint_idx = joint_info[0]
            joint_name = joint_info[1]
            joint_name2joint_index[joint_name] = joint_idx
            print("motorinfo:", joint_info[3], joint_info[1], joint_info[0])
        print(joint_name2joint_index)

    def randomizeGripperPos(self):
        # Randomize the right arm start position
        gripperPos = np.array([np.random.uniform(self.llSpace[i], self.ulSpace[i]) for i in range(len(self.llSpace))])

        joints = [1, 2, 3, 4, 5, 6, 7]
        iter = 0
        # Loop until arm is in correct position alternatively use for loop with range(50)
        while np.any(np.abs(gripperPos - np.array(self.getEndEffectorPos())) > np.array([0.01, 0.01, 0.01])) and (iter < self.maxIter):
            jointPoses = np.array(p.calculateInverseKinematics(self.baxterUid, self.baxterEndEffectorIndex, gripperPos))
            jointPoses = [jointPoses[i] for i in joints]
            iter += 1

            for i in range(len(self.motorIndices)):
                p.resetJointState(self.baxterUid, self.motorIndices[i], jointPoses[i])

        #print("Gripper expected: ", gripperPos, "\t Actual gripper pos:", self.getEndEffectorPos())
        #TODO check collision with torus, if true, recalculate gripperPos

    def calculateInverseKinematics(self, targetPosition, ll=None, ul=None, jr=None, rp=None,
                                useNullSpace=False, maxIter=40, threshold=1e-2):
        """Use inverse kinematics on the right arm of the baxter robot
        """
        closeEnough = False
        iter = 0
        dist2 = 1e30

        joints = [1, 2, 3, 4, 5, 6, 7]

        while (not closeEnough and iter < maxIter):
            if useNullSpace:
                jointPoses = np.array(p.calculateInverseKinematics(self.baxterUid, self.baxterEndEffectorIndex, targetPosition,
                                                                   lowerLimits=ll, upperLimits=ul, jointRanges=jr, restPoses=rp))
            else:
                jointPoses = np.array(p.calculateInverseKinematics(self.baxterUid, self.baxterEndEffectorIndex, targetPosition))

            jointPoses = [jointPoses[i] for i in joints]

            for i in range(len(joints)):
                p.resetJointState(self.baxterUid, self.motorIndices[i], jointPoses[i])

            ls = p.getLinkState(self.baxterUid, self.baxterEndEffectorIndex)
            newPos = ls[4]
            diff = [targetPosition[0] - newPos[0], targetPosition[1] - newPos[1], targetPosition[2] - newPos[2]]
            dist2 = np.sqrt((diff[0] * diff[0] + diff[1] * diff[1] + diff[2] * diff[2]))
            # print("dist2=", dist2)
            closeEnough = (dist2 < threshold)
            iter = iter + 1
        #print("RandomPos:", targetPosition, "Actual Pos:", np.array(p.getLinkState(self.baxterUid, self.baxterEndEffectorIndex)[0]), "iter:", iter)
        return jointPoses

    def getEndEffectorPos(self):
        return p.getLinkState(self.baxterUid, self.baxterEndEffectorIndex)[0]

    def calculateEndEffectorPos(self, action):
        old_pos = []

        for i in range(len(self.motorIndices)):
            joint_state = p.getJointState(
                            self.baxterUid,
                            self.motorIndices[i]
                        )
            old_pos.append(joint_state[0])

        for i in range(len(self.motorIndices)):
            p.resetJointState(
                            self.baxterUid,
                            self.motorIndices[i],
                            action[i])

        endEffectorPos = p.getLinkState(self.baxterUid, self.baxterEndEffectorIndex)[0]

        for i in range(len(self.motorIndices)):
            p.resetJointState(
                            self.baxterUid,
                            self.motorIndices[i],
                            old_pos[i])

        return endEffectorPos

    def applyAction(self, motorCommands):
        assert len(motorCommands) == len(self.motorIndices)

        p.setJointMotorControlArray(
            self.baxterUid,
            self.motorIndices,
            controlMode=p.POSITION_CONTROL,
            targetPositions=motorCommands
        )

        # Close right arm gripper
        p.setJointMotorControl2(
            self.baxterUid, 27, controlMode=p.POSITION_CONTROL, targetPosition=0, force=10000)
        p.setJointMotorControl2(
            self.baxterUid, 29, controlMode=p.POSITION_CONTROL, targetPosition=0, force=10000)


    def applyVelocity(self, velocityCommands):
        assert len(velocityCommands) == len(self.motorIndices)

        commands = [x for x in velocityCommands] #Scaling
        forces = [500 for x in range(len(velocityCommands))]

        p.setJointMotorControlArray(
            self.baxterUid,
            self.motorIndices,
            controlMode=p.VELOCITY_CONTROL,
            targetVelocities=commands,
            forces=forces
        )
