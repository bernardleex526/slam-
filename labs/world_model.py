"""课22：动作条件线性动力学；独立动作值测试 + 候选序列规划。"""
from itertools import product
import math

TRAIN = [(1., .81), (2., 1.59), (-1., -.80), (-2., -1.60)]
TEST = [(0.5, .4), (1.5, 1.2), (-.5, -.4)]


def fit(samples):
    samples = list(samples)
    if not samples or not all(math.isfinite(a) and math.isfinite(d) for a, d in samples):
        raise ValueError('Finite nonempty training data required')
    denominator = sum(a*a for a, displacement in samples)
    if denominator == 0:
        raise ValueError('Zero actions do not identify the motion coefficient')
    return sum(a*d for a, d in samples)/denominator


def rollout(position, actions, theta):
    path = [position]
    for action in actions:
        position += theta*action
        path.append(position)
    return path


def mse(theta, samples):
    return sum((theta*a-d)**2 for a, d in samples)/len(samples)


def plan(position, goal, theta, horizon=2):
    candidates = product((-1., 0., 1.), repeat=horizon)
    return min(candidates, key=lambda seq: (rollout(position, seq, theta)[-1]-goal)**2)


if __name__ == '__main__':
    theta = fit(TRAIN)
    print('learned theta:', round(theta, 4))
    print('held-out MSE baseline / learned:', round(mse(1., TEST), 6), round(mse(theta, TEST), 6))
    actions = plan(0., 1.6, theta)
    print('plan:', actions)
    print('model final:', round(rollout(0., actions, theta)[-1], 4))
    print('true synthetic final:', round(rollout(0., actions, .8)[-1], 4))
    print('shifted friction final:', round(rollout(0., actions, .5)[-1], 4))
    print('Teaching model only: no images, obstacles, latent states or policy training.')
