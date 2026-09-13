"""课19/21：人工语义标签 + 等权图搜索。没有图像/自然语言模型。"""
from collections import deque

GRAPH = {'S': ['A', 'B'], 'A': ['S', 'R'], 'B': ['S', 'D'], 'R': ['A'], 'D': ['B']}
LABELS = {'R': 'red door', 'D': 'blue door'}


def select_goal(labels, description):
    candidates = [node for node, label in labels.items() if label == description]
    if len(candidates) != 1:
        raise ValueError('Goal missing or ambiguous; obtain more evidence')
    return candidates[0]


def shortest_path(graph, start, goal):
    if start not in graph or goal not in graph:
        raise ValueError('Unknown start or goal')
    queue = deque([start])
    parent = {start: None}
    while queue:
        node = queue.popleft()
        if node == goal:
            path = []
            while node is not None:
                path.append(node)
                node = parent[node]
            return list(reversed(path))
        for neighbor in graph[node]:
            if neighbor not in graph:
                raise ValueError('Edge points to an unknown node')
            if neighbor not in parent:
                parent[neighbor] = node
                queue.append(neighbor)
    return None  # 不可达是合法任务结果，不编造路径。


def spl(success, shortest, actual):
    if shortest <= 0 or actual < 0:
        raise ValueError('This exercise excludes zero-length goals')
    return int(bool(success))*shortest/max(shortest, actual)


if __name__ == '__main__':
    goal = select_goal(LABELS, 'red door')
    print('manual-label goal:', goal)
    print('route:', shortest_path(GRAPH, 'S', goal))
    print('SPL successful detour:', round(spl(True, 4, 6), 4))
    print('SPL wrong goal:', spl(False, 4, 4))
