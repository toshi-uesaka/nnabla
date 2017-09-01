# Copyright (c) 2017 Sony Corporation. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from __future__ import print_function

from setuptools import setup
from distutils.extension import Extension
import os
import shutil
import sys
from collections import namedtuple
import copy

setup_requires = [
    'numpy>=1.10',
    'Cython>=0.24,<0.26',  # Requires python-dev.
]

install_requires = setup_requires + [
    'contextlib2',
    'futures',
    'h5py',
    'protobuf',
    'scikit-image',
    'scipy',
    'tqdm',
]


def extopts(library_name, library_dir):
    import numpy as np
    include_dir = os.path.realpath(os.path.join(
        os.path.dirname(__file__), '../include'))
    ext_opts = dict(
        include_dirs=[include_dir, np.get_include()],
        libraries=[library_name],
        library_dirs=[library_dir],
        language="c++",
        # The below definition breaks build. Use -Wcpp instead.
        # define_macros=[('NPY_NO_DEPRECATED_API', 'NPY_1_7_API_VERSION')],
    )
    if sys.platform != 'win32':
        ext_opts.update(dict(
            extra_compile_args=[
                '-std=c++11', '-Wno-sign-compare', '-Wno-unused-function', '-Wno-cpp'],
            runtime_library_dirs=['$ORIGIN/'],
        ))
    else:
        ext_opts.update(dict(extra_compile_args=['/W0']))
    return ext_opts

################################################################################
# Main

