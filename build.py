from pybuilder.core import use_plugin, init

use_plugin("python.core")
use_plugin("python.install_dependencies")
use_plugin("python.flake8")
#use_plugin("python.coverage")
use_plugin("python.distutils")
use_plugin('pypi:pybuilder_pytest')

name = "omnibus"
default_task = "publish"


@init
def set_properties(project):
    project.set_property("dir_source_main_python", "src/main")
    project.set_property("dir_source_main_scripts", "src/scripts")
    project.set_property("dir_source_pytest_python", "src/test")
    project.depends_on("boto3")
    project.depends_on("marshmallow")
    project.depends_on("pyopenssl")