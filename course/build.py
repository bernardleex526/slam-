"""生成无网络依赖教材。运行：python course/build.py（Windows 用 py）。

课程正文在 lessons.py；本文件负责把每课渲染成页面，并生成首页、术语页、实验手册、AI 陪练手册，
修订旧周教材的入口说明，同步 labs/cpp 中的 C++ 示例。
"""
from pathlib import Path
from html import escape, unescape
import re
from lessons import LESSONS

ROOT = Path(__file__).resolve().parents[1]

SOURCES = {
 'book': ('机器人推理：状态、观测与行动', 'https://www.roboticsbook.org/S12_reasoning.html', 'Dellaert 与 Hutchinson 的课程书；用于建立建模入口。'),
 'python': ('Python 官方：数字与程序基础', 'https://docs.python.org/3/tutorial/introduction.html', '核对赋值、数值、列表等语言语义；本课程标准库代码在 Python 3.13 验证。'),
 'eigen': ('Eigen 官方：Getting started', 'https://libeigen.gitlab.io/eigen/docs-nightly/GettingStarted.html', '核对矩阵声明、编译和入门用法；实际工程按所用版本锁定。'),
 'ceres': ('Ceres 官方：非线性最小二乘', 'https://ceres-solver.readthedocs.io/latest/nnls_tutorial.html', '核对残差、自动求导、鲁棒损失和优化建模。'),
 'localization': ('机器人课程书：Localization', 'https://www.roboticsbook.org/S44_logistics_perception.html', '用于概率定位与滤波的进一步推导。'),
 'geometry': ('机器人课程书：三维运动', 'https://www.roboticsbook.org/S71_drone_state.html', '三维旋转与刚体运动的数学背景。'),
 'opencv': ('OpenCV 官方：相机标定与三维重建', 'https://docs.opencv.org/4.13.0/d9/d0c/group__calib3d.html', '核对投影、内外参与实际畸变模型。'),
 'fastlio': ('HKU-MARS：FAST_LIO 上游仓库', 'https://github.com/hku-mars/FAST_LIO', '核对激光惯性系统组成、ROS 1 环境与安装说明；阅读源码时额外记录提交。'),
 'icp': ('PCL 官方：ICP 入门', 'https://pointclouds.org/documentation/tutorials/iterative_closest_point.html', '核对点云配准接口与最小流程。'),
 'gtsam': ('GTSAM：Factor Graphs and GTSAM', 'https://gtsam.org/tutorials/intro.html', '核对变量、因子、位姿图与地标 SLAM 的关系。'),
 'rep105': ('Open Robotics：REP-105', 'https://github.com/openrobotics/reps/blob/main/_posts/rep-0105.md', '移动机器人坐标系命名与语义。'),
 'ros': ('ROS 2 Jazzy 教程源码', 'https://github.com/ros2/ros2_documentation/blob/jazzy/source/Tutorials.rst', '官方教程入口；docs.ros.org 本次访问被保护页阻挡，使用官方源码入口。'),
 'tum': ('TUM RGB-D 数据集与基准', 'https://cvg.cit.tum.de/data/datasets/rgbd-dataset', '真实轨迹评估数据与协议；不可把视觉 RGB-D 数据直接当作激光 IMU 输入。'),
 'nav2': ('Nav2 Jazzy：环境表达', 'https://docs.nav2.org/jazzy/getting_started/navigation_concepts/environmental_representation/', '占据、代价地图与导航接口，工程命令需按版本核对。'),
 'torch': ('PyTorch 官方：优化参数', 'https://docs.pytorch.org/tutorials/beginner/basics/optimization_tutorial.html', '训练循环、损失与参数更新；本课程基础实验不依赖 PyTorch。'),
 'vln': ('Anderson 等：Vision-and-Language Navigation', 'https://arxiv.org/abs/1711.07280', 'R2R 与视觉语言导航原始任务；进一步学习时先读任务设置。'),
 'spl': ('Anderson 等：On Evaluation of Embodied Navigation Agents', 'https://arxiv.org/abs/1807.06757', '通用导航评估与 SPL；遵循具体任务的成功定义。'),
 'world': ('Ha 与 Schmidhuber：World Models', 'https://worldmodels.github.io/', '早期学习世界模型的原论文与演示。'),
 'docker': ('Docker 官方：安装 Docker Engine', 'https://docs.docker.com/engine/install/ubuntu/', '部署课使用的容器工具；Windows 用户先装 WSL2 与 Docker Desktop。'),
 'dreamer': ('Hafner 等：DreamerV3', 'https://arxiv.org/abs/2301.04104', '学习世界模型与想象行为训练；本课程标量实验不是论文复现。'),
}


