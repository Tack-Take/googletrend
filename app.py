import streamlit as st
from pytrends.request import TrendReq
import pandas as pd
import matplotlib.pyplot as plt
import base64
import matplotlib
import time
import plotly.graph_objects as go
from datetime import datetime, timedelta

# 日本語フォント設定（Windows用 / 他の環境では適宜変更してください）
matplotlib.rcParams['font.family'] = 'MS Gothic'

# --- 定数定義 ---
DEFAULT_KEYWORDS = "摂南大学,近畿大学,立命館大学"  # デフォルトキーワードを変更
CACHE_TTL = 60 * 60  # キャッシュの有効時間 (秒) 1時間

# 都道府県名とコードの対応辞書
prefecture_to_code = {
    "全国": "JP", "北海道": "JP-01", "青森県": "JP-02", "岩手県": "JP-03", "宮城県": "JP-04",
    "秋田県": "JP-05", "山形県": "JP-06", "福島県": "JP-07", "茨城県": "JP-08",
    "栃木県": "JP-09", "群馬県": "JP-10", "埼玉県": "JP-11", "千葉県": "JP-12",
    "東京都": "JP-13", "神奈川県": "JP-14", "新潟県": "JP-15", "富山県": "JP-16",
    "石川県": "JP-17", "福井県": "JP-18", "山梨県": "JP-19", "長野県": "JP-20",
    "岐阜県": "JP-21", "静岡県": "JP-22", "愛知県": "JP-23", "三重県": "JP-24",
    "滋賀県": "JP-25", "京都府": "JP-26", "大阪府": "JP-27", "兵庫県": "JP-28",
    "奈良県": "JP-29", "和歌山県": "JP-30", "鳥取県": "JP-31", "島根県": "JP-32",
    "岡山県": "JP-33", "広島県": "JP-34", "山口県": "JP-35", "徳島県": "JP-36",
    "香川県": "JP-37", "愛媛県": "JP-38", "高知県": "JP-39", "福岡県": "JP-40",
    "佐賀県": "JP-41", "長崎県": "JP-42", "熊本県": "JP-43", "大分県": "JP-44",
    "宮崎県": "JP-45", "鹿児島県": "JP-46", "沖縄県": "JP-47"
}

# 国コード (適宜追加してください)
COUNTRY_CODES = {
    "日本": "JP",
    "アメリカ": "US",
    "イギリス": "GB",
    "カナダ": "CA",
    "ドイツ": "DE",
    "フランス": "FR",
    "オーストラリア": "AU",
}

# --- 関数定義 ---

# キャッシュを考慮したデータ取得関数
@st.cache_data(ttl=CACHE_TTL)
def get_trends_data(keyword_list, timeframe, geo, cat=0):
    pytrends = TrendReq(hl='ja-JP', tz=360, timeout=(10, 25))
    pytrends.build_payload(keyword_list, timeframe=timeframe, geo=geo, cat=cat)
    trend_data = pytrends.interest_over_time()
    if "isPartial" in trend_data.columns:
        trend_data.drop(columns=["isPartial"], inplace=True)
    return trend_data

# 関連キーワード取得関数 (修正: リトライ処理を追加)
@st.cache_data(ttl=CACHE_TTL)
def get_related_queries(keyword_list, timeframe, geo, cat=0, retries=3, delay=5):
    pytrends = TrendReq(hl='ja-JP', tz=360, timeout=(10, 25))
    for i in range(retries):
        try:
            pytrends.build_payload(keyword_list, timeframe=timeframe, geo=geo, cat=cat)
            related_queries = pytrends.related_queries()
            # データがあるか確認
            if related_queries and any(related_queries[kw]['top'] is not None and not related_queries[kw]['top'].empty for kw in keyword_list if kw in related_queries):
                return related_queries
            else:
                print(f"関連キーワードが空です。リトライします: {i+1}/{retries}")
                time.sleep(delay)  # リトライ前に待機
        except Exception as e:
            print(f"エラー発生: {e} リトライします: {i+1}/{retries}")
            time.sleep(delay)
    return {}  # リトライ失敗時は空の辞書を返す


