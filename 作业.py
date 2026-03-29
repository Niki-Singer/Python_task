import os
import random
import time


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
        # 新增属性：座位号，默认为None，由系统逻辑分配
        self.seat_number = None

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

        if not os.path.exists(file_path):
            print(f"警告：找不到文件 {file_path}，请确保路径正确。")
            return

        # 初始化数据加载
        with open(file_path, 'r', encoding='utf-8') as file:
            lines = file.readlines()
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
        静态方法：校验输入是否为纯数字。
        """
        return input_str.isdigit() and len(input_str) > 0

    @staticmethod
    def format_current_time():
        """
        静态方法：使用time库获取当前格式化时间。
        """
        time_struct = time.localtime(time.time())
        return time.strftime("%Y-%m-%d %H:%M:%S", time_struct)

    def find_student_by_id(self):
        """
        按学号查询学生详细信息。
        """
        while True:
            search_id = input("\n请输入要查询的学号 (输入 'q' 退出查询): ").strip()
            if search_id.lower() == 'q':
                break

            if not self.validate_input_digit(search_id):
                print("学号格式不正确，请输入纯数字。")
                continue

            student = self.students_map.get(search_id)
            print(student if student else f"未找到学号为 '{search_id}' 的学生。")

    def perform_random_roll_call(self):
        """
        随机点名功能。
        """
        total_count = len(self.students_map)
        while True:
            count_input = input(f"\n当前总人数 {total_count}，请输入点名人数 (输入 'q' 退出): ").strip()
            if count_input.lower() == 'q':
                break

            if not self.validate_input_digit(count_input):
                print("请输入有效的数字数量。")
                continue

            num_to_pick = int(count_input)
            if 0 < num_to_pick <= total_count:
                all_students = list(self.students_map.values())
                selected = random.sample(all_students, num_to_pick)
                print(f"\n--- 随机点名结果 ---")
                for i, s in enumerate(selected, 1):
                    print(f"[{i}] {s.name} ({s.student_id})")
                break
            else:
                print(f"输入范围错误，应在 1-{total_count} 之间。")

    def generate_exam_arrangement(self):
        """
        生成考场安排表：
        1. 随机分配座位号。
        2. 按座位号从小到大排序。
        3. 输出文件，包含生成时间。
        """
        if not self.students_map:
            print("数据为空，无法生成安排表。")
            return

        # 1. 获取所有学生对象列表
        student_list = list(self.students_map.values())
        num_students = len(student_list)

        # 2. 生成 1 到 N 的随机座位号序列
        seat_indices = list(range(1, num_students + 1))
        random.shuffle(seat_indices)

        # 3. 将座位号赋予学生对象
        for i in range(num_students):
            student_list[i].seat_number = seat_indices[i]

        # 4. 关键：按照座位号 (seat_number) 从小到大排序
        # 使用 lambda 表达式指定排序关键字
        student_list.sort(key=lambda x: x.seat_number)

        # 5. 写入文件
        file_path = "考场安排表.txt"
        current_time_str = self.format_current_time()

        try:
            with open(file_path, "w", encoding="utf-8") as f:
                # 写入第一行时间
                f.write(f"生成时间：{current_time_str}\n")

                # 遍历排序后的学生列表，按格式输出
                for student in student_list:
                    line = f"{student.seat_number} | {student.name} | {student.student_id}\n"
                    f.write(line)

            print(f"\n[成功] 考场安排表已生成！")
            print(f"保存位置：{os.path.abspath(file_path)}")
        except Exception as e:
            print(f"文件写入失败，错误信息：{e}")


# --- 程序主入口 ---
if __name__ == "__main__":
    target_file = "人工智能编程语言学生名单.txt"
    system = ExamSystem(target_file)

    while True:
        print("\n===== 学生信息与考场管理系统 =====")
        print("1. 按学号查询学生信息")
        print("2. 随机点名抽取")
        print("3. 生成考场安排表")
        print("4. 退出系统")
        print("==================================")

        user_choice = input("请选择操作序号 (1-4): ").strip()

        if user_choice == '1':
            system.find_student_by_id()
        elif user_choice == '2':
            system.perform_random_roll_call()
        elif user_choice == '3':
            system.generate_exam_arrangement()
        elif user_choice == '4':
            print("系统已退出。")
            break
        else:
            print("输入无效，请输入 1-4 之间的数字。")