# Image Inverter

## Information

App was inspired by this [gist](https://gist.github.com/MaxBQb/3140ffe5a3bc40301555cbf337eba4ad).

App can invert images from the clipboard and those that user drags onto the application window.

Ttk theme was used from [Azure-ttk-theme](https://github.com/rdbende/Azure-ttk-theme) repository.

## Requirements

* [Python 3.8-3.10](https://www.python.org/downloads/)

## Build

### Lib installation

Type in command prompt, you must have [requirements.txt](requirements.txt) in root folder of the project.

```
pip install -r requirements.txt
```

### Build with Nuitka

Type in command prompt `make` in root directory of the project to build it.

Executable file will be in `%project_root_dir%/image_inverter.dist`.

## Tested platforms

For now works and tested on Windows 7 or higher (64 bit).