# 関連トピック取得関数 (修正: リトライ処理を追加)
@st.cache_data(ttl=CACHE_TTL)
def get_related_topics(keyword_list, timeframe, geo, cat=0, retries=3, delay=5):
    pytrends = TrendReq(hl='ja-JP', tz=360, timeout=(10, 25))
    for i in range(retries):
        try:
            pytrends.build_payload(keyword_list, timeframe=timeframe, geo=geo, cat=cat)
            related_topics = pytrends.related_topics()
            # データがあるか確認
            if related_topics and any(related_topics[kw]['top'] is not None and not related_topics[kw]['top'].empty for kw in keyword_list if kw in related_topics):
                return related_topics
            else:
                print(f"関連トピックが空です。リトライします: {i+1}/{retries}")
                time.sleep(delay)  # リトライ前に待機
        except Exception as e:
            print(f"エラー発生: {e} リトライします: {i+1}/{retries}")
            time.sleep(delay)
    return {}  # リトライ失敗時は空の辞書を返す

# CSVダウンロードリンク生成関数
def download_csv(data):
    csv = data.to_csv(index=False, encoding='utf-8-sig')
    b64 = base64.b64encode(csv.encode('utf-8-sig')).decode()
    href = f'<a href="data:file/csv;base64,{b64}" download="trends_data.csv">CSVをダウンロード</a>'
    return href

# エラーメッセージ表示関数
def display_error(message):
    st.error(message)
    st.stop()

# --- UI設定 ---

st.set_page_config(page_title="Google Trends Dashboard", page_icon=":chart_with_upwards_trend:", layout="wide")

# サイドバー
st.sidebar.title("オプション設定")

# # テーマ選択 (ダークテーマをデフォルトに)
# theme = st.sidebar.selectbox("テーマ", ["dark", "light"], index=0)

# # テーマ設定
# if theme == "light":
#     st.markdown(
#         """
#         <style>
#         body {
#             color: black;
#             background-color: #FFFFFF;
#         }
#         .sidebar .sidebar-content {
#             background-color: #FFFFFF;
#         }
#         </style>
#         """,
#         unsafe_allow_html=True
#     )
# else:
#     st.markdown(
#         """
#         <style>
#         body {
#             color: white;
#             background-color: #262730;
#         }
#         .sidebar .sidebar-content {
#             background-color: #262730;
#         }
#         </style>
#         """,
#         unsafe_allow_html=True
#     )

# キーワード入力
keywords = st.sidebar.text_input("キーワード（複数の場合はカンマ区切り）", DEFAULT_KEYWORDS)
keyword_list = [kw.strip() for kw in keywords.split(",")]

# 期間選択
timeframe_options = {
    "過去1時間": "now 1-H",
    "過去4時間": "now 4-H",
    "過去1日": "now 1-d",
    "過去7日": "now 7-d",
    "過去30日": "today 1-m",
    "過去90日": "today 3-m",
    "過去12ヶ月": "today 12-m",
    "過去5年": "today 5-y",
    "全期間(2004年から現在)": "all",
}
timeframe = st.sidebar.selectbox("期間を選択", list(timeframe_options.keys()), index=5)  # デフォルトを過去90日に
selected_timeframe = timeframe_options[timeframe]

# 地域選択
country = st.sidebar.selectbox("国を選択", list(COUNTRY_CODES.keys()), index=0)
selected_country = COUNTRY_CODES[country]
prefecture = st.sidebar.selectbox("都道府県を選択", list(prefecture_to_code.keys()), index=0)  # デフォルトを全国に
geo = prefecture_to_code[prefecture] if selected_country == "JP" else selected_country

