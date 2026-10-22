#!/usr/bin/env bash
# 在宿主机（Ubuntu 或 WSL2）执行：bash labs/deploy/run.sh
# 第一次运行创建容器；以后再运行会直接进入同一个容器，编译结果不会丢。
set -e
NAME=slam-noetic
IMAGE=slam-noetic:latest
WS="$HOME/slam_ws"
REPO="$(cd "$(dirname "$0")/../.." && pwd)"

mkdir -p "$WS/data" "$WS/catkin_ws/src" "$WS/ws_livox/src"

if ! docker image inspect "$IMAGE" >/dev/null 2>&1; then
  echo "没有找到镜像 $IMAGE。请先在仓库目录执行：docker build -t slam-noetic labs/deploy"
  exit 1
fi

# 允许容器在宿主机屏幕上显示 rviz 窗口；失败不影响编译和回放。
xhost +local:docker >/dev/null 2>&1 || echo "提示：xhost 不可用，rviz 窗口可能无法显示（编译和回放不受影响）。"

if docker container inspect "$NAME" >/dev/null 2>&1; then
  echo "进入已有容器 $NAME"
  docker start "$NAME" >/dev/null
  exec docker exec -it "$NAME" bash
fi

echo "创建容器 $NAME：宿主机 $WS ↔ 容器 /root/slam_ws；课程仓库只读挂载到 /root/course"
exec docker run -it --name "$NAME" \
  --network host \
  -e DISPLAY="${DISPLAY:-:0}" -e QT_X11_NO_MITSHM=1 \
  -v /tmp/.X11-unix:/tmp/.X11-unix \
  -v "$WS":/root/slam_ws \
  -v "$REPO":/root/course:ro \
  "$IMAGE" bash
