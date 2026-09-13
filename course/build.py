"""生成无网络依赖教材。运行：python course/build.py。"""
from pathlib import Path
from html import escape
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
 'dreamer': ('Hafner 等：DreamerV3', 'https://arxiv.org/abs/2301.04104', '学习世界模型与想象行为训练；本课程标量实验不是论文复现。'),
}

TERMS = [
 ('状态 state','希望估计的内部量，例如位置；传感器未必直接读到它。',1),
 ('观测 measurement','传感器实际读数，例如到墙的距离；与状态区分。',1),
 ('模型 model','把输入与预期输出连接的规则，例如 h(x)=10−x。',1),
 ('残差 residual','本教材一般用预测减实测；其他代码可能反过来，先看定义。',1),
 ('函数 function','输入一个或多个值，按规则产生输出；h(x) 不是 h 乘 x。',2),
 ('维度 shape','向量分量数或矩阵行列数；不要和物理单位混淆。',4),
 ('坐标系 frame','原点与轴方向的约定；同一物理点可有不同坐标。',3),
 ('向量 vector','多个有顺序的分量，可表达位移等量。',3),
 ('范数 norm','本课欧氏范数是向量长度；例如 (3,4) 长度为 5。',3),
 ('点积 dot product','对应分量相乘再求和；对单位方向点积才直接是投影长度。',3),
 ('矩阵 matrix','按行列组织的数表，乘向量时每行做一次点积。',4),
 ('弧度 radian','旋转的计量方式；180°=π 弧度。',4),
 ('转置 transpose','行列互换；Rᵀ 的第一行来自 R 的第一列。',4),
 ('逆 inverse','撤销变换的操作；不是把矩阵每个数取倒数。',4),
 ('导数 derivative','输入很小的变化引起输出多大变化。',5),
 ('偏导 partial derivative','固定其他输入，只对一个输入求变化率。',5),
 ('雅可比 Jacobian','多个输出对多个输入的局部变化率表。',5),
 ('线性化 linearization','在当前点附近用直线或线性映射近似函数。',5),
 ('均值 mean','相加再除数量，描述中心。',6),
 ('方差 variance','偏离均值的平方的平均量，单位也平方。',6),
 ('标准差 standard deviation','方差的非负平方根，单位与原变量一致。',6),
 ('协方差 covariance','多个变量的误差是否共同变化。',6),
 ('高斯 Gaussian','一种由均值和协方差描述的概率模型，不适用所有异常。',6),
 ('先验 prior / 后验 posterior','加入本次观测之前 / 之后的概率判断。',6),
 ('最小二乘 least squares','让残差平方总和尽量小的估计方法。',7),
 ('梯度 gradient','各输入方向导数组成的向量，指出局部增大方向。',7),
 ('优化 optimization','根据目标函数寻找更好的参数或状态。',7),
 ('鲁棒损失 robust loss','降低大残差影响的目标函数设计，不代替检查错误关联。',7),
 ('增益 gain','测量差异进入状态修正的比例或矩阵。',8),
 ('EKF / iEKF','非线性系统的局部线性滤波 / 迭代线性化更新。',8),
 ('位姿 pose','位置与朝向；三维刚体通常有 6 个自由度。',9),
 ('自由度 DOF','描述变化所需的独立量数目。',9),
 ('SO(3) / SE(3)','合法三维旋转 / 旋转加平移的刚体变换集合。',9),
 ('李代数 Lie algebra','用于表达旋转等变换的局部增量空间。',9),
 ('四元数 quaternion','以四个有约束的数表达旋转，顺序要按库核对。',9),
 ('内参 intrinsics / 外参 extrinsics','相机内部投影参数 / 两坐标系之间的刚体关系。',10),
 ('投影 projection','把相机坐标三维点变成像素位置。',10),
 ('BA 束调整','联合优化相机位姿与三维点，使重投影误差减小。',10),
 ('IMU','测角速度与比力的惯性传感器组合。',11),
 ('偏置 bias','持续偏离真实读数的误差成分，平均不一定消除。',11),
 ('积分 integration','累加许多小时间段的变化，速度积分成位移。',11),
 ('去畸变 deskew','按各点采集时间，把移动中扫描的点变到共同参考时刻。',11),
 ('点云 point cloud','空间采样点的集合。',12),
 ('配准 registration / ICP','求两组数据的对齐变换 / 交替最近点关联和估计的算法。',12),
 ('法向量 normal','垂直平面的方向；距离公式中的法向通常要求单位长度。',12),
 ('退化 degeneracy / 可观性 observability','观测能否约束各状态方向；某方向弱约束会使估计不稳。',12),
 ('秩 rank','线性映射中独立信息方向的数量。',12),
 ('SVD 奇异值分解','将矩阵拆为正交变换、缩放、正交变换。',12),
 ('因子 factor','连接一组变量的一条概率约束或误差关系。',13),
 ('回环 loop closure','重新来到过去地点形成的约束，加入前需要验证。',13),
 ('规范自由度 gauge','整体换参考系仍解释相同观测的自由度。',13),
 ('Eigen','C++ 线性代数库，负责计算而不决定物理模型。',15),
 ('节点 node / 话题 topic','程序组件 / 持续消息通道。',16),
 ('TF','带时间的坐标变换管理。',16),
 ('QoS','通信可靠性、队列等服务约定。',16),
 ('里程计 odometry / LIO','连续运动估计 / 激光惯性里程计。',17),
 ('体素 voxel','三维空间分桶，常用于降采样和地图组织。',17),
 ('ATE / RPE','全局轨迹误差 / 相对运动误差，需明确对齐与时间规则。',18),
 ('RMSE','误差平方平均后开方；保留原误差的单位。',18),
 ('基线 baseline / 消融 ablation','比较起点 / 移除某组件观察影响的实验。',18),
 ('代价地图 costmap','用数值表达障碍或通行代价的空间表示。',19),
 ('启发式 heuristic','搜索中对剩余代价的估计。',19),
 ('损失 loss','评价模型预测多差的标量分数。',20),
 ('反向传播 backpropagation','按链式法则计算网络参数的导数。',20),
 ('泛化 generalization','对未用于拟合与选择的数据仍能工作的能力。',20),
 ('嵌入 embedding / 注意力 attention','向量表示 / 用匹配分数加权选择信息。',20),
 ('VLN / VLM','视觉语言导航任务 / 处理视觉与语言的模型，二者不同。',21),
 ('grounding 落地','把语言中的对象与关系对应到实际环境。',21),
 ('SPL','同时考虑任务成功与路径效率的导航指标。',21),
 ('世界模型 world model','学习或表达动作条件下后续状态/观测的模型。',22),
 ('潜在状态 latent state','从数据得到的内部表示，不一定有直接物理单位。',22),
 ('策略 policy / 回报 return','如何选择动作的规则 / 累积奖励。',22),
 ('滚动规划 MPC 思路','预测多步，只执行第一步，再观察和重算。',22),
]

