from conans import ConanFile, CMake, tools
import os


class LibmikmodConan(ConanFile):
    name = "libmikmod"
    version = "3.3.11.1"
    description = "Module player and library supporting many formats, including mod, s3m, it, and xm."
    topics = ("conan", "libmikmod", "audio")
    url = "https://github.com/bincrafters/conan-libmikmod"
    homepage = "http://mikmod.sourceforge.net"
    license = "LGPL-2.1"
    exports_sources = ["patches/*"]
    generators = "cmake"

    settings = "os", "arch", "compiler", "build_type"
    options = {
        "shared": [True, False],
        "fPIC": [True, False],
        "with_dsound": [True, False],
        "with_mmsound": [True, False],
        "with_alsa": [True, False],
        "with_oss": [True, False],
        "with_pulse": [True, False],
        "with_coreaudio": [True, False]
    }
    default_options = {
        "shared": False,
        "fPIC": True,
        "with_dsound": True,
        "with_mmsound": True,
        "with_alsa": True,
        "with_oss": True,
        "with_pulse": True,
        "with_coreaudio": True
    }

    _source_subfolder = "source_subfolder"
    _build_subfolder = "build_subfolder"

    def config_options(self):
        if self.settings.os == "Windows":
            del self.options.fPIC
        else:
            del self.options.with_dsound
            del self.options.with_mmsound
        if self.settings.os != "Linux":
            del self.options.with_alsa
        # Non-Apple Unices
        if self.settings.os not in ["Linux", "FreeBSD"]:
            del self.options.with_oss
            del self.options.with_pulse
        # Apple
        if self.settings.os not in ["Macos", "iOS", "watchOS", "tvOS"]:
            del self.options.with_coreaudio

    def configure(self):
        del self.settings.compiler.libcxx
        del self.settings.compiler.cppstd

    def requirements(self):
        if self.settings.os == "Linux":
            if self.options.with_alsa:
                self.requires("libalsa/1.1.9")
            if self.options.with_pulse:
                self.requires("pulseaudio/13.0@bincrafters/stable")

    def source(self):
        tools.get(**self.conan_data["sources"][self.version])
        extracted_dir = self.name + "-" + self.version
        os.rename(extracted_dir, self._source_subfolder)

    def _configure_cmake(self):
        cmake = CMake(self, set_cmake_flags=True)
        cmake.definitions["ENABLE_STATIC"] = not self.options.shared
        cmake.definitions["ENABLE_DOC"] = False
        cmake.definitions["ENABLE_DSOUND"] = self._get_safe_bool("with_dsound")
        cmake.definitions["ENABLE_MMSOUND"] = self._get_safe_bool("with_mmsound")
        cmake.definitions["ENABLE_ALSA"] = self._get_safe_bool("with_alsa")
        cmake.definitions["ENABLE_OSS"] = self._get_safe_bool("with_oss")
        cmake.definitions["ENABLE_PULSE"] = self._get_safe_bool("with_pulse")
        cmake.definitions["ENABLE_COREAUDIO"] = self._get_safe_bool("with_coreaudio")
        cmake.configure(build_folder=self._build_subfolder, source_folder=self._source_subfolder)
        return cmake

    def _get_safe_bool(self, option_name):
        opt = self.options.get_safe(option_name)
        if opt is not None:
            return opt
        else:
            return False

    def build(self):
        if self.conan_data["patches"][self.version]:
            # 0001:
            #   Patch CMakeLists.txt to run `conan_basic_setup`, to avoid building shared lib when
            #   shared=False, and a fix to install .dlls correctly on Windows
            for patch in self.conan_data["patches"][self.version]:
                tools.patch(**patch)
 
         # Ensure missing dependencies yields errors
        tools.replace_in_file(os.path.join(self._source_subfolder, "CMakeLists.txt"),
                              "MESSAGE(WARNING",
                              "MESSAGE(FATAL_ERROR")
 
        tools.replace_in_file(os.path.join(self._source_subfolder, "drivers", "drv_alsa.c"),
                              "alsa_pcm_close(pcm_h);",
                              "if (pcm_h) alsa_pcm_close(pcm_h);")

        cmake = self._configure_cmake()
        cmake.build()

    def package(self):
        self.copy(pattern="COPYING.LESSER", dst="licenses", src=self._source_subfolder)
        cmake = self._configure_cmake()
        cmake.install()
        os.remove(os.path.join(self.package_folder, "bin", "libmikmod-config"))
        if not self.options.shared:
            tools.rmdir(os.path.join(self.package_folder, "bin"))
        tools.rmdir(os.path.join(self.package_folder, "lib", "pkgconfig"))

    def package_info(self):
        self.cpp_info.libs = tools.collect_libs(self)
        if not self.options.shared:
            self.cpp_info.defines = ["MIKMOD_STATIC"]

        if self._get_safe_bool("with_dsound"):
            self.cpp_info.system_libs.append("dsound")
        if self._get_safe_bool("with_mmsound"):
            self.cpp_info.system_libs.append("winmm")
        if self._get_safe_bool("with_coreaudio"):
            self.cpp_info.frameworks.append("CoreAudio")
