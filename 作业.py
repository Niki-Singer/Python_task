import os
import random
import time


class Student:      #定义Student数据类
    """
    学生数据类，负责存储单个学生的基本信息。
    """

    def __init__(self, index, name, gender, class_name, student_id, college):
        self.index = index
        self.name = name
        self.gender = gender
        self.class_name = class_name
        self.student_id = student_id
        self.college = college
        self.seat_number = None     #提前增加一个座位号的属性，便于后面实现考场安排表的相关功能

    def __str__(self):          #规范打印格式
        return (f"--- 学生详细信息 ---\n"
                f"姓名：{self.name}\n"
                f"性别：{self.gender}\n"
                f"班级：{self.class_name}\n"
                f"学号：{self.student_id}\n"
                f"学院：{self.college}\n"
                f"--------------------")


class ExamSystem:
    """
    逻辑控制类，封装系统的核心功能。
    """

    def __init__(self, file_path):
        self.students_map = {}

        # 在初始化阶段直接读取文件
        with open(file_path, 'r', encoding='utf-8') as file:
            lines = file.readlines()    #读取跳过首行后的每一行数据
            for line in lines[1:]:
                data = line.strip().split()     #对每行数据以空格为分隔符进行分割读取
                if len(data) >= 6:
                    index, name, gender, class_name, s_id, college = data[:6]
                    new_student = Student(index, name, gender, class_name, s_id, college)
                    self.students_map[s_id] = new_student           #将每个学生的每个信息储存

        print(f"系统初始化成功：已载入 {len(self.students_map)} 名学生数据。")

    @staticmethod
    def validate_input_digit(input_str):
        """
        静态方法：校验输入是否为纯数字且非空。
        """
        return input_str.isdigit() and len(input_str) > 0  #第一个用于判断是否为纯数字，第二个用于判断是否为空，两个同时成立才是正确输入

    @staticmethod
    def get_current_time_str():
        """
        静态方法：使用 time 库获取格式化时间字符串。
        """
        return time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())         #获取时间并格式化打印，在考场安排表中实现时间输出功能

    def find_student_by_id(self):
        """
        功能1：交互式按学号查询功能
        """
        while True:
            search_id = input("\n请输入要查询的学号 (输入 'q' 退出查询): ").strip()

            if search_id.lower() == 'q':        #说明要退出这个功能，跳出当前功能模块
                break

            # 校验学号输入格式
            if not self.validate_input_digit(search_id):
                print("您的输入不符合要求，学号必须为纯数字，请重新输入。")          #校验是否符合输入要求，不符合的进行提醒并让用户再次输入
                continue

            student = self.students_map.get(search_id)

            if student:
                print(student)
            else:
                print(f"您的输入不符合要求，未找到学号为 '{search_id}' 的学生，请重新输入。")         #查询学号对应学生信息，返回查询结果

    def perform_random_roll_call(self):
        """
        功能2：随机点名功能（保持原样）。
        """
        total_count = len(self.students_map)

        while True:
            print(f"\n当前系统总人数：{total_count}")
            count_input = input("请输入需要随机点名的学生数量 (输入 'q' 退出点名): ").strip()

            if count_input.lower() == 'q':        #说明要退出这个功能，跳出当前功能模块
                break

            # 校验数量输入格式
            if not self.validate_input_digit(count_input):
                print("您的输入不符合要求，输入数量必须为纯数字，请重新输入。")          #校验是否符合输入要求，不符合的进行提醒并让用户再次输入
                continue

            num_to_pick = int(count_input)      #记录要抽取的人数

            # 校验数量范围
            if num_to_pick <= 0 or num_to_pick > total_count:
                print(f"您的输入不符合要求，数量必须在 1 到 {total_count} 之间，请重新输入。")           #如果人数超过总人数，提醒用户重新输入
            else:                                                                               #人数合法，进行随机抽取
                # 转换为列表进行不重复随机采样
                all_students = list(self.students_map.values())        #转换为列表
                selected_students = random.sample(all_students, num_to_pick)        #用random里的函数实现随机抽取

                print(f"\n--- 随机点名结果 ({num_to_pick}人) ---")                     #打印点名结果
                for i, student in enumerate(selected_students, 1):
                    print(f"[{i}] {student.name} | 学号: {student.student_id} | 班级: {student.class_name}")
                print("---------------------------------")
                break

    def generate_exam_arrangement(self):
        """
        功能3：生成考场安排表。
        1. 随机分配座位。
        2. 座位号统一为两位数输出。
        3. 按座位号升序写入文件。（这部分是我给AI拆解的过程指令）
        """
        if not self.students_map:               #排除特殊情况（空）
            print("数据为空，无法生成考场安排表。")
            return

        #转换为列表进行随机分配数字（座位号）
        student_list = list(self.students_map.values())          #转换为列表
        num_students = len(student_list)                        #记录学生人数

        # 随机分配 1 到 N 的座位号
        seats = list(range(1, num_students + 1))
        random.shuffle(seats)                                   #用random.shuffle（）打乱里面的元素，实现给每个人分配随机的座位
        for i in range(num_students):
            student_list[i].seat_number = seats[i]              #分配好作为以后将座位号存进原本的数据集，这样保证座位号成为了学生的属性之一，方便后续功能使用

        student_list.sort(key=lambda x: x.seat_number)          #按照座位号从小到大排序（规范打印的安排表）

        file_name = "考场安排表.txt"
        create_time = self.get_current_time_str()