TERMS = [
 ('状态 state','希望估计的内部量，例如位置；传感器未必直接读到它。','problem'),
 ('观测 measurement','传感器实际读数，例如到墙的距离；与状态区分。','problem'),
 ('模型 model','把输入与预期输出连接的规则，例如 h(x)=10−x。','problem'),
 ('残差 residual','本教材一般用预测减实测；其他代码可能反过来，先看定义。','problem'),
 ('函数 function','输入一个或多个值，按规则产生输出；h(x) 不是 h 乘 x。','py_functions_debug'),
 ('维度 shape','向量分量数或矩阵行列数；不要和物理单位混淆。','rotation2d'),
 ('坐标系 frame','原点与轴方向的约定；同一物理点可有不同坐标。','vector'),
 ('向量 vector','多个有顺序的分量，可表达位移等量。','vector'),
 ('范数 norm','本课欧氏范数是向量长度；例如 (3,4) 长度为 5。','vector'),
 ('点积 dot product','对应分量相乘再求和；对单位方向点积才直接是投影长度。','vector'),
 ('矩阵 matrix','按行列组织的数表，乘向量时每行做一次点积。','rotation2d'),
 ('弧度 radian','旋转的计量方式；180°=π 弧度。','rotation2d'),
 ('转置 transpose','行列互换；Rᵀ 的第一行来自 R 的第一列。','rotation2d'),
 ('逆 inverse','撤销变换的操作；不是把矩阵每个数取倒数。','rotation2d'),
 ('导数 derivative','输入很小的变化引起输出多大变化。','derivative'),
 ('偏导 partial derivative','固定其他输入，只对一个输入求变化率。','derivative'),
 ('雅可比 Jacobian','多个输出对多个输入的局部变化率表。','derivative'),
 ('线性化 linearization','在当前点附近用直线或线性映射近似函数。','derivative'),
 ('均值 mean','相加再除数量，描述中心。','probability'),
 ('方差 variance','偏离均值的平方的平均量，单位也平方。','probability'),
 ('标准差 standard deviation','方差的非负平方根，单位与原变量一致。','probability'),
 ('协方差 covariance','多个变量的误差是否共同变化。','probability'),
 ('高斯 Gaussian','一种由均值和协方差描述的概率模型，不适用所有异常。','probability'),
 ('先验 prior / 后验 posterior','加入本次观测之前 / 之后的概率判断。','probability'),
 ('最小二乘 least squares','让残差平方总和尽量小的估计方法。','lsq_objective'),
 ('梯度 gradient','各输入方向导数组成的向量，指出局部增大方向。','lsq_iterate'),
 ('优化 optimization','根据目标函数寻找更好的参数或状态。','lsq_iterate'),
 ('鲁棒损失 robust loss','降低大残差影响的目标函数设计，不代替检查错误关联。','lsq_iterate'),
 ('增益 gain','测量差异进入状态修正的比例或矩阵。','kalman'),
 ('EKF / iEKF','非线性系统的局部线性滤波 / 迭代线性化更新。','kalman'),
 ('位姿 pose','位置与朝向；三维刚体通常有 6 个自由度。','pose_chain'),
 ('自由度 DOF','描述变化所需的独立量数目。','rot3d'),
 ('SO(3) / SE(3)','合法三维旋转 / 旋转加平移的刚体变换集合。','pose_chain'),
 ('李代数 Lie algebra','用于表达旋转等变换的局部增量空间。','pose_chain'),
 ('四元数 quaternion','以四个有约束的数表达旋转，顺序要按库核对。','rot3d'),
 ('内参 intrinsics / 外参 extrinsics','相机内部投影参数 / 两坐标系之间的刚体关系。','camera'),
 ('投影 projection','把相机坐标三维点变成像素位置。','camera'),
 ('BA 束调整','联合优化相机位姿与三维点，使重投影误差减小。','camera'),
 ('IMU','测角速度与比力的惯性传感器组合。','imu'),
 ('偏置 bias','持续偏离真实读数的误差成分，平均不一定消除。','imu'),
 ('积分 integration','累加许多小时间段的变化，速度积分成位移。','imu'),
 ('去畸变 deskew','按各点采集时间，把移动中扫描的点变到共同参考时刻。','imu'),
 ('点云 point cloud','空间采样点的集合。','icp'),
 ('配准 registration / ICP','求两组数据的对齐变换 / 交替最近点关联和估计的算法。','icp'),
 ('法向量 normal','垂直平面的方向；距离公式中的法向通常要求单位长度。','icp'),
 ('退化 degeneracy / 可观性 observability','观测能否约束各状态方向；某方向弱约束会使估计不稳。','icp'),
 ('秩 rank','线性映射中独立信息方向的数量。','icp'),
 ('SVD 奇异值分解','将矩阵拆为正交变换、缩放、正交变换。','icp'),
 ('因子 factor','连接一组变量的一条概率约束或误差关系。','graph'),
 ('回环 loop closure','重新来到过去地点形成的约束，加入前需要验证。','graph'),
 ('规范自由度 gauge','整体换参考系仍解释相同观测的自由度。','graph'),
 ('Eigen','C++ 线性代数库，负责计算而不决定物理模型。','cpp_eigen_cmake'),
 ('节点 node / 话题 topic','程序组件 / 持续消息通道。','ros_tf'),
 ('TF','带时间的坐标变换管理。','ros_tf'),
 ('QoS','通信可靠性、队列等服务约定。','ros_tf'),
 ('里程计 odometry / LIO','连续运动估计 / 激光惯性里程计。','fastlio_read'),
 ('体素 voxel','三维空间分桶，常用于降采样和地图组织。','fastlio_read'),
 ('ATE / RPE','全局轨迹误差 / 相对运动误差，需明确对齐与时间规则。','evaluate'),
 ('RMSE','误差平方平均后开方；保留原误差的单位。','evaluate'),
 ('基线 baseline / 消融 ablation','比较起点 / 移除某组件观察影响的实验。','evaluate'),
 ('代价地图 costmap','用数值表达障碍或通行代价的空间表示。','navigation'),
 ('启发式 heuristic','搜索中对剩余代价的估计。','navigation'),
 ('损失 loss','评价模型预测多差的标量分数。','ml'),
 ('反向传播 backpropagation','按链式法则计算网络参数的导数。','ml'),
 ('泛化 generalization','对未用于拟合与选择的数据仍能工作的能力。','ml'),
 ('嵌入 embedding / 注意力 attention','向量表示 / 用匹配分数加权选择信息。','ml'),
 ('VLN / VLM','视觉语言导航任务 / 处理视觉与语言的模型，二者不同。','vln'),
 ('grounding 落地','把语言中的对象与关系对应到实际环境。','vln'),
 ('SPL','同时考虑任务成功与路径效率的导航指标。','vln'),
 ('世界模型 world model','学习或表达动作条件下后续状态/观测的模型。','world'),
 ('潜在状态 latent state','从数据得到的内部表示，不一定有直接物理单位。','world'),
 ('策略 policy / 回报 return','如何选择动作的规则 / 累积奖励。','world'),
 ('滚动规划 MPC 思路','预测多步，只执行第一步，再观察和重算。','world'),
 ('主动回忆 active recall','合上书自己说出来、算出来，比反复阅读更能记住。','howto'),
 ('间隔复习 spaced review','隔天、约一周、约一月各重做一次，在快忘时复习效果最好。','howto'),
 ('终端 terminal','输入命令、查看程序输出的窗口；当前目录决定相对路径从哪里算。','py_basics'),
 ('变量 variable / 赋值','给数据起的名字；= 表示先算右边再存进左边。','py_basics'),
 ('类型 type','int 整数、float 小数、str 文字；文字 "3" 不能直接参与减法。','py_basics'),
 ('列表 list / 索引 index','按顺序保存多个数据；编号从 0 开始。','py_loops'),
 ('循环 loop / 缩进','for 对每个元素重复执行；Python 用缩进表示哪些行属于循环。','py_loops'),
 ('报错 traceback','出错时的调用记录；先读最后一行的错误类型，再看行号。','py_functions_debug'),
 ('断言 assert','条件不成立就停止并报告，用已知答案检查代码。','py_functions_debug'),
 ('权重 weight','测量在目标函数中的影响大小，常取 1/σ²。','lsq_objective'),
 ('步长 step size','每次沿梯度反方向走多远；太大会发散，太小收敛慢。','lsq_iterate'),
 ('欧拉角 Euler angles','用三个绕轴转角表示朝向，必须说明旋转顺序。','rot3d'),
 ('齐次变换 homogeneous transform','给坐标补 1，把旋转和平移合成一个矩阵乘法。','pose_chain'),
 ('编译 compile / 链接 link','把源代码翻译成机器码 / 把多个文件和库拼成一个程序。','cpp_basics'),
 ('引用 reference / const','& 让函数直接使用原数据 / const 保证不修改。','cpp_functions'),
 ('头文件 header','.h/.hpp 中放函数声明，供其他文件 include 后调用。','cpp_functions'),
 ('CMake','描述“用哪些文件、找哪些库、生成什么程序”的构建工具。','cpp_eigen_cmake'),
 ('ROS 1 / ROS 2','两代机器人软件框架，构建工具与命令不同，不能混用。','ros_tf'),
 ('镜像 image / 容器 container','打包好的系统环境 / 由镜像运行起来的独立环境。','deploy_env'),
 ('挂载 mount','让宿主机和容器共享同一个文件夹。','deploy_env'),
 ('工作空间 workspace','catkin 的固定目录结构：src 放源码，编译生成 build 与 devel。','deploy_run'),
 ('source 环境','让当前终端认识某个 ROS 安装或工作空间中的包；每个新终端都要做。','deploy_run'),
 ('录包 rosbag','保存的话题消息，可反复回放以重复实验。','deploy_run'),
 ('提交号 commit','代码版本的唯一编号，复现与读源码都以它为准。','deploy_run'),
 ('重映射 remap','运行时把话题改名，例如 旧名:=新名。','deploy_debug'),
 ('Bug 案例库','记录现象、根因、验证、修复、预防的个人排错手册。','deploy_debug'),
]

