# 一手资料

核验日期：2026-09-13。

## Knowledge

- [机器人推理：状态、观测与行动](https://www.roboticsbook.org/S12_reasoning.html)
  Dellaert 与 Hutchinson 的课程书；用于建立建模入口。

- [Python 官方：数字与程序基础](https://docs.python.org/3/tutorial/introduction.html)
  核对赋值、数值、列表等语言语义；本课程标准库代码在 Python 3.13 验证。

- [Eigen 官方：Getting started](https://libeigen.gitlab.io/eigen/docs-nightly/GettingStarted.html)
  核对矩阵声明、编译和入门用法；实际工程按所用版本锁定。

- [Ceres 官方：非线性最小二乘](https://ceres-solver.readthedocs.io/latest/nnls_tutorial.html)
  核对残差、自动求导、鲁棒损失和优化建模。

- [机器人课程书：Localization](https://www.roboticsbook.org/S44_logistics_perception.html)
  用于概率定位与滤波的进一步推导。

- [机器人课程书：三维运动](https://www.roboticsbook.org/S71_drone_state.html)
  三维旋转与刚体运动的数学背景。

- [OpenCV 官方：相机标定与三维重建](https://docs.opencv.org/4.13.0/d9/d0c/group__calib3d.html)
  核对投影、内外参与实际畸变模型。

- [HKU-MARS：FAST_LIO 上游仓库](https://github.com/hku-mars/FAST_LIO)
  核对激光惯性系统组成、ROS 1 环境与安装说明；阅读源码时额外记录提交。

- [PCL 官方：ICP 入门](https://pointclouds.org/documentation/tutorials/iterative_closest_point.html)
  核对点云配准接口与最小流程。

- [GTSAM：Factor Graphs and GTSAM](https://gtsam.org/tutorials/intro.html)
  核对变量、因子、位姿图与地标 SLAM 的关系。

- [Open Robotics：REP-105](https://github.com/openrobotics/reps/blob/main/_posts/rep-0105.md)
  移动机器人坐标系命名与语义。

- [ROS 2 Jazzy 教程源码](https://github.com/ros2/ros2_documentation/blob/jazzy/source/Tutorials.rst)
  官方教程入口；docs.ros.org 本次访问被保护页阻挡，使用官方源码入口。

- [TUM RGB-D 数据集与基准](https://cvg.cit.tum.de/data/datasets/rgbd-dataset)
  真实轨迹评估数据与协议；不可把视觉 RGB-D 数据直接当作激光 IMU 输入。

- [Nav2 Jazzy：环境表达](https://docs.nav2.org/jazzy/getting_started/navigation_concepts/environmental_representation/)
  占据、代价地图与导航接口，工程命令需按版本核对。

- [PyTorch 官方：优化参数](https://docs.pytorch.org/tutorials/beginner/basics/optimization_tutorial.html)
  训练循环、损失与参数更新；本课程基础实验不依赖 PyTorch。

- [Anderson 等：Vision-and-Language Navigation](https://arxiv.org/abs/1711.07280)
  R2R 与视觉语言导航原始任务；进一步学习时先读任务设置。

- [Anderson 等：On Evaluation of Embodied Navigation Agents](https://arxiv.org/abs/1807.06757)
  通用导航评估与 SPL；遵循具体任务的成功定义。

- [Ha 与 Schmidhuber：World Models](https://worldmodels.github.io/)
  早期学习世界模型的原论文与演示。

- [Hafner 等：DreamerV3](https://arxiv.org/abs/2301.04104)
  学习世界模型与想象行为训练；本课程标量实验不是论文复现。

## Wisdom

未要求加入社区；不以外部问答代替课内解释。

## Gaps 与边界

浏览器和 Python 教学实验已单独验证；真实 FAST-LIO2、ROS、VLN 基准及 Dreamer 训练没有在本环境运行。学习者设备、每周时间与独立编程能力仍未知。高级课提供概念桥梁与工程验收，不宣称完整复现论文。
