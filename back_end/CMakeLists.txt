cmake_minimum_required(VERSION 3.25)
project(back_end C)

# Spécifiez la norme C
set(CMAKE_C_STANDARD 11)

# Ajouter l'exécutable
add_executable(back_end main.c)

# Ajouter le chemin d'inclusion de cJSON
target_include_directories(back_end PRIVATE /usr/include/cjson)

# Lier la bibliothèque cJSON
target_link_libraries(back_end PRIVATE cjson)

# Inclusion de SQLite3
find_package(SQLite3 REQUIRED)
target_link_libraries(back_end PRIVATE SQLite::SQLite3)

# Ajouter la bibliothèque crypt
target_link_libraries(back_end PRIVATE crypt)
