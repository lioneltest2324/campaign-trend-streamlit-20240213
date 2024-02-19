import streamlit as st
import pandas as pd
import altair as alt
from universal_component_for_campaign import load_and_process_data,out_date_range_data,create_date_filtered_df,\
    output_groupby_df,add_custom_proportion_to_df,process_hk_cost_and_value_on_ads_data

st.set_page_config(layout="wide")
@st.cache_data(ttl=2400)
def load_data():
    sensor_url = 'https://docs.google.com/spreadsheets/d/1btySv1zKyH5zQvMXk1DqjByMU8_fQ-79OHqt67X1njI/edit#gid=0'
    ads_url = 'https://docs.google.com/spreadsheets/d/1K__Mzx-lwk7USJXMj_MdvGmO2ud_3MIJpQAZ7IAkfzU/edit#gid=0'
    ads_df = load_and_process_data(ads_url,0)
    change_ads_df  = load_and_process_data(ads_url,345453249)
    sensor_daily_1 = load_and_process_data(sensor_url,0)
    sensor_daily_2 = load_and_process_data(sensor_url,2063213808)
    sensor_df = pd.concat([sensor_daily_1, sensor_daily_2], ignore_index=True)
    change_ads_df = change_ads_df.rename(columns={'campaign name': 'campaign'})
    ads_df = ads_df.rename(columns={'campaignname': 'campaign'})
    ads_df['campaign'] = ads_df['campaign'].astype(str)
    ads_df = ads_df.drop(columns=['campaignid'])
    sensor_df = sensor_df.rename(columns={'行为时间': 'date','Campaign': 'campaign','CampaignID': 'campaignid'})
    sensor_df['campaign'] = sensor_df['campaign'].astype(str)
    return ads_df,sensor_df,change_ads_df

@st.cache_data(ttl=2400)
def output_combine_df(selected_range, campaign_options, ads_df, sensor_df, change_ads_df):
    # 制作日期筛选后的表格
    ads_df['date'] = pd.to_datetime(ads_df['date'])
    sensor_df['date'] = pd.to_datetime(sensor_df['date'])
    change_ads_df['date'] = pd.to_datetime(change_ads_df['date'])
    ads_filtered_date_range_df = create_date_filtered_df(ads_df, 'date', selected_range)
    change_ads_filtered_date_range_df = create_date_filtered_df(change_ads_df, 'date', selected_range)
    sensor_filtered_date_range_df = create_date_filtered_df(sensor_df, 'date', selected_range)
    # 进行广告系列筛选
    ads_camapign_filtered_date_range_df = ads_filtered_date_range_df[
        ads_filtered_date_range_df['campaign'].isin(campaign_options)]
    change_ads_camapign_filtered_date_range_df = change_ads_filtered_date_range_df[
        change_ads_filtered_date_range_df['campaign'].isin(campaign_options)]
    sensor_camapign_filtered_date_range_df = sensor_filtered_date_range_df[
        sensor_filtered_date_range_df['campaign'].isin(campaign_options)]
    # 广告筛选后更改日期格式
    ads_camapign_filtered_date_range_df['date'] = ads_camapign_filtered_date_range_df['date'].dt.strftime('%Y-%m-%d')
    change_ads_camapign_filtered_date_range_df['date'] = change_ads_camapign_filtered_date_range_df['date'].dt.strftime(
        '%Y-%m-%d')
    sensor_camapign_filtered_date_range_df['date'] = sensor_camapign_filtered_date_range_df['date'].dt.strftime(
        '%Y-%m-%d')
    # 处理筛选完成后的操作记录的数据
    change_ads_camapign_filtered_date_range_df = change_ads_camapign_filtered_date_range_df[
        ['date', 'campaign', 'change', 'detail']]
    change_ads_camapign_filtered_date_range_df = change_ads_camapign_filtered_date_range_df.drop_duplicates()
    change_ads_camapign_filtered_date_range_df = change_ads_camapign_filtered_date_range_df
    # 把细节操作变成list用于后续合并
    change_ads_camapign_filtered_date_range_df = output_groupby_df(change_ads_camapign_filtered_date_range_df,
                                                                   ['date', 'campaign'], ['change', 'detail'],
                                                                   list).reset_index()
    # 合并ads数据和操作记录
    ads_camapign_filtered_date_range_merge_change_df = pd.merge(ads_camapign_filtered_date_range_df,
                                                                change_ads_camapign_filtered_date_range_df[
                                                                    ['date', 'campaign', 'change', 'detail']],
                                                                on=['date', 'campaign'], how='left')
    merge_df = pd.merge(ads_camapign_filtered_date_range_merge_change_df,
                        sensor_camapign_filtered_date_range_df[
                            ['date', 'campaign', 'GMV', 'uv', 'AddtoCart', 'saleuser', 'sale', 'firstuser',
                             'firstuserfristbuy']], on=['date', 'campaign'], how='left')
    merge_df = add_custom_proportion_to_df(merge_df, 'GMV', 'cost', '神策ROI')
    merge_df = add_custom_proportion_to_df(merge_df, 'ads value', 'cost', 'ads ROI')
    merge_df = add_custom_proportion_to_df(merge_df, 'cost', 'click', 'CPC')
    merge_df = add_custom_proportion_to_df(merge_df, 'click', 'impression', 'CTR')
    merge_df = add_custom_proportion_to_df(merge_df, 'sale', 'uv', '神策转化率')
    merge_df = add_custom_proportion_to_df(merge_df, 'AddtoCart', 'uv', '神策加购率')
    merge_df[['神策ROI', 'ads ROI', 'CPC', 'GMV', 'ads value', 'cost', 'conversions', 'allconversions']] = \
        (merge_df[['神策ROI', 'ads ROI', 'CPC', 'GMV', 'ads value', 'cost', 'conversions', 'allconversions']]).round(2)
    merge_df[['CTR', '神策转化率', '神策加购率']] = (merge_df[['CTR', '神策转化率', '神策加购率']]).round(4)
    merge_df = merge_df.rename(
        columns={'conversions': 'ads转化', 'allconversions': 'ads所有转化', 'firstuser': '首访用户',
                 'firstuserfristbuy': '首访首购用户', 'sale': '销量', 'saleuser': '购买用户数',
                 'viewconversions': '浏览转化次数', 'AddtoCart': '加购数'})
    return merge_df

