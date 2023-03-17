from conan import ConanFile
from conan.tools.build import can_run
from conan.tools.cmake import cmake_layout, CMake
from six import StringIO
import os
import re


# It will become the standard on Conan 2.x
class TestPackageConan(ConanFile):
    settings = "os", "arch", "compiler", "build_type"
    generators = "CMakeDeps", "CMakeToolchain", "VirtualRunEnv"
    test_type = "explicit"

    def requirements(self):
        self.requires(self.tested_reference_str)

    def layout(self):
        cmake_layout(self)

    def build(self):
        cmake = CMake(self)
        cmake.configure()
        cmake.build()

    def test(self):
        output = StringIO()
        self.run("swig -version", output)
        output_str = str(output.getvalue())
        self.output.info("Installed version: {}".format(output_str))
        tokens = re.split('[@#]', self.tested_reference_str)
        require_version = tokens[0].split("/", 1)[1]
        self.output.info("Expected version: {}".format(require_version))
        assert_swig_version = f"SWIG Version {require_version}"
        #assert(assert_swig_version in output_str)

        output = StringIO()
        self.run("swig -swiglib", output)
        output_str = str(output.getvalue())
        self.output.info("SWIG_LIB: {}".format(output_str))

        if can_run(self):
            bin_path = os.path.join(self.cpp.build.bindirs[0], "test_package")
            self.run(bin_path, env="conanrun")
