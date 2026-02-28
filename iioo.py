import re
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from multiprocessing import Pool, cpu_count
from typing import List, Dict, Any
import requests
from bs4 import BeautifulSoup


from sqlalchemy import create_engine, Column, Integer, String, Float, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from sqlalchemy.exc import SQLAlchemyError

#将爬出来的数据：影名 导演 年份 放入父表 评分和加权评分放进子表
#  数据库配置
DB_CONFIG = {
    "user": "postgres",       
    "password": "741852SQL",     
    "host": "localhost",  
    "port": "5432",           
    "db_name": "dou_ban_score"   
}

# 创建数据库连接URL
DB_URL = f"postgresql://{DB_CONFIG['user']}:{DB_CONFIG['password']}@{DB_CONFIG['host']}:{DB_CONFIG['port']}/{DB_CONFIG['db_name']}"

# 创建基类
Base = declarative_base()

#  定义数据库模型（父表+子表）
class MovieInfo(Base):
    """
    电影基础信息表（父表）
    电影名称、导演、年份
    """
    __tablename__ = "movie_info"                                        #表名
                               
    id = Column(Integer, primary_key=True, autoincrement=True)          # 主键，自增
    title = Column(String(255), nullable=False, comment="电影名称")     # 电影名称，非空
    director = Column(String(100), comment="导演")                      # 导演
    year = Column(String(10), comment="上映年份")                       # 上映年份
    
    # 建立与子表的一对多关系
    scores = relationship("MovieScore", back_populates="movie",  cascade="all, delete-orphan")  # cascade 为级联操作

class MovieScore(Base):
    """
    电影评分表（子表）
    评分、加权评分 关联父表的movie_id
    """
    __tablename__ = "movie_score"
    
    id = Column(Integer, primary_key=True, autoincrement=True)                                                   # 主键，自增
    movie_id = Column(Integer, ForeignKey("movie_info.id"), nullable=False, comment="关联电影基础信息表的ID")     # 外键
    original_score = Column(Float, comment="豆瓣原始评分")                                                       # 原始评分
    weighted_score = Column(Float, comment="加权评分")                                                               # 加权评分
    
    # 反向关联父表
    movie = relationship("MovieInfo", back_populates="scores")

# 创建引擎    echo=False不打印SQL语句
engine = create_engine(DB_URL, echo=False)     

#会话工厂 关闭自动提交和自动刷新                              
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)



# 原有的爬虫
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
raw_movies: List[Dict[str, Any]] = []

# -------------------------- 原有爬虫函数 --------------------------
def fetch_movies(start_num: int) -> List[Dict[str, Any]]:
    """
    返回：这一页解析出的电影列表，每个元素是 {"title", "score", "info"} 的字典。
    """
    url = f'https://movie.douban.com/top250?start={start_num}&filter='
    movie_list = []

    try:
        response = requests.get(url, headers=headers, timeout=10)

        if response.status_code != 200:
            print(f"Page {start_num//PAGE_SIZE+1} 请求失败，状态码：{response.status_code}")
            return movie_list
        
        soup = BeautifulSoup(response.text, 'html.parser')

        for item in soup.find_all('div', class_='item'):
            title_tag = item.find('span', class_='title')
            title = title_tag.string.strip() if title_tag and title_tag.string else "未知"

            score_tag = item.find('span', class_='rating_num')
            score = score_tag.string.strip() if score_tag and score_tag.string else "0.0"

            info_p = item.find('p', )
            info = info_p.get_text(strip=True) if info_p else ""

            movie_list.append({
                "title": title.split('/')[0] if '/' in title else title,
                "score": score,
                "info": info
            })

        print(f"Page {start_num//PAGE_SIZE+1} 爬取完成，本页 {len(movie_list)} 部电影")

    except Exception as e:        
        print(f"Page {start_num//PAGE_SIZE+1} 爬取出错：{str(e)}")

    return movie_list 


