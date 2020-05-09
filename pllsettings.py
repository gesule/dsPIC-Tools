#! /usr/bin/python
# -*- coding: utf-8 -*-

import sys
import math

ayuda = f'''
NOMBRE
  {sys.argv[0]} 
  Aplicación python para calcular los ajustes del PLL para MCUs: 
  dsPIC33Ep y PIC24EP

SINOPSIS
  {sys.argv[0]} [-h|--help]
  {sys.argv[0]} [[-fi] <Freq_de_entrada>[k|K|M]] [-fo] <Freq_de_salida>[k|K|M]]

Se requiere al menos un argumento de entrada para indicar la frecuencia de
salida requerida. La frecuencia ha de especificarse como un número que 
expresará Hz, kHz o MHz añadiendo los sufijos correspondientes.
por ejemplo las siguientes llamadas son eqivalentes:
                {sys.argv[0]}  22118400
                {sys.argv[0]}  22118.4K
                {sys.argv[0]}  22.1184M

Por omisión se toma la frecuencia de entrada del oscilador INTRC = 7,37MHz.
También puede especificar la frecuencia de entrada, y puesto que no existe
solapamiento entre los intervalos de definición de ambas frecuencias,
pueden especificarse ambas sin más, y en cualquier orden. Por ejemplo:
                {sys.argv[0]}  8M 100M
                {sys.argv[0]}  100M 8M

En ambos casos la frecuencia de entrada es de 8MHz y la de salida de 100MHz.
Pero también puede ser mas explícito, asignando las frecuencas de entrada
y salida mediante los parámetros: -fo, -fi, --fout, --fin. Por ejemplo:
                {sys.argv[0]}  -fi 8M -fo 100M
               
PARAMETROS:
  -h, --help:     Muestran esta ayuda
  -fo, --fout:    Antecede al parámetro que especifica la frecuencia de salida
  -fi, --fin:     Antecede al parámetro que especifica la frecuencia de entrada

'''

import sys
import math

'''\
Convierte una cadena que contiene un valor numérico que puede contener, o no,
un sufijo para expresar Hz, kHz o MHz, en un número entero.
Si la conversión falla lanzará una excepción

@args
	token Cadena del tipo n[0-9][k,K,M]
'''
def getHz(token):
    if token[-1] == 'k' or token[-1] == 'K':
        return round(abs(float(token[:-1])) * 1000)
    elif token[-1] == 'M':
        return round(abs(float(token[:-1])) * 1000000)
    else:
        return round(abs(float(token)))


def pll(fi, prescaler, postscaler, divider):
    return fi * divider / prescaler / postscaler


def desviacion(objetivo, efectivo):
    return abs((efectivo - objetivo) / objetivo)


# ------------------------------------------------------------------------------
# Calcula los parámetros de configuración del PLL: pll_prescaler,
# pll_postscaler y pll_feedback_divisor,
# El cálculo tratará de obtener la mejor aproximación a la frecuencia de salida
# requerida.
# En algunos casos habrá mas de una solución, en estos casos se ofrecerá
# la solución en la que el punto de trabajo de fplli y fvco  estén mas
#  centrados respecto de su intervalo de funcionamiento.
# definición.
# @arguments:
# fin:      Frecuencia de entrada al prescaler.
# fout:     Frecuencia requerida de salida
# @return:
# Devuelve una tupla cde tres números que se han de interpretar como:
#   (pll_prescaler, pll_postscaler, pll_feedback_divisor) o
#   (N1, N2, M)
#
def pll_settings(fin, fout):
    # Restricciones aplicadas al cálculo.
    fplli_min = 800000  # Frecuencia mínima de entrada al PLL
    fplli_max = 8000000  # Frecuencia máxima de salida al PLL
    fplli_mid = (fplli_min + fplli_max) / 2

    fvco_min = 120000000  # Frecuencia mínima de salida del VCO
    fvco_max = 340000000  # Frecuencia máxima de salida del VCO
    fvco_mid = (fvco_min + fvco_max) / 2

    pllpre_min = 2
    pllpre_max = 33
    ###pllpre_mid = (pllpre_min + pllpre_max)/2

    plldiv_min = 2
    plldiv_max = 513
    ###plldiv_mid = (plldiv_min + plldiv_max)/2

    pllpost_set = [2, 4, 8]
    ###pllpost_mid = 4

    # Antes de comenzar a iterar se determinan los límites en los que el cálculo
    # queda dentro de las restricciones físicas.

    n1_min = math.ceil(fin / fplli_max)
    if n1_min < pllpre_min:
        n1_min = pllpre_min

    n1_max = math.floor(fin / fplli_min)
    if n1_max > pllpre_max:
        n1_max = pllpre_max

    n2_min = math.ceil(fvco_min / fout)
    if n2_min < pllpost_set[0]:
        n2_min = pllpost_set[0]

    n2_max = math.floor(fvco_max / fout)
    if n2_max > pllpost_set[-1]:
        n2_max = pllpost_set[-1]

    # Variables a empleadas en las iteraciones de cálculo.
    pll_n1 = 0
    pll_n2 = 0
    fout_error = fout
    test_fout = 0

    for test_post in pllpost_set:
        # sólo se itera sobre los valores previamente acotados para descartar las soluciones
        # que no encajan con las restricciones físicas del mcu.
        if test_post < n2_min:
            continue
        elif test_post > n2_max:
            break

        for test_pre in range(n1_min, n1_max + 1):
            for test_div in range(plldiv_min, plldiv_max + 1):
                test_fout = pll(fin, test_pre, test_post, test_div)
                test_error = abs(fout - test_fout)
                if test_error < fout_error:
                    fout_error = test_error
                    pll_n1 = test_pre
                    pll_n2 = test_post
                    pll_div = test_div
                elif test_error == fout_error:
                    # Desviación del punto de funcionamiento medio de la solución actual
                    desv_fplli = desviacion(fplli_mid, fin / pll_n1)
                    test_fplli = desviacion(fplli_mid, fin / test_pre)

                    desv_fvco = desviacion(fvco_mid, fout * pll_n2)
                    test_fvco = desviacion(fvco_mid, fout * test_post)

                    if (test_fplli * test_fvco) < (desv_fplli * desv_fvco):
                        fout_error = test_error
                        pll_n1 = test_pre
                        pll_n2 = test_post
                        pll_div = test_div

        return pll_n1, pll_n2, pll_div