def slider(name, label, lo, hi, step, value):
    return f'<label>{label}<input type="range" name="{name}" min="{lo}" max="{hi}" step="{step}" value="{value}"></label>'

def laboratory(kind):
    if not kind: return ''
    head = '<h2>改一个条件，观察因果</h2><p>先写下你的预测，再动滑块。图下会展开当前数字的计算过程。</p>'
    if kind == 'residual':
        controls = slider('x','机器人位置 x（米）',0,9,.1,6)
        graphic = '<svg viewBox="0 0 460 110" role="img" aria-label="一维走廊：圆点是机器人，右侧竖线是10米处的墙"><line x1="30" y1="55" x2="430" y2="55" stroke="#888"/><line x1="430" y1="15" x2="430" y2="80" stroke="#8a4b22" stroke-width="5"/><circle class="robot" cx="270" cy="55" r="10" fill="#17604d"/><text x="25" y="95">0米</text><text x="368" y="100">墙 10米</text></svg>'
    elif kind == 'transform':
        controls = slider('angle','朝向 θ（度）',-180,180,5,90)+slider('px','点的机器人 x（米）',-2,2,.1,1)+slider('py','点的机器人 y（米）',-2,2,.1,0)
        graphic = '<svg viewBox="0 0 480 330" role="img" aria-label="地图中的点随机器人朝向改变；箭头表示机器人前方"><path d="M20 200H460 M180 20V310" stroke="#bbb"/><text x="460" y="190">x</text><text x="190" y="25">y</text><circle cx="240" cy="170" r="6" fill="#17604d"/><line class="direction" x1="240" y1="170" x2="240" y2="135" stroke="#17604d" stroke-width="5"/><circle class="point" cx="240" cy="140" r="9" fill="#286bac"/><text x="250" y="190">机器人 (2,1)</text><text x="155" y="220">(0,0)</text></svg>'
    elif kind == 'fusion':
        controls = slider('r','测量方差 R（米²）',.005,1,.005,.2)
        graphic = '<svg viewBox="0 0 440 120" role="img" aria-label="融合位置位于1米预测与1.2米测量之间"><line x1="60" y1="50" x2="360" y2="50" stroke="#aaa"/><circle cx="60" cy="50" r="5" fill="#666"/><circle cx="360" cy="50" r="5" fill="#666"/><circle class="estimate" cx="120" cy="50" r="10" fill="#17604d"/><text x="20" y="100">预测 1米</text><text x="290" y="100">测量 1.2米</text></svg>'
    elif kind == 'camera':
        controls = slider('z','深度 Z（米）',1,8,.1,2)
        graphic = '<svg viewBox="0 0 640 480" role="img" aria-label="640乘480像素画幅；十字为主点，圆点为投影"><path d="M0 240H640 M320 0V480" stroke="#ccc"/><circle class="pixel" cx="520" cy="340" r="9" fill="#17604d"/><text x="330" y="225">主点 (320,240)</text><text x="15" y="25">像素 x 向右，y 向下</text></svg>'
    else:
        controls = slider('theta','模型 θ（米/单位动作）',.4,1.2,.01,1)+slider('n','连续动作步数',1,10,1,2)
        graphic = '<svg viewBox="0 0 420 150" role="img" aria-label="模型预测与真实位置的横条比较，条长按同一比例绘制"><text x="10" y="30">预测</text><rect class="prediction" x="90" y="12" width="40" height="28" fill="#8a4b22"/><text x="10" y="90">真实</text><rect class="truth" x="90" y="72" width="32" height="28" fill="#17604d"/><text x="90" y="135">每20图像单位 = 1米</text></svg>'
    return head+f'<section class="lab" data-lab="{kind}" aria-label="互动实验"><div class="lab-controls">{controls}</div>{graphic}<output aria-live="polite"></output></section>'



KEY = {item['key']: n for n, item in enumerate(LESSONS, 1)}
# 与课程配套的 C++ 文件，由课文代码同步生成，保证“页面上的代码”和“仓库里的文件”一致。
CPP_FILES = {'cpp_basics': 'labs/cpp/01_basics.cpp', 'cpp_functions': 'labs/cpp/02_functions.cpp', 'cpp_eigen_cmake': 'labs/cpp/eigen_demo/main.cpp'}
STEP_HEADING = {'howto', 'py_basics', 'cpp_basics', 'cpp_functions', 'cpp_eigen_cmake', 'ros_tf', 'deploy_env', 'deploy_run', 'deploy_debug'}
LANG_NOTE = {'python': 'Python：可直接运行。先写下预测，再运行核对。', 'cpp': 'C++：需要在 Linux 中编译后运行，命令见上文。',
             'bash': '终端命令：在对应环境（本课为 Docker 容器内的 ROS 1 Noetic）逐条执行，每条都对照检查点。'}


def write(path, value):
    path = ROOT/path
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(value, encoding='utf-8', newline='\n')


def filename(n):
    return f'{n:04d}-lesson.html'


def num(ref):
    return ref if isinstance(ref, int) else KEY[ref]


def link(ref, prefix=''):
    n = num(ref)
    return f'<a href="{prefix}{filename(n)}">{n:02d} · {escape(LESSONS[n-1]["title"])}</a>'


def resolve(text, prefix='', html=True):
    """把 {L:key} 换成“第 NN 课”；html=True 时带链接。"""
    def replace(match):
        n = KEY[match[1]]
        return f'<a href="{prefix}{filename(n)}">第 {n:02d} 课</a>' if html else f'第 {n:02d} 课'
    return re.sub(r'\{L:(\w+)\}', replace, text)


def plain(text):
    """HTML 片段转纯文本，用于 AI 提示词。"""
    return unescape(re.sub(r'<[^>]+>', '', resolve(text, html=False))).strip()


