# CMAKE generated file: DO NOT EDIT!
# Generated by "Unix Makefiles" Generator, CMake Version 3.5

# Delete rule output on recipe failure.
.DELETE_ON_ERROR:


#=============================================================================
# Special targets provided by cmake.

# Disable implicit rules so canonical targets will work.
.SUFFIXES:


# Remove some rules from gmake that .SUFFIXES does not remove.
SUFFIXES =

.SUFFIXES: .hpux_make_needs_suffix_list


# Suppress display of executed commands.
$(VERBOSE).SILENT:


# A target that is always out of date.
cmake_force:

.PHONY : cmake_force

#=============================================================================
# Set environment variables for the build.

# The shell in which to execute make rules.
SHELL = /bin/sh

# The CMake executable.
CMAKE_COMMAND = /usr/bin/cmake

# The command to remove a file.
RM = /usr/bin/cmake -E remove -f

# Escaping for special characters.
EQUALS = =

# The top-level source directory on which CMake was run.
CMAKE_SOURCE_DIR = /home/dvercaut/ugent_git/bullet3

# The top-level build directory on which CMake was run.
CMAKE_BINARY_DIR = /home/dvercaut/ugent_git/bullet3

# Include any dependencies generated for this target.
include test/BulletDynamics/CMakeFiles/Test_btKinematicCharacterController.dir/depend.make

# Include the progress variables for this target.
include test/BulletDynamics/CMakeFiles/Test_btKinematicCharacterController.dir/progress.make

# Include the compile flags for this target's objects.
include test/BulletDynamics/CMakeFiles/Test_btKinematicCharacterController.dir/flags.make

test/BulletDynamics/CMakeFiles/Test_btKinematicCharacterController.dir/test_btKinematicCharacterController.o: test/BulletDynamics/CMakeFiles/Test_btKinematicCharacterController.dir/flags.make
test/BulletDynamics/CMakeFiles/Test_btKinematicCharacterController.dir/test_btKinematicCharacterController.o: test/BulletDynamics/test_btKinematicCharacterController.cpp
	@$(CMAKE_COMMAND) -E cmake_echo_color --switch=$(COLOR) --green --progress-dir=/home/dvercaut/ugent_git/bullet3/CMakeFiles --progress-num=$(CMAKE_PROGRESS_1) "Building CXX object test/BulletDynamics/CMakeFiles/Test_btKinematicCharacterController.dir/test_btKinematicCharacterController.o"
	cd /home/dvercaut/ugent_git/bullet3/test/BulletDynamics && /usr/bin/c++   $(CXX_DEFINES) $(CXX_INCLUDES) $(CXX_FLAGS) -o CMakeFiles/Test_btKinematicCharacterController.dir/test_btKinematicCharacterController.o -c /home/dvercaut/ugent_git/bullet3/test/BulletDynamics/test_btKinematicCharacterController.cpp

test/BulletDynamics/CMakeFiles/Test_btKinematicCharacterController.dir/test_btKinematicCharacterController.i: cmake_force
	@$(CMAKE_COMMAND) -E cmake_echo_color --switch=$(COLOR) --green "Preprocessing CXX source to CMakeFiles/Test_btKinematicCharacterController.dir/test_btKinematicCharacterController.i"
	cd /home/dvercaut/ugent_git/bullet3/test/BulletDynamics && /usr/bin/c++  $(CXX_DEFINES) $(CXX_INCLUDES) $(CXX_FLAGS) -E /home/dvercaut/ugent_git/bullet3/test/BulletDynamics/test_btKinematicCharacterController.cpp > CMakeFiles/Test_btKinematicCharacterController.dir/test_btKinematicCharacterController.i

test/BulletDynamics/CMakeFiles/Test_btKinematicCharacterController.dir/test_btKinematicCharacterController.s: cmake_force
	@$(CMAKE_COMMAND) -E cmake_echo_color --switch=$(COLOR) --green "Compiling CXX source to assembly CMakeFiles/Test_btKinematicCharacterController.dir/test_btKinematicCharacterController.s"
	cd /home/dvercaut/ugent_git/bullet3/test/BulletDynamics && /usr/bin/c++  $(CXX_DEFINES) $(CXX_INCLUDES) $(CXX_FLAGS) -S /home/dvercaut/ugent_git/bullet3/test/BulletDynamics/test_btKinematicCharacterController.cpp -o CMakeFiles/Test_btKinematicCharacterController.dir/test_btKinematicCharacterController.s

test/BulletDynamics/CMakeFiles/Test_btKinematicCharacterController.dir/test_btKinematicCharacterController.o.requires:

.PHONY : test/BulletDynamics/CMakeFiles/Test_btKinematicCharacterController.dir/test_btKinematicCharacterController.o.requires

