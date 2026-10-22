"""部署体检：对照 rosbag info 的输出和 FAST_LIO 配置，找出话题名、消息类型和频率问题。

只用 Python 标准库，宿主机和容器里都能运行，不需要 ROS：
    rosbag info 你的录包.bag > info.txt          （在容器里执行）
    python3 labs/deploy/check_bag.py info.txt 你的FAST_LIO/config/avia.yaml
不带参数时使用仓库里的教学示例：python3 labs/deploy/check_bag.py
"""
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
# FAST_LIO preprocess/lidar_type：1 Livox，2 Velodyne，3 Ouster。
EXPECTED_LIDAR_TYPE = {1: 'livox_ros_driver/CustomMsg', 2: 'sensor_msgs/PointCloud2', 3: 'sensor_msgs/PointCloud2'}


def parse_info(text):
    """返回 (时长秒, {话题: (消息数, 类型)})。"""
    match = re.search(r'^duration:.*?\((\d+(?:\.\d+)?)s\)', text, re.M) or re.search(r'^duration:\s*(\d+(?:\.\d+)?)s', text, re.M)
    if not match:
        raise ValueError('没有找到 duration 行：请确认文件是 rosbag info 的完整输出')
    duration = float(match[1])
    topics = {}
    for name, count, kind in re.findall(r'(/\S+)\s+(\d+) msgs?\s*:\s*(\S+)', text):
        topics[name] = (int(count), kind)
    if not topics:
        raise ValueError('没有找到 topics 列表')
    return duration, topics


def parse_config(text):
    """只读取体检需要的三个字段，避免依赖第三方 YAML 库。"""
    values = {}
    for key in ('lid_topic', 'imu_topic', 'lidar_type'):
        match = re.search(rf'^\s*{key}\s*:\s*"?([^"#\s]+)"?', text, re.M)
        if match:
            values[key] = match[1]
    if 'lidar_type' in values:
        values['lidar_type'] = int(values['lidar_type'])
    return values


def check(info_text, config_text):
    """返回 (问题列表, 说明列表)。问题列表为空表示没有发现接口不一致。"""
    duration, topics = parse_info(info_text)
    config = parse_config(config_text)
    problems, notes = [], []
    for key in ('lid_topic', 'imu_topic'):
        name = config.get(key)
        if name is None:
            problems.append(f'配置里没有 {key}')
            continue
        if name not in topics:
            options = '、'.join(sorted(topics))
            problems.append(f'{key}={name} 不在录包里。录包中的话题：{options}。改配置，或回放时重映射：rosbag play 录包.bag 录包话题:={name}')
            continue
        count, kind = topics[name]
        hz = count / duration if duration > 0 else 0
        notes.append(f'{key}={name}：{count} 条，约 {hz:.0f} Hz，类型 {kind}')
        if key == 'imu_topic':
            if kind != 'sensor_msgs/Imu':
                problems.append(f'{name} 的类型是 {kind}，IMU 应为 sensor_msgs/Imu')
            elif hz < 100:
                problems.append(f'IMU 只有约 {hz:.0f} Hz，偏低；先确认录包和驱动设置，再判断算法')
        if key == 'lid_topic' and 'lidar_type' in config:
            expected = EXPECTED_LIDAR_TYPE.get(config['lidar_type'])
            if expected and kind != expected:
                problems.append(f'lidar_type={config["lidar_type"]} 需要 {expected}，但 {name} 是 {kind}；Livox 要用 livox_lidar_msg.launch 录的 CustomMsg 才有逐点时间')
    return problems, notes


def main(argv):
    info = Path(argv[1]) if len(argv) > 1 else HERE/'sample_rosbag_info.txt'
    config = Path(argv[2]) if len(argv) > 2 else HERE/'sample_config.yaml'
    problems, notes = check(info.read_text(encoding='utf-8'), config.read_text(encoding='utf-8'))
    for line in notes:
        print('信息：', line)
    for line in problems:
        print('问题：', line)
    if not problems:
        print('通过：话题名、类型和频率与配置一致。下一步再看 TF 和算法输出。')
    return 1 if problems else 0


if __name__ == '__main__':
    sys.exit(main(sys.argv))
