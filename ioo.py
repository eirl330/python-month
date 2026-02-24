import re
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from multiprocessing import Pool, cpu_count
from typing import List, Dict, Any
import requests
from bs4 import BeautifulSoup



# 配置项
TARGET_MOVIE_COUNT = 100    # 最终要爬取多少部电影
PRINT_COUNT = 50            # 程序最后只打印前多少条结果
PAGE_SIZE = 25              # 豆瓣 Top250 每页固定 25 部电影
MAX_TOTAL_PAGE = 10         # Top250 一共 10 页
THREAD_POOL_SIZE = 10       # 线程池里最多同时跑几个线程
PROCESS_POOL_SIZE = cpu_count()  # 进程池大小



headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
}



results_lock = threading.Lock()
# 创建一个「锁」：多线程同时往 raw_movies 里追加数据时，用锁保证同一时刻只有一个线程在写，避免数据错乱

raw_movies: List[Dict[str, Any]] = []
# 列表存放原始电影数据 每条是一个字典


#多线程爬取
def fetch_movies(start_num: int) -> List[Dict[str, Any]]:
    """
    返回：这一页解析出的电影列表，每个元素是 {"title", "score", "info"} 的字典。
    """
    # 豆瓣分页 URL：start=0 是第 1 页，start=25 是第 2 页，以此类推
    url = f'https://movie.douban.com/top250?start={start_num}&filter='
    movie_list = []  # 本页的电影列表，先设为空

    try:
        # 发 GET 请求
        response = requests.get(url, headers=headers, timeout=10)

        if response.status_code != 200:
            print(f"Page {start_num//PAGE_SIZE+1} 请求失败，状态码：{response.status_code}")
            return movie_list  # 直接返回空列表
        
        soup = BeautifulSoup(response.text, 'html.parser')

        # 豆瓣每部电影在一个 class="item" 的 div 里，找出本页所有这样的 div
        for item in soup.find_all('div', class_='item'):
            
            # 解析标题 strip用于去掉空格
            title_tag = item.find('span', class_='title')
            title = title_tag.string.strip() if title_tag and title_tag.string else "未知"

            # 解析评分 
            score_tag = item.find('span', class_='rating_num')
            score = score_tag.string.strip() if score_tag and score_tag.string else "0.0"

            # 解析简介
            info_p = item.find('p', )
            info = info_p.get_text(strip=True) if info_p else ""
            #不要直接把tag的哪些beautifulsoup对象放进去了
            movie_list.append({
                "title": title.split('/')[0] if '/' in title else title,  # 把标题按 / 分割，取分割后的第一个部分
                "score": score,
                "info": info
            })

        print(f"Page {start_num//PAGE_SIZE+1} 爬取完成，本页 {len(movie_list)} 部电影")

    #捕获异常并打印 防止程序崩溃
    except Exception as e:        
        print(f"Page {start_num//PAGE_SIZE+1} 爬取出错：{str(e)}")

    return movie_list 


# 多进程处理数据
def process_movie(movie: Dict[str, Any]) -> Dict[str, Any]:
    """
    在进程里处理一条电影数据：从 info 里解析年份、导演，并计算加权评分。
    参数 movie是原始的电影字典至少包含 "title", "score", "info"。
    返回 加工后的字典，多了 "year", "director", "weighted_score"。
    """
    info = movie.get("info", "")  # 没有 "info" 键时用空字符串
    year = "未知"
    director = "未知"
    print(f"[DEBUG] 原始 info 内容:\n{repr(info)}\n")
    # 按行分割 info（豆瓣格式里导演、年份等在不同行）
    for part in info.split('\n'):
        part = part.strip()  
        if '导演:' in part:
            # 按 "导演:" 分割，取后面的部分，再按空格分割取第一个名字
            director_part = part.split('导演:')[-1].strip()
            director = director_part.split(' ')[0].strip() if director_part else "未知"
       
        
        year_match = re.search(r'\b(\d{4})\b', part)
        if year_match:
            year_candidate = year_match.group(1)
            # 简单校验：年份一般在 1900 到 2025 之间
            if 1900 <= int(year_candidate) <= 2025:
                year = year_candidate
                break  # 找到年份后就跳出循环
    try:        
        score = float(movie["score"])
        year_num = int(year) if year.isdigit() else 2000            # 解析不出年份时用 2000
        weighted_score = score * (1 + (2026 - year_num)/100)        #如2001年的电影加权系数是1.25
    except:
        weighted_score = 0.0

    # 返回一条加工后的电影数据
    return {
        "title": movie["title"],
        "score": movie["score"],
        "weighted_score": round(weighted_score, 2),
        "year": year,
        "director": director
    }



def main():
    global raw_movies  
    raw_movies = []    # 每次运行主程序时清空，避免重复运行残留数据

    
    # 算需要爬几页
    need_page = min((TARGET_MOVIE_COUNT + PAGE_SIZE - 1) // PAGE_SIZE, MAX_TOTAL_PAGE)
    # 每页的 start 参数
    start_nums = [i * PAGE_SIZE for i in range(need_page)]

    # 创建线程池
    with ThreadPoolExecutor(max_workers=THREAD_POOL_SIZE) as thread_executor:
        # 为每一页提交一个任务：fetch_movies(0), fetch_movies(25), ...        
        futures = [thread_executor.submit(fetch_movies, sn) for sn in start_nums]        
       
       #哪个任务先完成，就先返回哪个的 future  as_completed
        for future in as_completed(futures):
            page_movies = future.result()  
            with results_lock:                       # 加锁，保证下面两行执行时别的线程不会同时改 raw_movies
                raw_movies.extend(page_movies)       #用append的话会把整个列表当一个列表元素塞进去
                # 若已超过目标数量，只保留前 TARGET_MOVIE_COUNT 条并跳出
                if len(raw_movies) >= TARGET_MOVIE_COUNT:
                    raw_movies = raw_movies[:TARGET_MOVIE_COUNT]
                    break

   
    print(f"\n开始用 {PROCESS_POOL_SIZE} 个进程处理 {len(raw_movies)} 条电影数据...")
    with Pool(PROCESS_POOL_SIZE) as process_pool:
        processed_movies = process_pool.map(process_movie, raw_movies)

    # 排序与打印
    # 按加权评分从高到低排序  .sort()列表内置排序 key排序依据  reverse=True降序
    processed_movies.sort(key=lambda x: x["weighted_score"], reverse=True)

    print(f"\n=== 处理结果（按加权评分排序，前 {PRINT_COUNT} 条）===")
    for i, movie in enumerate(processed_movies[:PRINT_COUNT], 1):
        print(f"{i}. {movie['title']} | 原评分：{movie['score']} | 加权评分：{movie['weighted_score']} | 年份：{movie['year']} | 导演：{movie['director']}")

    return processed_movies  


if __name__ == "__main__":
    main()