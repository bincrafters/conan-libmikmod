#!/usr/bin/env python
# -*- coding: utf-8 -*-

from conans import ConanFile, CMake, tools
import os


class LibmikmodConan(ConanFile):
    name = "libmikmod"
    version = "3.3.11.1"
    description = "Module player and library supporting many formats, including mod, s3m, it, and xm."
    topics = ("conan", "libmikmod", "audio")
    url = "https://github.com/bincrafters/conan-libmikmod"
    homepage = "http://mikmod.sourceforge.net/"
    author = "Bincrafters <bincrafters@gmail.com>"
    license = "LGPL-2.1"
    exports = ["LICENSE.md"]
    exports_sources = ["CMakeLists.txt.patch"]
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
        if self.settings.os == 'Windows':
            del self.options.fPIC
        else:
            del self.options.with_dsound
            del self.options.with_mmsound
        if self.settings.os != 'Linux':
            del self.options.with_alsa
        # Non-Apple Unices
        if self.settings.os not in ['Linux', 'Android', 'FreeBSD']:
            del self.options.with_oss
            del self.options.with_pulse
        # Apple
        if self.settings.os not in ['Macos', 'iOS', 'watchOS', 'tvOS']:
            del self.options.with_coreaudio

    def system_requirements(self):
        if self.settings.os == "Linux" and tools.os_info.is_linux:
            if tools.os_info.with_apt:
                installer = tools.SystemPackageTool()
                arch_suffix = ''
                if self.settings.arch == "x86":
                    arch_suffix = ':i386'
                elif self.settings.arch == "x86_64":
                    arch_suffix = ':amd64'

                if self.options.with_alsa:
                    installer.install('libasound2-dev' + arch_suffix)
                if self.options.with_pulse:
                    installer.install('libpulse-dev' + arch_suffix)

    def source(self):
        extracted_dir = self.name + "-" + self.version
        download_url = "https://sourceforge.net/projects/mikmod/files/{0}/{1}/{2}.tar.gz".format(self.name, self.version, extracted_dir)
        tools.get(download_url, sha256="ad9d64dfc8f83684876419ea7cd4ff4a41d8bcd8c23ef37ecb3a200a16b46d19")

        os.rename(extracted_dir, self._source_subfolder)

        # Patch CMakeLists.txt to run `conan_basic_setup`, to avoid building shared lib when
        # shared=False, and a fix to install .dlls correctly on Windows
        tools.patch(patch_file="CMakeLists.txt.patch", base_path=self._source_subfolder)

        # Ensure missing dependencies yields errors
        tools.replace_in_file(os.path.join(self._source_subfolder, 'CMakeLists.txt'),
            'MESSAGE(WARNING',
            'MESSAGE(FATAL_ERROR')

    def _configure_cmake(self):
        cmake = CMake(self)
        cmake.definitions['ENABLE_STATIC'] = not self.options.shared
        cmake.definitions['ENABLE_DOC'] = False
        cmake.definitions['ENABLE_DSOUND'] = self._get_safe_bool('with_dsound')
        cmake.definitions['ENABLE_MMSOUND'] = self._get_safe_bool('with_mmsound')
        cmake.definitions['ENABLE_ALSA'] = self._get_safe_bool('with_alsa')
        cmake.definitions['ENABLE_OSS'] = self._get_safe_bool('with_oss')
        cmake.definitions['ENABLE_PULSE'] = self._get_safe_bool('with_pulse')
        cmake.definitions['ENABLE_COREAUDIO'] = self._get_safe_bool('with_coreaudio')
        cmake.configure(build_folder=self._build_subfolder, source_folder=self._source_subfolder)
        return cmake

    def _get_safe_bool(self, option_name):
        opt = self.options.get_safe(option_name)
        if opt is not None:
            return opt
        else:
            return False

    def build(self):
        cmake = self._configure_cmake()
        cmake.build()

    def package(self):
        self.copy(pattern="COPYING.LESSER", dst="licenses", src=self._source_subfolder)
        cmake = self._configure_cmake()
        cmake.install()

    def package_info(self):
        self.cpp_info.libs = tools.collect_libs(self)
        if not self.options.shared:
            self.cpp_info.defines = ['MIKMOD_STATIC']

        if self._get_safe_bool('with_dsound'):
            self.cpp_info.libs.append('dsound')
        if self._get_safe_bool('with_mmsound'):
            self.cpp_info.libs.append('winmm')
        if self._get_safe_bool('with_alsa'):
            self.cpp_info.libs.append('asound')
        if self._get_safe_bool('with_pulse'):
            self.cpp_info.libs.extend(['pulse-simple', 'pulse'])
        if self._get_safe_bool('with_coreaudio'):
            self.cpp_info.exelinkflags.append('-framework CoreAudio')
            self.cpp_info.sharedlinkflags = self.cpp_info.exelinkflags
