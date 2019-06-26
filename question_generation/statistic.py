import os
import json

dir = "CLEVR_1.0_templates"
tar_file = "total.json"

text_ex = dict()
for json_file in os.listdir(dir):
    if json_file.endswith(".json"):
        file = os.path.join(dir, json_file)
        with open(file, 'r') as f:
            data = json.load(f)
            for i, d in enumerate(data):
                text_ex[str(json_file.split('.')[0]) + '_' +str(i)] = d['text'][0]

with open(tar_file, "w+") as t:
    json.dump(text_ex, t, indent=4)

def filter(questions, name):
    for i, q in enumerate(questions):
        if q['image'] == name:
            print(i, q["template_filename"], q['question_family_index'])
            print(q["question"])

