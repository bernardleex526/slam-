#!/usr/bin/env bash
# 在容器内执行：bash /root/course/labs/deploy/build_fastlio.sh
# 这是第 25 课手动步骤的“参考答案”。建议先手动做一遍，卡住再对照本脚本。
set -eo pipefail
source /opt/ros/noetic/setup.bash
WS=/root/slam_ws
VERSIONS="$WS/data/versions.txt"

echo "== 1/3 编译 livox_ros_driver（提供 Livox 消息类型）"
if [ ! -d "$WS/ws_livox/src/livox_ros_driver" ]; then
  git clone https://github.com/Livox-SDK/livox_ros_driver.git "$WS/ws_livox/src/livox_ros_driver"
fi
cd "$WS/ws_livox" && catkin_make
source "$WS/ws_livox/devel/setup.bash"

echo "== 2/3 编译 FAST_LIO（必须在 source 了 ws_livox 之后）"
if [ ! -d "$WS/catkin_ws/src/FAST_LIO" ]; then
  git clone https://github.com/hku-mars/FAST_LIO.git "$WS/catkin_ws/src/FAST_LIO"
fi
cd "$WS/catkin_ws/src/FAST_LIO" && git submodule update --init
cd "$WS/catkin_ws" && catkin_make
source "$WS/catkin_ws/devel/setup.bash"

echo "== 3/3 记录版本，写入 $VERSIONS"
{
  echo "date: $(date -Iseconds)"
  echo "ros: $(rosversion -d)"
  echo "livox_ros_driver: $(git -C "$WS/ws_livox/src/livox_ros_driver" rev-parse HEAD)"
  echo "FAST_LIO: $(git -C "$WS/catkin_ws/src/FAST_LIO" rev-parse HEAD)"
} | tee -a "$VERSIONS"

# 新终端自动加载工作空间（FAST_LIO 的 devel 已经叠加了 ws_livox）。
grep -q 'catkin_ws/devel/setup.bash' /root/.bashrc || echo "source $WS/catkin_ws/devel/setup.bash" >> /root/.bashrc

echo "检查点：下一行应显示 FAST_LIO 的路径"
rospack find fast_lio
