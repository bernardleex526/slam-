#include <iostream>
#include <vector>

double residual(double position, double measured, double wall = 10.0) {
    return (wall - position) - measured;
}

void shiftAll(std::vector<double>& values, double offset) {
    for (double& v : values) v += offset;
}

double mean(const std::vector<double>& values) {
    double total = 0.0;
    for (double v : values) total += v;
    return total / values.size();
}

int main() {
    std::vector<double> z = {2.9, 3.0, 3.1};
    std::cout << residual(7.0, 3.1) << "\n";
    shiftAll(z, 0.2);
    std::cout << mean(z) << "\n";
    return 0;
}
