#include <Eigen/Dense>
#include <iostream>

int main() {
    Eigen::Matrix2d R;
    R << 0, -1, 1, 0;
    Eigen::Vector2d p(1, 0), t(2, 1);
    Eigen::Vector2d world = R * p + t;
    std::cout << world.transpose() << "\n";
}
