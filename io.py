import asyncio
import aiohttp
from bs4 import BeautifulSoup
from typing import List, Dict, Any  


TARGET_MOVIE_COUNT = 100    # 爬取的电影总数
PRINT_COUNT = 50            # 打印展示的电影条数
PAGE_SIZE = 25              # 豆瓣Top250每页固定显示25部
MAX_TOTAL_PAGE = 10         # 豆瓣Top250总页数

# 请求头  这个头是我的浏览器复制来的
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
}

async def fetch_movies(session: aiohttp.ClientSession, start_num: int) -> List[Dict[str, Any]]:
    
    """  
        session: 共享的异步HTTP会话对象
        start_num: 分页起始数（0,25,50...）
    Returns:
        包含电影信息的列表，每个元素是字典：{"title": 电影名, "score": 评分}
    """

    url = f'https://movie.douban.com/top250?start={start_num}&filter='
    movie_list: List[Dict[str, Any]] = []  
    
    try:
        async with session.get(url, headers=headers) as response:
            if response.status != 200:
                print(f"Page {start_num//PAGE_SIZE + 1} 请求失败，状态码：{response.status}")
                return movie_list
            
            html = await response.text()
            soup = BeautifulSoup(html, 'html.parser')
            
            # 定位每一部电影的容器
            movie_items = soup.find_all('div', class_='item')
            for item in movie_items:
                # 提取电影名称（排除外文）
                title_movie = item.find('span', class_='title')
                title = title_movie.string if title_movie else "未知名称"
                if "/" in title:  # 过滤带/的外文名称
                    continue
                
                # 电影评分
                score_movie = item.find('span', class_='rating_num')
                score = score_movie.string if score_movie else "0.0"
                
                # 组装电影的信息
                movie_info = {"title": title, "score": score}
                movie_list.append(movie_info)
                
            print(f"Page {start_num//PAGE_SIZE + 1} 爬取完成，共{len(movie_list)}部电影")
            
    except Exception as e:
        print(f"Page {start_num//PAGE_SIZE + 1} 爬取出错：{str(e)}")
    
    return movie_list

async def main() -> List[Dict[str, Any]]:
    all_movies: List[Dict[str, Any]] = []  # 存储所有电影信息
    
    # 计算需要爬取的页数：向上取整（目标数/每页条数），但不超过总页数
     # 生成需要爬取的页码列表（0,25,50...）
    need_page = min((TARGET_MOVIE_COUNT + PAGE_SIZE - 1) // PAGE_SIZE, MAX_TOTAL_PAGE)
    start_nums = [i * PAGE_SIZE for i in range(need_page)]
    
    async with aiohttp.ClientSession() as session:
        # 生成对应页数的爬取任务
        tasks = [fetch_movies(session, start_num) for start_num in start_nums]    
        page_results = await asyncio.gather(*tasks)
        
        # 合并结果并截断到目标数量
        for page_movies in page_results:
            all_movies.extend(page_movies)
            if len(all_movies) >= TARGET_MOVIE_COUNT:
                all_movies = all_movies[:TARGET_MOVIE_COUNT]
                break
    
    # 打印结果
    print(f"\n=== 爬取结果（前{min(PRINT_COUNT, len(all_movies))}条）===")
    for i, movie in enumerate(all_movies[:PRINT_COUNT], 1):
        print(f"{i}. {movie['title']} - {movie['score']}分")
    
    return all_movies

if __name__ == "__main__":
    total_movies = asyncio.run(main())
    print(f"\n实际爬取到 {len(total_movies)} 部电影信息（目标：{TARGET_MOVIE_COUNT}）")