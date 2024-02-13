import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime, timedelta
import re
import numpy as np
from functools import reduce
import operator
from streamlit_tags import st_tags
@st.cache_data(ttl=2400)
def load_and_process_data(url,sheetname):
    conn = st.connection("gsheets", type=GSheetsConnection)
    data_source = conn.read(spreadsheet=url, ttl="25m", worksheet=sheetname)
    data_df = pd.DataFrame(data_source)
    return data_df

@st.cache_data(ttl=2400)
def process_usfeed_and_hmfeed_sku_on_ads_data(df,MC_ID_COLUMNS,OLD_MC_ID_NUMBER,REPLACE_MC_ID_NUMBER,SKU_COLUMNS):
    df.loc[df[MC_ID_COLUMNS] == OLD_MC_ID_NUMBER, SKU_COLUMNS] = df[SKU_COLUMNS].str[:-3]
    df.loc[df[MC_ID_COLUMNS] == OLD_MC_ID_NUMBER, MC_ID_COLUMNS] = REPLACE_MC_ID_NUMBER
    df.loc[df[SKU_COLUMNS].str.endswith('-hm', na=False), SKU_COLUMNS,] = df[SKU_COLUMNS].str[:-3]
    df = df.drop(columns=[MC_ID_COLUMNS])
    return df

@st.cache_data(ttl=2400)
def process_hk_cost_and_value_on_ads_data(df,CURRENCY_COLUMNS,COST_COLUMNS,ADS_VALUE_COLUMNS,CURRENCY):
    df.loc[df[CURRENCY_COLUMNS] == CURRENCY, COST_COLUMNS] *= 0.13
    df.loc[df[CURRENCY_COLUMNS] == CURRENCY, ADS_VALUE_COLUMNS] *= 0.13
    df = df.drop(columns=[CURRENCY_COLUMNS])
    return df

@st.cache_data(ttl=2400)
def process_old_new_sku_2022_and_2023_on_ads_data(df,CUSTOMLABEL_COLUMNS):
    df.loc[df[CUSTOMLABEL_COLUMNS].str.contains('2023', na=False), CUSTOMLABEL_COLUMNS] = '2023新品'
    df.loc[df[CUSTOMLABEL_COLUMNS].str.contains('2022', na=False) | df[CUSTOMLABEL_COLUMNS].isna(), CUSTOMLABEL_COLUMNS] = '老品'
    df = df.rename(columns={CUSTOMLABEL_COLUMNS: 'old_or_new'})
    return df

@st.cache_data(ttl=2400)
def merged_spu_to_sku_on_ads_data(base_df,spu_df,SKU_COLUMNS,SPU_COLUMNS):
    df= pd.merge(base_df,spu_df[[SKU_COLUMNS, SPU_COLUMNS]], on=SKU_COLUMNS, how='left')
    return df

@st.cache_data(ttl=2400)
def merged_imagelink_to_sku_on_ads_data(base_df,old_or_new_df,SKU_COLUMNS,IMAGELINK_COLUMNS):
    df= pd.merge(base_df,old_or_new_df[[SKU_COLUMNS, IMAGELINK_COLUMNS]], on=SKU_COLUMNS, how='left')
    return df

@st.cache_data(ttl=2400)
def merged_saleprice_to_sku_on_ads_data(base_df,old_or_new_df,SKU_COLUMNS,IMAGELINK_COLUMNS):
    df= pd.merge(base_df,old_or_new_df[[SKU_COLUMNS, IMAGELINK_COLUMNS]], on=SKU_COLUMNS, how='left')
    return df

@st.cache_data(ttl=2400)
def create_date_filtered_df(base_df,DATE_COLUMNS,DATE_RANGE):
    df = base_df[(base_df[DATE_COLUMNS] >= pd.to_datetime(DATE_RANGE[0])) & (base_df[DATE_COLUMNS] <= pd.to_datetime(DATE_RANGE[1]))]
    return df

@st.cache_data(ttl=2400)
def output_groupby_df(df, groupby_list, agg_list_for_process, agg_method):
    df = df.groupby(groupby_list).agg(dict(map(lambda x: (x, agg_method), agg_list_for_process)))
    return df

def out_date_range_data(df,DATE_COLUMNS,DATE_RANGE_LABEL):
    min_date = df[DATE_COLUMNS].min()
    min_date = datetime.strptime(min_date, "%Y-%m-%d")
    max_date = df[DATE_COLUMNS].max()
    max_date = datetime.strptime(max_date, "%Y-%m-%d")
    default_start_date = datetime.today() - timedelta(days=14)
    default_end_date = datetime.today() - timedelta(days=7)
    selected_range = st.date_input(
        DATE_RANGE_LABEL,
        [default_start_date, default_end_date],
        min_value=min_date,
        max_value=max_date
    )
    return selected_range

