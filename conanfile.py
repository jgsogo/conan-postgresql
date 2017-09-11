import os
import sys
from conans import ConanFile, CMake, AutoToolsBuildEnvironment, tools, VisualStudioBuildEnvironment
from conans.tools import os_info, SystemPackageTool, download, untargz, replace_in_file, unzip, pythonpath
from conans.errors import ConanException


class PostgreSQLConan(ConanFile):
    name = "postgresql"
    version = "v9.6.5"
    settings = "os", "compiler", "build_type", "arch"
    description = "Conan package for the postgresql library"
    url = "https://github.com/jgsogo/conan-postgresql"
    license = "https://www.postgresql.org/about/licence/"

    @property
    def version_short(self):
        return self.version[1:]

    @property
    def pq_source_folder(self):
        return 'postgresql-{}'.format(self.version_short)

    @property
    def pq_msvc_dir(self):
        return os.path.abspath(os.path.join(self.pq_source_folder, 'src', 'tools', 'msvc'))

    def build_requirements(self):
        if self.settings.os == "Windows":
            try:
                self.run("perl -v")
            except ConanException:
                self.build_requires("strawberryperl/5.26.0@conan/stable")

    def source(self):
        if self.version == 'master':
            raise NotImplementedError("Compilation of master branch not implemented")
        else:
            url = "https://ftp.postgresql.org/pub/source/{}/postgresql-{}.tar.gz".format(self.version, self.version_short)
            zip_name = 'postgresql.tar.gz'
            download(url, zip_name)
            untargz(zip_name)
            os.unlink(zip_name)

    def build(self):
        if self.settings.os == "Linux" or self.settings.os == "Macos":
            raise NotImplementedError("Compilation of master branch not implemented")
        else:
            if self.settings.compiler == "Visual Studio":
                # Visual Studio: https://www.postgresql.org/docs/current/static/install-windows-full.html
                msvc_dir = os.path.abspath(os.path.join(self.pq_source_folder, 'src', 'tools', 'msvc'))

                #config_pl = os.path.join(msvc_dir, 'config.pl')
                #with open(config_pl, 'w') as cfg:
                #    cfg.write("$config->{python} = '%s';" % os.path.dirname(sys.executable))

                env = VisualStudioBuildEnvironment(self)
                with tools.environment_append(env.vars):
                    with tools.chdir(self.pq_msvc_dir):
                        self.run("build.bat")
            else:
                raise NotImplementedError("Windows compiler {!r} not implemented".format(self.settings.compiler))

    def package(self):
        install_folder = os.path.join(self.pq_source_folder, 'install')
        if self.settings.os == "Windows":
            with tools.chdir(self.pq_msvc_dir):
                # self.run("cpan Module::Install")  <-- This one fails...
                replace_in_file('install.pl', 'use Install qw(Install);', 'use FindBin qw( $RealBin );\nuse lib $RealBin;\nuse Install qw(Install);')
                print("*"*20)
                with open('install.pl') as f:
                    print(f)
                print("*" * 20)
                self.run("install %s" % install_folder)

        self.copy("*", dst="include", src=install_folder, keep_path=True)
        self.copy(pattern="COPYRIGHT", dst="licenses", src=self.pq_source_folder, ignore_case=True, keep_path=False)

        #if self.settings.os == "Windows":
        #    self.copy("*.lib", dst="lib", src=os.path.join(self.pq_source_folder, str(self.settings.build_type)))
        #    self.copy("*.dll", dst="bin", src=os.path.join(self.pq_source_folder, str(self.settings.build_type)))

    def package_info(self):
        self.cpp_info.libs = ["pq",]

