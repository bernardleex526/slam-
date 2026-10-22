# Bug 案例库

每次排错（不论最后是不是自己解决、有没有靠 AI）都记一条。攒够 10 条，你就有了一本自己的排错手册，面试时也能讲出真实经历。

## 模板

### 编号 · 一句话标题（例：rviz 一片空白，原来是 imu_topic 写错）

- 日期 / 环境：（系统、ROS 版本、Docker 镜像、代码分支或提交）
- 现象：看到了什么？原样贴出报错的前 20 行或截图描述。
- 我的第一猜测：（先写下来，再验证）
- 验证步骤：用了哪些命令确认？（如 `rostopic list`、`rosbag info`、`rosrun tf tf_echo`、`py labs/deploy/check_bag.py`）
- 根因：真正的原因是什么？
- 修复：改了哪一处？（一次只改一处）
- AI 用法：问了什么、AI 哪句话对、哪句话错、我怎样核对的。
- 预防：下次怎样更早发现？（检查脚本、清单、测试）

---

### 001 · 示例：rviz 空白但终端不报错

- 环境：Ubuntu 20.04 容器，ROS 1 Noetic，FAST_LIO main 分支
- 现象：`roslaunch fast_lio mapping_avia.launch` 正常启动，回放录包后 rviz 无点云。
- 第一猜测：rviz 显示设置不对。
- 验证：`rosbag info` 看到 IMU 话题是 `/livox/imu`；`py labs/deploy/check_bag.py info.txt avia.yaml` 报 `imu_topic=/imu/data 不在录包里`。
- 根因：配置里的 imu_topic 与录包不一致，算法一直在等 IMU。
- 修复：把 `config/avia.yaml` 的 imu_topic 改为 `/livox/imu`。
- AI 用法：AI 先建议重装 rviz（错）；追问“怎样用一条命令确认数据有没有进来”后，给出 `rostopic hz /livox/imu`（对）。
- 预防：每次换录包先跑 check_bag.py。

（以上为示例，换成你自己的真实记录。）