NUMERIC = [
 ('墙在12米，测距4米，正确位置多少米？',8,'使用 x=m−z；回到本课墙距例子。'),
 ('wall=10, position=6, measured=3，残差是多少？',1,'先预测 10−6，再减3。'),
 ('向量(−3,4)的长度是多少？',5,'平方相加再开方；负数平方为正。'),
 ('θ=90°，p=(0,2)，t=(2,1)，变换后的 x 分量？',0,'先旋转得到(−2,0)，再加平移。'),
 ('f(x)=x² 在 x=2 的精确导数是多少？',4,'局部导数是2x。'),
 ('2.9、3.0、3.1 都加0.2，新均值是多少？',3.2,'均值整体增加0.2。'),
 ('第7课两观测例子，x=6 时总平方误差是多少？',2,'残差分别1与−1，平方相加。'),
 ('P⁻=0.05，R=0.05，K是多少？',.5,'K=P⁻/(P⁻+R)。'),
 ('机器人(2,1)、θ=90°，地图点(2,3)变回后的 x 分量？',2,'先减平移，再反向旋转。'),
 ('X=1,Z=4,fx=400,cx=320，u是多少像素？',420,'先求400×1/4，再加320。'),
 ('b=0.1米/秒²，10秒位置偏差多少米？',5,'使用0.5×b×t²。'),
 ('对应点偏移2、2、8，最小二乘平移多少米？',4,'等权情况下取偏移均值。'),
 ('所有位置与地标都加5，运动残差改变量多少？',0,'相对差中的常数相消。'),
 ('第14课全部测距加2，新地标位置约多少米？',6.0625,'在原4.0625基础上加2，位置不变。'),
 ('3×2 乘 2×1，结果有多少行？',3,'结果是3×1。'),
 ('1米/秒直行，0.02秒时间差对应多少米？',.02,'速度乘时间。'),
 ('边长为1的体素均分到边长0.5，三维有多少子体素？',8,'每轴2份，2×2×2；点数未必也恰好增加8倍。'),
 ('误差0、0.2、0.1，RMSE约多少米？',.1291,'先平方平均再开方，容差0.001。'),
 ('(0,0)到(2,1)，四邻接单位步长距离下界？',3,'横纵距离相加。'),
 ('w=1,a=2,y=1.6，平方损失对w的导数？',1.6,'2×(wa−y)×a。'),
 ('失败任务，最短4米，实际4米，SPL是多少？',0,'成功指示为0。'),
 ('θ=0.8，连续两次a=1，从0出发预测终点？',1.6,'累加两次0.8。'),
 ('调参后仅测试1个场景，能证明适用于所有场景吗？能填1，不能填0。',0,'结论必须受数据覆盖和实验条件限制。'),
]