@st.cache_data(ttl=2400)
def add_custom_proportion_to_df_x100(df,A_COLUMNS,B_COLUMNS,CUSTOM_COLUMNS_NAME):
    df[CUSTOM_COLUMNS_NAME] = (df[A_COLUMNS] / df[B_COLUMNS])*100
    df[CUSTOM_COLUMNS_NAME] = df[CUSTOM_COLUMNS_NAME].fillna(0)  # 将NaN替换为0
    df[CUSTOM_COLUMNS_NAME] = df[CUSTOM_COLUMNS_NAME].replace([np.inf, -np.inf], 0)  # 将无限值替换为0
    return df

def add_custom_proportion_to_df(df,A_COLUMNS,B_COLUMNS,CUSTOM_COLUMNS_NAME):
    df[CUSTOM_COLUMNS_NAME] = (df[A_COLUMNS] / df[B_COLUMNS])
    df[CUSTOM_COLUMNS_NAME] = df[CUSTOM_COLUMNS_NAME].fillna(0)  # 将NaN替换为0
    df[CUSTOM_COLUMNS_NAME] = df[CUSTOM_COLUMNS_NAME].replace([np.inf, -np.inf], 0)  # 将无限值替换为0
    return df

@st.cache_data(ttl=2400)
def add_groupby_sum_columns_to_list_df(before_list_df,list_df,GROUPBY_LIST,SUM_COLUMNS,RE_NAME):
    sum = before_list_df.groupby(GROUPBY_LIST)[SUM_COLUMNS].sum().rename(RE_NAME).round(2)
    df = pd.merge(list_df, sum,on=GROUPBY_LIST,how='left')
    return df

@st.cache_data(ttl=2400)
def create_dynamic_column_setting(raw_select_df, avoid_list, image_list,progresslist,percentage_list,int_list,Bar_min,Bar_max):
    column_config = {}
    for column in raw_select_df.columns:
        if column in avoid_list:
            continue
        if column in image_list:
            column_config[column] = st.column_config.ImageColumn(
                width="small"
            )
        elif column in percentage_list:  # 百分比格式
            if raw_select_df[column].empty:
                max_value = 1
            else:
                max_value = float(raw_select_df[column].max())
            column_config[column] = st.column_config.ProgressColumn(
                format='%.2f%%',  # 显示为百分比
                min_value=0,
                max_value=max_value,
                label=column
            )
        elif column in progresslist:
            if raw_select_df[column].empty:
                max_value = 1
            else:
                max_value = float(raw_select_df[column].max())
            column_config[column] = st.column_config.ProgressColumn(
                format='%.2f',
                min_value=0,
                max_value=max_value,
                label=column
            )
        elif column in int_list:
            if raw_select_df[column].empty:
                max_value = 1
            else:
                max_value = float(raw_select_df[column].max())
            column_config[column] = st.column_config.ProgressColumn(
                format='%d',
                min_value=0,
                max_value=max_value,
                label=column
            )
        else:  # 其它列的正常处理
            # max_value = max(raw_select_df[column])
            column_config[column] = st.column_config.BarChartColumn(
                width='small',
                y_min=Bar_min,
                y_max=Bar_max
            )
    return column_config

def create_sensor_gmv_filter_input(label):
    with st.container(border=True):
        st.subheader(label)
        col1, col2,col3 = st.columns(3)
        # 三个条件范围
        with col1:
            and_tags = st_tags(
            label='“并”条件输入(非完全匹配)',
            )
        with col2:
            or_tags = st_tags(
            label='“或”条件输入(非完全匹配)',
            )
        with col3:
            exclude_tags = st_tags(
            label='排除条件输入(非完全匹配)',
            )
    return and_tags,or_tags,exclude_tags

