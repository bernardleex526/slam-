# ROS 1 Noetic + FAST-LIO2 依赖的学习环境（Ubuntu 20.04）。
# 只安装系统依赖和 Livox-SDK；livox_ros_driver 与 FAST_LIO 留给你在容器里亲手编译（见第 25 课）。
# 构建：docker build -t slam-noetic labs/deploy
FROM osrf/ros:noetic-desktop-full

ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get update && apt-get install -y --no-install-recommends \
        git build-essential cmake nano less \
        libeigen3-dev libpcl-dev ros-noetic-pcl-ros pcl-tools \
    && rm -rf /var/lib/apt/lists/*

# Livox-SDK 是 livox_ros_driver 的依赖；即使不用 Livox 雷达，FAST_LIO 也要用到它的消息类型。
RUN git clone --depth 1 https://github.com/Livox-SDK/Livox-SDK.git /opt/Livox-SDK \
    && cd /opt/Livox-SDK/build && cmake .. && make -j"$(nproc)" && make install

# 每个新终端自动加载 ROS 1 环境。
RUN echo 'source /opt/ros/noetic/setup.bash' >> /root/.bashrc
WORKDIR /root/slam_ws
CMD ["bash"]