def page(title, content, prefix='', ident='home', wide=False):
    return f'''<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>{escape(title)} · SLAM 学习实验室</title><link rel="stylesheet" href="{prefix}assets/style.css"><script src="{prefix}assets/app.js" defer></script></head>
<body data-lesson="{ident}"><a class="skip" href="#main">跳到正文</a><nav class="top" aria-label="主导航"><a href="{prefix}index.html">SLAM 学习实验室</a><a href="{prefix}reference/glossary.html">术语与符号</a><a href="{prefix}reference/labs.html">实验手册</a><a href="{prefix}reference/ai.html">AI 陪练</a><a href="{prefix}reference/sources.html">一手资料</a></nav><main id="main" class="shell {'' if wide else 'reading'}">{content}<footer>离线教材 · 2026-10 修订 · 先预测，再计算，再运行，最后解释。学习目标：能独立建模、实现与诊断，继续走向 VLN 和世界模型。</footer></main></body></html>'''


def numeric(question, expected, explain, ident):
    return f'''<div class="numeric panel"><label for="q-{ident}">{escape(question)}</label><input id="q-{ident}" type="number" step="any" inputmode="decimal"><button type="button" data-check="{expected}" data-explain="{escape(explain, quote=True)}">检查数值</button><output aria-live="polite"></output></div>'''


def prompt_box(label, text):
    return f'<details class="prompt"><summary>{label}</summary><pre><code>{escape(text)}</code></pre><button type="button" data-copy>复制提示词</button></details>'


def ai_prompts(item):
    title, code = item['title'], resolve(item['code'], html=False)
    prompts = [('① 追问我：检查是不是真懂',
                f'我在学 SLAM 入门课《{title}》。本课目标：{plain(item["goal"])}\n请做我的追问教练：一次只问一个问题，共 3 题，依次考直觉、手算、“改一个条件会怎样”。等我回答后先指出对错和原因，再问下一题。不要提前给答案，不要一次讲一大段。')]
    if item['lang'] == 'cpp':
        prompts.append(('② 换个写法出题：先预测再编译', f'下面是课里的 C++ 代码。请出 2 道“改一处代码，先预测输出或编译报错”的练习，只给题目不给答案。等我写出预测，再告诉我怎样编译运行来核对。\n\n{code}'))
    elif item['lang'] == 'bash':
        prompts.append(('② 逐条考我命令：做什么、成功看什么、失败查什么', f'下面是课里的终端命令（ROS 1 Noetic 环境，不要引入 ROS 2 命令）。请一次问我一条：这条命令做什么、成功时应看到什么、失败时先查什么。等我回答再继续。\n\n{code}'))
    else:
        prompts.append(('② 换个数出题：先预测再运行', f'下面是课里的代码。请出 2 道“改一个数字，先预测输出”的练习，只给题目不给答案。等我写出预测，再告诉我怎样自己运行来核对。\n\n{code}'))
    prompts.append(('③ 审查我的解答', f'题目：{plain(item["question"])}\n我的解答：（在这里粘贴你的过程和理由）\n请只指出哪一步的单位、符号、坐标系或逻辑有问题，用提问引导我自己改，不要直接给出完整答案。'))
    prompts.append(('④ 讲给 AI 听：费曼复述', f'我会用自己的话讲解《{title}》的核心内容。请扮演完全不懂的初学者，在我讲得含糊、跳步或用了没解释的术语时打断我提问。最后列出我讲错的地方。不要替我讲。'))
    if item['ai']:
        prompts.append(('⑤ 本课专用', resolve(item['ai'], html=False)))
    return ''.join(prompt_box(label, text) for label, text in prompts)


def lesson_terms(key):
    return [term for term, _, k in TERMS if k == key]


def build_lessons():
    for n, item in enumerate(LESSONS, 1):
        key = item['key']
        R = lambda text: resolve(text)
        prerequisites = '；'.join(link(i) for i in item['prereq']) or '无需先修；只从具体数字开始。'
        refs = '；'.join(f'<a href="{SOURCES[k][1]}">{SOURCES[k][0]}</a>' for k in item['refs'])
        prev = link(n-1) if n > 1 else '<a href="../index.html">入口诊断</a>'
        nxt = link(n+1) if n < len(LESSONS) else '<a href="../index.html#legacy">按能力回到原教材</a>'
        terms = lesson_terms(key)
        term_box = f'<p class="subtle">本课新词（{len(terms)} 个）：{"、".join(escape(t) for t in terms)}。随时可查 <a href="../reference/glossary.html">术语页</a>。</p>' if terms else ''
        heading = '一步步讲清楚' if key in STEP_HEADING else '从实际问题走到公式'
        code = resolve(item['code'], html=False)
        content = f'''<header class="hero"><div class="eyebrow">{item['stage']} / LESSON {n:02d}</div><h1>{item['title']}</h1><p>{R(item['goal'])}</p><p class="subtle">先修：{prerequisites}</p><p class="subtle">预计用时：{item['time']}。一次学不完就分开，第二天先闭卷重做上一段。</p>{term_box}</header>
<section class="panel"><h2>先打个比方</h2><p>{R(item['analogy'])}</p><p class="subtle">比喻只帮你建立直觉；下面用数字、公式和代码把它说准确。</p></section>
<div class="flow" aria-label="学习步骤"><span>比方</span><b>→</b><span>具体问题</span><b>→</b><span>手算</span><b>→</b><span>代码</span><b>→</b><span>解释</span></div>
<h2>{heading}</h2>{R(item['body'])}
{laboratory(item['lab'])}<h2>{escape(item['code_title'] or '把公式落实到每行代码')}</h2><p class="subtle">{LANG_NOTE[item['lang']]}</p><pre><code>{escape(code)}</code></pre><p>{R(item['trace'])}</p>
<h2>先独立作答，再打开提示</h2><p>{R(item['question'])}</p><label for="answer">你的过程、单位与理由</label><textarea id="answer" data-save="answer" placeholder="不要只写结论：说明已知什么、求什么、每一步为什么这样算。"></textarea>
<details><summary>提示：只给下一步</summary><p>{R(item['hint'])}</p></details><details><summary>核对解答与常见错因</summary><p>{R(item['answer'])}</p><p>若还无法解释，回到先修：{prerequisites}。闭上答案，换一组数字重算。</p></details>
{numeric(*item['check'], ident=str(n))}<details><summary>改变条件的迁移练习与解析</summary><p>{R(item['transfer'])}</p></details>
<section class="panel" id="ai"><h2>AI 陪练：让它追问你，而不是替你做</h2><p>先自己写完上面的解答，再打开 AI。它给出的数字要手算或运行核对，命令要先问清会改动什么。完整规则见 <a href="../reference/ai.html">AI 陪练手册</a>。</p>{ai_prompts(item)}</section>
<section class="panel"><h2>一句话总结</h2><p><b>{R(item['summary'])}</b></p><p class="subtle">合上页面，用自己的话说一遍；说不出来，回到上面卡住的那一段。</p></section>
<h2>留下理解证据</h2><p>用自己的话说：这个方法解决什么问题？公式或命令中的量从哪里来？改一个条件，结果为什么变化？把没理解的具体步骤、AI 说错的地方都写下来。</p><textarea aria-label="本课解释与疑问" data-save="reason"></textarea>
<label>学习状态（自评，不是自动认证）<select data-save="state"><option>尚未记录</option><option>需要补课</option><option>能跟着算</option><option>能独立解释与迁移</option><option>隔天闭卷复做通过</option></select></label><label>复习记录<textarea data-save="review" placeholder="隔天、约一周后、约一月后重做；写日期、是否看答案、哪里又忘了。"></textarea></label>
<div class="toolbar"><button data-export type="button">导出学习记录</button></div><p id="save-status" class="subtle" role="status"></p>
<details><summary>选读一手资料</summary><p>{refs}</p><p>本课数值例子是教学构造。外部链接用于核对和深入，不是完成本课练习的前置要求。网页可能更新；真实系统复现应额外锁定软件提交与环境。</p></details><nav class="bottom-nav" aria-label="课程翻页"><span>上一课<br>{prev}</span><span>下一课<br>{nxt}</span></nav>'''
        write('lessons/'+filename(n), page(item['title'], content, '../', f'{n:04d}'))
    for key, path in CPP_FILES.items():
        write(path, resolve(LESSONS[KEY[key]-1]['code'], html=False)+'\n')


