from PIL import Image

# Открываем оригинальную морковку
im = Image.open('assets/carrot.png').convert('RGBA')
data = im.getdata()
new_data = []

for item in data:
    r, g, b, a = item
    # Если пиксель оранжевый (морковка), перекрашиваем в синий
    if r > 150 and g > 80 and b < 80:
        # Синий цвет, сохраняем альфу
        new_data.append((60, 120, 255, a))
    else:
        new_data.append(item)

im.putdata(new_data)
im.save('assets/blue_carrot.png')
print('Синяя морковка сохранена как assets/blue_carrot.png') 