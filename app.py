import streamlit as st
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
from eda_core import EDAProcessor

st.set_page_config(
    page_title="EDA Master",
    page_icon="📊",
    layout="wide"
)

st.title("🛠️ Программный модуль для автоматизации EDA")
st.markdown("---")

with st.sidebar:
    st.header("1. Загрузка данных")
    uploaded_file = st.file_uploader("Выберите CSV или Excel файл", type=["csv", "xlsx"])
    
    st.info("Загрузите файл, чтобы начать анализ.")

if uploaded_file is not None:
    processor = EDAProcessor(uploaded_file, uploaded_file.name)
    df = processor.df

    if df.empty:
        if hasattr(processor, 'last_error') and processor.last_error:
            st.error(f"❌ Ошибка загрузки: {processor.last_error}")
            st.warning("Совет: Проверьте, что файл не поврежден. Попробуйте пересохранить его в формате CSV (UTF-8) или Excel.")
        else:
            st.error("Файл пуст или имеет неверную структуру.")
    else:
        tab1, tab2, tab3, tab4 = st.tabs(["📋 Обзор", "📈 Статистика", "🎨 Визуализация", "🚀 Выбросы и Экспорт"])

        with tab1:
            st.subheader("Общая информация")
            # Блок инсайтов тута
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
            
            st.divider()
            # ---------------------
            col1, col2, col3 = st.columns(3)
            rows, cols = processor.get_shape()
            
            col1.metric("Строки", rows)
            col2.metric("Столбцы", cols)
            col3.metric("Дубликаты", processor.get_duplicates())

            st.write("### Первые 5 строк данных")
            st.dataframe(df.head())
            st.divider()

            st.write("### Интерактивная таблица с фильтрацией")
            
            # Фильтры для таблицы
            filtered_df = df.copy()
            
            with st.expander("🔍 Фильтры", expanded=False):
                filter_cols = st.multiselect("Выберите столбцы для фильтрации", df.columns.tolist())
                
                for col in filter_cols:
                    if col in processor.numeric_cols:
                        # Фильтр для числовых столбцов
                        col_min, col_max = float(df[col].min()), float(df[col].max())
                        range_values = st.slider(
                            f"{col}",
                            min_value=col_min,
                            max_value=col_max,
                            value=(col_min, col_max),
                            key=f"filter_{col}"
                        )
                        filtered_df = filtered_df[(filtered_df[col] >= range_values[0]) & (filtered_df[col] <= range_values[1])]
                    else:
                        # Фильтр для категориальных столбцов (галочки)
                        unique_vals = df[col].dropna().unique().tolist()
                        selected_vals = st.multiselect(
                            f"{col}",
                            unique_vals,
                            default=unique_vals,
                            key=f"filter_{col}"
                        )
                        if selected_vals:
                            filtered_df = filtered_df[filtered_df[col].isin(selected_vals)]
            
            st.write(f"**Показано строк:** {len(filtered_df)} из {len(df)}")
            st.dataframe(filtered_df, use_container_width=True, height=400)
            
            st.write("### Типы данных")
            st.dataframe(pd.DataFrame(df.dtypes, columns=['Тип данных']).astype(str).T)

            st.write("### Пропущенные значения")
            missing_df = processor.get_missing_values()
            if not missing_df.empty:
                st.dataframe(missing_df)
                st.warning("В данных есть пропуски! Обратите внимание.")
            else:
                st.success("Пропусков нет.")

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

        with tab3:
            st.subheader("Интерактивный графопостроитель")
            
            plot_type = st.selectbox("Выберите тип графика", [
                "Гистограмма (Распределение)", 
                "Boxplot (Ящик с усами)", 
                "Scatter Plot (Точечная)", 
                "Bar Chart (Столбчатая)",
                "Boxplot по категориям",
                "Среднее по категориям"
            ])
            
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
            
            elif plot_type == "Boxplot по категориям":
                if processor.numeric_cols:
                    # Включаем категориальные + числовые с небольшим числом уникальных значений
                    cat_options = processor.categorical_cols.copy()
                    for col in processor.numeric_cols:
                        if df[col].nunique() <= 20:  # Числовые столбцы с <=20 уникальными значениями
                            cat_options.append(col)
                    
                    if cat_options and processor.numeric_cols:
                        col_cat = st.selectbox("Категориальный столбец", cat_options, key="box_cat")
                        col_num = st.selectbox("Числовой столбец", processor.numeric_cols, key="box_num")
                        if col_cat and col_num and col_cat != col_num:
                            fig, ax = plt.subplots(figsize=(10, 6))
                            sns.boxplot(data=df, x=col_cat, y=col_num, ax=ax)
                            plt.xticks(rotation=45, ha='right')
                            st.pyplot(fig)
                        elif col_cat == col_num:
                            st.warning("Выберите разные столбцы")
                    else:
                        st.warning("Нужны столбцы для анализа")
                else:
                    st.warning("Нужны числовые столбцы")
            
            elif plot_type == "Среднее по категориям":
                if processor.numeric_cols:
                    # Включаем категориальные + числовые с небольшим числом уникальных значений
                    cat_options = processor.categorical_cols.copy()
                    for col in processor.numeric_cols:
                        if df[col].nunique() <= 20:  # Числовые столбцы с <=20 уникальными значениями
                            cat_options.append(col)
                    
                    if cat_options and processor.numeric_cols:
                        col_cat = st.selectbox("Категориальный столбец", cat_options, key="mean_cat")
                        col_num = st.selectbox("Числовой столбец", processor.numeric_cols, key="mean_num")
                        if col_cat and col_num and col_cat != col_num:
                            grouped = df.groupby(col_cat)[col_num].mean().sort_values(ascending=False)
                            fig, ax = plt.subplots(figsize=(10, 6))
                            grouped.plot(kind='bar', ax=ax, color='steelblue')
                            ax.set_ylabel(col_num)
                            ax.set_title(f"Среднее значение {col_num} по {col_cat}")
                            plt.xticks(rotation=45, ha='right')
                            st.pyplot(fig)
                        elif col_cat == col_num:
                            st.warning("Выберите разные столбцы")
                    else:
                        st.warning("Нужны столбцы для анализа")
                else:
                    st.warning("Нужны числовые столбцы")

        with tab4:
            st.subheader("💡 Анализ выбросов (Метод IQR)")
            
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
            
            cols_to_clean = st.multiselect(
                "Выберите столбцы, из которых удалить выбросы перед скачиванием:", 
                processor.numeric_cols
            )
            
            if cols_to_clean:
                col1, col2 = st.columns(2)
                
                with col1:
                    if st.button("Применить очистку и подготовить файл"):
                        clean_df = processor.get_clean_dataframe(cols_to_clean)
                        st.session_state['clean_df'] = clean_df
                        st.session_state['outliers_df'] = processor.get_outliers_dataframe(cols_to_clean)
                        st.rerun()
                
                # Показываем результаты, если они есть в session_state
                if 'clean_df' in st.session_state and 'outliers_df' in st.session_state:
                    clean_df = st.session_state['clean_df']
                    outliers_df = st.session_state['outliers_df']
                    
                    st.write(f"**Размер исходного файла:** {df.shape}")
                    st.write(f"**Размер очищенного файла:** {clean_df.shape}")
                    st.write(f"**Удалено строк:** {df.shape[0] - clean_df.shape[0]}")
                    st.write(f"**Найдено выбросов:** {len(outliers_df)} строк")
                    
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        csv_clean = clean_df.to_csv(index=False).encode('utf-8')
                        st.download_button(
                            label="⬇️ Скачать очищенный CSV",
                            data=csv_clean,
                            file_name='cleaned_data.csv',
                            mime='text/csv',
                        )
                    
                    with col2:
                        if not outliers_df.empty:
                            csv_outliers = outliers_df.to_csv(index=False).encode('utf-8')
                            st.download_button(
                                label="⬇️ Скачать датасет с выбросами",
                                data=csv_outliers,
                                file_name='outliers_data.csv',
                                mime='text/csv',
                            )
                        else:
                            st.info("Выбросы не найдены")
                    
                    # Показываем предпросмотр выбросов
                    if not outliers_df.empty:
                        st.markdown("---")
                        st.subheader("🔍 Предпросмотр выбросов")
                        st.dataframe(outliers_df.head(20))
                        if len(outliers_df) > 20:
                            st.caption(f"Показано 20 из {len(outliers_df)} строк с выбросами")
            else:
                st.info("Выберите столбцы для анализа выбросов")

else:
    st.markdown("""
    ### 👋 Добро пожаловать!
    Этот инструмент разработан в рамках курсовой работы.
    
    **Функционал:**
    *   Автоматический расчет статистик.
    *   Анализ пропусков и типов данных.
    *   Построение графиков для числовых и категориальных данных.
    
    ⬅️ **Загрузите файл CSV в меню слева, чтобы начать.**
    """)