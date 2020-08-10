from gym.envs.registration import register

register(
    id='Tank-v0',
    entry_point='gym_tanks.envs:TanksEnvironment'
)