import os
import inspect
currentdir = os.path.dirname(os.path.abspath(
    inspect.getfile(inspect.currentframe())))
print ("current_dir=" + currentdir)
os.sys.path.insert(0, currentdir)

import math
import gym
import logging
import numpy as np
import pybullet as p
import pybullet_data
import random
import sys
import time

from utils import int2action
from baxter import Baxter
from reward_function import RewardZoo

from gym import spaces
from gym.utils import seeding
from numpy.linalg import norm
from numpy import vdot
from pkg_resources import parse_version


RENDER_HEIGHT = 720
RENDER_WIDTH = 960


class BaxterGymEnv(gym.Env):
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
        self._algorithm = _algorithm
        self._reward_function = _reward_function
        self._action_type = _action_type
        self._logLevel = _logLevel
        self._terminated = 0
        self._collision_pen = 0.
        self.action = [0, 0, 0, 0, 0, 0, 0]
        self._p = p
        if self._renders:
            cid = p.connect(p.SHARED_MEMORY)
            if (cid < 0):
                p.connect(p.GUI)
            p.resetDebugVisualizerCamera(1.3, 180, -41, [0.52, -0.2, -0.33])
        else:
            p.connect(p.DIRECT)
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
        if self._action_type == 'discrete':
            self.action_space = spaces.Box(
                low=0, high=2, shape=(7,))

        elif self._action_type == 'single':
            self.action_space = spaces.Discrete(21)

        elif self._action_type == 'continuous':
            action_dim = 7
            self._action_bound = 1
            action_high = np.array([self._action_bound] * action_dim)
            self.action_space = spaces.Box(-action_high, action_high)

        if (self._useCamera):
            self.observation_space = spaces.Box(
                low=0, high=255, shape=(self._height, self._width, 3))
        else:
            self.observation_space = spaces.Box(-observation_high,
                                                observation_high)

        self.viewer = None

    def _reset(self):
        """Environment reset called at the beginning of an episode.
        """
        p.resetSimulation()
        p.setPhysicsEngineParameter(numSolverIterations=150)
        p.setTimeStep(self._timeStep)

        # Load in Baxter together with all the other objects
        self._baxter = Baxter(
            urdfRootPath=self._urdfRoot, timeStep=self._timeStep, useBlock=self._useBlock)

        # Set action according to randomized gripper position
        if self._useRandomPos:
            self._baxter.randomizeGripperPos()
            self.setAction()

        # Set the camera settings.
        head_camera_index = 9
        t_v = [.95, 0, -.1]  # Translation of the camera position
        cam_pos = np.array(p.getLinkState(
            self._baxter.baxterUid, head_camera_index)[0]) + t_v
        p.resetDebugVisualizerCamera(1.3, 180, -41, cam_pos)

        # TODO self._cameraRandom*np.random.uniform(-3, 3) randomize yaw, pitch and roll as example of domain randomization
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

        self._attempted_grasp = False
        self._env_step = 0
        self._terminated = 0
        self._envStepCounter = 0
        self.setAction()
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
                    self._baxter.torusUid)[0]) + [0, 0, self._baxter.torusRad]
                self._observation += list(torus_pos)

            return self._observation

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
            print("\nAction:", type(action), action)
            assert isinstance(action, np.int32) or isinstance(action, np.int64) == True

            row = int(action / len(self._baxter.motorIndices))
            column = action % len(self._baxter.motorIndices)

            self.action[column] += [-self._dv, 0, self._dv][row]

        elif self._action_type == 'discrete':
            self.assertTrue(isinstance(action, int))
            if self._algorithm == 'DDPG':
                action = [int(round(np.nan_to_num(x)))
                          for x in np.clip(action, -1, 1)]
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
            self.assertTrue(len(action) == 7)
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
        for i in range(self._actionRepeat):
            if self._action_type == 'discrete' or self._action_type == 'single':
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

        self.logger.debug("self._envStepCounter: %s" %
                          str(self._envStepCounter))

        reward = self._reward()
        done = self._termination()
        # print("len=%r" % len(self._observation))

        return np.array(self._observation), reward, done, {}

    def _render(self, mode='human', close=False):
        pass

    def _termination(self):
        """Terminates the episode if the peg-insertion was succesful, if we are above
        maxSteps steps or the object is no longer in the gripper.
        """

        torus_pos = np.array(
            p.getBasePositionAndOrientation(self._baxter.torusUid)[0])

        if self._useBlock:
            block_pos = np.array(
                p.getBasePositionAndOrientation(self._baxter.blockUid)[0])
        else:
            block_pos = np.array(
                p.getLinkState(self._baxter.baxterUid, 26)[0])  # 26 or avg between 28 and 30

        # Caculate distance between the center of the torus and the block
        distance = np.linalg.norm(np.array(torus_pos) - np.array(block_pos))

        x_bool = (torus_pos[0] + self._baxter.margin) < block_pos[0]
        y_bool = (
            torus_pos[1] - self._baxter.torusRad) < block_pos[1] and (torus_pos[1] + self._baxter.torusRad) > block_pos[1]
        z_bool = (
            torus_pos[2] - self._baxter.torusRad) < block_pos[2] and (block_pos[2] + self._baxter.torusRad) > block_pos[2]

        if y_bool and z_bool and x_bool:
            print("Task completed!")
            self._terminated = 1

        if(self._terminated or self._envStepCounter >= self._maxSteps):
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
