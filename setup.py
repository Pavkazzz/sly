from cx_Freeze import setup, Executable

# Dependencies are automatically detected, but it might need
# fine tuning.
buildOptions = dict(packages = [], excludes = [])

executables = [
    Executable('sly.py', 'Console')
]

setup(name='sly',
      version = '0.0.1',
      description = 'Player for vk',
      options = dict(build_exe = buildOptions),
      executables = executables)
