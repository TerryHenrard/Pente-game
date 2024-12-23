cmake_minimum_required(VERSION 3.25)
project(back_end C)

# Spécifiez la norme C
set(CMAKE_C_STANDARD 11)

# Ajout de l'exécutable
add_executable(back_end main.c)

# Ajout de cJSON
add_subdirectory(libs/cJSON)
target_link_libraries(back_end PRIVATE cjson)

# Inclusion de SQLite3
find_package(SQLite3 REQUIRED)
target_link_libraries(back_end PRIVATE SQLite::SQLite3)

# Inclusion d'OpenSSL
find_package(OpenSSL REQUIRED)
target_link_libraries(back_end PRIVATE OpenSSL::SSL OpenSSL::Crypto)

# Ajout des répertoires pour inclure cJSON
target_include_directories(back_end PRIVATE libs/cJSON)