def create_bulk_sku_input(init_session,init_save_session,label):
    # 检查会话状态中是否有 'text' 和 'saved_text'，如果没有，初始化它们
    if init_session not in st.session_state:
        st.session_state[init_session] = ""
    if init_save_session not in st.session_state:
        st.session_state[init_save_session] = []

    def pass_param():
        # 保存当前文本区域的值到 'saved_text'
        if len(st.session_state[init_session]) > 0:
            separatedata = st.session_state[init_session].split('\n')
            for singedata in separatedata:
                st.session_state[init_save_session].append(singedata)
        else:
            st.session_state[init_save_session].append(st.session_state[init_session])
        # 清空文本区域
        st.session_state[init_session] = ""

    def clear_area():
        st.session_state[init_save_session] = []

    # 创建文本区域，其内容绑定到 'text'
    st.text_area(label, value=st.session_state[init_session], key=init_session, height=10)

    # 创建一个按钮，当按下时调用 on_upper_clicked 函数
    st.button("确定", on_click=pass_param)

    sku_tags = st_tags(
        label='',
        value=st.session_state[init_save_session]  # 使用会话状态中保存的tags
    )
    st.button("清空", on_click=clear_area)
    return sku_tags

@st.cache_data(ttl=2400)
def create_sensor_campaign_filter_input_df(df,and_tags,or_tags,exclude_tags,CAMPAIGN_COLUMNS):
    or_regex = '|'.join(map(str, or_tags))  # 用于“或”筛选
    exclude_regex = '|'.join(map(str, exclude_tags))  # 用于排除
    # 普通日期内的筛选条件
    and_condition = reduce(operator.and_, [df[CAMPAIGN_COLUMNS].str.contains(tag, regex=True, flags=re.IGNORECASE) for tag in and_tags]) if and_tags else True
    or_condition = df[CAMPAIGN_COLUMNS].str.contains(or_regex, regex=True, flags=re.IGNORECASE) if or_tags else True
    exclude_condition = ~df[CAMPAIGN_COLUMNS].str.contains(exclude_regex, regex=True, flags=re.IGNORECASE) if exclude_tags else True
    combined_condition = and_condition & or_condition & exclude_condition
    df = df[combined_condition]
    return df

def condition_evaluate(main_condition=None, main_true_function=None, main_false_function=None):
    if main_condition:
        return main_true_function()  # 注意这里是调用函数
    else:
        return main_false_function()  # 注意这里是调用函数

@st.cache_data(ttl=2400)
def format_first_two_rows(value, format_str):
    # 检查 value 是否为非空值（不是 NaN）
    if pd.notna(value):
        # 如果 value 不是 NaN，则使用 format_str 格式化 value，并返回格式化后的结果
        return format_str.format(value)
    # 如果 value 是 NaN，则直接返回原始的 NaN 值
    return value

# 汇总列百分比处理
@st.cache_data(ttl=2400)
def format_comparison(row):
    if row['日期范围'] == '对比':
        # 只有当 '日期范围' 列的值是 '对比' 时，才进行格式化
        return [f"{x*100:.2f}%" if isinstance(x, (int, float)) and col != '日期范围' else x for col, x in row.iteritems()]
    else:
        return row  # 对于不是 '对比' 的行，返回原始行

# 汇总列样式处理
@st.cache_data(ttl=2400)
def colorize_comparison(row):
    # 新建一个与行长度相同的样式列表，初始值为空字符串
    colors = [''] * len(row)
    # 检查当前行是否为 "对比" 行
    if row['日期范围'] == '对比':
        # 遍历除了 '日期范围' 列之外的所有值
        for i, v in enumerate(row):
            # 跳过 '日期范围' 列
            if row.index[i] != '日期范围':
                try:
                    # 将字符串转换为浮点数进行比较
                    val = float(v.strip('%'))
                    if val <= 0:
                        colors[i] = 'background-color: LightCoral'
                    elif val >= 0:
                        colors[i] = 'background-color: LightGreen'
                except ValueError:
                    # 如果转换失败，说明这不是一个数值，忽略它
                    pass
    # 返回颜色样式列表
    return colors

@st.cache_data(ttl=2400)
def create_compare_summary_df(origin_df,compare_df,select_column):
    # 合并 DataFrame
    origin_df = origin_df[select_column]
    compare_df = compare_df[select_column]
    combined_df = pd.concat([origin_df, compare_df], ignore_index=True)
    # 计算百分比变化
    comparison = {}
    for col in origin_df.columns:
        if col != '日期范围' and col != 'imagelink':
            val1 = origin_df[col].values[0]
            val2 = compare_df[col].values[0]
            # 计算百分比变化
            if val1 != 0:  # 防止除以零
                change = ((val2 - val1) / val1)
            else:
                change = ''  # 如果原值为0，则变化无穷大
            comparison[col] = change
    # 添加对比行
    comparison['日期范围'] = '对比'
    combined_df = combined_df.append(comparison, ignore_index=True)
    return combined_df
