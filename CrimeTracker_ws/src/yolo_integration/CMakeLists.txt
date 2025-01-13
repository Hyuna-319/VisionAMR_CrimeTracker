cmake_minimum_required(VERSION 3.5)
project(yolo_integration)

find_package(ament_cmake REQUIRED)
find_package(rclpy REQUIRED)

# If you have any C++ code, add it here
# add_executable(yolo_node src/yolo_node.cpp)

install(
  DIRECTORY resource
  DESTINATION share/${PROJECT_NAME}
)

install(
  PROGRAMS
  DESTINATION lib/${PROJECT_NAME}
)

ament_package()
