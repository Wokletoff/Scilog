from base64 import b64decode
import base64
import zlib
import urllib

txt = open('/home/student/PycharmProjects/MagProject/project3/ProjectOnTeam/nlp/question_answering/5000.tab', 'r')
while True:
    line = txt.readline()
    txtId = line.split("\t")[0]
    src = line.split("\t")[1].replace("\n","")
    text2 = base64.b64decode(src)
    decompressed_data=zlib.decompress(text2, 16+zlib.MAX_WBITS)
    print(src, decompressed_data)
txt.close	