test/BulletDynamics/CMakeFiles/Test_btKinematicCharacterController.dir/test_btKinematicCharacterController.o.provides: test/BulletDynamics/CMakeFiles/Test_btKinematicCharacterController.dir/test_btKinematicCharacterController.o.requires
	$(MAKE) -f test/BulletDynamics/CMakeFiles/Test_btKinematicCharacterController.dir/build.make test/BulletDynamics/CMakeFiles/Test_btKinematicCharacterController.dir/test_btKinematicCharacterController.o.provides.build
.PHONY : test/BulletDynamics/CMakeFiles/Test_btKinematicCharacterController.dir/test_btKinematicCharacterController.o.provides

test/BulletDynamics/CMakeFiles/Test_btKinematicCharacterController.dir/test_btKinematicCharacterController.o.provides.build: test/BulletDynamics/CMakeFiles/Test_btKinematicCharacterController.dir/test_btKinematicCharacterController.o


# Object files for target Test_btKinematicCharacterController
Test_btKinematicCharacterController_OBJECTS = \
"CMakeFiles/Test_btKinematicCharacterController.dir/test_btKinematicCharacterController.o"

# External object files for target Test_btKinematicCharacterController
Test_btKinematicCharacterController_EXTERNAL_OBJECTS =

test/BulletDynamics/Test_btKinematicCharacterController: test/BulletDynamics/CMakeFiles/Test_btKinematicCharacterController.dir/test_btKinematicCharacterController.o
test/BulletDynamics/Test_btKinematicCharacterController: test/BulletDynamics/CMakeFiles/Test_btKinematicCharacterController.dir/build.make
test/BulletDynamics/Test_btKinematicCharacterController: src/BulletDynamics/libBulletDynamics.a
test/BulletDynamics/Test_btKinematicCharacterController: src/BulletCollision/libBulletCollision.a
test/BulletDynamics/Test_btKinematicCharacterController: src/LinearMath/libLinearMath.a
test/BulletDynamics/Test_btKinematicCharacterController: test/gtest-1.7.0/libgtest.a
test/BulletDynamics/Test_btKinematicCharacterController: test/BulletDynamics/CMakeFiles/Test_btKinematicCharacterController.dir/link.txt
	@$(CMAKE_COMMAND) -E cmake_echo_color --switch=$(COLOR) --green --bold --progress-dir=/home/dvercaut/ugent_git/bullet3/CMakeFiles --progress-num=$(CMAKE_PROGRESS_2) "Linking CXX executable Test_btKinematicCharacterController"
	cd /home/dvercaut/ugent_git/bullet3/test/BulletDynamics && $(CMAKE_COMMAND) -E cmake_link_script CMakeFiles/Test_btKinematicCharacterController.dir/link.txt --verbose=$(VERBOSE)

# Rule to build all files generated by this target.
test/BulletDynamics/CMakeFiles/Test_btKinematicCharacterController.dir/build: test/BulletDynamics/Test_btKinematicCharacterController

.PHONY : test/BulletDynamics/CMakeFiles/Test_btKinematicCharacterController.dir/build

test/BulletDynamics/CMakeFiles/Test_btKinematicCharacterController.dir/requires: test/BulletDynamics/CMakeFiles/Test_btKinematicCharacterController.dir/test_btKinematicCharacterController.o.requires

.PHONY : test/BulletDynamics/CMakeFiles/Test_btKinematicCharacterController.dir/requires

test/BulletDynamics/CMakeFiles/Test_btKinematicCharacterController.dir/clean:
	cd /home/dvercaut/ugent_git/bullet3/test/BulletDynamics && $(CMAKE_COMMAND) -P CMakeFiles/Test_btKinematicCharacterController.dir/cmake_clean.cmake
.PHONY : test/BulletDynamics/CMakeFiles/Test_btKinematicCharacterController.dir/clean

test/BulletDynamics/CMakeFiles/Test_btKinematicCharacterController.dir/depend:
	cd /home/dvercaut/ugent_git/bullet3 && $(CMAKE_COMMAND) -E cmake_depends "Unix Makefiles" /home/dvercaut/ugent_git/bullet3 /home/dvercaut/ugent_git/bullet3/test/BulletDynamics /home/dvercaut/ugent_git/bullet3 /home/dvercaut/ugent_git/bullet3/test/BulletDynamics /home/dvercaut/ugent_git/bullet3/test/BulletDynamics/CMakeFiles/Test_btKinematicCharacterController.dir/DependInfo.cmake --color=$(COLOR)
.PHONY : test/BulletDynamics/CMakeFiles/Test_btKinematicCharacterController.dir/depend