def write(path, value):
    path = ROOT/path
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(value, encoding='utf-8', newline='\n')

def filename(n):
    return f'{n:04d}-lesson.html'

def link(n, prefix=''):
    return f'<a href="{prefix}{filename(n)}">{n:02d} · {escape(LESSONS[n-1]["title"])}</a>'

def page(title, content, prefix='', ident='home', wide=False):
    return f'''<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>{escape(title)} · SLAM 学习实验室</title><link rel="stylesheet" href="{prefix}assets/style.css"><script src="{prefix}assets/app.js" defer></script></head>
<body data-lesson="{ident}"><a class="skip" href="#main">跳到正文</a><nav class="top" aria-label="主导航"><a href="{prefix}index.html">SLAM 学习实验室</a><a href="{prefix}reference/glossary.html">术语与符号</a><a href="{prefix}reference/labs.html">实验手册</a><a href="{prefix}reference/sources.html">一手资料</a></nav><main id="main" class="shell {'' if wide else 'reading'}">{content}<footer>离线教材 · 2026-09-13 · 先预测，再计算，再运行，最后解释。学习目标：能独立建模、实现与诊断，继续走向 VLN 和世界模型。</footer></main></body></html>'''

def numeric(question, expected, explain, ident):
    return f'''<div class="numeric panel"><label for="q-{ident}">{escape(question)}</label><input id="q-{ident}" type="number" step="any" inputmode="decimal"><button type="button" data-check="{expected}" data-explain="{escape(explain, quote=True)}">检查数值</button><output aria-live="polite"></output></div>'''

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

