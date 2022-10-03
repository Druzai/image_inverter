@ECHO OFF
python -m nuitka --standalone --enable-plugin=tk-inter --enable-plugin=numpy --windows-icon-from-ico=icon.ico ^
 --disable-console --windows-product-name="Image Inverter" --windows-file-version=0.1 ^
 --windows-file-description="Image Inverter" --follow-imports image_inverter.py
copy /y .\\icon.ico .\\image_inverter.dist\\icon.ico
copy /y .\\clipboard_placeholder.png .\\image_inverter.dist\\clipboard_placeholder.png
copy /y .\\azure.tcl .\\image_inverter.dist\\azure.tcl
xcopy .\\theme .\\image_inverter.dist\\theme\\ /E /H