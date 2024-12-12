cmake_minimum_required(VERSION 3.25)
project(back_end C)

set(CMAKE_C_STANDARD 11)

add_executable(back_end main.c)

# Ajout du répertoire contenant cJSON
add_subdirectory(libs/cJSON)

# Inclusion de la bibliothèque cJSON dans la cible principale
target_include_directories(back_end PRIVATE libs/cJSON)
target_link_libraries(back_end PRIVATE cjson)

