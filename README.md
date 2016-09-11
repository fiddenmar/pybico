# pybico
Python Bibliography Converter

# Platforms
pybico is developed on elementary OS Freya, Ubuntu 14.04 or higher should be workable as well as Debian 8.0 or higher.

# Installation
In order to run pybico you'll need Python 3 and some modules that could be installed via pip3: xlsxwriter, regex, pymysql  
It also requires mysql server running on localhost and having database 'pybico' (there's an example named pybico.sql).

# Run
## Help
python3 pybico.py -h
## Import txt
python3 pybico.py -i import.txt -u mysql_user -p path_to_file_with_mysql_user_password
## Export txt
python3 pybico.py -e output.xlsx -u mysql_user -p path_to_file_with_mysql_user_password
## Import and export
python3 pybico.py -i import.txt -e output.xlsx -u mysql_user -p path_to_file_with_mysql_user_password