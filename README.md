Инструкция
======
Запуск через собранный скрипт
------
* UNIX - https://disk.yandex.ru/d/pBdXcCzzuqdpOQ
1) Разорхивировать папку
2) Имя скрипта - local_environment
3) Команда для запуска: ```./local_environment <путь/до/.mol> --r_cut <int>``` делолтный r_cut - 5
4) Рядом c .mol файлом появится директория с mol_submols с локальным окружением каждого атома
* WINDOWS wip

*P.S.* Для упаковки питона в скрипт использовал [pyinstaller](https://pyinstaller.org/en/stable/)
____
Внесение изменений/запуск из источников
---------
Для внесения изменений в код и запуска из источников требуется установить библиотеку **RDKit**  
Подробная инструкция - https://rdkit.org/docs/Install.html  
*P.S.* Я пробовал только установку через anaconda и miniconda.  
Она описана в пунктах **How to get conda** и **How to install RDKit with Conda**
