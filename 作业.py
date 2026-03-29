import os


class Student:
    """
    学生数据类，负责存储单个学生的基本信息。
    """
#为Student类添加初始化方法和基本属性
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
    def __init__(self):
        # 使用字典存储学生对象，键为学号，方便快速查找
        self.students_map = {}

    @staticmethod
    def validate_student_id(student_id_str):
        """
        进行基础学号校验，确保输入不为空且为纯数字。
        """
        return student_id_str.isdigit() and len(student_id_str) > 0

    def load_students_from_file(self, file_path):
        """
        从指定文本文件读入学生名单。
        """
        if not os.path.exists(file_path):
            print(f"错误：找不到文件 '{file_path}'，请检查文件路径。")
            return False

        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                # 跳过表头行
                lines = file.readlines()
                for line in lines[1:]:
                    # 按照制表符或空格分割数据
                    data = line.strip().split()
                    if len(data) >= 6:
                        index, name, gender, class_name, s_id, college = data[:6]
                        # 实例化学生对象
                        new_student = Student(index, name, gender, class_name, s_id, college)
                        # 存入映射表
                        self.students_map[s_id] = new_student
            print(f"系统提示：成功导入 {len(self.students_map)} 名学生信息。")
            return True
        except Exception as e:
            print(f"读取文件时发生未知错误: {e}")
            return False

    def find_student_by_id(self):
        """
        交互式查找功能。
        """
        while True:
            search_id = input("\n请输入要查询的学号 (输入 'q' 退出): ").strip()

            if search_id.lower() == 'q':
                print("系统已退出。")
                break

            # 调用静态方法进行格式校验
            if not self.validate_student_id(search_id):
                print("您的输入不符合输入要求，输入学号必须为纯数字，请重新输入。")
                continue

            # 在字典中检索
            student = self.students_map.get(search_id)

            if student:
                print(student)
            else:
                print(f"抱歉，未找到学号为 '{search_id}' 的学生信息，请核对后再次尝试。")


# --- 程序入口 ---
if __name__ == "__main__":
    # 1. 实例化系统
    system = ExamSystem()

    # 2. 加载数据 (请确保该文件名与代码在同一目录下)
    data_file = "人工智能编程语言学生名单.txt"

    # 第一次运行前，如果文件不存在，这里会提示错误
    if system.load_students_from_file(data_file):
        # 3. 开启查询功能
        system.find_student_by_id()