def build_lessons():
    for n, item in enumerate(LESSONS, 1):
        prerequisites = '；'.join(link(i) for i in item['prereq']) or '无需先修；只从具体数字开始。'
        refs = '；'.join(f'<a href="{SOURCES[k][1]}">{SOURCES[k][0]}</a>' for k in item['refs'])
        prev = link(n-1) if n>1 else '<a href="../index.html">入口诊断</a>'
        nxt = link(n+1) if n<len(LESSONS) else '<a href="../index.html#legacy">按能力回到原教材</a>'
        q = NUMERIC[n-1]
        content = f'''<header class="hero"><div class="eyebrow">{item['stage']} / LESSON {n:02d}</div><h1>{item['title']}</h1><p>{item['goal']}</p><p class="subtle">先修：{prerequisites}</p></header>
<div class="flow" aria-label="学习步骤"><span>具体问题</span><b>→</b><span>手算</span><b>→</b><span>公式</span><b>→</b><span>代码</span><b>→</b><span>解释</span></div>
<h2>从实际问题走到公式</h2>{item['body']}
{laboratory(item['lab'])}<h2>把公式落实到每行代码</h2><pre><code>{escape(item['code'])}</code></pre><p>{item['trace']}</p>
<h2>先独立作答，再打开提示</h2><p>{item['question']}</p><label for="answer">你的过程、单位与理由</label><textarea id="answer" data-save="answer" placeholder="不要只写结论：说明已知什么、求什么、每一步为什么这样算。"></textarea>
<details><summary>提示：只给下一步</summary><p>{item['hint']}</p></details><details><summary>核对解答与常见错因</summary><p>{item['answer']}</p><p>若还无法解释，回到先修：{prerequisites}。闭上答案，换一组数字重算。</p></details>
{numeric(*q, ident=str(n))}<details><summary>改变条件的迁移练习与解析</summary><p>{item['transfer']}</p></details>
<h2>留下理解证据</h2><p>用自己的话说：这个方法解决什么问题？公式中的量从哪里来？改一个条件，结果为什么变化？把没理解的具体步骤写下来。</p><textarea aria-label="本课解释与疑问" data-save="reason"></textarea>
<label>学习状态（自评，不是自动认证）<select data-save="state"><option>尚未记录</option><option>需要补课</option><option>能跟着算</option><option>能独立解释与迁移</option><option>隔天闭卷复做通过</option></select></label><label>复习记录<textarea data-save="review" placeholder="隔天、约一周后、约一月后重做；写日期、是否看答案、哪里又忘了。"></textarea></label>
<div class="toolbar"><button data-export type="button">导出学习记录</button></div><p id="save-status" class="subtle" role="status"></p>
<details><summary>选读一手资料</summary><p>{refs}</p><p>本课数值例子是教学构造。外部链接用于核对和深入，不是完成本课练习的前置要求。网页可能更新；真实系统复现应额外锁定软件提交与环境。</p></details><nav class="bottom-nav" aria-label="课程翻页"><span>上一课<br>{prev}</span><span>下一课<br>{nxt}</span></nav>'''
        write('lessons/'+filename(n), page(item['title'], content, '../', f'{n:04d}'))

LEGACY = [('一','线性代数、C++、Eigen、FAST-LIO2',[4,12,15,17]),('二','导数、雅可比、运动学',[5,9,19]),('三','概率、Kalman、ROS、TF',[6,8,16]),('四','优化与调试',[7,16,18]),('五','新增补课与阶段验收',[1,8,14]),('六','EKF 与里程计',[8,11]),('七','点云配准与 LIO',[11,12,17]),('八','外参与双雷达',[9,11,16,17]),('九','图搜索与导航',[19]),('十','全局规划与通过性',[19]),('十一','局部规划与控制',[19]),('十二','回环与综合项目',[13,14,18,23])]