LEGACY = [('一','线性代数、C++、Eigen、FAST-LIO2',['rotation2d','icp','cpp_basics','cpp_eigen_cmake','deploy_run','fastlio_read']),
          ('二','导数、雅可比、运动学',['derivative','rot3d','pose_chain','navigation']),
          ('三','概率、Kalman、ROS、TF',['probability','kalman','ros_tf']),
          ('四','优化与调试',['lsq_objective','lsq_iterate','deploy_debug','evaluate']),
          ('五','新增补课与阶段验收',['problem','kalman','slam1d']),
          ('六','EKF 与里程计',['kalman','imu']),
          ('七','点云配准与 LIO',['imu','icp','deploy_run','fastlio_read']),
          ('八','外参与双雷达',['pose_chain','imu','ros_tf','fastlio_read']),
          ('九','图搜索与导航',['navigation']),('十','全局规划与通过性',['navigation']),('十一','局部规划与控制',['navigation']),
          ('十二','回环与综合项目',['graph','slam1d','evaluate','capstone'])]
DIAG = ['problem', 'vector', 'rotation2d', 'derivative', 'kalman']


def build_home():
    cards = ''
    last_stage = None
    for n, item in enumerate(LESSONS, 1):
        if item['stage'] != last_stage:
            if last_stage: cards += '</div>'
            cards += f'<h3>{item["stage"]}</h3><div class="grid">'
            last_stage = item['stage']
        cards += f'<article class="card"><div class="number">LESSON {n:02d} · {escape(item["time"])}</div><h3>{link(n,"lessons/")}</h3><p>{resolve(item["goal"], "lessons/")}</p><span class="state" data-progress="{n:04d}">尚未记录</span></article>'
    cards += '</div>'
    diagnostics = ''.join(numeric(*LESSONS[KEY[k]-1]['check'], ident='diag'+str(i)) for i, k in enumerate(DIAG, 1))
    route = '；'.join(f'题{i}→{link(k, "lessons/")}' for i, k in enumerate(DIAG, 1))
    rows = ''.join(f'<tr><td><a href="第{w}周学习教材.html">原第{w}周</a></td><td>{topic}</td><td>{"<br>".join(link(k,"lessons/") for k in ks)}</td></tr>' for w, topic, ks in LEGACY)
    d1, d3, ros = KEY['deploy_env'], KEY['deploy_debug'], KEY['ros_tf']
    content = f'''<header class="hero"><div class="eyebrow">BUILD UNDERSTANDING / 学习路径</div><h1>让公式、代码<br>和机器人对上号。</h1><p>从一条走廊里的测距开始，逐步学到 SLAM 工程、视觉语言导航和世界模型。每课先打比方，再用具体数字讲清楚，最后让 AI 追问你是否真懂。</p><a class="button" href="lessons/{filename(1)}">从第 01 课开始</a> <a href="#diagnosis">先做入口诊断</a></header>
<div class="flow"><span>学习方法与 AI 陪练</span><b>→</b><span>数学与 Python</span><b>→</b><span>几何与估计</span><b>→</b><span>C++ 与部署</span><b>→</b><span>VLN / 世界模型</span></div>
<section class="panel"><h2>这一次怎样学</h2><p>已知你的起点是“会部署、会让 AI 帮忙调试，但说不清公式和代码为什么这样写”。每课只推进一个核心问题，页首列出本课新词。流程是：<b>先打比方 → 看完整数值例子 → 逐项读公式 → 对应代码 → 独立作答 → AI 陪练 → 一句话总结</b>。</p><p><b>AI 是陪练，不是替身。</b>每课都有可复制的提示词，让 AI 追问你、给你换数出题、审查你的解答、听你复述。先自己做，再问 AI；AI 给的数字要核对，命令要问清楚会改什么。规则见{link('howto','lessons/')}和 <a href="reference/ai.html">AI 陪练手册</a>。</p><p>学习一节 → 隔天闭卷重做 → 一周后混合复习。错题回到先修课，能独立解释与迁移才往下推进。每课标注了预计用时；<b>不承诺“几周成为工程师”</b>，以每周约 5 小时估计，主线前 19 课通常需要几个月。</p><p><b>目标是可验证的能力，读完页数不是职级认证。</b>第 {KEY["capstone"]:02d} 课给出初级到中级所需的项目证据。</p></section>
<section class="panel"><h2>你擅长部署：可以先把系统跑起来</h2><p>如果你想先看到成果，学完第 01 课后可以直接做第 {d1:02d}–{d3:02d} 课：用 Docker 搭好 ROS 1 Noetic，编译 FAST-LIO2，回放官方录包，看到地图和轨迹。每一步都有检查点和故障对照表。开始前先读第 {ros:02d} 课里的 ROS 1/ROS 2 命令对照表。</p><p>跑起来不等于懂了。部署课会反复指回主线：去畸变在第 {KEY["imu"]:02d} 课，配准在第 {KEY["icp"]:02d} 课，迭代更新在第 {KEY["lsq_iterate"]:02d} 和 {KEY["kalman"]:02d} 课。主线学到第 {KEY["fastlio_read"]:02d} 课时，再回到你跑过的系统，沿一帧数据把它读懂。</p></section>
<section id="diagnosis"><h2>入口诊断：定位缺口，不给你贴分数</h2><p>没有学过的内容可以空着。{route}。即使数字答对，也试着解释“这些数字从哪里来”。编程方面，如果你看不懂 <code>for z in [2.9, 3.0]:</code>，从{link('py_basics','lessons/')}开始。</p><details><summary>展开 5 道诊断题</summary>{diagnostics}</details></section>
<section id="curriculum"><h2>{len(LESSONS)} 节课，按能力逐步接上</h2><label>查课程<input type="search" data-filter=".card" placeholder="输入：矩阵、Docker、相机、VLN……"></label>{cards}</section>
<section class="panel"><h2>你的学习记录</h2><p>每课保存解题过程、自评和复习记录。数据保存在当前浏览器，不上传。直接打开文件时，不同浏览器可能把每页存储隔离；请在学过的页面导出，再到首页合并导入。要统一来源，也可按实验手册启动本地网页服务。部署和调试中遇到的问题，记到 <code>learning-records/bug-cases.md</code>。</p><div class="toolbar"><button type="button" data-export>导出当前记录</button><label>导入记录<input id="import-progress" type="file" accept=".json,application/json"></label></div><p id="import-status" role="status">导入时同课采用文件记录，其他课保留。</p></section>
<section id="legacy"><h2>回到原教材：每一周应该什么时候读</h2><p>原仓库的十一份周教材保留为<b>进阶阅读</b>，不是入门主线。它们原本写着“零基础、三个月成为导航算法工程师”，这并不成立：实际需要初中数学、能读简单 C++，并按每周约 15 小时推进。每页顶部已加修订说明。</p><p><b>ROS 版本提醒：</b>旧教材的 ROS 示例多为 ROS 2（Jazzy），而本课程部署的 FAST-LIO2 官方 main 分支是 ROS 1（Noetic），两套命令不能混用，对照表见{link('ros_tf','lessons/')}。原本缺少第五周文件，这里新增补课导航。</p><div class="table-wrap"><table><thead><tr><th>原入口</th><th>内容</th><th>先完成新课程</th></tr></thead><tbody>{rows}</tbody></table></div></section>'''
    write('index.html', page('从零建立 SLAM 理解', content, wide=True))



