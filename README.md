# SLAM：从基础到工程，再到 VLN 与世界模型

下载整个仓库后，双击 **[index.html](index.html)** 开始。GitHub 文件页显示 HTML 源码；不要只下载单个页面。教材离线运行，不需要账号、GPU 或安装网页依赖。

适合的起点：对 SLAM 一知半解、编程基础弱，但会部署环境、会用 AI 帮忙调试。课程不假装你会自己写大段代码，而是把“读懂代码、改一个数、编译、跑起来、定位问题”拆成小步，并把 AI 当成**追问教练和排错助手**，不是答案生成器。

## 课程结构（33 课）

| 阶段 | 课号 | 内容 |
| --- | --- | --- |
| 0 · 起步 | 01 | 怎样学：节奏、证据、怎样用 AI |
| A · 找回基础 | 02–09 | 问题建模；Python ①变量 ②循环 ③函数与调试；向量、二维旋转、导数、概率 |
| B · 从测量到估计 | 10–16 | 最小二乘①目标函数 ②迭代与鲁棒（原一课拆二）；卡尔曼；三维旋转、位姿链（原一课拆二）；相机；IMU |
| C · 组成 SLAM | 17–19 | 点云配准、图优化、一维 SLAM 项目 |
| D · 工程编程（C++） | 20–22 | C++ ①编译运行 ②函数与引用 ③Eigen 与 CMake（原一课拆三） |
| D · 部署、系统与评估 | 23–29 | ROS/TF（含 ROS 1/ROS 2 命令对照）；部署①Docker 环境 ②编译并跑通 FAST-LIO2 ③排错与录包检查；读 FAST-LIO2；评估；导航 |
| E · 通向学习模型 | 30–32 | 机器学习、VLN、世界模型 |
| F · 初级到中级 | 33 | 综合项目验收 |

每课有：预计用时、本课新词（最多 6 个）、生活类比、手算、逐行代码说明、提示与解答、数值自查、迁移题、**AI 陪练提示词**（可一键复制）和一句话总结。AI 使用规则见 [reference/ai.html](reference/ai.html)。

## 可执行实验

在仓库目录打开终端。Windows 用 `py`，Linux/macOS 用 `python3`：

```text
py labs/core.py
py labs/slam_1d.py
py labs/navigation.py
py labs/world_model.py
py labs/deploy/check_bag.py          # 录包话题/频率与 FAST-LIO 配置是否一致（示例故意写错一处）
py -m unittest discover -s tests -v
```

C++（Linux / WSL，需 g++；Eigen 示例另需 `libeigen3-dev` 与 cmake）：

```text
g++ -std=c++17 -Wall labs/cpp/01_basics.cpp -o basics && ./basics
g++ -std=c++17 -Wall labs/cpp/02_functions.cpp -o functions && ./functions
cmake -S labs/cpp/eigen_demo -B build && cmake --build build && ./build/eigen_demo
```

部署 FAST-LIO2（ROS 1 Noetic，Docker）：见第 24–26 课与 `labs/deploy/`（`Dockerfile`、`run.sh`、`build_fastlio.sh`）。**这些脚本按上游 README 编写，未在本仓库的自动检查中实际构建镜像或回放录包**，第一次运行时请按课中检查点逐步核对。

## 使用方式

1. 首页完成诊断，按错题回到对应基础课；想先看到效果的，可走首页“部署先跑起来”路线，再回头补原理。
2. 每次只学一节：先预测，再手算，再运行，再解释变化；卡住时用本课的 AI 提示词让 AI 追问你。
3. 隔天闭卷重做；能解释和迁移后再记录状态。排错经历写进 `learning-records/bug-cases.md`。
4. 浏览器存储可能受限，请导出 JSON 备份。旧版（23 课）的记录会在首次打开时自动迁到新课号；旧导出文件也可直接导入。

## 旧周教材

原来的 11 份周教材保留为**进阶参考**，不是零基础入门，“三个月成为导航算法工程师”的说法已在页首更正。FAST_LIO 主分支是 ROS 1；涉及 ROS 2 / Jazzy 命令的页面有醒目提示，不能与 ROS 1 命令混用。第五周是新增补课导航，不冒充找回的原稿。

## 修改教材

`course/lessons.py` 保存正文（每课用 `key` 标识，课间引用写 `{L:key}`，生成时自动变成课号链接）；`course/build.py` 生成课程、首页、术语、实验手册、AI 陪练手册，并同步 `labs/cpp` 中的 C++ 文件。修改后执行 `py course/build.py`，再运行测试。`RESOURCES.md` 记录一手资料，`MISSION.md` 记录目标，`learning-records/` 记录真实学习证据。
