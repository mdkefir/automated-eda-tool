import streamlit as st
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
from eda_core import EDAProcessor  # Импортируем наш модуль

# --- Настройки страницы ---
st.set_page_config(
    page_title="EDA Master",
    page_icon="📊",
    layout="wide"
)

# --- Заголовок ---
st.title("🛠️ Программный модуль для автоматизации EDA")
st.markdown("---")

# --- Боковая панель (Загрузка) ---
with st.sidebar:
    st.header("1. Загрузка данных")
    uploaded_file = st.file_uploader("Выберите CSV или Excel файл", type=["csv", "xlsx"])
    
    st.info("Загрузите файл, чтобы начать анализ.")

# --- Основная логика ---
if uploaded_file is not None:
    # Инициализируем наш класс-обработчик
    processor = EDAProcessor(uploaded_file, uploaded_file.name)
    df = processor.df

    if df.empty:
        # Проверяем, записал ли наш процессор конкретную ошибку
        if hasattr(processor, 'last_error') and processor.last_error:
            st.error(f"❌ Ошибка загрузки: {processor.last_error}")
            st.warning("Совет: Проверьте, что файл не поврежден. Попробуйте пересохранить его в формате CSV (UTF-8) или Excel.")
        else:
            st.error("Файл пуст или имеет неверную структуру.")
    else:
        # ... (дальше идет код создания вкладок tab1, tab2, tab3 как было раньше)
        # Создаем вкладки для удобства (как в ТЗ: Обзор, Статистика, Визуализация)
        tab1, tab2, tab3, tab4 = st.tabs(["📋 Обзор", "📈 Статистика", "🎨 Визуализация", "🚀 Выбросы и Экспорт"])

        # === ВКЛАДКА 1: ОБЗОР ===
        with tab1:
            st.subheader("Общая информация")
            # --- Блок Инсайтов ---
            st.subheader("💡 Автоматические выводы")
            insights = processor.generate_insights()
            
            for item in insights:
                if item["type"] == "danger":
                    st.error(f"❌ {item['msg']}")
                elif item["type"] == "warning":
                    st.warning(f"⚠️ {item['msg']}")
                elif item["type"] == "info":
                    st.info(f"ℹ️ {item['msg']}")
                elif item["type"] == "success":
                    st.success(f"✅ {item['msg']}")
            
            st.divider() # Горизонтальная линия для красоты
            # ---------------------
            col1, col2, col3 = st.columns(3)
            rows, cols = processor.get_shape()
            
            col1.metric("Строки", rows)
            col2.metric("Столбцы", cols)
            col3.metric("Дубликаты", processor.get_duplicates())

            st.write("### Первые 5 строк данных")
            st.dataframe(df.head())
            
            st.write("### Типы данных")
            st.dataframe(pd.DataFrame(df.dtypes, columns=['Тип данных']).astype(str).T)

            st.write("### Пропущенные значения")
            missing_df = processor.get_missing_values()
            if not missing_df.empty:
                st.dataframe(missing_df)
                st.warning("В данных есть пропуски! Обратите внимание.")
            else:
                st.success("Пропусков нет.")

        # === ВКЛАДКА 2: СТАТИСТИКА ===
        with tab2:
            st.subheader("Числовые признаки")
            stats = processor.get_numeric_stats()
            if stats is not None:
                st.dataframe(stats.style.background_gradient(cmap="Blues"))
            else:
                st.info("Числовых колонок не найдено.")

            st.subheader("Корреляционная матрица")
            corr = processor.get_correlation()
            if corr is not None:
                fig, ax = plt.subplots(figsize=(10, 6))
                sns.heatmap(corr, annot=True, fmt=".2f", cmap="coolwarm", ax=ax)
                st.pyplot(fig)
            else:
                st.info("Недостаточно данных для корреляции.")

        # === ВКЛАДКА 3: ВИЗУАЛИЗАЦИЯ ===
        with tab3:
            st.subheader("Интерактивный графопостроитель")
            
            # Выбор типа графика
            plot_type = st.selectbox("Выберите тип графика", ["Гистограмма (Распределение)", "Boxplot (Ящик с усами)", "Scatter Plot (Точечная)", "Bar Chart (Столбчатая)"])
            
            if plot_type == "Гистограмма (Распределение)":
                col_to_plot = st.selectbox("Выберите столбец", processor.numeric_cols)
                if col_to_plot:
                    fig, ax = plt.subplots()
                    sns.histplot(df[col_to_plot], kde=True, ax=ax, color="skyblue")
                    st.pyplot(fig)

            elif plot_type == "Boxplot (Ящик с усами)":
                col_to_plot = st.selectbox("Выберите числовой столбец", processor.numeric_cols)
                if col_to_plot:
                    fig, ax = plt.subplots()
                    sns.boxplot(x=df[col_to_plot], ax=ax, color="lightgreen")
                    st.pyplot(fig)

            elif plot_type == "Scatter Plot (Точечная)":
                col_x = st.selectbox("Ось X", processor.numeric_cols)
                col_y = st.selectbox("Ось Y", processor.numeric_cols, index=1 if len(processor.numeric_cols) > 1 else 0)
                if col_x and col_y:
                    fig, ax = plt.subplots()
                    sns.scatterplot(x=df[col_x], y=df[col_y], ax=ax, color="purple")
                    st.pyplot(fig)
            
            elif plot_type == "Bar Chart (Столбчатая)":
                col_cat = st.selectbox("Выберите категориальный столбец", processor.categorical_cols)
                if col_cat:
                    fig, ax = plt.subplots()
                    top_n = st.slider("Сколько категорий показать?", 5, 20, 10)
                    val_counts = df[col_cat].value_counts().head(top_n)
                    sns.barplot(x=val_counts.values, y=val_counts.index, ax=ax, palette="viridis")
                    st.pyplot(fig)

            # === ВКЛАДКА 4: ВЫБРОСЫ И ЭКСПОРТ ===
        with tab4:
            st.subheader("💡 Анализ выбросов (Метод IQR)")
            
            # Выбор колонки для проверки
            outlier_col = st.selectbox("Проверить столбец на выбросы:", processor.numeric_cols)
            
            if outlier_col:
                res = processor.detect_outliers(outlier_col)
                
                col1, col2, col3 = st.columns(3)
                col1.metric("Найдено выбросов", res['count'])
                col2.metric("Нижняя граница", f"{res['lower_bound']:.2f}")
                col3.metric("Верхняя граница", f"{res['upper_bound']:.2f}")
                
                if res['count'] > 0:
                    st.warning(f"В столбце '{outlier_col}' найдено {res['count']} аномальных значений.")
                    
                    # Визуализация выбросов
                    fig, ax = plt.subplots(figsize=(8, 4))
                    sns.boxplot(x=df[outlier_col], ax=ax, color='orange')
                    ax.set_title(f"Boxplot для {outlier_col} (с выбросами)")
                    st.pyplot(fig)
                else:
                    st.success("Выбросов не обнаружено (распределение в пределах нормы).")

            st.markdown("---")
            st.subheader("📥 Скачивание обработанных данных")
            
            # Мультивыбор колонок для очистки
            cols_to_clean = st.multiselect(
                "Выберите столбцы, из которых удалить выбросы перед скачиванием:", 
                processor.numeric_cols
            )
            
            if st.button("Применить очистку и подготовить файл"):
                clean_df = processor.get_clean_dataframe(cols_to_clean)
                st.write(f"Размер исходного файла: {df.shape}")
                st.write(f"Размер очищенного файла: {clean_df.shape}")
                st.write(f"Удалено строк: {df.shape[0] - clean_df.shape[0]}")
                
                # Конвертация в CSV для скачивания
                csv = clean_df.to_csv(index=False).encode('utf-8')
                
                st.download_button(
                    label="⬇️ Скачать очищенный CSV",
                    data=csv,
                    file_name='cleaned_data.csv',
                    mime='text/csv',
                )

else:
    # Заставка при пустом экране
    st.markdown("""
    ### 👋 Добро пожаловать!
    Этот инструмент разработан в рамках курсовой работы.
    
    **Функционал:**
    *   Автоматический расчет статистик.
    *   Анализ пропусков и типов данных.
    *   Построение графиков для числовых и категориальных данных.
    
    ⬅️ **Загрузите файл CSV в меню слева, чтобы начать.**
    """)