import pandas as pd
import numpy as np
from io import StringIO

class EDAProcessor:
    """
    Класс для обработки данных и расчета статистик.
    Выполняет аналитический этап работы.
    """
    
    def __init__(self, file_buffer, filename):
        self.filename = filename
        self.last_error = None # Сюда будем писать ошибку, если она случится
        self.df = self._load_data(file_buffer)
        
        # Если загрузка прошла успешно, инициализируем списки колонок
        if not self.df.empty:
            self.numeric_cols = self.df.select_dtypes(include=[np.number]).columns.tolist()
            self.categorical_cols = self.df.select_dtypes(exclude=[np.number]).columns.tolist()
        else:
            self.numeric_cols = []
            self.categorical_cols = []

    def _load_data(self, file_buffer):
        """
        Пытается загрузить данные, перебирая кодировки.
        Умеет пропускать "битые" строки.
        """
        # 1. Excel
        if self.filename.endswith(('.xls', '.xlsx')):
            try:
                return pd.read_excel(file_buffer)
            except Exception as e:
                self.last_error = f"Ошибка Excel: {e}"
                return pd.DataFrame()

        # 2. CSV
        if self.filename.endswith('.csv'):
            from io import BytesIO
            
            # Варианты кодировок и разделителей
            options = [
                ('utf-8', ','),
                ('utf-8', ';'),
                ('cp1251', ';'),
                ('cp1251', ','),
                ('latin1', ';'),
                ('latin1', ',')
            ]
            
            # Читаем файл в байты один раз
            file_buffer.seek(0)
            bytes_data = file_buffer.read()
            
            for encoding, sep in options:
                try:
                    # Попытка 1: Строгое чтение (все строки должны быть идеальны)
                    temp_buffer = BytesIO(bytes_data)
                    df = pd.read_csv(temp_buffer, encoding=encoding, sep=sep)
                    
                    if df.shape[1] > 1:
                        return df

                except Exception:
                    # Попытка 2: Если ошибка, пробуем читать, пропуская битые строки
                    try:
                        temp_buffer = BytesIO(bytes_data)
                        # on_bad_lines='skip' выкинет строки с ошибками (только для pandas >= 1.3)
                        df = pd.read_csv(
                            temp_buffer, 
                            encoding=encoding, 
                            sep=sep, 
                            on_bad_lines='skip'
                        )
                        if df.shape[1] > 1:
                            # Если получилось, сохраняем предупреждение, но возвращаем данные
                            self.last_error = "Файл прочитан, но некоторые строки с ошибками были пропущены."
                            return df
                    except:
                        continue
            
            # Если ничего не помогло, пробуем движок Python (он медленнее, но умнее)
            try:
                temp_buffer = BytesIO(bytes_data)
                return pd.read_csv(temp_buffer, sep=None, engine='python', on_bad_lines='skip')
            except Exception as e:
                self.last_error = f"Не удалось прочитать CSV. Ошибка: {e}"
                return pd.DataFrame()

        self.last_error = "Неподдерживаемый формат файла"
        return pd.DataFrame()

    def get_shape(self):
        """Возвращает размеры датасета."""
        return self.df.shape

    def get_missing_values(self):
        """Возвращает статистику по пропущенным значениям."""
        missing = self.df.isnull().sum()
        missing = missing[missing > 0]
        missing_percent = (missing / len(self.df)) * 100
        return pd.DataFrame({'Количество пропусков': missing, 'Процент %': missing_percent})

    def get_duplicates(self):
        """Возвращает количество дубликатов."""
        return self.df.duplicated().sum()

    def get_numeric_stats(self):
        """Возвращает описательную статистику для числовых данных."""
        if self.numeric_cols:
            return self.df[self.numeric_cols].describe().T
        return None

    def get_categorical_stats(self, column):
        """Возвращает частоты для выбранной категории."""
        if column in self.categorical_cols:
            return self.df[column].value_counts().reset_index()
        return None
    
    def get_correlation(self):
        """Возвращает матрицу корреляций."""
        if len(self.numeric_cols) > 1:
            return self.df[self.numeric_cols].corr()
        return None