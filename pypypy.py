'''
print("hello world")

str = 'Runoob'  # 定义一个字符串变量

print(str)           # 打印整个字符串
print(str[0:-1])     # 打印字符串第一个到倒数第二个字符（不包含倒数第一个字符）
print(str[0])        # 打印字符串的第一个字符
print(str[2:5])      # 打印字符串第三到第五个字符（不包含索引为 5 的字符）
print(str[2:])       # 打印字符串从第三个字符开始到末尾
print(str * 2)       # 打印字符串两次
print(str + "TEST")  # 打印字符串和"TEST"拼接在一起
#空的东西才被视为false大王 
#list像一个很包容的数组，可以和命名一样直接改变 []到（）即元组 里面东西不能改 t(2,)    t(2)
#集合 空集合set()  普通集合{a,b,c} # set可以进行集合运算 和数学的一样  
#a = set('abracadabra')
 #b= set('alacazam')
#print(a)
'''

'''
print(a - b)     # a 和 b 的差集
print(a | b)     # a 和 b 的并集
print(a & b)     # a 和 b 的交集
print(a ^ b)     # a 和 b 中不同时存在的元素
字典存映射关系  x:y(y可以是个式子)  {x: x**2 for x in (2, 4, 6)}
'''
# -*- coding: utf-8 -*-





#删掉'''就可以玩了
'''
import random                           # 随机数模块


def play_one_round() -> int:              #int 让函数易读
    
    target = random.randint(10, 50)  # 随机整数  用random不加int会变成浮点数
    guess_history = [] 
    guess_count = 0     

    print("\n 一个 10 到 50 之间的数字，来猜猜看吧！")

    while True:    
        try:      #处理异常 防止程序崩溃
            user_input = input("输入你猜的数字（按q 退出本轮）：")       
            if user_input.lower() == "q":        #大写转小写
                print(f"本轮退出，正确答案是：{target}")     #f-string
                return guess_count

            guess = int(user_input)
            guess_count += 1
            guess_history.append(guess)  # 把这次猜测加入历史列表

            if guess < target:
                print("太小了，试试大一点的数")
            elif guess > target:
                print("太大了，试试小一点的数")
            else:
                print(f"恭喜你猜对了！答案就是 {target}！")
                print(f"你一共猜了 {guess_count} 次，历史记录：{guess_history}")                         
                return guess_count                                               # 结束本轮，返回次数

        except ValueError:       
            print("输入不合法，请输入一个整数，或者输入 'q' 退出本轮。")     
'''


         





'''
def main():
    print("=" * 30)            
    print(" 欢迎来到 趣味猜数字游戏 ")
    print("=" * 30)

    total_rounds = 0                  # 轮数
    total_guesses = 0                 # 猜测次数

    while True:                      #一直玩 除非自己退出
        total_rounds += 1
        print(f"\n 第 {total_rounds} 轮游戏开始 ")
        guesses = play_one_round()
        total_guesses += guesses

        again = input("\n是否再来一轮 输入 y 继续，其他键退出：")
        if again.lower() != "y":
            break

    print("\n" + "=" * 30)
    print("游戏结束！")
    print(f"你一共玩了 {total_rounds} 轮")
    if total_rounds > 0:
        avg_guesses = total_guesses / total_rounds
        print(f"平均每轮猜测 {avg_guesses:.1f} 次")
    print("=" * 30)


if __name__ == "__main__":        #代码结尾习惯 方便被调用
    main()                 
'''

# -*- coding: utf-8 -*-
"""





冒险寻宝小游戏

"""


import random
import time

