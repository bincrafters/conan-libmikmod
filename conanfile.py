#!/usr/bin/env python
# -*- coding: utf-8 -*-

from conans import ConanFile, CMake, tools
import os


class LibmikmodConan(ConanFile):
    name = "libmikmod"
    version = "3.3.11.1"
    description = "Module player and library supporting many formats, including mod, s3m, it, and xm."
    topics = ("conan", "libmikmod", "audio")
    url = "https://github.com/sixten-hilborn/conan-libmikmod"
    homepage = "http://mikmod.sourceforge.net/"
    author = "Sixten Hilborn <sixten.hilborn@gmail.com>"
    license = "LGPL-2.1"
    exports = ["LICENSE.md"]
    exports_sources = ["CMakeLists.txt.patch"]
    generators = "cmake"

    settings = "os", "arch", "compiler", "build_type"
    options = {
        "shared": [True, False],
        "fPIC": [True, False]
    }
    default_options = {
        "shared": False,
        "fPIC": True
    }

    _source_subfolder = "source_subfolder"
    _build_subfolder = "build_subfolder"

    def config_options(self):
        if self.settings.os == 'Windows':
            del self.options.fPIC

    def source(self):
        extracted_dir = self.name + "-" + self.version
        tools.get("https://sourceforge.net/projects/mikmod/files/{0}/{1}/{2}.tar.gz".format(self.name, self.version, extracted_dir))

        # Rename to "source_subfolder" is a convention to simplify later steps
        os.rename(extracted_dir, self._source_subfolder)

    def _configure_cmake(self):
        cmake = CMake(self)
        cmake.definitions['ENABLE_STATIC'] = not self.options.shared
        cmake.definitions['ENABLE_DOC'] = False
        cmake.configure(build_folder=self._build_subfolder, source_folder=self._source_subfolder)
        return cmake

    def build(self):
        cmake = self._configure_cmake()
        cmake.build()

    def package(self):
        self.copy(pattern="COPYING.LESSER", dst="licenses", src=self._source_subfolder)
        cmake = self._configure_cmake()
        cmake.install()

    def package_info(self):
        self.cpp_info.libs = tools.collect_libs(self)
