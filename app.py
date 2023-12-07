from flask import Flask, render_template, request, send_file
from wordcloud import WordCloud
import matplotlib.pyplot as plt
from io import BytesIO
import csv
import pandas as pd

app = Flask(__name__)

# CSV 파일에서 데이터를 읽어오기
def load_data_from_csv(file_path):
    data = []
    with open(file_path, 'r', encoding='utf-8') as file:
        csv_reader = csv.DictReader(file)
        for row in csv_reader:
            data.append(row)
    return data

# CSV 파일 경로 설정 (실제 파일 경로에 맞게 수정 필요)
csv_file_path = 'reviews_with_product_info.csv'
data = load_data_from_csv(csv_file_path)

# 데이터프레임 생성
df = pd.DataFrame(data)

# '광고 의심' 여부를 판단하는 함수
def detect_advertisement(review_content):
    advertisement_keywords = ['협찬', '광고', '제공', '업체', '소정의 비용']
    for keyword in advertisement_keywords:
        if keyword in review_content:
            return '광고 의심'
    return '내돈내산'

# '광고 의심' 여부 열 추가
df['Advertisement_Suspicion'] = df['Review_Content'].apply(detect_advertisement)


# '내돈내산' 여부를 판단하는 함수
def determine_my_money_ratio_ratio(my_money_ratio):
    return '내돈내산' if my_money_ratio > 0.5 else '광고 의심'

@app.route('/')
def index():
    # '내돈내산 비율' 계산
    my_money_ratio = df.groupby('Product_Name')['Advertisement_Suspicion'].apply(lambda x: (x == '내돈내산').sum() / len(x)).reset_index()
    my_money_ratio.columns = ['Product_Name', 'My_Money_Ratio']

    # '광고 의심 비율' 계산
    ad_suspicion_ratio = df.groupby('Product_Name')['Advertisement_Suspicion'].apply(lambda x: (x == '광고 의심').sum() / len(x)).reset_index()
    ad_suspicion_ratio.columns = ['Product_Name', 'Ad_Suspicion_Ratio']

    # 데이터 병합
    merged_df = pd.merge(df, my_money_ratio, on='Product_Name')
    merged_df = pd.merge(merged_df, ad_suspicion_ratio, on='Product_Name')

    # '내돈내산' 여부 판단
    merged_df['My_Money_Decision'] = merged_df['My_Money_Ratio'].apply(determine_my_money_ratio_ratio)

    # 결과를 딕셔너리 형태로 변환
    result_data = merged_df.to_dict(orient='records')

    return render_template('index.html', data=result_data, my_money_ratio=my_money_ratio)

@app.route('/generate_wordcloud/<product_name>')
def generate_wordcloud(product_name):
    # 해당 제품명에 해당하는 리뷰 내용을 모두 가져옴
    reviews = [row['Review_Content'] for row in data if row['Product_Name'] == product_name]

    # 리뷰 내용을 하나의 텍스트로 합침
    text = ' '.join(reviews)

    # 한글 폰트 지정
    font_path = 'NanumSquareNeo-dEb.ttf'  # 한글 폰트 파일 경로에 맞게 수정 필요

    # WordCloud 생성 (한글 폰트 지정)
    wordcloud = WordCloud(font_path=font_path, width=800, height=400, background_color='white').generate(text)

    # 생성된 WordCloud를 이미지로 저장
    image_stream = BytesIO()
    wordcloud.to_image().save(image_stream, format='PNG')
    image_stream.seek(0)

    # 이미지를 클라이언트에게 전송
    return send_file(image_stream, mimetype='image/png')

if __name__ == '__main__':
    app.run(debug=True)
