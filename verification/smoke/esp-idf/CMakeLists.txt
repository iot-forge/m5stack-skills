# The ESP-IDF smoke project. Generate it first: uv run scripts/smoke.py generate esp-idf
# (writes main/smoke_gen.h, main/smoke_probe.hpp and sdkconfig.defaults, with the target from board.py).
cmake_minimum_required(VERSION 3.16)
include($ENV{IDF_PATH}/tools/cmake/project.cmake)
project(smoke)