#这是一个保护机制，当磁盘满了、文件被占用或者没有写入权限时，保证程序不会直接崩溃，而是跳到下面的except处理错误。
        try:
            with open(file_name, "w", encoding="utf-8") as f:           #打开文件并写入，并保证文件可以自动关闭
                f.write(f"生成时间：{create_time}\n")                     #输出生成时间
                for s in student_list:
                    # 座位号格式化为两位数字
                    formatted_seat = f"{s.seat_number:0>2}"
                    f.write(f"{formatted_seat} | {s.name} | {s.student_id}\n")      #格式化输出的表格
            print(f"\n[成功] 考场安排表已生成至：{os.path.abspath(file_name)}")         #输出文件生成路径
        except Exception as e:
            print(f"文件写入失败：{e}")        #处理错误

    def generate_admission_cards(self):
        """
        功能4：生成准考证目录与文件。
        在'准考证'文件夹下为每个学生生成 01.txt 等文件。
        """
        if not self.students_map:               #排除特殊情况（空）
            print("数据为空，无法生成准考证。")
            return

        # 检查是否已分配座位号
        student_list = list(self.students_map.values())
        if any(s.seat_number is None for s in student_list):
            print("检测到尚未分配座位，正在执行随机分配...")
            # 自动执行一次分配逻辑（逻辑同上，不加以赘述）
            seats = list(range(1, len(student_list) + 1))
            random.shuffle(seats)
            for i in range(len(student_list)):
                student_list[i].seat_number = seats[i]

        # 创建目录
        folder_name = "准考证"
        if not os.path.exists(folder_name):         #如果这个目录还不存在
            os.makedirs(folder_name)                #就创建储存准考证的目录

        try:
            for s in student_list:
                formatted_seat = f"{s.seat_number:0>2}"         #将座位号格式化规范化（命名的时候符合“01”“02”的规范化）
                file_path = os.path.join(folder_name, f"{formatted_seat}.txt")  #进行路径拼接，这种方式能兼容各种系统，将文件夹名和文件名组合成完整的路径

                with open(file_path, "w", encoding="utf-8") as f:       #在路径中创建准考证文件，按座位号给每个准考证文件命名
                    f.write(f"考场座位号：{formatted_seat}\n")            #准考证的信息
                    f.write(f"姓名：{s.name}\n")
                    f.write(f"学号：{s.student_id}\n")

            print(f"\n[成功] 准考证文件夹已更新，共生成 {len(student_list)} 份文件。")     #提示准考证生成成功，且为当前版本
        except Exception as e:                          #处理准考证生成失败的问题
            print(f"准考证文件生成失败：{e}")


# --- 程序主入口 ---
if __name__ == "__main__":
    target_file = "人工智能编程语言学生名单.txt"
    system = ExamSystem(target_file)

    while True:                 #告知对应操作，并且永远为真（直到用户输入“5”这个退出条件才在break中跳出循环，执行完整个程序）
        print("\n===== 学生信息与考场管理系统 =====")
        print("1. 按学号查询学生信息")
        print("2. 随机点名抽取")
        print("3. 生成考场安排表")
        print("4. 生成准考证目录与文件")
        print("5. 退出系统")
        print("==================================")

        user_choice = input("请选择操作序号 (1-5): ").strip()

        if user_choice == '1':          #输入1就调用查询操作的函数方法进行操作
            system.find_student_by_id()
        elif user_choice == '2':          #输入2就调用随机点名的函数方法进行操作
            system.perform_random_roll_call()
        elif user_choice == '3':          #输入3就调用生成考场安排表的函数方法进行操作
            system.generate_exam_arrangement()
        elif user_choice == '4':          #输入4就调用生成准考证的函数方法进行操作
            system.generate_admission_cards()
        elif user_choice == '5':          #输入5就结束功能，用break跳出循环
            print("程序已安全退出。")
            break
        else:
            print("您的输入不符合要求，序号必须为 1 到 5 之间的数字，请重新输入。")     #校验操作输入字符不符合要求，提醒重新输入