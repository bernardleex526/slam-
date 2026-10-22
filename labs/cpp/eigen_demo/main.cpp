#include <Eigen/Dense>
#include <iostream>

int main() {
    Eigen::Matrix2d R;
    R << 0, -1,
         1,  0;                          // 绕 z 转 90°，按行填写
    Eigen::Vector2d p(1, 0), t(2, 1);
    Eigen::Vector2d world = R * p + t;   // 第 07 课的 pᵂ = R pᴮ + t
    Eigen::Vector2d back = R.transpose() * (world - t);
    std::cout << world.transpose() << "\n";
    std::cout << back.transpose() << "\n";
    return 0;
}
