from pybuilder.core import use_plugin, init

use_plugin("python.core")
use_plugin("python.install_dependencies")
use_plugin("python.flake8")
use_plugin("python.coverage")
use_plugin("python.distutils")

#use_plugin('pypi:pybuilder_pytest')

name = "melange"
version = "1.0-arrakis"
default_task = "publish"


@init
def set_properties(project):
    project.set_property("dir_source_main_python", "src/main")
    project.set_property("dir_source_main_scripts", "src/scripts")
    project.set_property("dir_source_pytest_python", "src/test")

    project.set_property("coverage_break_build", False)
    project.set_property("flake8_verbose_output", True)
    project.set_property("flake8_break_build", True)

    project.depends_on("boto3")
    project.depends_on("marshmallow")
    project.depends_on("pyopenssl")
    project.depends_on("redis-simple-cache", url="git+https://github.com/Rydra/redis-simple-cache")

    project.version = version
