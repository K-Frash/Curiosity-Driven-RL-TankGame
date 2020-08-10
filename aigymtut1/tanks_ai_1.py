import gym
import numpy as np
# import gym-TanksEnvironment
import time

env = gym.make('gym_tanks:Tank-v0')

done = False
cnt = 0

observation = env.reset()

while not done:
    env.render()

    cnt += 1
    print(cnt)

    action = env.action_space.sample()
    print(action)

    # time.sleep(1)
    strin = input("Press Enter to continue...")

    # if "u" in strin:
    #     pass

    observation, reward, done, _ = env.step(action)
    print(observation)

    if done:
        break

print('game lasted', cnt, 'moves')