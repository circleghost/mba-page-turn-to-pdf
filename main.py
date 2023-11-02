from urllib.parse import urljoin
import base64
import requests
from bs4 import BeautifulSoup
from hanziconv import HanziConv
from xhtml2pdf import pisa
import streamlit as st
import io

# 設定 Streamlit
st.header('抓取 MBA 智庫內容，並轉成 PDF 檔案下載', divider ='rainbow')

st.subheader('請輸入 :blue[MBA 智庫]的網址 :sunglasses:')


# 輸入網址
url = st.text_input('↓↓↓↓↓↓')
submit_button = st.button('送出')

if url and submit_button:
    with st.spinner('處理中...'):
        # 抓取網頁內容
        response = requests.get(url)
        soup = BeautifulSoup(response.text, 'html.parser')

        # 提取<div id="content">內的HTML內容
        content_div = soup.find(id='content')

        # 移除<div id="column-one">內的內容
        column_one_div = content_div.find(id='column-one')
        if column_one_div:
            column_one_div.decompose()

        # 移除class是toc及wikitable的相關table以及class是editsection的div
        for table in content_div.find_all('table', {'class': ['toc', 'wikitable']}):
            table.decompose()
        for div in content_div.find_all('div', {'class': 'editsection'}):
            div.decompose()

        # 移除id是siteSub的h3標籤以及class是code-lay visualClear的div
        siteSub_h3 = content_div.find('h3', {'id': 'siteSub'})
        if siteSub_h3:
            siteSub_h3.decompose()
        code_lay_div = content_div.find('div', {'class': 'code-lay visualClear'})
        if code_lay_div:
            code_lay_div.decompose()

        # 移除<!-- Tidy found serious XHTML errors -->之後的內容
        content_div = str(content_div).split('<!-- Tidy found serious XHTML errors -->')[0]

        # 簡體轉繁體
        content = HanziConv.toTraditional(content_div)

        # 確保所有圖片URL都是絕對的
        soup = BeautifulSoup(content, 'html.parser')
        for img in soup.find_all('img'):
            img_url = urljoin(url, img['src'])
            response = requests.get(img_url)
            img_data = base64.b64encode(response.content).decode('utf-8')
            img['src'] = 'data:image/png;base64,' + img_data

        # 在 HTML 開頭添加 @font-face 規則
        font_face_css = """
        <style>
        @font-face {
            font-family: 'Noto Sans TC';
            src: url('https://raw.githubusercontent.com/circleghost/mba-page-turn-to-pdf/master/path/to/font.woff2') format('woff2');
            font-weight: normal;
            font-style: normal;
        }
        body {
            font-family: 'Noto Sans TC';
        }
        </style>
        """
        content = font_face_css + str(soup)

        # 創建 PDF 文件的完整路徑
        pdf_path = soup.find('h1').get_text() + '.pdf'

        # 將 HTML 轉換為 PDF
        pdf_file = io.BytesIO()
        pisa.CreatePDF(io.BytesIO(content.encode()), pdf_file)

        # 檢查檔案是否存在
        if pdf_file.getbuffer().nbytes > 0:
            st.success('PDF 檔案已建立完成')
            # 提供下載連結
            btn = st.download_button(
                label="下載 PDF 檔吧！",
                data=pdf_file.getvalue(),
                file_name=pdf_path,
                mime='application/pdf',
            )
            if btn:
                st.button('清除並重新輸入網址', type = "primary")
        else:
            st.error('PDF 檔案創建失敗')
