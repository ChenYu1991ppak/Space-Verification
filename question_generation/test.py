import os
import json
from PIL import Image
import numpy as np

image_dir = 'output/images'
sence_dir = 'output/scenes'
shade_dir = 'output/shade'
question_dir = 'output/questions_zh'


def rewrite(file):
    f = open(file, 'r')
    data = json.load(f)
    with open(file, 'w+') as t:
        json.dump(data, t, indent=2)
    f.close()


def mark_object(name, obj_idx):
    file = os.path.join(image_dir, name + '.png')
    image = Image.open(file)
    matrix = np.asarray(image).copy()
    file2 = os.path.join(sence_dir, name + '.json')
    with open(file2, 'r+') as f:
        data = json.load(f)
        loc = data['objects'][obj_idx]['pixel_coords']
    matrix[loc[1] - 2:loc[1] + 2, loc[0] - 1:loc[0] + 2, 0] = 0
    matrix[loc[1] - 2:loc[1] + 2, loc[0] - 1:loc[0] + 2, 1] = 255
    matrix[loc[1] - 2:loc[1] + 2, loc[0] - 1:loc[0] + 2, 2] = 0
    return Image.fromarray(matrix)


def enclose_object(name):
    image = Image.open(os.path.join(shade_dir, name + '.png'))
    matrix = np.asarray(image)
    with open(os.path.join(sence_dir, name + '.json'), 'r') as f:
        data = json.load(f)
        for obj in data['objects']:
            loc = obj['pixel_coords']
            x = loc[0]
            y = loc[1]
            if x > 343:
                x = 343
            if x < 1:
                x = 1
            if y > 343:
                y = 343
            if y < 1:
                y = 1

            color = matrix[y, x, :]
            cmp = (matrix == color).all(axis=2)
            ys, xs = np.where(cmp == True)
            height = max(max(ys) - min(ys), 34)
            width = max(max(xs) - min(xs), 34)
            obj['height'] = int(height)
            obj['width'] = int(width)
    # print(data)
    with open(os.path.join(sence_dir, name + '.json'), 'w') as f:
        json.dump(data, f)


def reinforce_answer(name):
    with open(os.path.join(sence_dir, name + '.json'), 'r') as f:
        data = json.load(f)
    with open(os.path.join(question_dir, name + '_question' + '.json'), 'r', encoding='utf-8') as f:
        questions = json.load(f)
        for q in questions['questions']:
            idx = (q['answer'])
            h = data['objects'][idx]['height']
            w = data['objects'][idx]['width']
            loc = data['objects'][idx]['pixel_coords'][:2]
            x = loc[0]
            y = loc[1]
            if x > 343 - int(w / 2):
                x = 343 - int(w / 2)
            if x < int(w / 2):
                x = int(w / 2)
            if y > 343 - int(h / 2):
                y = 343 - int(h / 2)
            if y < int(h / 2):
                y = int(h / 2)
            q["loc"] = [x, y]
            q["height"] = h
            q["width"] = w
    with open(os.path.join(question_dir, name + '_question' + '.json'), 'w', encoding='utf-8') as f:
        json.dump(questions, f, indent=1, ensure_ascii=False)

if __name__ == '__main__':

    # for root, _, files in os.walk('question_generation/CLEVR_1.0_templates'):
    #     for f in files:
    #         if f.endswith('.json'):
    #             rewrite(os.path.join(root, f))
    # image = mark_object('CLEVR_new_000003', 1)
    # image.show()


    for root, _, files in os.walk('output/shade/'):
        for f in files:
            print(f)
            f = f.split(".")[0]
            enclose_object(f)
            reinforce_answer(f)

    # from PIL import Image
    # for root, _, files in os.walk('output/images/'):
    #     for f in files:
    #         i = os.path.join(root, f)
    #         im = Image.open(i)
    #         im = im.convert("RGB")
    #         name = f.split(".")[0]
    #         im.save(os.path.join("output/images2", name + ".jpg"))

