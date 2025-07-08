import re
import ast

class LuaMapLoader:
    def __init__(self):
        self.tile_size = 32
        
    def load_map_from_lua(self, file_path):
        """Загружает карту из Lua файла формата Tiled"""
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                content = file.read()
            # Используем только _simple_lua_parser для надёжности
            map_data = self._simple_lua_parser(content)
            width = map_data.get('width', 30)
            height = map_data.get('height', 20)
            tile_width = map_data.get('tilewidth', 32)
            tile_height = map_data.get('tileheight', 32)
            layers = map_data.get('layers', [])
            # Конвертируем слои в формат, понятный нашей игре
            game_layers = []
            for layer in layers:
                if layer.get('type') == 'tilelayer':
                    # Отладочный вывод
                    print(f"[LUA MAP] Layer '{layer.get('name','')}' size: {layer.get('width', width)}x{layer.get('height', height)}, data len: {len(layer.get('data', []))}")
                    layer_data = {
                        'name': layer.get('name', ''),
                        'width': layer.get('width', width),
                        'height': layer.get('height', height),
                        'data': self._convert_tile_data(layer.get('data', []), layer.get('width', width), layer.get('height', height))
                    }
                    game_layers.append(layer_data)
            print(f"[LUA MAP] Map size: {width}x{height}, layers: {len(game_layers)}")
            if game_layers and 'data' in game_layers[0]:
                print(f"[LUA MAP] tile_ids shape: {len(game_layers[0]['data'])}x{len(game_layers[0]['data'][0]) if game_layers[0]['data'] else 0}")
            return {
                'width': width,
                'height': height,
                'tile_width': tile_width,
                'tile_height': tile_height,
                'layers': game_layers
            }
        except Exception as e:
            print(f"Ошибка загрузки карты: {e}")
            return None
    
    def _parse_lua_table(self, content):
        """Парсит Lua таблицу в Python словарь"""
        # Убираем комментарии и лишние пробелы
        content = re.sub(r'--.*$', '', content, flags=re.MULTILINE)
        
        # Заменяем Lua синтаксис на Python
        content = content.replace('{', '[')
        content = content.replace('}', ']')
        content = content.replace('=', ':')
        content = content.replace('nil', 'None')
        
        # Обрабатываем строки
        content = re.sub(r'"([^"]*)"', r'"\1"', content)
        
        # Убираем лишние запятые
        content = re.sub(r',\s*]', ']', content)
        content = re.sub(r',\s*}', '}', content)
        
        try:
            # Пытаемся выполнить как Python код
            return ast.literal_eval(content)
        except:
            # Если не получилось, используем более простой парсер
            return self._simple_lua_parser(content)
    
    def _find_layers_block(self, content):
        """Находит блок layers = { ... } или layers : { ... } с учётом вложенности фигурных скобок"""
        import re
        match = re.search(r'layers\s*[:=]\s*\{', content)
        if not match:
            return ''
        start = content.find('{', match.start())
        if start == -1:
            return ''
        count = 0
        for i in range(start, len(content)):
            if content[i] == '{':
                count += 1
            elif content[i] == '}':
                count -= 1
                if count == 0:
                    return content[start:i+1]
        return ''

    def _find_tilelayer_blocks(self, content):
        """Находит все массивы первого уровня внутри блока layers, содержащие type = "tilelayer" (фигурные скобки)"""
        blocks = []
        stack = []
        block_start = None
        i = 0
        while i < len(content):
            if content[i] == '{':
                if not stack:
                    block_start = i
                stack.append(i)
            elif content[i] == '}':
                if stack:
                    stack.pop()
                    if not stack and block_start is not None:
                        block = content[block_start:i+1]
                        if 'type = "tilelayer"' in block or 'type = \'tilelayer\'' in block:
                            blocks.append(block)
                        block_start = None
            i += 1
        return blocks

    def _simple_lua_parser(self, content):
        """Простой парсер для Lua таблиц (Tiled)"""
        result = {}
        # Извлекаем основные параметры
        width_match = re.search(r'width\s*=\s*(\d+)', content)
        height_match = re.search(r'height\s*=\s*(\d+)', content)
        tilewidth_match = re.search(r'tilewidth\s*=\s*(\d+)', content)
        tileheight_match = re.search(r'tileheight\s*=\s*(\d+)', content)
        if width_match:
            result['width'] = int(width_match.group(1))
        if height_match:
            result['height'] = int(height_match.group(1))
        if tilewidth_match:
            result['tilewidth'] = int(tilewidth_match.group(1))
        if tileheight_match:
            result['tileheight'] = int(tileheight_match.group(1))
        # Извлекаем блок layers
        layers_block = self._find_layers_block(content)
        print(f"DEBUG: Длина блока layers: {len(layers_block)}")
        # Извлекаем слои только из блока layers
        layers = []
        tilelayer_blocks = self._find_tilelayer_blocks(layers_block)
        print(f"DEBUG: Найдено блоков tilelayer: {len(tilelayer_blocks)}")
        for i, layer_block in enumerate(tilelayer_blocks):
            print(f"DEBUG: block {i} start: {layer_block[:80]} ...")
        for layer_block in tilelayer_blocks:
            layer = {}
            name_match = re.search(r'name\s*=\s*"([^"]*)"', layer_block)
            width_match = re.search(r'width\s*=\s*(\d+)', layer_block)
            height_match = re.search(r'height\s*=\s*(\d+)', layer_block)
            if name_match:
                layer['name'] = name_match.group(1)
            if width_match:
                layer['width'] = int(width_match.group(1))
            if height_match:
                layer['height'] = int(height_match.group(1))
            # Извлекаем данные тайлов
            data_pattern = r'data\s*=\s*\{([^}]*)\}'
            data_match = re.search(data_pattern, layer_block, re.DOTALL)
            if data_match:
                data_str = data_match.group(1)
                data_str = re.sub(r'\s+', ' ', data_str)
                data = []
                for x in data_str.split(','):
                    x = x.strip()
                    if x.isdigit():
                        data.append(int(x))
                layer['data'] = data
                layer['type'] = 'tilelayer'
                print(f"DEBUG: Слой {layer.get('name', 'unnamed')} - {len(data)} тайлов")
            else:
                print(f"DEBUG: Данные не найдены для слоя {layer.get('name', 'unnamed')}")
            if layer:
                layers.append(layer)
        result['layers'] = layers
        return result
    
    def _convert_tile_data(self, data, width, height):
        """Конвертирует данные тайлов в формат для игры"""
        if not data:
            return []
        result = []
        for y in range(height):
            row = []
            for x in range(width):
                index = y * width + x
                if index < len(data):
                    tile_id = data[index] - 1 if data[index] > 0 else -1
                    row.append(tile_id)
                else:
                    row.append(-1)
            row = row[:width]
            result.append(row)
        return result

# Функция для тестирования
def test_map_loader():
    loader = LuaMapLoader()
    map_data = loader.load_map_from_lua('assets/map.lua')
    
    if map_data:
        print(f"Карта загружена успешно!")
        print(f"Размер: {map_data['width']}x{map_data['height']}")
        print(f"Тайл размер: {map_data['tile_width']}x{map_data['tile_height']}")
        print(f"Количество слоев: {len(map_data['layers'])}")
        
        for i, layer in enumerate(map_data['layers']):
            print(f"Слой {i}: {layer['name']} ({layer['width']}x{layer['height']})")
    else:
        print("Ошибка загрузки карты")

if __name__ == "__main__":
    test_map_loader() 