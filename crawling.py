from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import time
import csv

# 시작 상품 ID와 종료 상품 ID 설정
start_product_id = 120040506
end_product_id = 120040806 

# 크롬 드라이버 설정 (크롬 드라이버가 설치되어 있어야 합니다)
driver = webdriver.Chrome()

# 모든 리뷰를 저장할 리스트
all_reviews = []

try:
    for product_id in range(start_product_id, end_product_id + 1):
        url = f"https://zigzag.kr/catalog/products/{product_id}?tab=review"
        driver.get(url)

        try:
            # 리뷰 컨테이너가 나타날 때까지 대기
            reviews_container = WebDriverWait(driver, 5).until(
                EC.presence_of_element_located((By.CLASS_NAME, 'css-z61zy2'))
            )

            # 상품명 가져오기
            product_name = driver.find_element(By.CLASS_NAME, 'BODY_16.REGULAR.css-jdi3f5.e1wgb8lp0').text
            print(f"상품명: {product_name}")

            # 가격 가져오기
            product_price_element = driver.find_element(By.CLASS_NAME, 'css-15ex2ru.e1i71w5g1')
            product_price = product_price_element.text.strip()
            print(f"가격: {product_price[:-2]}원\n")

            # 리뷰 페이지로 이동
            review_url = f"https://zigzag.kr/review/list/{product_id}"
            driver.get(review_url)

            # 초기 페이지 소스 가져오기
            html_code = driver.page_source

            # BeautifulSoup으로 계속 진행
            soup = BeautifulSoup(html_code, 'html.parser')
            reviews = []

            # 이미 수집한 사용자 이름 기록
            collected_usernames = set()

            # 페이지 하단으로 스크롤하는 함수
            def scroll_to_bottom():
                driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(2)  # 새로운 콘텐츠가 로드될 때까지 기다리기 위한 딜레이

            while True:
                # 페이지 하단으로 스크롤
                scroll_to_bottom()

                # 업데이트된 페이지 소스 가져오기
                html_code = driver.page_source

                # BeautifulSoup으로 계속 진행
                soup = BeautifulSoup(html_code, 'html.parser')

                # 리뷰 추출
                for review_tag in soup.find_all('div', class_='css-1uql0ux e1pdzmd01'):
                    user_name = review_tag.select_one('.BODY_16.SEMIBOLD.css-1k3hx0v.e1fnwskn0').text

                    # 중복 체크
                    if user_name not in collected_usernames:
                        review_info = {}
                        review_info['product_name'] = product_name
                        review_info['user_name'] = user_name
                        review_info['review_content'] = review_tag.select_one('.BODY_14.REGULAR.css-epr5m6.e1j2jqj72').text
                        reviews.append(review_info)

                        # 수집한 사용자 이름 기록에 추가
                        collected_usernames.add(user_name)

                # 리뷰가 더 이상 없으면 루프 종료
                if not soup.find('div', class_='css-1uql0ux e1pdzmd01'):
                    break

                # 더 이상 로드할 리뷰가 없으면 루프 종료
                if not soup.find('button', class_='css-1ny60k3'):
                    break

            if not reviews:
                print(f"상품 {product_id}에 대한 리뷰가 없습니다.")
            else:
                # 모든 리뷰를 all_reviews 리스트에 추가
                all_reviews.extend(reviews)

        except TimeoutException:
            print(f"타임아웃 예외: 리뷰 컨테이너가 {product_id}에 대해 나타나지 않음")
        except NoSuchElementException:
            print(f"요소 찾기 예외: {product_id}에 대한 요소를 찾을 수 없음")
        except Exception as e:
            print(f"상품 {product_id} 크롤링 중 알 수 없는 오류 발생: {e}")

finally:
    # 모든 상품에 대한 크롤링이 완료된 후에 브라우저를 종료
    driver.quit()

# 모든 리뷰를 하나의 CSV 파일로 저장
csv_file_path = "all_reviews.csv"
with open(csv_file_path, mode='w', encoding='utf-8', newline='') as file:
    fieldnames = ['Product_Name', 'User_Name', 'Review_Content']
    writer = csv.DictWriter(file, fieldnames=fieldnames)

    # CSV 파일 헤더 작성
    writer.writeheader()

    # 리뷰 정보를 CSV 파일에 작성
    for review in all_reviews:
        writer.writerow({'Product_Name': review['product_name'], 'User_Name': review['user_name'], 'Review_Content': review['review_content']})

print(f"데이터가 {csv_file_path}에 저장")