@st.cache_data(ttl=2400)
def output_summary_df(selected_range, campaign_options, ads_df, sensor_df):
    ads_df['date'] = pd.to_datetime(ads_df['date'])
    sensor_df['date'] = pd.to_datetime(sensor_df['date'])
    change_ads_df['date'] = pd.to_datetime(change_ads_df['date'])
    ads_filtered_date_range_df = create_date_filtered_df(ads_df, 'date', selected_range)
    sensor_filtered_date_range_df = create_date_filtered_df(sensor_df, 'date', selected_range)
    # 进行广告系列筛选
    ads_camapign_filtered_date_range_df = ads_filtered_date_range_df[
        ads_filtered_date_range_df['campaign'].isin(campaign_options)]
    sensor_camapign_filtered_date_range_df = sensor_filtered_date_range_df[
        sensor_filtered_date_range_df['campaign'].isin(campaign_options)]
    # 广告筛选后更改日期格式
    ads_camapign_filtered_date_range_df['date'] = ads_camapign_filtered_date_range_df['date'].dt.strftime('%Y-%m-%d')
    sensor_camapign_filtered_date_range_df['date'] = sensor_camapign_filtered_date_range_df['date'].dt.strftime(
        '%Y-%m-%d')
    merge_df = pd.merge(ads_camapign_filtered_date_range_df,
                        sensor_camapign_filtered_date_range_df[
                            ['date', 'campaign', 'GMV', 'uv', 'AddtoCart', 'saleuser', 'sale', 'firstuser',
                             'firstuserfristbuy']], on=['date', 'campaign'], how='left')
    merge_df = output_groupby_df(merge_df, ['campaign'],
    ['impression','click','cost','ads value','conversions','allconversions','viewconversions','GMV', 'uv', 'AddtoCart', 'saleuser', 'sale','firstuser','firstuserfristbuy'], 'sum').reset_index()
    merge_df = add_custom_proportion_to_df(merge_df, 'GMV', 'cost', '神策ROI')
    merge_df = add_custom_proportion_to_df(merge_df, 'ads value', 'cost', 'ads ROI')
    merge_df = add_custom_proportion_to_df(merge_df, 'cost', 'click', 'CPC')
    merge_df = add_custom_proportion_to_df(merge_df, 'click', 'impression', 'CTR')
    merge_df = add_custom_proportion_to_df(merge_df, 'sale', 'uv', '神策转化率')
    merge_df = add_custom_proportion_to_df(merge_df, 'AddtoCart', 'uv', '神策加购率')
    merge_df[['神策ROI', 'ads ROI', 'CPC', 'GMV', 'ads value', 'cost', 'conversions', 'allconversions']] = \
        (merge_df[['神策ROI', 'ads ROI', 'CPC', 'GMV', 'ads value', 'cost', 'conversions', 'allconversions']]).round(2)
    merge_df[['CTR', '神策转化率', '神策加购率']] = (merge_df[['CTR', '神策转化率', '神策加购率']]).round(4)
    merge_df = merge_df.rename(
        columns={'conversions': 'ads转化', 'allconversions': 'ads所有转化', 'firstuser': '首访用户',
                 'firstuserfristbuy': '首访首购用户', 'sale': '销量', 'saleuser': '购买用户数',
                 'viewconversions': '浏览转化次数', 'AddtoCart': '加购数'})
    merge_df = merge_df.drop(columns=['campaign'])
    return merge_df

