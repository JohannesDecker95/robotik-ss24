cmake_minimum_required(VERSION 3.8)
project(visualizer)

if(CMAKE_COMPILER_IS_GNUCXX OR CMAKE_CXX_COMPILER_ID MATCHES "Clang")
  add_compile_options(-Wall -Wextra -Wpedantic -fPIC)
endif()

# Set position independent code
set(CMAKE_POSITION_INDEPENDENT_CODE ON)

add_subdirectory("./poly2tri")

# Dependencies
find_package(Qt5 REQUIRED COMPONENTS Widgets Core)
find_package(Coin3D REQUIRED)
find_package(ament_cmake REQUIRED)
find_package(rclcpp REQUIRED)
find_package(std_msgs REQUIRED)
find_package(geometry_msgs REQUIRED)
find_package(interfaces REQUIRED)
find_package(yaml-cpp REQUIRED)

# Include directories
include_directories(${Qt5Widgets_INCLUDE_DIRS} ${COIN3D_INCLUDE_DIRS})

# Tell CMake to create the main executable
add_executable(visualizer src/main.cpp src/robot.cpp src/move.cpp src/puzzle.cpp src/environment.cpp src/watchdog/Watchdog.cpp)

# ament target dependencies
ament_target_dependencies(visualizer rclcpp std_msgs geometry_msgs interfaces)

# Link libraries
target_link_libraries(visualizer Coin SoQt Qt5::Widgets poly2tri yaml-cpp)

# Exports the rendered robot geometry as collision meshes for pkg_control (data/collision)
add_executable(export_collision_meshes tools/export_collision_meshes.cpp)
target_link_libraries(export_collision_meshes Coin)

# Installation
install(TARGETS
  visualizer
  export_collision_meshes
  DESTINATION lib/${PROJECT_NAME})

if(BUILD_TESTING)
  find_package(ament_lint_auto REQUIRED)
  # the following line skips the linter which checks for copyrights
  # comment the line when a copyright and license is added to all source files
  set(ament_cmake_copyright_FOUND TRUE)
  # the following line skips cpplint (only works in a git repo)
  # comment the line when this package is in a git repo and when
  # a copyright and license is added to all source files
  set(ament_cmake_cpplint_FOUND TRUE)
  ament_lint_auto_find_test_dependencies()
endif()

ament_package()