def build_home():
    cards = ''
    last_stage = None
    for n, item in enumerate(LESSONS,1):
        if item['stage'] != last_stage:
            if last_stage: cards += '</div>'
            cards += f'<h3>{item["stage"]}</h3><div class="grid">'
            last_stage = item['stage']
        cards += f'<article class="card"><div class="number">LESSON {n:02d}</div><h3>{link(n,"lessons/")}</h3><p>{item["goal"]}</p><span class="state" data-progress="{n:04d}">尚未记录</span></article>'
    cards += '</div>'
    diagnostics = ''.join(numeric(*NUMERIC[n-1],ident='diag'+str(n)) for n in [1,3,4,5,8])
    rows = ''.join(f'<tr><td><a href="第{w}周学习教材.html">原第{w}周</a></td><td>{topic}</td><td>{"<br>".join(link(n,"lessons/") for n in ns)}</td></tr>' for w,topic,ns in LEGACY)
    content = f'''<header class="hero"><div class="eyebrow">BUILD UNDERSTANDING / 学习路径 01</div><h1>让公式、代码<br>和机器人对上号。</h1><p>从一条走廊里的测距开始，逐步学到 SLAM 工程、视觉语言导航和世界模型。用直白语言解释每个新概念，以成年人的方式讨论问题。</p><a class="button" href="lessons/{filename(1)}">从第 01 课开始</a> <a href="#diagnosis">先做入口诊断</a></header>
<div class="flow"><span>数学与代码</span><b>→</b><span>几何与估计</span><b>→</b><span>SLAM 工程</span><b>→</b><span>VLN / 世界模型</span></div>
<section class="panel"><h2>这一次怎样学</h2><p>已知你的起点是“能运行代码，但不明白它为什么这样算”。每课只推进一个核心问题：先看完整数值例子，逐项读公式，再对应代码。不会的词可以在页内解释或术语页查到，不必复制句子去问。</p><p>学习一节 → 先预测再做题 → 核对错因 → 隔天闭卷重做 → 一周后混合复习。错题回到先修课，能独立解释与迁移才往下推进。建议每次先留 30–60 分钟；复杂内容分多次，不以旧教材的周号催进度。</p><p><b>目标是可验证的能力，读完页数不是职级认证。</b>第23课给出初级到中级所需的项目证据。全部基础交互离线可用；真实系统项目需要另行配置匹配环境、数据与传感器。</p></section>
<section id="diagnosis"><h2>入口诊断：定位缺口，不给你贴分数</h2><p>没有学过的内容可以空着。题1卡住→第01课；题2→第03课；题3→第04课；题4→第05课；题5→第06、08课。即使数字答对，也试着解释“这些数字从哪里来”。</p><details><summary>展开 5 道诊断题</summary>{diagnostics}</details></section>
<section id="curriculum"><h2>23 节课，按能力逐步接上</h2><label>查课程<input type="search" data-filter=".card" placeholder="输入：矩阵、相机、VLN……"></label>{cards}</section>
<section class="panel"><h2>你的学习记录</h2><p>每课保存解题过程、自评和复习记录。数据保存在当前浏览器，不上传。直接打开文件时，不同浏览器可能把每页存储隔离；请在学过的页面导出，再到首页合并导入。要统一来源，也可按实验手册启动本地网页服务。</p><div class="toolbar"><button type="button" data-export>导出当前记录</button><label>导入记录<input id="import-progress" type="file" accept=".json,application/json"></label></div><p id="import-status" role="status">导入时同课采用文件记录，其他课保留。</p></section>
<section id="legacy"><h2>回到原教材：每一周应该什么时候读</h2><p>原仓库的十一份周教材作为进阶阅读保留。原本缺少第五周文件，这里新增补课导航。旧材料的“零基础、三个月”安排不再作为本课程门槛；其中工程片段需按上游实际版本核验。</p><div class="table-wrap"><table><thead><tr><th>原入口</th><th>内容</th><th>先完成新课程</th></tr></thead><tbody>{rows}</tbody></table></div></section>'''
    write('index.html',page('从零建立 SLAM 理解',content,wide=True))

