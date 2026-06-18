cmake_minimum_required(VERSION 3.22)
project(Office_delivery_bot2)

find_package(ament_cmake REQUIRED)

install(
  DIRECTORY urdf meshes launch config world textures
  DESTINATION share/${PROJECT_NAME}
)

ament_package()
