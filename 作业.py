import os
import random


class Student:
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

    def __str__(self):
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
            lines = file.readlines()
            # 解析跳过首行后的每一行数据
            for line in lines[1:]:
                data = line.strip().split()
                if len(data) >= 6:
                    index, name, gender, class_name, s_id, college = data[:6]
                    new_student = Student(index, name, gender, class_name, s_id, college)
                    self.students_map[s_id] = new_student

        print(f"系统初始化成功：已载入 {len(self.students_map)} 名学生数据。")

    @staticmethod
    def validate_input_digit(input_str):
        """
        静态方法：校验输入是否为纯数字且非空。
        """
        return input_str.isdigit() and len(input_str) > 0

    def find_student_by_id(self):
        """
        交互式按学号查询功能。
        """
        while True:
            search_id = input("\n请输入要查询的学号 (输入 'q' 退出查询): ").strip()

            if search_id.lower() == 'q':
                break

            # 校验学号输入格式
            if not self.validate_input_digit(search_id):
                print("您的输入不符合要求，学号必须为纯数字，请重新输入。")
                continue

            student = self.students_map.get(search_id)

            if student:
                print(student)
            else:
                print(f"您的输入不符合要求，未找到学号为 '{search_id}' 的学生，请重新输入。")

    def perform_random_roll_call(self):
        """
        随机点名功能：包含输入异常处理及数量上限限制。
        """
        total_count = len(self.students_map)

        while True:
            print(f"\n当前系统总人数：{total_count}")
            count_input = input("请输入需要随机点名的学生数量 (输入 'q' 退出点名): ").strip()

            if count_input.lower() == 'q':
                break

            # 校验数量输入格式
            if not self.validate_input_digit(count_input):
                print("您的输入不符合要求，输入数量必须为纯数字，请重新输入。")
                continue

            num_to_pick = int(count_input)

            # 校验数量范围
            if num_to_pick <= 0 or num_to_pick > total_count:
                print(f"您的输入不符合要求，数量必须在 1 到 {total_count} 之间，请重新输入。")
            else:
                # 转换为列表进行不重复随机采样
                all_students = list(self.students_map.values())
                selected_students = random.sample(all_students, num_to_pick)

                print(f"\n--- 随机点名结果 ({num_to_pick}人) ---")
                for i, student in enumerate(selected_students, 1):
                    print(f"[{i}] {student.name} | 学号: {student.student_id} | 班级: {student.class_name}")
                print("---------------------------------")
                break


# --- 程序主入口 ---
if __name__ == "__main__":
    target_file = "人工智能编程语言学生名单.txt"

    # 实例化即完成数据加载
    system = ExamSystem(target_file)

    while True:
        print("\n===== 学生信息与考场管理系统 =====")
        print("1. 按学号查询学生信息")
        print("2. 随机点名抽取")
        print("3. 退出系统")
        print("==================================")

        user_choice = input("请选择操作序号 (1-3): ").strip()

        if user_choice == '1':
            system.find_student_by_id()
        elif user_choice == '2':
            system.perform_random_roll_call()
        elif user_choice == '3':
            print("程序已安全退出。")
            break
        else:
            print("您的输入不符合要求，序号必须为 1, 2 或 3，请重新输入。")