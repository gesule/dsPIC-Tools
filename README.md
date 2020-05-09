## dsPIC-Tools
Colección de utilidades relacionadas con la programción de microcontroladores 
dsPIC33

### pllsettings.py
Permite calcular los ajustes del PLL para MCUs de tipo:
dsPIC33Ep y PIC24EP

Ejemplos de uso:

    python pllsettings.py -fo 100M -fi 8M

O bien tras otorgarle permisos de ejecución a pllsettings.py
    ./pllsettings.py -fo 100M -fi 8M

El parámetro -fi es opcional, si se omite se utiliza la frecuencia del
oscliador interno INTRC = 7,37MHz

