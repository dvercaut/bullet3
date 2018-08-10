import os
import inspect
currentdir = os.path.dirname(os.path.abspath(
    inspect.getfile(inspect.currentframe())))
print ("current_dir=" + currentdir)
os.sys.path.insert(0, currentdir)

import gym
import logging
import numpy as np
import pybullet as p
import pybullet_data
import time
import math
import random

import matplotlib.pyplot as plt

from utils import int2action
from baxter import Baxter
from reward_function import RewardZoo

from gym import spaces
from gym.utils import seeding
from pkg_resources import parse_version


RENDER_HEIGHT = 720
RENDER_WIDTH = 960


class BaxterGymEnv(gym.Env):
    _baxter: Baxter
    metadata = {
        'render.modes': ['human', 'rgb_array'],
        'video.frames_per_second': 50
    }

    def __init__(self,
                 urdfRoot=pybullet_data.getDataPath(),
                 actionRepeat=1,
                 renders=False,
                 dv=0.01,
                 useCamera=True,
                 useHack=True,
                 useBlock=True,
                 useRandomPos=True,
                 useTorusCollision=False,
                 use2D=False,
                 stepExploration=None,
                 _algorithm='DDPG',
                 _reward_function=None,
                 _action_type='discrete',
                 _logLevel=logging.INFO,
                 maxSteps=100,
                 timeStep=(1. / 240.),
                 cameraRandom=0):
        #self._timeStep = 1. / 240.
        self._timeStep = timeStep
        self._urdfRoot = urdfRoot
        self._actionRepeat = actionRepeat
        self._observation = []
        self._envStepCounter = 0
        self._renders = renders
        self._maxSteps = maxSteps
        self._dv = dv
        self._cameraRandom = cameraRandom
        self._width = 240
        self._height = 240
        self._useCamera = useCamera
        self._useHack = useHack
        self._useBlock = useBlock
        self._useRandomPos = useRandomPos
        self._stepExploration = stepExploration
        self._success_rate = None
        self._useTorusCollision = useTorusCollision
        self._use2d = use2D
        self._algorithm = _algorithm
        self._reward_function = _reward_function
        self._action_type = _action_type
        self._logLevel = _logLevel
        self._terminated = 0
        self._notCompleted = 0  # Whether task was completed or episode was terminated early
        self._collision_pen = -10000 #0.
        self.action_batch = []
        self.action = [0, 0, 0, 0, 0, 0, 0]
        self.old_pos = None
        self.clipped_counter = 0
        self.completion = 0
        self._p = p
        if self._renders:
            cid = p.connect(p.SHARED_MEMORY)
            if (cid < 0):
                p.connect(p.GUI)
            p.resetDebugVisualizerCamera(1.3, 180, -41, [0.52, -0.2, -0.33])
        else:
            p.connect(p.DIRECT)

        # Load in Baxter together with all the other objects
        self._baxter = Baxter(
            urdfRootPath=self._urdfRoot, timeStep=self._timeStep, useBlock=self._useBlock, use2D=self._use2d)

        self._seed()
        self.reset()
        observationDim = len(self.getExtendedObservation())

        # create logger
        logging.basicConfig()
        self.logger = logging.getLogger()
        self.logger.setLevel(self._logLevel)

        self.logger.debug("observationDim: %s" % str(observationDim))
        self.logger.debug("self.action: %s" % str(self.action))

        observation_high = np.array(
            [np.finfo(np.float32).max] * observationDim)

        if self._use2d:
            self.action_space = spaces.Discrete(4)
            self._action_type = '2d'
            print("\n\tAction_type set to 2D!")

        elif self._action_type == 'discrete':
            self.action_space = spaces.Box(
                low=0, high=2, shape=(7,))

        elif self._action_type == 'single':
            self.action_space = spaces.Discrete(21)

        elif self._action_type == 'end_effector':
            self.action_space = spaces.Discrete(6)

        elif self._action_type == 'continuous':
            action_dim = 7
            self._action_bound = 1
            action_high = np.array([self._action_bound] * action_dim)
            self.action_space = spaces.Box(-action_high, action_high)

        if self._useCamera:
            self.observation_space = spaces.Box(
                low=0, high=255, shape=(self._height, self._width, 3))
        else:
            self.observation_space = spaces.Box(-observation_high,
                                                observation_high)

        self.viewer = None

    def _reset(self):
        """Environment reset called at the beginning of an episode.
        """
        #p.resetSimulation()
        p.setPhysicsEngineParameter(numSolverIterations=150)
        p.setTimeStep(self._timeStep)

        self._baxter.reset()

        # Set action according to randomized gripper position
        # TODO: curriculum learning
        if self._useRandomPos:
            if self._stepExploration is not None:
                self._baxter.setExplorationSpace(self._stepExploration)

            self.old_pos = self._baxter.getEndEffectorPos()
            self._baxter.randomizeGripperPos()

        self.setAction()

        # Set the camera settings.
        head_camera_index = 9
        t_v = [.95, 0, -.1]  # Translation of the camera position
        cam_pos = np.array(p.getLinkState(
            self._baxter.baxterUid, head_camera_index)[0]) + t_v
        p.resetDebugVisualizerCamera(1.3, 180, -41, cam_pos)

        # TODO self._cameraRandom*np.random.uniform(-3, 3)
        # randomize yaw, pitch and roll as example of domain randomization
        # see kuka_diverse_object_gym_env
        look = cam_pos
        distance = 1.
        pitch = -20  # -10
        yaw = -100  # 245
        roll = 0
        self._view_matrix = p.computeViewMatrixFromYawPitchRoll(
            look, distance, yaw, pitch, roll, 2)
        fov = 85.
        aspect = 640. / 480.
        near = 0.01
        far = 10
        self._proj_matrix = p.computeProjectionMatrixFOV(
            fov, aspect, near, far)

        self._env_step = 0
        self._terminated = 0
        self._notCompleted = 0
        self._envStepCounter = 0
        self.clipped_counter = 0
        self.completion = 0
        # p.setGravity(0, 0, -10)

        p.stepSimulation()
        self._observation = self.getExtendedObservation()
        return np.array(self._observation)

    def __del__(self):
        p.disconnect()

    def _seed(self, seed=None):
        self.np_random, seed = seeding.np_random(seed)
        return [seed]

    def setAction(self):
        for i in range(len(self._baxter.motorIndices)):
            self.action[i] = p.getJointState(
                self._baxter.baxterUid, self._baxter.motorIndices[i])[0]

    def getGuidedAction(self, margin=0.3):
        torus_pos = np.array(p.getBasePositionAndOrientation(self._baxter.torusUid)[0])
        torus_pos[0] += self._baxter.margin
        end_effector_pos = self._baxter.getEndEffectorPos()

        distance = math.sqrt((torus_pos[0] - end_effector_pos[0]) ** 2 +
                             (torus_pos[1] - end_effector_pos[1]) ** 2)

        self.logger.debug("Distance:", distance)

        if distance < margin:
            # Do random action to explore this space
            single = self.action_space.sample()
        else:
            # Do action to move towards interesting area of the space
            action = self._baxter.calculateInverseKinematics(torus_pos)
            pos = self.getPossibleSingleActions(action)
            self.logger.debug("Possible actions:", pos)
            single = random.choice(pos)

        return single

    def getPossibleSingleActions(self, action):
        """
        Convert a multi-joint action into a list of single joint actions (No-op actions are left out)
        :param action: numpy.ndarray
        :return: numpy.ndarray
        """
        res = []
        for i in range(len(action)):
            if action[i] > self._dv:
                res.append(i + 2*7)
            elif action[i] < -self._dv:
                res.append(i + 2*0)
        return np.array(res)

    def createActionHist(self, fn):
        avg_action = sum(self.action_batch) / len(self.action_batch)

        n, bins, patches = plt.hist(self.action_batch, bins=[x+0.5 for x in range(-1,21)], facecolor='green')
        ax = plt.gca()
        ax.set_xticks([x for x in range(21)])
        plt.xlabel('Actions')
        plt.ylabel('Frequency')
        plt.title(r'$\mathrm{Histogram\ of\ actions}$' + ' (avg action: {})'.format(avg_action))
        #plt.grid(True)
        #plt.axis([0, 20.5, 0, 2500])
        plt.xlim(0, 20.5)
        plt.savefig(fn)
        plt.show()

        return avg_action

    def getExtendedObservation(self):
        """Return the observation as an image.
        """
        if (self._useCamera):
            img_arr = p.getCameraImage(width=self._width,
                                       height=self._height,
                                       viewMatrix=self._view_matrix,
                                       projectionMatrix=self._proj_matrix,
                                       renderer=p.ER_BULLET_HARDWARE_OPENGL)
            rgb = img_arr[2]
            np_img_arr = np.reshape(rgb, (self._height, self._width, 4))
            self._observation = np_img_arr
            return np_img_arr[:, :, :3]

        else:
            jointPos = []
            for i in self._baxter.motorIndices:
                jointInfo = p.getJointState(self._baxter.baxterUid, i)
                # Index 0 for joint position, index 1 for joint velocity
                jointPos.append(jointInfo[0])

            self._observation = jointPos

            if (self._useHack):
                torus_pos = np.array(p.getBasePositionAndOrientation(
                    self._baxter.torusUid)[0])
                self._observation += list(torus_pos)

            return np.array(self._observation)

    def _step(self, action):
        """Environment step.

        Args:
          action: integer or 7-vector parameterizing joint offsets depending on
                  the algorithm that is used

        Returns:
          observation: Next observation.
          reward: Float of the per-step reward as a result of taking the action.
          done: Bool of whether or not the episode has ended.
          debug: Dictionary of extra information provided by environment.
        """
        # action = [int(round(x)) for x in action]

        if self._action_type == 'single':
            assert isinstance(action, np.int32) or isinstance(action, np.int64) or isinstance(action, int) == True

            self.action_batch.append(action)
            row = int(action / len(self._baxter.motorIndices))
            column = action % len(self._baxter.motorIndices)

            self.logger.debug("Action: {}, row: {}, column:{}".format(str(action), str(row), str(column)))

            self.action[column] += [-self._dv, 0, self._dv][row]

        elif self._action_type == 'end_effector':
            self.stepsize = .05
            # 6 actions: left (0), right (1), up (2), down (3), forward (4), backward (5)
            targetPos = np.array(self._baxter.getEndEffectorPos())
            if action < 2:
                # Move gripper left or right use IK (y not sure)
                targetPos[1] += self.stepsize if action == 0 else -self.stepsize
            elif action < 4:
                # Move gripper up or down use IK (z not sure)
                targetPos[2] += self.stepsize if action == 2 else -self.stepsize
            else:
                # Move gripper forward or backward use IK (x direction)
                targetPos[0] += self.stepsize if action == 4 else -self.stepsize

            self.logger.debug("Action: {}, Old end_effector_pos: {}".format(str(action), str(targetPos)))
            self.action = self._baxter.calculateInverseKinematics(targetPos)

        elif self._action_type == '2d':
            self.stepsize = .05
            # 6 actions: left (0), right (1), forward (2), backward (3)
            targetPos = np.array(self._baxter.getEndEffectorPos())
            if action < 2:
                # Move gripper left or right use IK (y not sure)
                targetPos[1] += self.stepsize if action == 0 else -self.stepsize
            else:
                # Move gripper forward or backward use IK (x direction)
                targetPos[0] += self.stepsize if action == 2 else -self.stepsize

            self.logger.debug("Action: {}, Old end_effector_pos: {}".format(str(action), str(targetPos)))
            self.action = self._baxter.calculateInverseKinematics(targetPos)

        elif self._action_type == 'discrete':
            if self._algorithm == 'DDPG':
                # action = [int(round(np.nan_to_num(x)))
                #           for x in np.clip(action, -1, 1)]
                action = [int(round(x)) for x in action]
            elif self._algorithm == 'DQN':
                action = int2action(action)

            self.logger.debug("Action: %s" % str(action))

            d_s0 = [-self._dv, 0, self._dv][action[0]]
            d_s1 = [-self._dv, 0, self._dv][action[1]]
            d_e0 = [-self._dv, 0, self._dv][action[2]]
            d_e1 = [-self._dv, 0, self._dv][action[3]]
            d_w0 = [-self._dv, 0, self._dv][action[4]]
            d_w1 = [-self._dv, 0, self._dv][action[5]]
            d_w2 = [-self._dv, 0, self._dv][action[6]]

            realAction = [d_s0, d_s1, d_e0, d_e1, d_w0, d_w1, d_w2]
            self.action = [x + y for x, y in zip(realAction, self.action)]
            # realAction = [dx, dy, -0.002, da, f] # dz=-0.002 to guide the search downward

        elif self._action_type == 'continuous':
            assert len(action) == 7
            action = [np.nan_to_num(x) for x in np.clip(action, -1, 1)]

            self._dv = 1
            d_s0 = action[0] * self._dv
            d_s1 = action[1] * self._dv
            d_e0 = action[2] * self._dv
            d_e1 = action[3] * self._dv
            d_w0 = action[4] * self._dv
            d_w1 = action[5] * self._dv
            d_w2 = action[6] * self._dv

            self.action = [d_s0, d_s1, d_e0, d_e1, d_w0, d_w1, d_w2]

        return self.step2(self.action)

    def step2(self, action):
        self.old_pos = self._baxter.getEndEffectorPos()
        for i in range(self._actionRepeat):
            if self._action_type == 'discrete' or self._action_type == 'single' or \
                    self._action_type == 'end_effector' or self._action_type == '2d':
                self._baxter.applyAction(action)
            else:
                self._baxter.applyVelocity(action)
            p.stepSimulation()
            if self._termination():
                break
            # self._observation = self.getExtendedObservation()
            self._envStepCounter += 1

        self._observation = self.getExtendedObservation()
        self.logger.debug("observation: %s" % str(self._observation))

        if self._renders:
            time.sleep(self._timeStep)

        self.logger.debug("self._envStepCounter: %s" % str(self._envStepCounter))

        reward = self._reward()
        done = self._termination()
        # print("len=%r" % len(self._observation))

        return self._observation, reward, done, {}

    def _render(self, mode='human', close=False):
        pass

    def _termination(self):
        """Terminates the episode if the peg-insertion was succesful, if we are above
        maxSteps steps or the object is no longer in the gripper.
        """

        torus_pos = np.array(
            p.getBasePositionAndOrientation(self._baxter.torusUid)[0])

        if False:
            block_pos = np.array(
                p.getBasePositionAndOrientation(self._baxter.blockUid)[0])
        else:
            block_pos = np.array(
                p.getLinkState(self._baxter.baxterUid, 26)[0])  # 26 or avg between 28 and 30

        if self._useTorusCollision:
            cp_list = p.getContactPoints(
                self._baxter.baxterUid, self._baxter.torusUid)
            if any(cp_list):
                print("Torus collision!")
                self._terminated = 1
                self._notCompleted = 1

        x_bool = (torus_pos[0] + self._baxter.margin) < block_pos[0]
        y_bool = (torus_pos[1] - self._baxter.torusRad) < block_pos[1] and (torus_pos[1] + self._baxter.torusRad) > block_pos[1]
        z_bool = (torus_pos[2] - self._baxter.torusRad) < block_pos[2] and (torus_pos[2] + self._baxter.torusRad) > block_pos[2]

        if y_bool and z_bool and x_bool:
            #print("Average action:", self.createActionHist("action_hist.png"))
            print("Task completed!")
            self._terminated = 1
            self.completion = 1

        if(self._terminated or self._envStepCounter >= self._maxSteps or self.clipped_counter > 2):
            self._observation = self.getExtendedObservation()
            return True
        else:
            return False

    def _reward(self):
        """Calculates the reward for the episode.
        """
        if self._reward_function is None:
            return 0.
        else:
            reward_function = RewardZoo.create_function(self._reward_function)
            return reward_function(self)

    if parse_version(gym.__version__) >= parse_version('0.9.6'):
        render = _render
        reset = _reset
        seed = _seed
        step = _step