AI_PAGE = '''<h1>AI 陪练手册</h1><p>这套课默认你会用 AI 帮忙调试。这一页把“怎样用 AI 学得更快，而不是学得更少”写成固定规则和可复制的模板。每课底部也有针对该课的提示词。</p>
<section class="panel"><h2>一条总原则</h2><p><b>先自己做，再让 AI 追问、出题、审查；AI 给出的数字一律核对，命令一律问清会改什么。</b>AI 生成的代码，你讲不清的那一行，就不能留在你的项目里。</p></section>
<h2>四种角色</h2><div class="table-wrap"><table><tr><th>角色</th><th>什么时候用</th><th>你必须先做的事</th></tr>
<tr><td>追问教练</td><td>学完一节，想确认是否真懂</td><td>先写下自己的解答</td></tr>
<tr><td>出题人</td><td>想多练几道“改一个数”的题</td><td>每题先写预测，再运行</td></tr>
<tr><td>代码审查员</td><td>读不懂 AI 或开源项目的代码</td><td>先给自己能懂的行写注释，只问不懂的行</td></tr>
<tr><td>报错翻译</td><td>部署或运行报错</td><td>收集环境、命令、完整日志，按分层顺序自己先查一遍</td></tr></table></div>
<h2>三条红线</h2><ol><li><b>核对</b>：数字手算或运行；命令先问“会修改哪些文件、能否撤销”。AI 常把 ROS 1 和 ROS 2 命令混在一起，求助时一定写明“ROS 1 Noetic”。</li><li><b>保密</b>：不粘贴密码、密钥、Token、公司内部代码和数据。</li><li><b>可解释</b>：提交任何代码前，你要能给每一行写注释。讲不清就继续问，或者删掉。</li></ol>
<h2>通用提示词</h2>'''

AI_TEMPLATES = [
 ('追问我（学完一节后）', '我在学《课程标题》。本课目标：（粘贴页首目标）\n请做我的追问教练：一次只问一个问题，共 3 题，依次考直觉、手算、“改一个条件会怎样”。等我回答后先指出对错和原因，再问下一题。不要提前给答案。'),
 ('解释 AI 或开源代码（逐行审查）', '下面这段代码我只看懂了一部分。我已经在看懂的行后面写了中文注释，没写注释的行请你逐行解释：输入是什么、输出是什么、单位和坐标系是什么。不要改写代码，也不要扩展功能。\n（粘贴代码）'),
 ('报错求助（部署与运行）', '环境：（例：Docker osrf/ros:noetic-desktop-full，Ubuntu 20.04，ROS 1 Noetic；FAST_LIO 提交号 xxxx）\n我在做：（哪一课、哪一步）\n运行的命令：（原样粘贴）\n完整输出：（从命令开始到报错结束，全部粘贴）\n我已经检查过：（rosversion -d、rospack find、rostopic hz 等的结果）\n这是 ROS 1，请不要给 ros2 或 colcon 命令。先告诉我最可能的 1 个原因和验证方法，等我验证后再说下一步。'),
 ('Bug 复盘（解决之后）', '请把下面的排查过程整理成一条 Bug 案例：现象（原文报错）、根因、验证方法、修复步骤、以后怎么预防。只用我提供的信息，缺的字段写“待补充”，不要猜。\n（粘贴过程）'),
 ('费曼复述（隔天复习）', '我会凭记忆讲解昨天学的《课程标题》。请扮演完全不懂的初学者，在我讲得含糊、跳步或用了没解释的术语时打断提问，最后列出我讲错的地方。不要替我讲。'),
]

AI_TAIL = '''<h2>怎样判断 AI 的回答靠不靠谱</h2><ul><li>它给的数字能否用课里的公式手算出来？</li><li>它给的命令属于哪一代 ROS？有没有 sudo、rm、修改系统文件？</li><li>它解释的原因能否用一个小实验验证？例如“话题名不一致”可以用 rostopic list 立刻确认。</li><li>它是否同时让你改了好几处？一次只改一处，才能知道是哪一处起了作用。</li></ul>
<h2>Bug 案例库模板</h2><p>复制到 <code>learning-records/bug-cases.md</code>，每解决一个问题写一条。攒到 10 条，你就有了自己的排错手册（保留自旧教材的做法）。</p>
<pre><code>## 2026-xx-xx 标题（用现象命名，例如“rviz 空白但不报错”）
- 所在课程/步骤：
- 环境与版本：
- 现象（原文报错）：
- 复现步骤：
- 根因：
- 我是怎么验证的：
- 修复：
- 以后怎么预防：
- AI 帮了什么 / AI 说错了什么：</code></pre>'''