def start_game()->NONE:
    for i in range(101):           
        bar = '[' + '=' * (i // 2) + ' ' * (50 - i // 2) + ']'
        print(f"\r{bar} {i:3}%", end='',flush=True)             #使用flush输出更顺畅
        time.sleep(0.02)
    print("\n你好，游戏开始")

# 房间数据
cave_rooms = {             
    (1, 1): {"name": "入口大厅", "item": "火把", "trap": False, "desc": "你站在洞穴入口，地上有一根火把"},
    (1, 2): {"name": "侧室", "item": "地图碎片", "trap": False, "desc": "狭小的侧室，有一张地图碎片"},
    (2, 1): {"name": "陷阱房", "item": None, "trap": True, "desc": "松动的石板，小心陷阱"},
    (2, 2): {"name": "宝藏室", "item": "宝藏", "trap": False, "desc": "房间中央有一个宝箱"}
}

REWARD=5
DIRECTIONS = {
    "上": (-1, 0),  # x-1, y不变            #用字典封起来 不用else if
    "下": (1, 0),   # x+1, y不变
    "左": (0, -1),  # x不变, y-1
    "右": (0, 1)    # x不变, y+1
}


def treasure_generator()->None:
    while True:
        yield random.randint(1, 10)                          


def get_available_rooms(current_pos:tuple)->list[tuple]:
    x, y = current_pos         
    # 遍历DIRECTIONS的偏移量，不用手写x+1,y等
    directions = [(x + dx, y + dy) for dx, dy in DIRECTIONS.values()]
    available = [pos for pos in directions if pos in cave_rooms]     #判断directions里坐标在不在洞穴房间里
    return available                #不用filter和lambda

def main():
    start_game()

    while True:
        print("=" * 30)
        print("规则：探索洞穴房间，收集道具，躲避陷阱，找到宝藏即获胜")
        print("      输入方向（上/下/左/右）移动，输入 q 退出游戏")
        print("=" * 30)

        current_pos = (1, 1)  # 初始位置
        inventory = []        
        score = 0             
        treasure_gen = treasure_generator()

        while True:  
            room_info = cave_rooms[current_pos]
            print(f"\n 当前位置：{room_info['name']}")
            print(f" 描述：{room_info['desc']}")

           
            if room_info["trap"]:
                print("  触发陷阱 损失 5 分")
                score -= REWARD
                current_pos = (1, 1)
                continue

            # 收集道具
            if room_info["item"] and room_info["item"] not in inventory:
                inventory.append(room_info["item"])
                print(f" 收集到：{room_info['item']}")
                score += 10

           
            if room_info["item"] == "宝藏":
                treasure_count = next(treasure_gen)
                score += treasure_count * 5
                print(f"\n 恭喜你找到宝藏 获得 {treasure_count} 个金币，加分 {treasure_count * 5}！")
                print(f" 最终得分：{score}")
                print(f" 你的背包：{inventory}")
                break

           
            available_rooms = get_available_rooms(current_pos)
            print(f"\n  可移动的方向：")                                                  
            for pos in available_rooms:                        
                dx = pos[0] - current_pos[0]               
                dy = pos[1] - current_pos[1]
                # 反向查找：通过偏移量找方向名（更优雅）
                direction = [k for k, v in DIRECTIONS.items() if v == (dx, dy)][0]
                print(f"  - {direction}：{cave_rooms[pos]['name']}")

            
            user_input = input("\n请输入移动方向（上/下/左/右），或 q 退出：").lower()
            if user_input == "q":
                print(f"\n 游戏退出！最终得分：{score}")
                print(f" 你的背包：{inventory}")
                return  

           
            
            if user_input not in DIRECTIONS:
                print(" 输入错误！请输入 上/下/左/右 或 q")
                continue

            #保存移动前的坐标
            old_pos = current_pos  
            x, y = current_pos

            # 从字典取偏移量，计算新坐标
            dx, dy = DIRECTIONS[user_input]
            new_pos = (x + dx, y + dy)

            # try-except处理无效坐标
            try:
                cave_rooms[new_pos]
                current_pos = new_pos
            except KeyError:
                print(f" 已超出游戏范围 自动返回上一位置")
                current_pos = old_pos

        
        again = input("\n是否再来一轮(y/n)：").lower()
        if again != "y":
            print("游戏结束，再见")
            break  

if __name__ == "__main__":
    main()