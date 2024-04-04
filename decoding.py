from base64 import b64decode

	
file = open('/home/student/Документы/test/5000.tab', 'r')
for line in file:
    print(line)
file.close()