def build_reference():
    entries = ''.join(f'<section class="glossary-entry" id="term-{i}"><h2>{escape(term)}</h2><p>{meaning} {link(k,"../lessons/")}</p></section>' for i, (term, meaning, k) in enumerate(TERMS))
    symbols = '<div class="table-wrap"><table><tr><th>符号</th><th>怎么读、什么意思</th></tr><tr><td>Σ / ∑</td><td>求和，把各项加起来；若表示协方差矩阵则看上下文定义。</td></tr><tr><td>Δ、δ、ε</td><td>变化量、小改变量、小步长；具体单位跟变量一致。</td></tr><tr><td>θ、μ、σ、π、α</td><td>theta 角度，mu 均值，sigma 标准差，alpha 步长；pi 可为圆周率，也可表示策略，按定义区分。</td></tr><tr><td>下标 i / 上标 T / 帽子</td><td>编号 / 转置 / 估计值；坐标系上标不是乘方。</td></tr><tr><td>T_AB</td><td>本教材约定为“把 B 坐标系中的坐标变到 A”，读下标从右往左。</td></tr><tr><td>argmin / ∂ / ∝</td><td>找使函数最小的输入 / 偏导符号 / 成比例，概率中常须再归一化。</td></tr><tr><td>米、米²、像素、弧度</td><td>位置与距离、方差、图像坐标、角度单位；相加前必须确认单位相容。</td></tr></table></div>'
    write('reference/glossary.html', page('术语和符号，随查随回', f'<h1>术语与符号</h1><p>字母会被不同代码重复使用。r 可能是残差，也可能是测量方差，先看所在公式的定义。每个术语后面是首次讲解它的课。</p>{symbols}<label>检索中英文术语<input type="search" data-filter=".glossary-entry" placeholder="例如 residual、雅可比、TF、Docker"></label>{entries}', '../'))
    refs = ''.join(f'<section><h2>{name}</h2><p>{note}</p><a href="{url}">打开一手资料</a></section>' for name, url, note in SOURCES.values())
    write('reference/sources.html', page('一手资料与核验边界', f'<h1>一手资料</h1><p>核验日期：2026-10。这里只选官方文档、作者论文或课程书。课程中的数字、程序与问题是教学构造；软件文档会更新，实际复现请记录提交或版本。</p>{refs}', '../'))
    write('RESOURCES.md', '# 一手资料\n\n核验日期：2026-10。\n\n## Knowledge\n\n'+'\n\n'.join(f'- [{name}]({url})\n  {note}' for name, url, note in SOURCES.values())+'\n\n## Wisdom\n\n未要求加入社区；不以外部问答代替课内解释。AI 只作为陪练使用，规则见 reference/ai.html。\n\n## Gaps 与边界\n\n浏览器、Python 标准库实验与 C++/Eigen 示例已在本环境验证；部署课的 Dockerfile 与脚本依据 FAST_LIO 官方 README、config/avia.yaml 与源码中的话题名编写，但本环境无法运行 Docker、ROS 与真实录包，首次使用请按检查点逐步核对。学习者设备、每周时间与独立编程能力仍未知。高级课提供概念桥梁与工程验收，不宣称完整复现论文。\n')
    write('reference/ai.html', page('AI 陪练手册', AI_PAGE+''.join(prompt_box(label, text) for label, text in AI_TEMPLATES)+AI_TAIL, '../'))
    L = lambda k: link(k, '../lessons/')
    labtext = f'''<h1>实验手册</h1><p>先看对应课的例子，再运行程序。命令在解压后的仓库目录执行；命令窗口叫终端，当前目录决定相对路径从哪里开始。实验分三层：浏览器、Python、Linux（C++ 与部署）。</p>
<h2>第一层：无需安装</h2><p>直接双击 index.html，打开带滑块的课（墙距残差、二维变换、测量融合、相机投影、世界模型）。网页不是 Python 编辑器，页面代码展示与运行脚本分开。</p>
<h2>第二层：Python 环境与执行位置</h2><p>Windows 先在终端输入 <code>py --version</code>，Linux/macOS 输入 <code>python3 --version</code>。若显示 Python 3.x，解释器可用；若找不到命令，先用浏览器实验，或到 <a href="https://www.python.org/downloads/">Python 官方下载页</a> 安装。详细步骤见 {L('py_basics')}。</p>
<p>在仓库文件夹里通过文件管理器“在终端打开”，确认能看到 labs 文件夹。Windows 以下用 py，Linux/macOS 替换为 python3。每次运行单独一条命令。若命令说找不到文件，先检查当前目录，不要重新装所有库。</p>
<pre>py labs/core.py
py labs/slam_1d.py
py labs/navigation.py
py labs/world_model.py
py labs/deploy/check_bag.py</pre>
<div class="table-wrap"><table><tr><th>程序与对应课</th><th>先预测什么</th><th>应看到什么</th><th>动手修改</th></tr>
<tr><td>core.py / {L('rotation2d')}、{L('kalman')}、{L('camera')}</td><td>旋转后的点、融合位置、像素</td><td>(2,2)；位置1.04，方差0.04，K=0.2；像素(520,340)</td><td>把旋转90改为0，先算再运行。</td></tr>
<tr><td>slam_1d.py / {L('slam1d')}</td><td>三条位置与未知地标</td><td>[0,1.1375,2.05]；地标4.0625；RMSE约0.12910→0.08447</td><td>将 estimate 的观测参数改为(6,5,4)，位置应不变，地标加2。</td></tr>
<tr><td>navigation.py / {L('navigation')}、{L('vln')}</td><td>红门对应节点与路径</td><td>R；[S,A,R]；SPL 0.6667 与0</td><td>增加另一个red door标签，应报歧义错误。将A与R双向断开，应返回None不可达。</td></tr>
<tr><td>world_model.py / {L('world')}</td><td>拟合系数与两步预测</td><td>θ=0.799；留出MSE约0.036667→0.000001；计划(1,1)，预测1.598，合成真实1.6；换摩擦后1.0</td><td>只用零动作训练应报不可辨识；把测试动力学改为0.5，旧模型误差增加。</td></tr>
<tr><td>deploy/check_bag.py / {L('deploy_debug')}</td><td>示例配置哪个话题对不上</td><td>lid_topic 约 10 Hz；imu_topic=/imu/data 不在录包里</td><td>把 sample_config.yaml 的 imu_topic 改成 /livox/imu，应显示“通过”。</td></tr></table></div>
<h2>第三层 A：C++ 与 Eigen（Linux / WSL2 / 容器）</h2><p>需要 g++；Eigen 示例另需 cmake 与 libeigen3-dev（<code>sudo apt install build-essential cmake libeigen3-dev</code>）。</p>
<pre>g++ -std=c++17 labs/cpp/01_basics.cpp -o basics &amp;&amp; ./basics
g++ -std=c++17 labs/cpp/02_functions.cpp -o functions &amp;&amp; ./functions
cd labs/cpp/eigen_demo &amp;&amp; mkdir -p build &amp;&amp; cd build &amp;&amp; cmake .. &amp;&amp; make &amp;&amp; ./eigen_demo</pre>
<p>应分别看到 7.1/7/6.9 与“3 3.5”（{L('cpp_basics')}）、−0.1 与 3.2（{L('cpp_functions')}）、“2 2”与“1 0”（{L('cpp_eigen_cmake')}）。</p>
<h2>第三层 B：部署 FAST-LIO2（Docker + ROS 1 Noetic）</h2><p>按 {L('deploy_env')} → {L('deploy_run')} → {L('deploy_debug')} 的顺序做，每步都有检查点。文件都在 <code>labs/deploy/</code>：</p>
<div class="table-wrap"><table><tr><th>文件</th><th>在哪里运行</th><th>作用</th></tr>
<tr><td>Dockerfile</td><td>宿主机：<code>docker build -t slam-noetic labs/deploy</code></td><td>Ubuntu 20.04 + ROS 1 Noetic + Eigen/PCL + Livox-SDK</td></tr>
<tr><td>run.sh</td><td>宿主机：<code>bash labs/deploy/run.sh</code></td><td>创建或进入容器；~/slam_ws 挂载到容器 /root/slam_ws，仓库只读挂载到 /root/course</td></tr>
<tr><td>build_fastlio.sh</td><td>容器内</td><td>手动步骤的参考答案：编译 livox_ros_driver 与 FAST_LIO，记录提交号</td></tr>
<tr><td>check_bag.py</td><td>宿主机或容器</td><td>对照 rosbag info 与 FAST_LIO 配置，检查话题名、类型、频率</td></tr></table></div>
<p><b>本环境未运行 Docker、ROS 与真实录包</b>：脚本依据 FAST_LIO 官方 README、config/avia.yaml 与源码编写。上游更新后命令可能变化，以检查点为准，遇到不一致请按 {L('deploy_debug')} 排查并记录。录包需从 FAST_LIO README 的链接下载（Google Drive，国内网络可能需要代理）。</p>
<h2>最小项目交付清单</h2><p>每个实验提交四项：运行前手算；修改过的代码；实际输出；一句能被实验否定的解释。部署实验另加：提交号、录包名、完整命令、截图与 Bug 记录。不要只交截图。运行测试可以检查实现，但不能替你证明理解。</p><pre>py -m unittest discover -s tests -v</pre>
<h2>让所有页面共用同一个学习记录来源</h2><p>可选：在仓库目录运行下列命令。http.server 是 Python 内置的静态网页服务，8765 是端口，127.0.0.1 只在本机监听。在浏览器打开 <a href="http://127.0.0.1:8765/">本机学习首页</a>。此终端保持运行，用 Ctrl+C 结束。若端口被占用，把命令和地址中的8765一起换成8766。</p><pre>py -m http.server 8765 --bind 127.0.0.1</pre>
<h2>常见卡点</h2><p>文件末尾看起来是 .py 但仍不能运行：检查是不是 .py.txt。小数出现极小差别：先按合理容差比较。import labs 失败：从仓库目录运行，或直接运行脚本。改了 C++ 没效果：忘了重新编译。ros2 命令找不到：你在 ROS 1 环境里，见 {L('ros_tf')} 的对照表。</p>'''
    write('reference/labs.html', page('实验手册', labtext, '../'))


