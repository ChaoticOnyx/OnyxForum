import ast
import re
from setuptools import find_packages, setup


with open("hub/__init__.py", "rb") as f:
    version_line = re.search(
        r"__version__\s+=\s+(.*)", f.read().decode("utf-8")
    ).group(1)
    version = str(ast.literal_eval(version_line))


setup(
    name="flaskbb-plugin-hub",
    version=version,
    packages=find_packages("."),
    include_package_data=True,
    package_data={
        "": ["hub/translations/*/*/*.mo", "hub/translations/*/*/*.po"]
    },
    zip_safe=False,
    platforms="any",
    entry_points={"flaskbb_plugins": ["hub = hub"]},
    install_requires=["FlaskBB>=2.0.dev0"],
)
