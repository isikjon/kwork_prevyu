import win32com.client
import os
import tempfile
from typing import List
from pathlib import Path
from config import PSD_FILE, OUTPUT_SIZE, TEXT_LAYER_NAMES

class PSDProcessor:
    def __init__(self):
        self.app = None
        self.doc = None
        self.original_doc = None
        self.text_layers = []
        self.base_font_size = 48
        self.min_font_size = 20
        
    def load_psd(self):
        try:
            print("Пытаюсь подключиться к Photoshop...")
            
            try:
                self.app = win32com.client.GetActiveObject("Photoshop.Application")
                print("Подключился к существующему Photoshop")
            except:
                print("Запускаю новый экземпляр Photoshop...")
                self.app = win32com.client.Dispatch("Photoshop.Application")
            
            self.app.Visible = True
            
            psd_path = str(Path(PSD_FILE).resolve())
            print(f"Путь к PSD: {psd_path}")
            
            for doc in self.app.Documents:
                print(f"Открытый документ: {doc.Name}")
                if doc.Name.lower() == Path(PSD_FILE).name.lower():
                    self.doc = doc
                    print(f"Найден открытый документ: {doc.Name}")
                    break
            
            if not self.doc:
                print("Открываю PSD файл...")
                self.doc = self.app.Open(psd_path)
                print(f"Документ открыт: {self.doc.Name}")
            
            self._find_text_layers()
            
        except Exception as e:
            raise Exception(f"Не удалось подключиться к Photoshop или открыть PSD: {e}")
    
    def _find_text_layers(self):
        self.text_layers = []
        
        try:
            print(f"Ищу текстовые слои в документе: {self.doc.Name}")
            print(f"Всего слоев в документе: {len(self.doc.Layers)}")
            print("Структура слоев:")
            
            self._search_layers_recursive(self.doc.Layers, 0)
            
            print(f"\nПозиции найденных текстовых слоев:")
            layer_positions = []
            for layer in self.text_layers:
                try:
                    bounds = layer.Bounds
                    y_position = float(bounds[1])
                    print(f"Слой '{layer.Name}': Y позиция = {y_position}")
                    layer_positions.append((layer, y_position))
                except:
                    layer_positions.append((layer, 0))
            
            layer_positions.sort(key=lambda x: x[1])
            self.text_layers = [layer for layer, _ in layer_positions]
            
            print(f"\nОтсортированные слои сверху вниз:")
            for i, layer in enumerate(self.text_layers):
                print(f"{i+1}. {layer.Name}")
                    
        except Exception as e:
            print(f"Ошибка поиска слоев: {e}")
            
        print(f"\nЦелевые имена слоев: {TEXT_LAYER_NAMES}")
        print(f"Найдено текстовых слоев: {len(self.text_layers)}")
        for layer in self.text_layers:
            print(f"- {layer.Name}")
    
    def _search_layers_recursive(self, layers, depth=0):
        indent = "  " * depth
        
        for i, layer in enumerate(layers):
            layer_type = "Unknown"
            try:
                if layer.Kind == 1:
                    layer_type = "Normal"
                elif layer.Kind == 2:
                    layer_type = "Text"
                elif layer.Kind == 3:
                    layer_type = "Group"
            except:
                pass
            
            print(f"{indent}{i+1}. '{layer.Name}' (Тип: {layer_type})")
            
            if layer.Name in TEXT_LAYER_NAMES and layer.Kind == 2:
                self.text_layers.append(layer)
                print(f"{indent}    ✓ Добавлен как текстовый слой")
            
            if layer_type == "Group" or hasattr(layer, 'Layers'):
                try:
                    print(f"{indent}    └ Группа содержит {len(layer.Layers)} слоев:")
                    self._search_layers_recursive(layer.Layers, depth + 2)
                except Exception as e:
                    print(f"{indent}    └ Ошибка доступа к слоям группы: {e}")
    
    def create_preview(self, text_lines: List[str]) -> bytes:
        if not self.doc:
            raise Exception("PSD не загружен")
        
        if len(self.text_layers) == 0:
            raise Exception("Не найдено текстовых слоев для редактирования!")
        
        try:
            self.app.ActiveDocument = self.doc
            print("Документ активирован")
        except Exception as e:
            print(f"Ошибка активации документа: {e}")
            try:
                self.load_psd()
                self.app.ActiveDocument = self.doc
            except:
                raise Exception("Не удалось переподключиться к Photoshop")
        
        try:
            self._replace_text_in_layers(text_lines)
            
            temp_path = self._export_to_jpg()
            
            with open(temp_path, 'rb') as f:
                image_bytes = f.read()
            
            os.unlink(temp_path)
            
            return image_bytes
            
        except Exception as e:
            raise Exception(f"Ошибка создания превью: {e}")
        finally:
            try:
                for layer in self.text_layers:
                    try:
                        layer.TextItem.Contents = "TEXT"
                        layer.Visible = True
                    except:
                        pass
                
                self._cleanup_photoshop()
                print("Документ восстановлен и память очищена")
            except:
                pass
    
    def _replace_text_in_layers(self, text_lines: List[str]):
        print(f"Заменяю текст в {len(self.text_layers)} слоях")
        print(f"Строки текста: {text_lines}")
        print(f"Количество непустых строк: {len([line for line in text_lines if line.strip()])}")
        
        for i, layer in enumerate(self.text_layers):
            layer_visible = i < len(text_lines) and text_lines[i].strip()
            
            try:
                if layer_visible:
                    text_line = text_lines[i]
                    print(f"Слой {layer.Name}: показываю и заменяю на '{text_line}'")
                    
                    layer.Visible = True
                    
                    original_size = float(layer.TextItem.Size)
                    print(f"Оригинальный размер шрифта: {original_size}")
                    
                    self.app.ActiveDocument.ActiveLayer = layer
                    layer.TextItem.Contents = text_line
                    
                    print(f"✓ Слой обновлен")
                    
                else:
                    print(f"Слой {layer.Name}: скрываю (нет текста)")
                    layer.Visible = False
                    
            except Exception as e:
                print(f"Ошибка с слоем {layer.Name}: {e}")
    
    def _calculate_font_size(self, text: str, layer) -> float:
        try:
            original_size = float(layer.TextItem.Size)
            print(f"Возвращаю оригинальный размер: {original_size}")
            return original_size
        except Exception as e:
            print(f"Ошибка получения размера шрифта: {e}")
            return self.base_font_size
    
    def _export_to_jpg(self) -> str:
        temp_dir = tempfile.gettempdir()
        temp_path = os.path.join(temp_dir, f"preview_{os.getpid()}.jpg")
        
        try:
            self.app.ActiveDocument = self.doc
            
            save_options = win32com.client.Dispatch("Photoshop.JPEGSaveOptions")
            save_options.Quality = 8
            save_options.EmbedColorProfile = False
            save_options.FormatOptions = 1
            save_options.Matte = 1
            
            self.doc.SaveAs(temp_path, save_options, True)
            print(f"JPEG сохранен: {temp_path}")
            
            self._cleanup_photoshop()
            
        except Exception as e:
            print(f"Ошибка JPEG: {e}")
            try:
                png_options = win32com.client.Dispatch("Photoshop.ExportOptionsSaveForWeb")
                png_options.Format = 13
                png_options.Quality = 80
                
                temp_path = os.path.join(temp_dir, f"preview_{os.getpid()}.png")
                self.doc.Export(temp_path, 2, png_options)
                print(f"PNG экспорт: {temp_path}")
                
                self._cleanup_photoshop()
                
            except Exception as e2:
                print(f"Ошибка PNG: {e2}")
                try:
                    png_save = win32com.client.Dispatch("Photoshop.PNGSaveOptions")
                    png_save.Compression = 6
                    png_save.Interlaced = False
                    
                    temp_path = os.path.join(temp_dir, f"preview_{os.getpid()}.png") 
                    self.doc.SaveAs(temp_path, png_save, True)
                    print(f"PNG SaveAs: {temp_path}")
                    
                    self._cleanup_photoshop()
                    
                except Exception as e3:
                    raise Exception(f"Все методы экспорта не работают: {e3}")
        
        return temp_path
    
    def _cleanup_photoshop(self):
        try:
            self.app.PurgeItem(1)
            self.app.PurgeItem(2) 
            self.app.PurgeItem(3)
            self.app.PurgeItem(4)
            print("Очистка кэша Photoshop")
        except:
            pass
    
    def close(self):
        try:
            if self.doc:
                pass
            self.app = None
            self.doc = None
        except:
            pass

processor = PSDProcessor()