def build_reference():
    entries=''.join(f'<section class="glossary-entry" id="term-{i}"><h2>{escape(term)}</h2><p>{meaning} {link(n,"../lessons/")}</p></section>' for i,(term,meaning,n) in enumerate(TERMS))
    symbols='<div class="table-wrap"><table><tr><th>符号</th><th>怎么读、什么意思</th></tr><tr><td>Σ / ∑</td><td>求和，把各项加起来；若表示协方差矩阵则看上下文定义。</td></tr><tr><td>Δ、δ、ε</td><td>变化量、小改变量、小步长；具体单位跟变量一致。</td></tr><tr><td>θ、μ、σ、π</td><td>theta 角度，mu 均值，sigma 标准差；pi 可为圆周率，也可表示策略，按定义区分。</td></tr><tr><td>下标 i / 上标 T / 帽子</td><td>编号 / 转置 / 估计值；坐标系上标不是乘方。</td></tr><tr><td>argmin / ∂ / ∝</td><td>找使函数最小的输入 / 偏导符号 / 成比例，概率中常须再归一化。</td></tr><tr><td>米、米²、像素、弧度</td><td>位置与距离、方差、图像坐标、角度单位；相加前必须确认单位相容。</td></tr></table></div>'
    write('reference/glossary.html',page('术语和符号，随查随回',f'<h1>术语与符号</h1><p>字母会被不同代码重复使用。r 可能是残差，也可能是测量方差，先看所在公式的定义。</p>{symbols}<label>检索中英文术语<input type="search" data-filter=".glossary-entry" placeholder="例如 residual、雅可比、TF"></label>{entries}','../'))
    refs=''.join(f'<section><h2>{name}</h2><p>{note}</p><a href="{url}">打开一手资料</a></section>' for name,url,note in SOURCES.values())
    write('reference/sources.html',page('一手资料与核验边界',f'<h1>一手资料</h1><p>核验日期：2026-09-13。这里只选官方文档、作者论文或课程书。课程中的数字、程序与问题是教学构造；软件文档会更新，实际复现请记录提交或版本。</p>{refs}','../'))
    write('RESOURCES.md','# 一手资料\n\n核验日期：2026-09-13。\n\n## Knowledge\n\n'+'\n\n'.join(f'- [{name}]({url})\n  {note}' for name,url,note in SOURCES.values())+'\n\n## Wisdom\n\n未要求加入社区；不以外部问答代替课内解释。\n\n## Gaps 与边界\n\n浏览器和 Python 教学实验已单独验证；真实 FAST-LIO2、ROS、VLN 基准及 Dreamer 训练没有在本环境运行。学习者设备、每周时间与独立编程能力仍未知。高级课提供概念桥梁与工程验收，不宣称完整复现论文。\n')
    labtext='''<h1>实验手册</h1><p>先看对应课的例子，再运行程序。全部 Python 实验只依赖标准库。命令在解压后的仓库目录执行；命令窗口叫终端，当前目录决定相对路径从哪里开始。</p>
<h2>无需安装的起步</h2><p>直接双击 index.html，打开第01、04、08、10、22课的滑块实验。网页不是 Python 编辑器，页面代码展示与运行脚本分开。想修改算法时再进入下面的文件实验。</p>
<h2>Python 环境与执行位置</h2><p>Windows 先在终端输入 <code>py --version</code>，Linux/macOS 输入 <code>python3 --version</code>。若显示 Python 3.x，解释器可用；若找不到命令，先用浏览器实验，或到 <a href="https://www.python.org/downloads/">Python 官方下载页</a> 安装。安装完成后重新打开终端。不要把代码贴进 PowerShell 当命令执行。</p>
<p>在仓库文件夹里通过文件管理器“在终端打开”，确认能看到 labs 文件夹。Windows 以下用 py，Linux/macOS 替换为 python3。每次运行单独一条命令。若命令说找不到文件，先检查当前目录，不要重新装所有库。</p>
<pre>py labs/core.py
py labs/slam_1d.py
py labs/navigation.py
py labs/world_model.py</pre>
<div class="table-wrap"><table><tr><th>程序与对应课</th><th>先预测什么</th><th>应看到什么</th><th>动手修改</th></tr>
<tr><td>core.py / 04、08、10</td><td>旋转后的点、融合位置、像素</td><td>(2,2)；位置1.04，方差0.04，K=0.2；像素(520,340)</td><td>把旋转90改为0，先算再运行。</td></tr>
<tr><td>slam_1d.py / 14</td><td>三条位置与未知地标</td><td>[0,1.1375,2.05]；地标4.0625；RMSE约0.12910→0.08447</td><td>将 estimate 的观测参数改为(6,5,4)，位置应不变，地标加2。</td></tr>
<tr><td>navigation.py / 19、21</td><td>红门对应节点与路径</td><td>R；[S,A,R]；SPL 0.6667 与0</td><td>增加另一个red door标签，应报歧义错误。将A与R双向断开，应返回None不可达。</td></tr>
<tr><td>world_model.py / 22</td><td>拟合系数与两步预测</td><td>θ=0.799；留出MSE约0.036667→0.000001；计划(1,1)，预测1.598，合成真实1.6；换摩擦后1.0</td><td>只用零动作训练应报不可辨识；把测试动力学改为0.5，旧模型误差增加。</td></tr></table></div>
<h2>最小项目交付清单</h2><p>每个实验提交四项：运行前手算；修改过的代码；实际输出；一句能被实验否定的解释。不要只交截图。运行测试可以检查实现，但不能替你证明理解。</p><pre>py -m unittest discover -s tests -v</pre>
<h2>让所有页面共用同一个学习记录来源</h2><p>可选：在仓库目录运行下列命令。http.server 是 Python 内置的静态网页服务，8765 是端口，127.0.0.1 只在本机监听。在浏览器打开 <a href="http://127.0.0.1:8765/">本机学习首页</a>。此终端保持运行，用 Ctrl+C 结束。若端口被占用，把命令和地址中的8765一起换成8766。</p><pre>py -m http.server 8765 --bind 127.0.0.1</pre>
<h2>常见卡点</h2><p>文件末尾看起来是 .py 但仍不能运行：检查是不是 .py.txt。小数出现极小差别：先按合理容差比较。import labs 失败：从仓库目录运行，或直接运行脚本。C++ 示例需要编译器与 Eigen，本环境未执行 C++ 编译；不要把 Python 实验通过当成 C++ 已通过。</p>
<h2>真实工程下一步</h2><p>第17、18、23课给出上游复现与实验协议。先确定传感器数据类型、代码提交和 ROS 版本，再按官方安装说明建立隔离环境。课程没有附带真实录包、VLN 图像数据或预训练模型；这些下载、授权、算力与运行条件应在选定项目时记录。</p>'''
    write('reference/labs.html',page('实验手册',labtext,'../'))

