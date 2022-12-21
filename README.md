# Инструкция
## Запуск через собранный скрипт
____
### LINUX / MacOS - https://disk.yandex.ru/d/z8yYun7k4vsEjQ
1) Скачать архив
2) Разархивировать папку
3) Имя скрипта - local_environment
4) Команда для запуска: ```<путь_до_папки>/local_environment <путь_до_.mol> --r_cut <int>```  
(дефолтный r_cut = 5)
5) Рядом c .mol файлом появится директории с <mol_name>_submols и <mol_name>_submols_xyz (в этой директории атом, для которого строим окружение, будет расположен на 1 месте) с локальным окружением каждого атома
____
### WINDOWS - https://disk.yandex.ru/d/EHRofw5H_3fbAA
1) Скачать архив
2) Разархивировать папку
3) Имя скрипта - local_environment.exe
4) Команда для запуска: ```<путь_до_папки>\local_environment.exe <путь_до_.mol> --r_cut <int>```  
(дефолтный r_cut = 5)
5) Рядом c .mol файлом появится директории с <mol_name>_submols и <mol_name>_submols_xyz (в этой директории атом, для которого строим окружение, будет расположен на 1 месте) с локальным окружением каждого атома
____
*P.S.* Для упаковки питона в скрипт использовал [pyinstaller](https://pyinstaller.org/en/stable/) v. 4.10
____
Внесение изменений/запуск из источников
---------
Для внесения изменений в код и запуска из источников требуется установить библиотеку **RDKit**  
Подробная инструкция - https://rdkit.org/docs/Install.html  
*P.S.* Я пробовал установку через anaconda и miniconda - она описана в пунктах **How to get conda** и **How to install RDKit with Conda**  
Команда для запуска из папки local_environment: ```python3 src/main.py <путь/до/.mol> --r_cut <int>```