# カテゴリ選択
# Google TrendsのカテゴリIDを取得 (必要に応じて調査・更新)
categories = {
    "すべてのカテゴリ": 0,
    "本 & 文学": 35,
    "ビジネス & 産業": 9,
    "コンピュータ & エレクトロニクス": 5,
    "ファイナンス": 7,
    "食品 & 飲料": 71,
    "ゲーム": 8,
    "インターネット & 通信": 12,
    "ニュース": 16,
    "オンラインコミュニティ": 299,
    "科学": 174,
    "スポーツ": 18,
}
category = st.sidebar.selectbox("カテゴリを選択", list(categories.keys()), index=0)
selected_category = categories[category]

# 検索ボタン
search_button = st.sidebar.button("検索開始")

# メインコンテンツ
st.title("Google Trends ダッシュボード")
st.write("Google Trendsの検索データを動的に取得し、分析します。")

if search_button:
    # 入力値検証
    if not keyword_list:
        display_error("キーワードを入力してください。")

    if not geo:
        display_error("地域を選択してください。")

    # 検索実行
    with st.spinner("データ取得中..."):
        try:
            trend_data = get_trends_data(keyword_list, selected_timeframe, geo, selected_category)
        except Exception as e:
            st.error(f"データ取得エラー: {e}")
            if "response with code 429" in str(e):
                st.error("Google Trendsへのリクエストが多すぎます。時間をおいて再度お試しください。")
            trend_data = None

        try:
            related_queries = get_related_queries(keyword_list, selected_timeframe, geo, selected_category)
        except Exception as e:
            st.error(f"関連クエリ取得エラー: {e}")
            related_queries = None

        try:
            related_topics = get_related_topics(keyword_list, selected_timeframe, geo, selected_category)
        except Exception as e:
            st.error(f"関連トピック取得エラー: {e}")
            related_topics = None

    # データ取得結果表示
    if trend_data is not None and not trend_data.empty:
        st.success("データ取得に成功しました！")

        # トレンドデータ表示
        st.subheader("検索トレンドデータ")

        # データフレームをシンプルに表示
        st.dataframe(trend_data)

        # CSVダウンロードリンク
        st.markdown(download_csv(trend_data), unsafe_allow_html=True)

        # トレンド比較グラフ (Plotlyを使用)
        st.subheader("キーワードごとの検索トレンド比較")
        fig = go.Figure()
        for kw in keyword_list:
            fig.add_trace(go.Scatter(x=trend_data.index, y=trend_data[kw], mode='lines', name=kw))

        # グラフのレイアウト設定
        fig.update_layout(
          xaxis_title="日付",
          yaxis_title="検索ボリューム（相対値）",
          hovermode="x",
          legend_title="キーワード",
          template="plotly"
        )
        st.plotly_chart(fig, use_container_width=True)

        # 関連キーワード表示
        st.subheader("関連キーワード")
        for kw in keyword_list:
            st.write(f"**{kw}** の関連キーワード:")
            if related_queries and kw in related_queries and related_queries[kw] and 'top' in related_queries[kw] and related_queries[kw]['top'] is not None:
                top_keywords = related_queries[kw]['top'].head(10).sort_values(by='value', ascending=False)
                st.dataframe(top_keywords) # 表をシンプルに
            else:
                st.write(f"`{kw}` に関連するキーワードデータがありません。")

        # 関連トピック表示
        st.subheader("関連トピック")
        for kw in keyword_list:
            st.write(f"**{kw}** の関連トピック:")
            if related_topics and kw in related_topics and related_topics[kw] and 'top' in related_topics[kw] and related_topics[kw]['top'] is not None:
                top_topics = related_topics[kw]['top'].head(10).sort_values(by='value', ascending=False)
                st.dataframe(top_topics) # 表をシンプルに
            else:
                st.write(f"`{kw}` に関連するトピックデータがありません。")
    else:
        st.warning("検索データが見つかりませんでした。")