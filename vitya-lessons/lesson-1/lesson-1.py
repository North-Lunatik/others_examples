from asyncore import read
from fileinput import close
from itertools import count
import string
from unicodedata import name
from unittest import result


f = open('/Users/smilevpn/Git/others_examples/vitya-lessons/lesson-1/lesson-1.txt', 'r')
try:
    x = f.read()
    print('Исходный текст:', '\n', x)
finally:
    f.close()
string.punctuation
for s in string.punctuation:
    if s in x:
        x = x.replace(s, '').lower()
x.strip().lower()
res = len(x.split())
sum = x.split()
sum.sort()
print('Количество слов в текстовом файле =', res, '\n',
      'Вывод текста с сортировкой слов в алфавитном порядке без знаков препинания:', '\n', * sum, sep=' ')
