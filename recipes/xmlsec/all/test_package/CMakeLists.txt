cmake_minimum_required(VERSION 3.15)
project(test_package LANGUAGES C)

find_package(xmlsec REQUIRED CONFIG)

add_executable(${PROJECT_NAME} main.c)
target_link_libraries(${PROJECT_NAME} PRIVATE xmlsec::xmlsec)
