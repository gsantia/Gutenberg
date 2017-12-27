import json, os

with open(diskBooksMetaData.json, 'r') as f:
    booknums = json.loads(f.read()).keys()

batches = {str(i+1): [] for i in range(20)}

for i, booknum in enumerate(booknums):
    batch_num = (i % 20) + 1
    batches[str(batch_num)].append(booknum)


with open('batches.json', 'w') as writefile:
    writefile.writelines(json.dumps(batches))

for j in batches.keys():
    os.system('python2 runMLE.py ' + j + '&')
