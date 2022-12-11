from asyncore import read
from fileinput import close
from itertools import count
import string
from unicodedata import name
from unittest import result


f = open('lesson-1.txt', 'r')
try:
    x = f.read()
finally:
    f.close()
string.punctuation
for s in string.punctuation:
    if s in x:
        x = x.replace(s, '').lower()
x.strip().lower()
res = len(x.split())
print(*x)
print(res)
sum = x.split()
sum.sort()
print(*sum, sep=', ')
