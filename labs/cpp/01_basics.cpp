#include <iostream>
#include <vector>

int main() {
    double wall = 10.0;
    std::vector<double> measurements = {2.9, 3.0, 3.1};
    for (double z : measurements) {
        double position = wall - z;
        std::cout << "position = " << position << "\n";
    }
    int a = 7, b = 2;
    std::cout << a / b << " " << 7.0 / 2 << "\n";
    return 0;
}