def get_right_and_left_select_dimensions(df):
    # 制作维度筛选框
    with st.container():
        col1, col2 = st.columns(2)
    with col1:
        left_options = st.selectbox(
            '左侧维度',
            df.columns
        )
    with col2:
        right_options = st.selectbox(
            '右侧维度',
            df.columns
        )
    return left_options, right_options

@st.cache_data(ttl=2400)
def output_trend_df(df, left_options, right_options,singe_campaign_option):
    # 创建基础图表
    base = alt.Chart(df, title=f'{singe_campaign_option}').encode(
        x=alt.X('date:T', axis=alt.Axis(format='%Y-%m-%d', title='Date')))
    # 为每个度量创建图表层
    left_line = base.mark_line(color='blue').encode(
        y=alt.Y(f'{left_options}:Q'))
    right_line = base.mark_line(color='red').encode(
        y=f'{right_options}:Q')
    annotation_df = df[['date', 'change', 'detail']]
    annotation_df = annotation_df[~annotation_df['change'].isnull()]
    annotation_df["y"] = 0
    annotation_layer = (
        alt.Chart(annotation_df)
        .mark_text(size=30, text="⬇", dx=0, dy=100, align="center")
        .encode(
            x=alt.X('date:T', axis=alt.Axis(format='%Y-%m-%d', title='Date')),
            y=alt.Y("y:Q", axis=None),
            tooltip=[alt.Tooltip('date:T', title='Date'),
                     alt.Tooltip('change', title='change'),
                     alt.Tooltip('detail', title='detail')],
        ).interactive())
    left_dimensions_layer = (
        alt.Chart(df).mark_line()
        .mark_text(size=10, align="center", baseline="middle", dy=15, color='blue')
        .encode(
            x=alt.X('date:T', axis=alt.Axis(format='%Y-%m-%d', title='Date')),
            y=alt.Y(f'{left_options}:Q', axis=None),
            text=f'{left_options}:Q',
            tooltip=[alt.Tooltip('date:T', title='Date'), alt.Tooltip(f'{left_options}:Q', title=f'{left_options}')]
        )
    )
    right_dimensions_layer = (
        alt.Chart(df).mark_line()
        .mark_text(size=10, align="center", baseline="middle", dy=15, color='red')
        .encode(
            x=alt.X('date:T', axis=alt.Axis(format='%Y-%m-%d', title='Date')),
            y=alt.Y(f'{right_options}:Q', axis=None),
            text=f'{right_options}:Q',
            tooltip=[alt.Tooltip('date:T', title='Date'), alt.Tooltip(f'{right_options}:Q', title=f'{right_options}')]
        )
    )
    combine_chart = alt.layer(left_line, right_line, annotation_layer, left_dimensions_layer,
                              right_dimensions_layer).resolve_scale(
        y='independent'
    ).interactive()
    return combine_chart

ads_df,sensor_df,change_ads_df = load_data()
ads_df = process_hk_cost_and_value_on_ads_data(ads_df,'currency','cost','ads value','HKD')
sensor_df = output_groupby_df(sensor_df, ['date','campaign'],
['GMV', 'uv', 'AddtoCart', 'saleuser', 'sale','firstuser','firstuserfristbuy'], 'sum').reset_index()
# 广告筛选框
unique_campaign = ads_df['campaign'].unique()
campaign_options = st.multiselect(
    '选择广告系列',
    unique_campaign
)
# 制作日期筛选框进行日期筛选
ads_df['date'] = pd.to_datetime(ads_df['date'])
ads_df['date'] = ads_df['date'].dt.strftime('%Y-%m-%d')
selected_range = out_date_range_data(ads_df,'date',"自选日期范围")
# 制作用于筛选左右维度的数据
if len(campaign_options) > 0:
    output_options_df = output_combine_df(selected_range,[campaign_options[0]],ads_df,sensor_df,change_ads_df)
    select_quantify_dimensions_df = output_options_df\
    .drop(columns=['date','campaign','campaigntype','change','detail'])
    left_options,right_options = get_right_and_left_select_dimensions(select_quantify_dimensions_df)

    for singe_campaign_option in campaign_options:
        merge_df = output_combine_df(selected_range,[singe_campaign_option],ads_df,sensor_df,change_ads_df)
        summary_df = output_summary_df(selected_range, [singe_campaign_option], ads_df, sensor_df)
        # summary_df[['CTR']] = summary_df['CTR'].apply(lambda x: f'{x:.2%}')
        # summary_df[['神策加购率']] = summary_df['神策加购率'].apply(lambda x: f'{x:.2%}')
        # summary_df[['神策转化率']] = summary_df['神策转化率'].apply(lambda x: f'{x:.2%}')
        combine_chart  = output_trend_df(merge_df,left_options,right_options,singe_campaign_option)
        st.altair_chart(combine_chart,use_container_width=600)
        st.dataframe(summary_df,width=1200,height=100)
