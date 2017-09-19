
import os
from conans import ConanFile, AutoToolsBuildEnvironment, tools, VisualStudioBuildEnvironment
from conans.tools import os_info, SystemPackageTool, download, untargz, replace_in_file
from conans.errors import ConanException


class ConanRecipe(ConanFile):
    name = "postgresql"
    version = "v9.6.5"
    settings = "os", "compiler", "build_type", "arch"
    description = "Conan package for the postgresql library"
    url = "https://github.com/jgsogo/conan-postgresql"
    license = "https://www.postgresql.org/about/licence/"
    options = {"without_readline": [True, False],}
    default_options = "without_readline=False"

    @property
    def version_short(self):
        return self.version[1:]

    @property
    def pq_source_folder(self):
        return os.path.abspath('postgresql-{}'.format(self.version_short))

    @property
    def pq_msvc_dir(self):
        return os.path.join(self.pq_source_folder, 'src', 'tools', 'msvc')

    @property
    def pq_install_folder(self):
        return os.path.join(self.pq_source_folder, 'install_dir')

    def build_requirements(self):
        if self.settings.os == "Windows":
            try:
                self.run("perl -v")
            except ConanException:
                self.build_requires("strawberryperl/5.26.0@conan/stable")

        if os_info.is_linux and os_info.with_apt:
            if not self.options.without_readline:
                installer = SystemPackageTool()
                #installer.install("libreadline")
                installer.install("libreadline-dev")

    def source(self):
        if self.version == 'master':
            raise NotImplementedError("Sources for master branch not implemented")
        else:
            url = "https://ftp.postgresql.org/pub/source/{}/postgresql-{}.tar.gz".format(self.version, self.version_short)
            zip_name = 'postgresql.tar.gz'
            download(url, zip_name)
            untargz(zip_name)
            os.unlink(zip_name)

    def build(self):
        if self.settings.os in ["Linux", "Macos"]:
            install_folder = self.pq_install_folder
            env = AutoToolsBuildEnvironment(self)
            with tools.environment_append(env.vars):
                with tools.chdir(self.pq_source_folder):
                    self.run("./configure --prefix={} && make".format(install_folder))
                    self.run("make install")

        elif self.settings.os == "Windows":
            if self.settings.compiler == "Visual Studio":
                # Visual Studio: https://www.postgresql.org/docs/current/static/install-windows-full.html

                #config_pl = os.path.join(msvc_dir, 'config.pl')
                #with open(config_pl, 'w') as cfg:
                #    cfg.write("$config->{python} = '%s';" % os.path.dirname(sys.executable))

                env = VisualStudioBuildEnvironment(self)
                with tools.environment_append(env.vars):
                    with tools.chdir(self.pq_msvc_dir):
                        self.run("build.bat")
            else:
                raise NotImplementedError("Windows compiler {!r} not implemented".format(str(self.settings.compiler)))
        else:
            raise NotImplementedError("Compiler {!r} for os {!r} not available".format(str(self.settings.compiler), str(self.settings.os)))

    def package(self):
        install_folder = self.pq_install_folder

        if self.settings.os == "Windows":
            # Modify install.pl file: https://stackoverflow.com/questions/46161246/cpan-install-moduleinstall-fails-passing-tests-strawberryperl/46162454?noredirect=1#comment79291874_46162454
            install_pl = os.path.join(self.pq_msvc_dir, 'install.pl')
            replace_in_file(install_pl, "use Install qw(Install);", "use FindBin qw( $RealBin );\nuse lib $RealBin;\nuse Install qw(Install);")
            with tools.chdir(os.path.abspath(self.pq_msvc_dir)):
                self.run("install %s" % install_folder)

        self.copy("*", dst="", src=install_folder, keep_path=True)
        self.copy(pattern="COPYRIGHT", dst="licenses", src=self.pq_source_folder, ignore_case=True, keep_path=False)

    def package_info(self):
        if self.settings.os == "Windows":
            self.cpp_info.libs = ["libpq",]
        else:
            self.cpp_info.libs = ["pq", ]