def repair_legacy():
    for w,topic,ns in LEGACY:
        target=ROOT/f'第{w}周学习教材.html'
        if w=='五':
            content='<h1>第五周：补课与阶段验收</h1><p>原仓库没有第五周文件。这是新增学习导航，不是恢复的原稿；不要求在一周内学完。</p><p>先完成新课01–08，再完成09–14的几何与最小SLAM项目。需要的入口如下。</p>'+'<p>'+ '</p><p>'.join(link(n,'lessons/') for n in range(1,15))+'</p><p>验收：不看答案解释单位、坐标、预测与观测的区别，手算一次更新，再独立运行一维SLAM。隔天重做通过后进入原第六周。</p>'
            write(target.relative_to(ROOT),page('第五周补课导航',content))
            continue
        text=target.read_text(encoding='utf-8')
        # 原生成器留下的双大括号仅修复 style/script 区域，不碰正文代码。
        text=re.sub(r'<(style|script)>(.*?)</\1>',lambda m:'<'+m[1]+'>'+m[2].replace('{{','{').replace('}}','}')+'</'+m[1]+'>',text,flags=re.S)
        # 原语法高亮 CSS 位于 style 之外、head 之内，补齐容器。
        text=re.sub(r'</style>\s*(pre \{.*?)(</head>)',r'</style><style>\n\1</style>\n\2',text,flags=re.S)
        if 'zero-foundation-entry' not in text:
            notice='<aside id="zero-foundation-entry" style="max-width:46rem;margin:20px auto;padding:18px;background:#e4efe8;border:1px solid #8ca99c;font:16px/1.8 system-ui"><b>这里是原版进阶资料。</b> <a href="index.html">返回新的零基础学习入口</a><br>建议先完成：'+ '；'.join(link(n,'lessons/') for n in ns)+'。<br>原周进度不再作为新课程期限；本页工程片段需按实际软件版本核对。</aside>'
            text=text.replace('<body>','<body>\n'+notice,1)
        target.write_text(text,encoding='utf-8',newline='\n')

if __name__=='__main__':
    build_lessons(); build_home(); build_reference(); repair_legacy()
    print(f'Built {len(LESSONS)} lessons, home, references and legacy navigation.')
