"""基础函数：每个变量的物理含义见课程 1、4、8、10。仅标准库。"""
import math


def transform(point, translation, degrees):
    """机器人坐标的二维米制点 -> 地图坐标；角度为逆时针度数。"""
    theta = math.radians(degrees)
    c, s = math.cos(theta), math.sin(theta)
    x, y = point
    tx, ty = translation
    return c*x-s*y+tx, s*x+c*y+ty


def inverse_transform(point, translation, degrees):
    x = point[0] - translation[0]
    y = point[1] - translation[1]
    return transform((x, y), (0, 0), -degrees)


def fuse(x, p, u, q, z, r):
    """一维直接位置观测；p/q/r 都是方差，r 不是残差。"""
    if any(not math.isfinite(v) for v in (x, p, u, q, z, r)):
        raise ValueError('Inputs must be finite')
    if min(p, q, r) < 0 or p+q+r <= 0:
        raise ValueError('Variances must be nonnegative with a positive total')
    predicted_x = x + u
    predicted_p = p + q
    gain = predicted_p / (predicted_p + r)
    return predicted_x+gain*(z-predicted_x), (1-gain)*predicted_p, gain


def project(point, fx=400, fy=400, cx=320, cy=240):
    """相机坐标 X右/Y下/Z前，米 -> 无畸变像素。"""
    x, y, z = point
    if z <= 0:
        raise ValueError('Point must be in front of the camera (Z > 0)')
    return fx*x/z+cx, fy*y/z+cy


if __name__ == '__main__':
    print('transform:', transform((1, 0), (2, 1), 90))
    print('fusion x, variance, gain:', tuple(round(v, 4) for v in fuse(0, .04, 1, .01, 1.2, .2)))
    print('projection:', project((1, .5, 2)))
