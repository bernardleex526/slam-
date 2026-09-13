"""课 14：未知 x1/x2/landmark，一维线性 SLAM，固定 x0=0。"""
import math


def solve(matrix, rhs):
    """小型线性方程，部分主元高斯消元；只用于教学小矩阵。"""
    n = len(rhs)
    if not n or len(matrix) != n or any(len(row) != n for row in matrix):
        raise ValueError('Expected a square system')
    a = [list(row) + [value] for row, value in zip(matrix, rhs)]
    for col in range(n):
        pivot = max(range(col, n), key=lambda row: abs(a[row][col]))
        if abs(a[pivot][col]) < 1e-12:
            raise ValueError('Unconstrained or singular system')
        a[col], a[pivot] = a[pivot], a[col]
        scale = a[col][col]
        a[col] = [v/scale for v in a[col]]
        for row in range(n):
            if row != col:
                factor = a[row][col]
                a[row] = [v-factor*w for v, w in zip(a[row], a[col])]
    return [row[-1] for row in a]


def build_system(odometry=(1.2, .9), observations=(4., 3., 2.)):
    if len(odometry) != 2 or len(observations) != 3:
        raise ValueError('This teaching model needs 2 motions and 3 observations')
    # 未知量顺序 x1, x2, landmark。每行对应一条物理约束。
    a = [[1, 0, 0], [-1, 1, 0], [0, 0, 1], [-1, 0, 1], [0, -1, 1]]
    b = list(odometry) + list(observations)
    if not all(math.isfinite(v) for v in b):
        raise ValueError('Measurements must be finite')
    return a, b


def estimate(odometry=(1.2, .9), observations=(4., 3., 2.)):
    a, b = build_system(odometry, observations)
    # A^T A 与 A^T b；生产系统不应照抄这个稠密小矩阵实现。
    normal = [[sum(row[i]*row[j] for row in a) for j in range(3)] for i in range(3)]
    rhs = [sum(row[i]*value for row, value in zip(a, b)) for i in range(3)]
    x1, x2, landmark = solve(normal, rhs)
    return [0., x1, x2], landmark


def rmse(estimate_values, truth):
    if not truth or len(estimate_values) != len(truth):
        raise ValueError('Paired nonempty trajectories required')
    return math.sqrt(sum((a-b)**2 for a, b in zip(estimate_values, truth))/len(truth))


if __name__ == '__main__':
    positions, landmark = estimate()
    truth = [0., 1., 2.]  # 合成评估真值，不传入估计器。
    print('estimated positions:', [round(v, 4) for v in positions])
    print('estimated landmark:', round(landmark, 4))
    print('odometry RMSE:', round(rmse([0., 1.2, 2.1], truth), 5))
    print('joint SLAM RMSE:', round(rmse(positions, truth), 5))