# 原有的爬虫数据处理
def process_movie(movie: Dict[str, Any]) -> Dict[str, Any]:
    """
    在进程里处理一条电影数据：从 info 里解析年份、导演，并计算加权评分。
    """
    info = movie.get("info", "")
    year = "未知"
    director = "未知"

    for part in info.split('\n'):
        part = part.strip()  
        if '导演:' in part:
            director_part = part.split('导演:')[-1].strip()
            director = director_part.split(' ')[0].strip() if director_part else "未知"
       
        year_match = re.search(r'\b(\d{4})\b', part)
        if year_match:
            year_candidate = year_match.group(1)
            if 1900 <= int(year_candidate) <= 2025:
                year = year_candidate
                break

    try:        
        score = float(movie["score"])
        year_num = int(year) if year.isdigit() else 2000
        weighted_score = score * (1 + (2026 - year_num)/100)
    except:
        weighted_score = 0.0

    return {
        "title": movie["title"],
        "score": score,
        "weighted_score": round(weighted_score, 2),
        "year": year,
        "director": director
    }




# 数据入库函数    自动建表  创建会话  遍历数据 提交 / 回滚  关闭会话
def save_movies_to_db(processed_movies: List[Dict[str, Any]]):
  
    # 创建所有数据表（如果不存在）
    Base.metadata.create_all(bind=engine)
    
    # 创建数据库会话
    db_session = SessionLocal()
    
    try:
        # 遍历处理后的电影数据，逐行入库

        for movie in processed_movies:           
            # 1. 创建父表（电影基础信息）
            movie_info = MovieInfo(
                title=movie["title"],
                director=movie["director"],
                year=movie["year"]
            )
            db_session.add(movie_info)
            db_session.flush()  # 刷新会话，获取刚插入的movie_info.id
            
            # 2. 创建子表（电影评分）
            movie_score = MovieScore(
                movie_id=movie_info.id,
                original_score=movie["score"],
                weighted_score=movie["weighted_score"]
            )
            db_session.add(movie_score)
        
        # 提交事务 统一提交 避免部分成功部分提交对于数据库造成干扰
        db_session.commit()
        print(f"\n 成功将 {len(processed_movies)} 条电影数据存入数据库！")
    
    except SQLAlchemyError as e:
        # 出错时回滚事务
        db_session.rollback()
        print(f"\n 数据入库失败：{str(e)}")
    finally:
        # 关闭会话
        db_session.close()



#  主函数（新增入库调用） 
def main():
    global raw_movies  
    raw_movies = []

    # 计算需要爬取的页数
    need_page = min((TARGET_MOVIE_COUNT + PAGE_SIZE - 1) // PAGE_SIZE, MAX_TOTAL_PAGE)
    start_nums = [i * PAGE_SIZE for i in range(need_page)]

    # 多线程爬取数据
    with ThreadPoolExecutor(max_workers=THREAD_POOL_SIZE) as thread_executor:
        futures = [thread_executor.submit(fetch_movies, sn) for sn in start_nums]        
        for future in as_completed(futures):
            page_movies = future.result()  
            with results_lock:
                raw_movies.extend(page_movies)
                if len(raw_movies) >= TARGET_MOVIE_COUNT:
                    raw_movies = raw_movies[:TARGET_MOVIE_COUNT]
                    break

    # 多进程处理数据
    print(f"\n开始用 {PROCESS_POOL_SIZE} 个进程处理 {len(raw_movies)} 条电影数据...")
    with Pool(PROCESS_POOL_SIZE) as process_pool:
        processed_movies = process_pool.map(process_movie, raw_movies)

    # 排序与打印
    processed_movies.sort(key=lambda x: x["weighted_score"], reverse=True)

    print(f"\n=== 处理结果（按加权评分排序，前 {PRINT_COUNT} 条）===")
    for i, movie in enumerate(processed_movies[:PRINT_COUNT], 1):
        print(f"{i}. {movie['title']} | 原评分：{movie['score']} | 加权评分：{movie['weighted_score']} | 年份：{movie['year']} | 导演：{movie['director']}")


    # 新增：调用入库函数
    save_movies_to_db(processed_movies)

  
    return processed_movies  


if __name__ == "__main__":
    main()