if __name__ == '__main__':
    from Cython.Build import cythonize

    ############################################################################
    # Get version info
    root_dir = os.path.realpath(os.path.dirname(__file__))
    a = dict()
    exec(open(os.path.join(root_dir, 'src', 'nnabla',
                           '_version.py')).read(), globals(), a)
    if '__version__' in a:
        __version__ = a['__version__']
    if '__email__' in a:
        __email__ = a['__email__']

    ############################################################################
    # Package information
    pkg_info = dict(
        name="nnabla",
        description='Neural Network Libraries',
        version=__version__,
        author_email=__email__,
        url="https://github.com/sony/nnabla",
        license='Apache Licence 2.0',
        classifiers=[
            'Development Status :: 4 - Beta',
            'Intended Audience :: Developers',
            'Intended Audience :: Education',
            'Intended Audience :: Science/Research',
            'Topic :: Scientific/Engineering',
            'Topic :: Scientific/Engineering :: Artificial Intelligence',
            'License :: OSI Approved :: Apache Software License',
            'Programming Language :: C++',
            'Programming Language :: Python :: 2',
            'Programming Language :: Python :: 2.7',
            'Programming Language :: Python :: 3',
            'Programming Language :: Python :: 3.4',
            'Programming Language :: Python :: 3.5',
            'Programming Language :: Python :: 3.6',
            'Programming Language :: Python :: Implementation :: CPython',
            'Operating System :: Microsoft :: Windows',
            'Operating System :: POSIX :: Linux',
        ],
        keywords="deep learning artificial intelligence machine learning neural network",
        python_requires='>=2.7,!=3.0.*,!=3.1.*,!=3.2.*,!=3.3.*',
    )

    ############################################################################
    # Parse setup.cfg
    from six.moves.configparser import ConfigParser
    path_cfg = os.path.join(os.path.dirname(__file__), "setup.cfg")
    if not os.path.isfile(path_cfg):
        raise ValueError(
            "`setup.cfg` does not exist. Read installation document and install using CMake.")
    cfgp = ConfigParser()
    cfgp.read(path_cfg)
    build_dir = cfgp.get("cmake", "build_dir")

    ############################################################################
    # Extension module information
    src_dir = os.path.join(root_dir, 'src')
    path_pkg = os.path.join(src_dir, 'nnabla')

    library_name = cfgp.get("cmake", "target_name")
    library_file_name = cfgp.get("cmake", "target_file_name")
    library_path = cfgp.get("cmake", "target_file")
    library_dir = os.path.dirname(library_path)

    ext_opts = extopts(library_name, library_dir)

    ext_modules = [
        Extension("nnabla._variable",
                  [os.path.join(path_pkg, '_variable.pyx')],
                  **ext_opts),
        Extension("nnabla.function",
                  [os.path.join(path_pkg, 'function.pyx')],
                  **ext_opts),
        Extension("nnabla.solver",
                  [os.path.join(path_pkg, 'solver.pyx')],
                  **ext_opts),
        Extension("nnabla.communicator",
                  [os.path.join(path_pkg, 'communicator.pyx')],
                  **ext_opts),
        Extension("nnabla._init",
                  [os.path.join(path_pkg, '_init.pyx')],
                  **ext_opts),
        Extension("nnabla._nd_array",
                  [os.path.join(path_pkg, '_nd_array.pyx')],
                  **ext_opts),
    ]

    # Cythonize
    ext_modules = cythonize(ext_modules, compiler_directives={
                            "embedsignature": True,
                            "c_string_type": 'str',
                            "c_string_encoding": "ascii"})

    ############################################################################
    # Package data
    # Move shared libs to module
    # http://stackoverflow.com/questions/6191942/distributing-pre-built-libraries-with-python-modules
    # Packaging shared lib
    # http://stackoverflow.com/questions/6191942/distributing-pre-built-libraries-with-python-modules

    shutil.copyfile(library_path, os.path.join(path_pkg, library_file_name))
    package_data = {"nnabla": [library_file_name, 'nnabla.conf']}

    for root, dirs, files in os.walk(os.path.join(build_dir, 'bin')):
        for fn in files:
            if os.path.splitext(fn)[1] == '' or os.path.splitext(fn)[1] == '.exe':
                if not os.path.isdir(os.path.join(path_pkg, 'bin')):
                    os.makedirs(os.path.join(path_pkg, 'bin'))
                shutil.copyfile(os.path.join(root, fn),
                                os.path.join(path_pkg, 'bin', fn))
                os.chmod(os.path.join(path_pkg, 'bin', fn), 0o755)
                package_data["nnabla"].append(os.path.join('bin', fn))

    for root, dirs, files in os.walk(os.path.join(build_dir, 'lib')):
        for fn in files:
            if os.path.splitext(fn)[1] == '.so' or os.path.splitext(fn)[1] == '.dylib':
                if not os.path.isdir(os.path.join(path_pkg, 'bin')):
                    os.makedirs(os.path.join(path_pkg, 'bin'))
                shutil.copyfile(os.path.join(root, fn),
                                os.path.join(path_pkg, 'bin', fn))
                os.chmod(os.path.join(path_pkg, 'bin', fn), 0o755)
                package_data["nnabla"].append(os.path.join('bin', fn))

    export_lib = ''
    # Read NNabla lib info
    if sys.platform == 'win32':
        for root, dirs, files in os.walk(os.path.join(build_dir, 'bin')):
            for fn in files:
                if os.path.splitext(fn)[1] == '.lib':
                    shutil.copyfile(os.path.join(root, fn),
                                    os.path.join(path_pkg, fn))
                    package_data["nnabla"].append(fn)

    package_dir = {'': src_dir,
                   'nnabla.extensions.cpu': os.path.join(src_dir, 'extensions/cpu')}
    packages = ['nnabla',
                'nnabla.contrib',
                'nnabla.utils',
                'nnabla.utils.cli',
                'nnabla.extensions',
                'nnabla.extensions.cpu']

    # Setup
    setup(
        entry_points={"console_scripts":
                      ["nnabla_cli=nnabla.utils.cli.cli:main"]},
        setup_requires=setup_requires,
        install_requires=install_requires,
        ext_modules=ext_modules,
        package_dir=package_dir,
        packages=packages,
        package_data=package_data,
        **pkg_info)

    os.unlink(os.path.join(root_dir, 'src', 'nnabla', library_file_name))
    shutil.rmtree(os.path.join(root_dir, 'src',
                               'nnabla', 'dev'), ignore_errors=True)
    shutil.rmtree(os.path.join(root_dir, 'src',
                               'nnabla', 'bin'), ignore_errors=True)
