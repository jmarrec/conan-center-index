from conan import ConanFile
from conan.tools.microsoft import is_msvc
from conan.tools.files import apply_conandata_patches, export_conandata_patches, get, copy, save
from conan.tools.cmake import CMake, CMakeDeps, CMakeToolchain, cmake_layout
import os
import textwrap


required_conan_version = ">=1.53.0"

class SwigConan(ConanFile):
    name = "swig"
    description = "SWIG is a software development tool that connects programs written in C and C++ with a variety of high-level programming languages."
    url = "https://github.com/conan-io/conan-center-index"
    homepage = "http://www.swig.org"
    license = "GPL-3.0-or-later"
    topics = ("swig", "python", "java", "wrapper")
    exports_sources = "patches/**", "cmake/*"
    settings = "os", "arch", "compiler", "build_type"
    options = {
        "shared": [True, False],
        "fPIC": [True, False],
    }
    default_options = {
        "shared": False,
        "fPIC": True,
    }

    def package_id(self):
        del self.info.settings.compiler

    def export_sources(self):
        export_conandata_patches(self)

    def config_options(self):
        if self.settings.os == "Windows":
            del self.options.fPIC

    def configure(self):
        if self.options.shared:
            self.options.rm_safe("fPIC")
        # for plain C projects only
        self.settings.rm_safe("compiler.libcxx")
        self.settings.rm_safe("compiler.cppstd")

    def layout(self):
        cmake_layout(self)

    def requirements(self):
        self.requires("pcre2/10.42")

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)

    def generate(self):
        # BUILD_SHARED_LIBS and POSITION_INDEPENDENT_CODE are automatically parsed when self.options.shared or self.options.fPIC exist
        tc = CMakeToolchain(self)
        # Boolean values are preferred instead of "ON"/"OFF"
        tc.variables["SWIG_LIB_RELATIVE_TO_EXE"] = True
        tc.variables["SWIG_LIB_RELATIVE_PATH"] = os.path.join("bin", "swiglib")
        tc.generate()
        # In case there are dependencies listed on requirements, CMakeDeps should be used
        tc = CMakeDeps(self)
        tc.generate()

    def _patch_sources(self):
        apply_conandata_patches(self)

    def build(self):
        self._patch_sources()  # It can be apply_conandata_patches(self) only in case no more patches are needed
        cmake = CMake(self)
        cmake.configure()
        cmake.build()

    def package(self):
        copy(self, pattern="LICENSE", dst=os.path.join(self.package_folder, "licenses"), src=self.source_folder)
        copy(self, pattern="COPYRIGHT", dst=os.path.join(self.package_folder, "licenses"), src=self.source_folder)
        cmake = CMake(self)
        cmake.install()
        #self._create_cmake_module_variables(
        #    os.path.join(self.package_folder, self._module_file_rel_path)
        #)

    def _create_cmake_module_variables(self, module_file):
        content = textwrap.dedent("""\
            find_program(SWIG_EXECUTABLE swig)
            if(NOT SWIG_DIR)
                execute_process(COMMAND ${SWIG_EXECUTABLE} -swiglib
                    OUTPUT_VARIABLE SWIG_lib_output OUTPUT_STRIP_TRAILING_WHITESPACE)
                set(SWIG_DIR ${SWIG_lib_output} CACHE STRING "Location of SWIG library" FORCE)
            endif()
            mark_as_advanced(SWIG_DIR SWIG_EXECUTABLE)
        """)
        save(self, module_file, content)

    @property
    def _module_file_rel_path(self):
        return os.path.join("lib", "cmake", f"conan-official-{self.name}-variables.cmake")

    def package_info(self):
        self.cpp_info.includedirs = []

        # if package has an official FindPACKAGE.cmake listed in https://cmake.org/cmake/help/latest/manual/cmake-modules.7.html#find-modules
        # examples: bzip2, freetype, gdal, icu, libcurl, libjpeg, libpng, libtiff, openssl, sqlite3, zlib...
        # self.cpp_info.set_property("cmake_module_file_name", "SWIG")
        # self.cpp_info.set_property("cmake_module_target_name", "SWIG::SWIG")
        # self.cpp_info.set_property("cmake_build_modules", [self._module_file_rel_path])

        # If they are needed on Linux, m, pthread and dl are usually needed on FreeBSD too
        if self.settings.os in ["Linux", "FreeBSD"]:
            self.cpp_info.system_libs.append("dl")

        # TODO: to remove in conan v2 once cmake_find_package_* generators removed
        self.cpp_info.filenames["cmake_find_package"] = "SWIG"
        self.cpp_info.filenames["cmake_find_package_multi"] = "SWIG"
        self.cpp_info.names["cmake_find_package"] = "SWIG"
        self.cpp_info.names["cmake_find_package_multi"] = "SWIG"
        # self.cpp_info.build_modules["cmake_find_package"] = [self._module_file_rel_path]
        # self.cpp_info.build_modules["cmake_find_package_multi"] = [self._module_file_rel_path]

        bindir = os.path.join(self.package_folder, "bin")
        self.output.info("Appending PATH environment variable: {}".format(bindir))
        self.env_info.PATH.append(bindir)
