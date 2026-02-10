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


import random
import time
 

for i in range(101):           #假装在加载                                 
     bar = '[' + '=' * (i // 2) + ' ' * (50 - i // 2) + ']'
     print(f"\r{bar} {i:3}%", end='',flush=True)            #end=''不换行 flush=True 输出更平滑
     time.sleep(0.02)
print()

def main():
     print("你好")          





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


import random  # 别忘了加这个！生成随机金币需要

cave_rooms = {              #字典 元组：内层字典   使用字典存储不同情况
    (1, 1): {"name": "入口大厅", "item": "火把", "trap": False, "desc": "你站在洞穴入口，地上有一根火把"},
    (1, 2): {"name": "侧室", "item": "地图碎片", "trap": False, "desc": "狭小的侧室，张地图碎片"},
    (2, 1): {"name": "陷阱房", "item": None, "trap": True, "desc": "松动的石板，小心陷阱"},
    (2, 2): {"name": "宝藏室", "item": "宝藏", "trap": False, "desc": "房间中央有一个宝箱"}
}

def treasure_generator():
    while True:
        yield random.randint(1, 10)                           # 可以重复找宝藏 每次金币不同

def get_available_rooms(current_pos):
    x, y = current_pos         #当前坐标
    directions = [(x+1, y), (x-1, y), (x, y+1), (x, y-1)]
    available = filter(lambda pos: pos in cave_rooms, directions)  # filter使用lambda:后的规则 逐个检查当前坐标对应的四个方向的pos判断在不在房间里
    return list(available)                # 转列表方便展示

def main():
    # ↓ 新增：外层循环（控制多轮游戏）↓
    while True:
        print("=" * 30)
        print("规则：探索洞穴房间，收集道具，躲避陷阱，找到宝藏即获胜")
        print("      输入方向（上/下/左/右）移动，输入 q 退出游戏")
        print("=" * 30)

        current_pos = (1, 1)                  # 初始位置（元组）
        inventory = []                        # 背包：存储收集的道具
        score = 0                             # 分数
        treasure_gen = treasure_generator()  # 创建生成器，即一个存很多次金币的箱子  通过一次拿一次

        while True:  # 单局游戏循环
            room_info = cave_rooms[current_pos]
            print(f"\n 当前位置：{room_info['name']}")
            print(f" 描述：{room_info['desc']}")

            if room_info["trap"]:
                print("  触发陷阱 损失 5 分")   # 触发陷阱后强制回到入口
                score -= 5
                current_pos = (1, 1)
                continue

            if room_info["item"] and room_info["item"] not in inventory:
                inventory.append(room_info["item"])
                print(f" 收集到：{room_info['item']}")
                score += 10                            # 收集道具加分

            if room_info["item"] == "宝藏":
                treasure_count = next(treasure_gen)  # 调用生成器  拿箱子的下一次金币
                score += treasure_count * 5
                print(f"\n 恭喜你找到宝藏 获得 {treasure_count} 个金币，加分 {treasure_count * 5}！")
                print(f" 最终得分：{score}")
                print(f" 你的背包：{inventory}")
                break  # 退出单局循环

            # 显示可移动的房间  （迭代器遍历结果）
            available_rooms = get_available_rooms(current_pos)
            print(f"\n  可移动的方向：")                                                  
            for pos in available_rooms:                        
                dx = pos[0] - current_pos[0]               # 把坐标转成方向描述
                dy = pos[1] - current_pos[1]                #这个pos是上面的可进入房间函数传出来的
                if dx == 1:
                    direction = "下"
                elif dx == -1:
                    direction = "上"
                elif dy == 1:
                    direction = "右"
                elif dy == -1:
                    direction = "左"
                print(f"  - {direction}：{cave_rooms[pos]['name']}")       #告诉玩家相邻坐标是什么

            user_input = input("\n请输入移动方向（上/下/左/右），或 q 退出：").lower()
            if user_input == "q":
                print(f"\n 游戏退出！最终得分：{score}")
                print(f" 你的背包：{inventory}")
                return  # 直接结束main函数

            x, y = current_pos
            if user_input == "上":
                new_pos = (x-1, y)
            elif user_input == "下":
                new_pos = (x+1, y)
            elif user_input == "左":
                new_pos = (x, y-1)
            elif user_input == "右":
                new_pos = (x, y+1)
            else:
                print(" 输入错误！请输入 上/下/左/右 或 q")
                continue

            if new_pos in cave_rooms:  #是否还在房间里
                current_pos = new_pos
            else:
                print(" 这个方向没有房间 重新选择移动方向")

        # ↓ 调整缩进：把这几行放到外层循环里（和单局while同级）↓
        again = input("\n是否再来一轮(y/n)：").lower()
        if again != "y":
            print("游戏结束，再见！")
            break  # 现在break有对应的循环了（外层while）

if __name__ == "__main__":
    main()