def main():
    # límites:
    pllfin_min = 1600000
    pllfin_max = 8000000
    pllfout_min = 15000000
    pllfout_max = 140000000
         
    # Variables de entrada para hacer los cálculos:
    # pll_fin: Por omisión, se asume conectado a INTRC = 7,37MHz
    pll_fin = int(7.37e6)    
    #
    # pll_fout: debe ser establecida mediante parámetro de línea de comando
    pll_fout = 0

    # Parámetros del ejecución:
    verbose = 5
    
    # Evaluación de parámetros:
    if len(sys.argv) < 2:
        msg_error = f''' 
ERROR:  Se requiere al menos un parámetro para especificar la frecuencia
        de salida requerida en Hz, kHz o MHz. Por ejemplo: 
            {sys.argv[0]} 100M
       
        Proporcionará los ajustes para obtener una frecuencia de 100MHz a
        partir del oscilador interno INTRC de 7,37MHz

        Utilice el parámetro -h o --help para mas información.\n '''

        print(msg_error)
        exit()

    # Variable para para asignar correctamente el significado de cada token
    #  en los argumentos compuestos.
    next_token = 'name'
    for token in sys.argv[1:]:
        if next_token == 'name':
            if token == '-h' or token == '--help':
                print(ayuda)
                exit(-1)
        
            elif token == '-fo' or token == '-fout' or token == '--fout':
                next_token = 'fout_val'
            
            elif token == '-fi' or token == '-fin' or token == '--fin':
                next_token = 'fin_val'

            # En última instancia se aceptan argumentos sin nombre tales que
            # que se interpretarán como una especificación de frecuencia
            # de entrada o salida en función a su valor.
            else:                
                try:
                    freq = getHz(token)
                    if freq >= pllfout_min and freq <= pllfout_max:
                        pll_fout = freq
                    elif freq >= pllfin_min and freq <= pllfin_max:
                        pll_fin = freq
                    else:
                        msg_error = f'''
ERROR:  La frecuencia: {token} está fuera del intervalo aceptable para las
        frecuencias de entrada y de salida. '''
                        print(msg_error)

                except ValueError:
                        msg_error = f'''
ERROR:  No se reconoce el argumento: {token} como un argumento válido.'''
                        print(msg_error)
                        exit(-1)

        elif next_token == 'fout_val':
            try:
                pll_fout = getHz(token)
            except ValueError:
                msg_error = f'''
ERROR:  En el valor especificado para --fout {token}
        {token} no tiene el formato adecuado.  '''

                print(msg_error)
                exit(-1)

            next_token = 'name'
    
        elif next_token == 'fin_val':
            try:
                pll_fin = getHz(token)
            except ValueError:
                msg_error = f'''
ERROR:  En el valor especificado para --fin {token}
        {token} no tiene el formato adecuado.  '''

                print(msg_error)
                exit(-1)

            next_token = 'name'

    if pll_fout == 0:
        print('ERROR:  No ha especificado una frecuencia de salida válida')
        exit(-1)

    if pll_fin < pllfin_min or pll_fin > pllfin_max:
        print(f'Frecuencia de entrada fuera del intervalo admitido: ({pllfin_min/1000000}M, {pllfin_max/1000000}M)')
        exit(-1)

    if pll_fout < pllfout_min or pll_fout > pllfout_max:
        print(f'Frecuencia de salida fuera del intervalo admitido: ({pllfout_min/1000000}M, {pllfout_max/1000000}M)')
        exit(-1)

    if verbose > 0:
        print(f'Calculando para: Fin={pll_fin / 1000000}MHz, Fout={pll_fout / 1000000}MHz')

    pll_n1, pll_n2, pll_m = pll_settings(pll_fin, pll_fout)

    print(f'N1 = {pll_n1}')
    print(f'N2 = {pll_n2}')
    print(f'M = {pll_m}')

    act_fout = pll(pll_fin, pll_n1, pll_n2, pll_m)

    print(f'Frecuencia obtenida: Fout={act_fout / 1000000}MHz')
    print(f'error: {100 * (act_fout - pll_fout) / pll_fout}%')
    print(f'Punto de funcionamiento: fplli = {pll_fin / pll_n1 / 1000000}MHz, fvco = {pll_fout * pll_n2 / 1000000}MHz')


if __name__ == '__main__':
    main()