LEGACY_TEXT = [
    ('四足机器狗导航算法工程师 · 三个月学习计划', '四足机器狗导航方向 · 原十二周进阶资料（参考节奏，不承诺期限或职级）'),
    ('四足机器狗导航算法 · 三个月学习计划', '四足机器狗导航方向 · 原十二周进阶资料'),
    ('零基础自包含版', '原版进阶资料（需先修新课程）'),
    ('（零基础版）', '（原版进阶）'),
    ('<strong>这本教材是写给"零基础"的你</strong>', '<strong>修订说明：本页并非零基础材料</strong>（原文写“这本教材是写给零基础的你”，实际要求见页首）'),
    ('<strong>本教材是写给"零基础"的你</strong>', '<strong>修订说明：本页并非零基础材料</strong>（原文写“本教材是写给零基础的你”，实际要求见页首）'),
    ('教材说明：本教材自包含、零基础友好。', '教材说明（已修订）：本页不是零基础材料，请先完成页首列出的新课程。'),
]


def legacy_notice(ks, text):
    box = 'max-width:46rem;margin:20px auto;padding:18px;border:1px solid #8ca99c;font:16px/1.8 system-ui'
    notice = (f'<aside id="zero-foundation-entry" style="{box};background:#e4efe8"><b>这里是原版进阶资料，不是零基础入门。</b> '
              '原文中“零基础”“三个月成为导航算法工程师”的说法不成立：本页默认你会初中数学、能读简单 C++，并按每周约 15 小时推进。'
              '<br>请先完成：'+'；'.join(link(k, 'lessons/') for k in ks)+'。<br>进度以新课程“隔天闭卷能重做”为准，不以周号为准；本页工程片段需按实际软件版本核对。 '
              '<a href="index.html">返回新课程首页</a></aside>')
    if re.search(r'ros2|jazzy|fast[-_]lio', text, re.I):
        notice += (f'<aside id="ros-version-warning" style="{box};background:#fbeee0;border-color:#c9925c"><b>ROS 版本提醒：</b>本页的 ROS 示例命令是 <b>ROS 2</b>（Jazzy：ros2、colcon、launch.py）。'
                   '课程部署的 FAST-LIO2 官方 main 分支是 <b>ROS 1</b>（Noetic：roslaunch、catkin_make、rosbag），两套命令不能在同一环境中混用，也不能把 ROS 1 的 README 改几个命令当作 ROS 2 移植。'
                   f'命令对照表见 {link("ros_tf", "lessons/")}，部署步骤见 {link("deploy_env", "lessons/")}。</aside>')
    return notice


def repair_legacy():
    for w, topic, ks in LEGACY:
        target = ROOT/f'第{w}周学习教材.html'
        if w == '五':
            content = '<h1>第五周：补课与阶段验收</h1><p>原仓库没有第五周文件。这是新增学习导航，不是恢复的原稿；不要求在一周内学完。</p><p>先完成新课 01–09（学习方法、数学与 Python 基础），再完成 10–19（估计、几何与最小 SLAM 项目）。需要的入口如下。</p>'+'<p>'+'</p><p>'.join(link(n, 'lessons/') for n in range(1, KEY['slam1d']+1))+'</p><p>验收：不看答案解释单位、坐标、预测与观测的区别，手算一次更新，再独立运行一维SLAM。隔天重做通过后进入原第六周。</p>'
            write(target.relative_to(ROOT), page('第五周补课导航', content))
            continue
        text = target.read_text(encoding='utf-8')
        # 原生成器留下的双大括号仅修复 style/script 区域，不碰正文代码。
        text = re.sub(r'<(style|script)>(.*?)</\1>', lambda m: '<'+m[1]+'>'+m[2].replace('{{', '{').replace('}}', '}')+'</'+m[1]+'>', text, flags=re.S)
        # 原语法高亮 CSS 位于 style 之外、head 之内，补齐容器。
        text = re.sub(r'</style>\s*(pre \{.*?)(</head>)', r'</style><style>\n\1</style>\n\2', text, flags=re.S)
        # 每次重建都替换为最新说明，保证幂等。
        text = re.sub(r'<aside id="zero-foundation-entry".*?</aside>(<aside id="ros-version-warning".*?</aside>)?\r?\n?', '', text, flags=re.S)
        for old, new in LEGACY_TEXT:
            text = text.replace(old, new)
        text = text.replace('<body>', '<body>\n'+legacy_notice(ks, text)+'\n', 1)
        # 保留原周教材 CRLF，避免整页仅因换行改动进入差异。
        target.write_text(text.replace('\r\n', '\n').replace('\n', '\r\n'), encoding='utf-8', newline='')


if __name__ == '__main__':
    build_lessons(); build_home(); build_reference(); repair_legacy()
    print(f'Built {len(LESSONS)} lessons, home, references and legacy navigation.')
