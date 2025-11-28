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

    def detect_outliers(self, column):
        """
        Определяет выбросы методом IQR (Межквартильный размах).
        Возвращает количество выбросов, границы и сами выбросы.
        """
        if column not in self.numeric_cols:
            return None
        
        Q1 = self.df[column].quantile(0.25)
        Q3 = self.df[column].quantile(0.75)
        IQR = Q3 - Q1
        
        lower_bound = Q1 - 1.5 * IQR
        upper_bound = Q3 + 1.5 * IQR
        
        outliers = self.df[(self.df[column] < lower_bound) | (self.df[column] > upper_bound)]
        
        return {
            'count': len(outliers),
            'lower_bound': lower_bound,
            'upper_bound': upper_bound,
            'indices': outliers.index.tolist()
        }

    def get_clean_dataframe(self, remove_outliers_cols=None):
        """
        Возвращает датафрейм без выбросов в указанных колонках.
        """
        if not remove_outliers_cols:
            return self.df
        
        df_clean = self.df.copy()
        
        for col in remove_outliers_cols:
            res = self.detect_outliers(col)
            if res:
                # Фильтруем по индексам
                df_clean = df_clean.drop(res['indices'], errors='ignore')
                
        return df_clean

    def generate_insights(self):
        """
        Генерирует список текстовых выводов и предупреждений о данных.
        """
        insights = []
        
        # 1. Проверка на пропуски
        missing = self.df.isnull().sum()
        for col, count in missing.items():
            if count > 0:
                pct = (count / len(self.df)) * 100
                if pct > 50:
                    insights.append({"type": "danger", "msg": f"Столбец '{col}' содержит {pct:.1f}% пропусков. Рекомендуется удаление."})
                elif pct > 5:
                    insights.append({"type": "warning", "msg": f"Столбец '{col}' имеет {pct:.1f}% пропусков. Требуется импутация (заполнение)."})

        # 2. Проверка на константные столбцы (одно значение везде)
        for col in self.df.columns:
            if self.df[col].nunique() <= 1:
                insights.append({"type": "danger", "msg": f"Столбец '{col}' содержит только одно значение. Он не несет информации."})

        # 3. Проверка высокой корреляции (Мультиколлинеарность)
        if len(self.numeric_cols) > 1:
            corr_matrix = self.df[self.numeric_cols].corr().abs()
            # Выбираем только верхний треугольник матрицы, чтобы не дублировать пары
            upper = corr_matrix.where(np.triu(np.ones(corr_matrix.shape), k=1).astype(bool))
            
            # Ищем пары с корреляцией > 0.85
            to_drop = [column for column in upper.columns if any(upper[column] > 0.85)]
            
            for col in to_drop:
                # Находим с чем коррелирует
                high_corr_col = upper[col][upper[col] > 0.85].index.tolist()
                for c in high_corr_col:
                    insights.append({"type": "info", "msg": f"Сильная корреляция между '{col}' и '{c}'. Возможно, стоит оставить только один из них."})

        # 4. Проверка категориального дисбаланса
        for col in self.categorical_cols:
            if self.df[col].nunique() < 20: # Проверяем только если категорий не слишком много
                top_freq = self.df[col].value_counts(normalize=True).iloc[0]
                if top_freq > 0.9:
                     insights.append({"type": "warning", "msg": f"В столбце '{col}' одно значение встречается в {top_freq:.1%}% случаев (сильный дисбаланс)."})

        # 5. Сводка
        if not insights:
            insights.append({"type": "success", "msg": "Явных проблем в структуре данных не обнаружено."})
            
        return insights